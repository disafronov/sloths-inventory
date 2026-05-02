"""Tests for ``common.application_groups``."""

import pytest
from django.apps import apps
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.test import RequestFactory, TestCase

from common.admin import ApplicationGroupProtectedGroupAdmin
from common.application_groups import (
    EDITOR_GROUP_NAME,
    STAFF_GROUP_NAME,
    enforce_application_groups,
    is_application_group,
    sync_user_staff_group_membership,
)
from inventory.models import Item

User = get_user_model()


@pytest.mark.django_db
def test_application_groups_exist_after_migrations_without_manual_enforce() -> None:
    """
    ``post_migrate`` must seed Staff/Editor during test DB setup.

    Regression guard: enforcement must not rely on ``AppConfig.ready()`` calling
    ``enforce_application_groups()`` (that triggers Django's DB-during-init warning).
    """

    assert Group.objects.filter(name=STAFF_GROUP_NAME).exists()
    assert Group.objects.filter(name=EDITOR_GROUP_NAME).exists()


@pytest.mark.django_db
def test_enforcer_creates_application_groups() -> None:
    enforce_application_groups()
    names = set(
        Group.objects.filter(
            name__in=(STAFF_GROUP_NAME, EDITOR_GROUP_NAME)
        ).values_list("name", flat=True)
    )
    assert names == {STAFF_GROUP_NAME, EDITOR_GROUP_NAME}


@pytest.mark.django_db
def test_enforcer_idempotent() -> None:
    enforce_application_groups()
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    first = set(staff.permissions.values_list("pk", flat=True))
    enforce_application_groups()
    second = set(staff.permissions.values_list("pk", flat=True))
    assert first == second


@pytest.mark.django_db
def test_enforcer_attaches_new_default_permissions_after_recreate() -> None:
    """
    ``create_permissions`` uses ``bulk_create`` (no ``post_save`` per row).

    ``enforce_application_groups()`` must still attach recreated default rows.
    """

    enforce_application_groups()
    ct = ContentType.objects.get_for_model(Item)
    perm = Permission.objects.get(content_type=ct, codename="view_item")
    perm.delete()

    create_permissions(apps.get_app_config("inventory"), verbosity=0)
    enforce_application_groups()

    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    editor = Group.objects.get(name=EDITOR_GROUP_NAME)
    new_perm = Permission.objects.get(content_type=ct, codename="view_item")
    assert staff.permissions.filter(pk=new_perm.pk).exists()
    assert editor.permissions.filter(pk=new_perm.pk).exists()


@pytest.mark.django_db
def test_staff_has_view_only_and_editor_has_crud_for_project_models() -> None:
    enforce_application_groups()
    ct = ContentType.objects.get_for_model(Item)
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    editor = Group.objects.get(name=EDITOR_GROUP_NAME)
    assert staff.permissions.filter(content_type=ct, codename="view_item").exists()
    assert not staff.permissions.filter(content_type=ct, codename="add_item").exists()
    for codename in ("add_item", "change_item", "delete_item", "view_item"):
        assert editor.permissions.filter(content_type=ct, codename=codename).exists()


@pytest.mark.django_db
def test_add_logentry_on_both_groups() -> None:
    enforce_application_groups()
    ct = ContentType.objects.get_for_model(LogEntry)
    log_perm = Permission.objects.get(content_type=ct, codename="add_logentry")
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    editor = Group.objects.get(name=EDITOR_GROUP_NAME)
    assert staff.permissions.filter(pk=log_perm.pk).exists()
    assert editor.permissions.filter(pk=log_perm.pk).exists()


@pytest.mark.django_db
def test_is_staff_assigns_staff_group() -> None:
    enforce_application_groups()
    with TestCase.captureOnCommitCallbacks(execute=True):
        user = User.objects.create_user(
            username="staffer",
            email="staffer@example.com",
            password="x",
            is_staff=True,
            is_superuser=False,
        )
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    assert staff.user_set.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_is_staff_false_removes_staff_group() -> None:
    enforce_application_groups()
    with TestCase.captureOnCommitCallbacks(execute=True):
        user = User.objects.create_user(
            username="nostaff",
            email="nostaff@example.com",
            password="x",
            is_staff=True,
            is_superuser=False,
        )
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    assert staff.user_set.filter(pk=user.pk).exists()
    with TestCase.captureOnCommitCallbacks(execute=True):
        user.is_staff = False
        user.save()
    assert not staff.user_set.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_superuser_skips_staff_membership_signal() -> None:
    enforce_application_groups()
    with TestCase.captureOnCommitCallbacks(execute=True):
        user = User.objects.create_user(
            username="su",
            email="su@example.com",
            password="x",
            is_staff=True,
            is_superuser=True,
        )
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    assert not staff.user_set.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_sync_user_staff_group_membership_superuser_noop() -> None:
    """Direct call: superusers are not added or removed from Staff."""

    enforce_application_groups()
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    user = User.objects.create_user(
        username="su2",
        email="su2@example.com",
        password="x",
        is_staff=True,
        is_superuser=True,
    )
    staff.user_set.add(user)
    sync_user_staff_group_membership(user)
    assert staff.user_set.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_admin_blocks_change_delete_for_application_groups_superuser() -> None:
    enforce_application_groups()
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    other = Group.objects.create(name="CustomAdmins")

    su = User.objects.create_user(
        username="root",
        email="root@example.com",
        password="x",
        is_superuser=True,
    )
    rf = RequestFactory()
    request = rf.get("/admin/")
    request.user = su

    model_admin = admin.site._registry[Group]
    assert isinstance(model_admin, ApplicationGroupProtectedGroupAdmin)
    assert model_admin.has_change_permission(request, staff) is False
    assert model_admin.has_delete_permission(request, staff) is False
    assert model_admin.has_change_permission(request, other) is True
    assert model_admin.has_delete_permission(request, other) is True


@pytest.mark.django_db
def test_is_application_group_helper() -> None:
    assert is_application_group(STAFF_GROUP_NAME) is True
    assert is_application_group(Group(name=EDITOR_GROUP_NAME)) is True
    assert is_application_group("Custom") is False


@pytest.mark.django_db
def test_staff_group_restored_after_save_m2m_style_groups_clear() -> None:
    """
    ``ModelAdmin`` saves the user before ``form.save_m2m()`` for ``groups``.

    Clearing ``groups`` inside the same ``atomic`` block must not drop Staff
    once callbacks run after commit.
    """

    enforce_application_groups()
    with TestCase.captureOnCommitCallbacks(execute=True):
        with transaction.atomic():
            user = User.objects.create_user(
                username="adminorder",
                email="adminorder@example.com",
                password="x",
                is_staff=True,
                is_superuser=False,
            )
            user.groups.clear()
    staff = Group.objects.get(name=STAFF_GROUP_NAME)
    assert staff.user_set.filter(pk=user.pk).exists()
