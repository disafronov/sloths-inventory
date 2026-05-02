"""
Application-defined auth groups (Staff, Editor) and permission enforcement.

These groups are managed only via ``enforce_application_groups()`` and related
signals (``post_migrate`` runs the enforcer for every installed app per ``migrate``,
idempotent) — not through the Django admin for the groups themselves.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable

from django.apps import AppConfig, apps
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import router, transaction
from django.db.models import Model
from django.db.models.signals import post_delete, post_migrate, post_save
from django.db.utils import OperationalError, ProgrammingError

# Fixed display names for application-managed groups (not translated: stable keys).
STAFF_GROUP_NAME = "Staff"
EDITOR_GROUP_NAME = "Editor"

APPLICATION_GROUP_NAMES: frozenset[str] = frozenset(
    {STAFF_GROUP_NAME, EDITOR_GROUP_NAME}
)

_run_lock = threading.Lock()
# Re-entrancy guard: ``Group.save`` / ``permissions.set`` can fire signals that call
# ``enforce_application_groups()`` again. The lock is not held across the whole body
# (only around the flag flip) so nested calls can enter, see ``True``, and return
# immediately without deadlocking.
#
# ``finally`` clears the flag for normal Python exits (including exceptions). A
# ``SIGKILL``-style death can skip ``finally`` in that process, but a new worker loads
# fresh module state; there is no long-lived shared memory requirement across kills.
_enforce_running = False


def is_application_group(group: Group | str) -> bool:
    """Return True if ``group`` is one of the code-managed application groups."""

    name = group if isinstance(group, str) else group.name
    return name in APPLICATION_GROUP_NAMES


def _iter_project_app_configs() -> Iterable[AppConfig]:
    """
    Yield installed app configs that belong to first-party code.

    Excludes everything under the ``django.`` namespace (contrib apps, auth,
    admin, sessions, etc.).
    """

    for app_config in apps.get_app_configs():
        if app_config.name.startswith("django."):
            continue
        yield app_config


def _iter_project_models() -> Iterable[type[Model]]:
    """Concrete and proxy models from project apps (no auto-created M2M tables)."""

    for app_config in _iter_project_app_configs():
        yield from app_config.get_models(include_auto_created=False)


def _standard_codenames_for_model(model: type[Model]) -> tuple[str, str, str, str]:
    """Default Django auth codenames (add/change/delete/view) for ``model``."""

    mn = model._meta.model_name
    return (f"add_{mn}", f"change_{mn}", f"delete_{mn}", f"view_{mn}")


def _permission_pks_for_project_models(*, staff_view_only: bool) -> set[int]:
    """
    Collect primary keys of ``Permission`` rows for all project models.

    When ``staff_view_only`` is True, only ``view_*`` permissions are included.
    """

    wanted: set[int] = set()
    for model in _iter_project_models():
        content_type = ContentType.objects.get_for_model(
            model, for_concrete_model=False
        )
        codenames: tuple[str, ...]
        if staff_view_only:
            codenames = (f"view_{model._meta.model_name}",)
        else:
            codenames = _standard_codenames_for_model(model)
        qs = Permission.objects.filter(
            content_type=content_type, codename__in=codenames
        )
        wanted.update(qs.values_list("pk", flat=True))
    return wanted


def _add_logentry_permission_pk() -> int:
    """Return the PK of ``admin.add_logentry`` (LogEntry / admin log)."""

    ct = ContentType.objects.get_for_model(LogEntry)
    return Permission.objects.values_list("pk", flat=True).get(
        content_type=ct, codename="add_logentry"
    )


def enforce_application_groups() -> None:
    """
    Ensure Staff and Editor groups exist and hold the correct permissions.

    Idempotent: repeated runs converge to the same permission sets. Safe to call
    from signals; re-entrant calls are ignored to avoid recursion when saving
    ``Group`` during enforcement.

    See module-level notes on ``_run_lock`` / ``_enforce_running`` for why the lock
    is not held for the full function body.
    """

    global _enforce_running
    with _run_lock:
        if _enforce_running:
            return
        _enforce_running = True
    try:
        logentry_pk = {_add_logentry_permission_pk()}
        staff_pks = (
            _permission_pks_for_project_models(staff_view_only=True) | logentry_pk
        )
        editor_pks = (
            _permission_pks_for_project_models(staff_view_only=False) | logentry_pk
        )

        staff_group, _ = Group.objects.get_or_create(name=STAFF_GROUP_NAME)
        editor_group, _ = Group.objects.get_or_create(name=EDITOR_GROUP_NAME)

        staff_group.permissions.set(Permission.objects.filter(pk__in=staff_pks))
        editor_group.permissions.set(Permission.objects.filter(pk__in=editor_pks))
    finally:
        with _run_lock:
            _enforce_running = False


def sync_user_staff_group_membership(user: AbstractUser) -> None:
    """
    Keep membership in the Staff group aligned with ``is_staff``.

    Superusers are left untouched (no add/remove of Staff) so promotion paths
    stay predictable for callers that rely on explicit group cleanup.
    """

    if user.is_superuser:
        return
    if not user.pk:
        return

    try:
        staff_group = Group.objects.get(name=STAFF_GROUP_NAME)
    except Group.DoesNotExist:
        enforce_application_groups()
        try:
            staff_group = Group.objects.get(name=STAFF_GROUP_NAME)
        except Group.DoesNotExist:
            return

    if user.is_staff:
        user.groups.add(staff_group)
    else:
        user.groups.remove(staff_group)


def _on_user_post_save(
    sender: type[AbstractUser],
    instance: AbstractUser,
    created: bool,
    **kwargs: object,
) -> None:
    """
    Defer sync until after the surrounding DB transaction commits.

    Django admin calls ``save_model()`` (``User.save()``) before
    ``save_related()`` / ``form.save_m2m()`` for ``groups``. A synchronous
    ``post_save`` hook would add Staff and then ``save_m2m`` would overwrite
    ``groups`` from POST data (often without Staff), dropping membership.
    """

    del created, kwargs
    if not instance.pk:
        return
    pk = instance.pk
    using = router.db_for_write(sender)

    def _sync_after_commit() -> None:
        fresh = sender.objects.using(using).get(pk=pk)
        sync_user_staff_group_membership(fresh)

    transaction.on_commit(_sync_after_commit)


def _on_group_post_save(
    sender: type[Group], instance: Group, created: bool, **kwargs: object
) -> None:
    del sender, instance, created, kwargs
    enforce_application_groups()


def _on_group_post_delete(
    sender: type[Group], instance: Group, **kwargs: object
) -> None:
    del sender, instance, kwargs
    enforce_application_groups()


def _on_permission_post_save(
    sender: type[Permission], instance: Permission, created: bool, **kwargs: object
) -> None:
    del sender, instance, created, kwargs
    enforce_application_groups()


def _on_permission_post_delete(
    sender: type[Permission], instance: Permission, **kwargs: object
) -> None:
    del sender, instance, kwargs
    enforce_application_groups()


def _on_post_migrate(sender: AppConfig, **kwargs: object) -> None:
    """
    Re-sync groups after each app emits ``post_migrate`` (during ``migrate``).

    Django emits ``post_migrate`` once per installed app, in order. Early passes may
    run before ``django.contrib.auth.management.create_permissions`` has bulk-created
    permissions for later apps (no per-row signals), so ``enforce_application_groups()``
    is **idempotent** and must run again on later apps until the final pass converges.

    We do not filter on ``sender``: tying this only to ``common`` could run once
    before ``inventory`` permissions exist and leave Staff/Editor under-assigned
    until an unrelated manual trigger.

    ``AppConfig.ready()`` is avoided here: querying the DB during ``ready()`` warns
    because ``django.apps.apps.ready`` is still false while other apps' hooks run.
    """

    del sender, kwargs
    try:
        enforce_application_groups()
    except (OperationalError, ProgrammingError):
        # Mirrors the old ``ready()`` guard: empty or partial DB during odd setups.
        pass


def connect_application_group_signals() -> None:
    """
    Register signal handlers for enforcement and Staff membership.

    Uses ``dispatch_uid`` so duplicate registration does not occur if
    ``AppConfig.ready()`` runs more than once (e.g. autoreloader).
    """

    from django.contrib.auth import get_user_model

    post_migrate.connect(
        _on_post_migrate,
        dispatch_uid="common.application_groups.post_migrate",
    )

    user_model = get_user_model()
    post_save.connect(
        _on_user_post_save,
        sender=user_model,
        dispatch_uid="common.application_groups.user_post_save",
    )
    post_save.connect(
        _on_group_post_save,
        sender=Group,
        dispatch_uid="common.application_groups.group_post_save",
    )
    post_delete.connect(
        _on_group_post_delete,
        sender=Group,
        dispatch_uid="common.application_groups.group_post_delete",
    )
    post_save.connect(
        _on_permission_post_save,
        sender=Permission,
        dispatch_uid="common.application_groups.permission_post_save",
    )
    post_delete.connect(
        _on_permission_post_delete,
        sender=Permission,
        dispatch_uid="common.application_groups.permission_post_delete",
    )
