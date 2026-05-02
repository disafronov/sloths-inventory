"""Tests for ``common.application_groups`` signal helpers and edge cases."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.utils import OperationalError, ProgrammingError

from common.application_groups import (
    STAFF_GROUP_NAME,
    _on_group_post_delete,
    _on_permission_post_delete,
    _on_permission_post_save,
    _on_post_migrate,
    _on_user_post_save,
    enforce_application_groups,
    sync_user_staff_group_membership,
)


@pytest.mark.django_db
def test_sync_user_staff_group_membership_superuser_noop() -> None:
    enforce_application_groups()
    user = get_user_model().objects.create_superuser(
        username="sync-su",
        email="sync-su@example.com",
        password="password",
    )
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    staff.user_set.add(user)
    sync_user_staff_group_membership(user)
    assert staff.user_set.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_sync_user_staff_group_membership_unsaved_user_noop() -> None:
    enforce_application_groups()
    user = get_user_model()(username="unsaved-sync")
    sync_user_staff_group_membership(user)


@pytest.mark.django_db
def test_sync_user_staff_group_membership_returns_when_staff_group_missing_twice() -> (
    None
):
    """
    If ``Staff`` is still missing after ``enforce_application_groups()``, bail out.

    ``Group`` deletion fires ``post_delete`` handlers that would normally recreate
    ``Staff``; those calls are patched so the group stays absent and the fallback
    path in ``sync_user_staff_group_membership`` is exercised.
    """

    enforce_application_groups()
    with patch(
        "common.application_groups.enforce_application_groups",
        autospec=True,
    ) as mock_enforce:
        Group.objects.filter(name=STAFF_GROUP_NAME).delete()
        user = get_user_model().objects.create_user(
            username="sync-miss",
            email="sync-miss@example.com",
            password="password",
            is_staff=True,
        )
        sync_user_staff_group_membership(user)
    # One call from the delete signal handler, one from ``sync`` after the first miss.
    assert mock_enforce.call_count == 2


@pytest.mark.django_db
def test_on_user_post_save_skips_without_primary_key() -> None:
    user = get_user_model()(username="noid")
    _on_user_post_save(get_user_model(), user, created=True)


@pytest.mark.django_db
def test_on_group_post_delete_triggers_enforce() -> None:
    enforce_application_groups()
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    with patch(
        "common.application_groups.enforce_application_groups",
        autospec=True,
    ) as mock_enforce:
        _on_group_post_delete(Group, staff)
    mock_enforce.assert_called_once()


@pytest.mark.django_db
def test_on_permission_post_save_and_delete_trigger_enforce() -> None:
    perm = Permission.objects.first()
    assert perm is not None
    with patch(
        "common.application_groups.enforce_application_groups",
        autospec=True,
    ) as mock_enforce:
        _on_permission_post_save(Permission, perm, created=False)
        _on_permission_post_delete(Permission, perm)
    assert mock_enforce.call_count == 2


@pytest.mark.django_db
def test_on_post_migrate_swallows_database_errors() -> None:
    with patch(
        "common.application_groups.enforce_application_groups",
        side_effect=OperationalError("boom"),
    ):
        _on_post_migrate(type("App", (), {"name": "dummy"})(), **{})


@pytest.mark.django_db
def test_on_post_migrate_runs_enforce_when_database_ok() -> None:
    with patch(
        "common.application_groups.enforce_application_groups",
        autospec=True,
    ) as mock_enforce:
        _on_post_migrate(type("App", (), {"name": "dummy"})(), **{})
    mock_enforce.assert_called_once()


@pytest.mark.django_db
def test_on_post_migrate_swallows_programming_error() -> None:
    with patch(
        "common.application_groups.enforce_application_groups",
        side_effect=ProgrammingError("boom"),
    ):
        _on_post_migrate(type("App", (), {"name": "dummy"})(), **{})
