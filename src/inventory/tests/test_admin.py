from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.admin import ItemAdmin, OperationAdmin
from inventory.models import Item, Operation


def _staff_user_with_item_admin_permissions(username: str) -> Any:
    """Non-superuser staff with inventory item change/delete/view for admin tests."""

    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="password",
        is_staff=True,
    )
    content_type = ContentType.objects.get_for_model(Item)
    for codename in ("change_item", "delete_item", "view_item"):
        user.user_permissions.add(
            Permission.objects.get(content_type=content_type, codename=codename)
        )
    return user


def _staff_view_only_item(username: str) -> Any:
    """Staff with ``view_item`` only (no ``change_item`` / ``delete_item``)."""

    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="password",
        is_staff=True,
    )
    content_type = ContentType.objects.get_for_model(Item)
    user.user_permissions.add(
        Permission.objects.get(content_type=content_type, codename="view_item")
    )
    return user


def _staff_view_only_operation(username: str) -> Any:
    """Staff with ``view_operation`` only."""

    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="password",
        is_staff=True,
    )
    content_type = ContentType.objects.get_for_model(Operation)
    user.user_permissions.add(
        Permission.objects.get(content_type=content_type, codename="view_operation")
    )
    return user


def _staff_user_with_operation_admin_permissions(username: str) -> Any:
    """Non-superuser staff with change/delete/view on ``Operation`` for admin tests."""

    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="password",
        is_staff=True,
    )
    content_type = ContentType.objects.get_for_model(Operation)
    for codename in ("change_operation", "delete_operation", "view_operation"):
        user.user_permissions.add(
            Permission.objects.get(content_type=content_type, codename=codename)
        )
    return user


@pytest.mark.django_db
def test_item_admin_current_fields_are_dash_without_operations() -> None:
    """
    With no operations, ``ItemAdmin`` ``current_*`` display methods show the hyphen
    placeholder documented on ``BaseAdmin._format_empty_value``. The test uses the
    public ``ModelAdmin`` API only (not HTML), so Django admin template changes do
    not break it.
    """

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    item = Item.objects.create(inventory_number="INV-EMPTY-CURRENT", device=device)
    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)

    assert admin_obj.current_status(item) == "-"
    assert admin_obj.current_location(item) == "-"
    assert admin_obj.current_responsible(item) == "-"


@pytest.mark.django_db
def test_item_admin_current_fields_and_fieldsets() -> None:
    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-010", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)

    assert admin_obj.current_status(item) == "In stock"
    assert admin_obj.current_location(item) == "Moscow"
    assert admin_obj.current_responsible(item) == str(responsible)

    rf = RequestFactory()
    request = rf.get("/")
    fieldsets = admin_obj.get_fieldsets(request, obj=item)

    # We expect an "Operation" section (localized title) to be inserted
    # with the current_* fields.
    assert len(fieldsets) >= 3
    operation_fields = fieldsets[2][1]["fields"]
    assert "current_status" in operation_fields
    assert "current_responsible" in operation_fields
    assert "current_location" in operation_fields


@pytest.mark.django_db
def test_operation_admin_responsible_display() -> None:
    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-011", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)

    assert admin_obj.get_responsible_display(op) == responsible.get_full_name()


@pytest.mark.django_db
def test_operation_admin_allows_edit_only_for_latest_operation() -> None:
    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-012", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    op2 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    user = get_user_model().objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )
    request.user = user

    assert admin_obj.has_change_permission(request, obj=op1) is False
    assert admin_obj.has_delete_permission(request, obj=op1) is False

    assert admin_obj.has_change_permission(request, obj=op2) is True
    assert admin_obj.has_delete_permission(request, obj=op2) is True


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_denies_change_after_correction_window() -> None:
    """Staff lose edit/delete on the latest op once the correction window ends."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-012-WINDOW", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )
    op.refresh_from_db()

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_operation_admin_permissions("staff-op-window")

    assert admin_obj.has_change_permission(request, obj=op) is False
    assert admin_obj.has_delete_permission(request, obj=op) is False


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_superuser_keeps_change_after_correction_window() -> None:
    """Superusers can still change/delete the latest operation after the window."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-OP-SU-WIN", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )
    op.refresh_from_db()

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-op-su-win",
        email="admin-op-su-win@example.com",
        password="password",
    )

    assert admin_obj.has_change_permission(request, obj=op) is True
    assert admin_obj.has_delete_permission(request, obj=op) is True


@pytest.mark.django_db
def test_operation_admin_permission_short_circuits() -> None:
    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-013", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()

    # If obj is None, we should fall back to the base permission check.
    request_any = rf.get("/")
    superuser = get_user_model().objects.create_superuser(
        username="admin2", email="admin2@example.com", password="password"
    )
    request_any.user = superuser
    assert admin_obj.has_change_permission(request_any, obj=None) is True
    assert admin_obj.has_delete_permission(request_any, obj=None) is True

    # If base permission check fails, we should short-circuit to False.
    request_denied = rf.get("/")
    normal_user = get_user_model().objects.create_user(
        username="user", email="user@example.com", password="password"
    )
    request_denied.user = normal_user
    assert admin_obj.has_change_permission(request_denied, obj=op) is False
    assert admin_obj.has_delete_permission(request_denied, obj=op) is False


@pytest.mark.django_db
def test_item_admin_queryset_is_select_related() -> None:
    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)
    rf = RequestFactory()
    request = rf.get("/")

    qs = admin_obj.get_queryset(request)
    assert isinstance(qs, QuerySet)
    assert "device" in qs.query.select_related


@pytest.mark.django_db
def test_operation_admin_queryset_is_select_related() -> None:
    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")

    qs = admin_obj.get_queryset(request)
    assert isinstance(qs, QuerySet)
    assert "item" in qs.query.select_related
    assert "status" in qs.query.select_related
    assert "responsible" in qs.query.select_related
    assert "location" in qs.query.select_related


@pytest.mark.django_db
def test_operation_admin_latest_operation_id_is_cached_per_request(
    django_assert_num_queries,
) -> None:
    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-CACHE-001", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    op2 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-cache", email="admin-cache@example.com", password="password"
    )

    # First lookup: 1 query for latest_id. (Permission base checks are in-memory.)
    with django_assert_num_queries(1):
        assert admin_obj.has_change_permission(request, obj=op1) is False

    # Second lookup for the same item within the same request should hit cache.
    with django_assert_num_queries(0):
        assert admin_obj.has_change_permission(request, obj=op2) is True


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_operation_lock_fieldset_description_for_non_latest_operation() -> None:
    """Lock fieldset only for frozen rows; no extra panel when editing is allowed."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-EDIT-DESC-1", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    op2 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-fs1", email="admin-fs1@example.com", password="password"
    )
    lock_title = str(_("Editing restrictions"))
    fs1 = admin_obj.get_fieldsets(request, op1)
    lock1 = next(fs for fs in fs1 if fs[0] is not None and str(fs[0]) == lock_title)
    assert "Only the latest" in str(lock1[1]["description"])

    fs2 = admin_obj.get_fieldsets(request, op2)
    assert not any(fs[0] is not None and str(fs[0]) == lock_title for fs in fs2)


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_lock_fieldset_description_when_correction_window_expired() -> None:
    """Latest row past the window shows the same wording as model validation."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-EDIT-DESC-2", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )
    op.refresh_from_db()

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_operation_admin_permissions("staff-op-fs2")
    lock_title = str(_("Editing restrictions"))
    fieldsets = admin_obj.get_fieldsets(request, op)
    lock = next(fs for fs in fieldsets if str(fs[0]) == lock_title)
    assert "contact an administrator" in str(lock[1]["description"]).lower()


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_change_page_renders_edit_lock_description_after_window() -> (
    None
):
    """Change/view page renders the restriction block in the HTML."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-EDIT-DESC-HTML", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )
    op.refresh_from_db()

    staff_user = _staff_user_with_operation_admin_permissions("staff-op-banner")
    client = Client()
    client.force_login(staff_user)
    url = reverse("admin:inventory_operation_change", args=[op.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"contact an administrator" in response.content.lower()


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_change_page_superuser_hides_lock_after_correction_window() -> None:
    """Superusers do not see the operation lock banner; they remain able to edit."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-OP-SU-HTML", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )

    admin_user = get_user_model().objects.create_superuser(
        username="admin-op-su-html",
        email="admin-op-su-html@example.com",
        password="password",
    )
    client = Client()
    client.force_login(admin_user)
    url = reverse("admin:inventory_operation_change", args=[op.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"Editing restrictions" not in response.content


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_operation_admin_change_page_hides_lock_section_when_editable() -> None:
    """Within the correction window, the restriction fieldset is not rendered."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-EDIT-NO-LOCK-UI", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    admin_user = get_user_model().objects.create_superuser(
        username="admin-no-lock-ui",
        email="admin-no-lock-ui@example.com",
        password="password",
    )

    client = Client()
    client.force_login(admin_user)
    url = reverse("admin:inventory_operation_change", args=[op.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"Editing restrictions" not in response.content


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_admin_denies_change_after_correction_window() -> None:
    """Non-superuser staff lose edit/delete once the item correction window ends."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-WINDOW", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    item.refresh_from_db()

    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_item_admin_permissions("staff-item-win")

    assert admin_obj.has_change_permission(request, obj=item) is False
    assert admin_obj.has_delete_permission(request, obj=item) is False


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_admin_staff_allows_change_after_window_without_responsible() -> None:
    """No operations yet: staff keep edit/delete past ``updated_at`` window."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-NO-RESP", device=device)
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    item.refresh_from_db()

    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_item_admin_permissions("staff-item-noresp")

    assert admin_obj.has_change_permission(request, obj=item) is True
    assert admin_obj.has_delete_permission(request, obj=item) is True


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_admin_superuser_keeps_change_after_correction_window() -> None:
    """Superusers can still change and delete items after the window (repair path)."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-SU-WIN", device=device)
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    item.refresh_from_db()

    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-item-su-win",
        email="admin-item-su-win@example.com",
        password="password",
    )

    assert admin_obj.has_change_permission(request, obj=item) is True
    assert admin_obj.has_delete_permission(request, obj=item) is True


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_lock_fieldset_description_when_correction_window_expired() -> None:
    """Expired window shows the same wording as ``Item.clean()``."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-FS", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    item.refresh_from_db()

    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_item_admin_permissions("staff-item-fs")
    lock_title = str(_("Editing restrictions"))
    fieldsets = admin_obj.get_fieldsets(request, item)
    lock = next(fs for fs in fieldsets if str(fs[0]) == lock_title)
    assert "contact an administrator" in str(lock[1]["description"]).lower()


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_fieldset_omits_lock_panel_without_model_change_permission() -> None:
    """
    View-only users should not see domain lock copy: they cannot edit for auth reasons.
    """

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-VIEW-ONLY", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    item.refresh_from_db()

    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_view_only_item("staff-item-view-only")
    lock_title = str(_("Editing restrictions"))
    fieldsets = admin_obj.get_fieldsets(request, item)
    assert not any(fs[0] is not None and str(fs[0]) == lock_title for fs in fieldsets)


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_operation_fieldset_omits_lock_panel_without_model_change_permission() -> None:
    """Same as item: view-only staff must not see append-only / window lock fieldset."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-OP-VIEW-ONLY", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_view_only_operation("staff-op-view-only")
    lock_title = str(_("Editing restrictions"))
    fieldsets = admin_obj.get_fieldsets(request, op1)
    assert not any(fs[0] is not None and str(fs[0]) == lock_title for fs in fieldsets)


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_change_page_renders_correction_window_lock_after_window() -> None:
    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-HTML", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )

    staff_user = _staff_user_with_item_admin_permissions("staff-item-html")
    client = Client()
    client.force_login(staff_user)
    url = reverse("admin:inventory_item_change", args=[item.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"contact an administrator" in response.content.lower()


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_change_page_no_lock_without_responsible_past_window() -> None:
    """Item with no operations: no correction-window lock text past ``updated_at``."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-DRAFT-OLD", device=device)
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )

    staff_user = _staff_user_with_item_admin_permissions("staff-item-draft-old")
    client = Client()
    client.force_login(staff_user)
    url = reverse("admin:inventory_item_change", args=[item.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"contact an administrator" not in response.content.lower()


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_change_page_superuser_hides_lock_after_correction_window() -> None:
    """Superusers do not see the lock banner; they remain able to edit."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-SU-HTML", device=device)
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )

    admin_user = get_user_model().objects.create_superuser(
        username="admin-item-su-html",
        email="admin-item-su-html@example.com",
        password="password",
    )
    client = Client()
    client.force_login(admin_user)
    url = reverse("admin:inventory_item_change", args=[item.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"Editing restrictions" not in response.content
    assert b"contact an administrator" not in response.content.lower()


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_item_change_page_hides_lock_section_when_editable() -> None:
    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(inventory_number="INV-ITEM-NO-LOCK", device=device)

    admin_user = get_user_model().objects.create_superuser(
        username="admin-item-nolock",
        email="admin-item-nolock@example.com",
        password="password",
    )
    client = Client()
    client.force_login(admin_user)
    url = reverse("admin:inventory_item_change", args=[item.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"Editing restrictions" not in response.content


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_superuser_post_saves_after_correction_window() -> None:
    """Superuser can persist a correction on the latest operation via admin POST."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status1 = Status.objects.create(name="S1")
    status2 = Status.objects.create(name="S2")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-OP-POST-WIN", device=device)
    op = Operation.objects.create(
        item=item,
        status=status1,
        responsible=responsible,
        location=location,
        notes="before",
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )

    admin_user = get_user_model().objects.create_superuser(
        username="admin-op-post",
        email="admin-op-post@example.com",
        password="password",
    )
    client = Client()
    client.force_login(admin_user)
    url = reverse("admin:inventory_operation_change", args=[op.pk])
    response = client.post(
        url,
        {
            "item": str(item.pk),
            "responsible": str(responsible.pk),
            "location": str(location.pk),
            "status": str(status2.pk),
            "notes": "after window via admin",
            "_save": "Save",
        },
    )
    assert response.status_code == 302
    op.refresh_from_db()
    assert op.status_id == status2.pk
    assert "after window via admin" in op.notes


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_admin_superuser_post_saves_after_correction_window() -> None:
    """Superuser can persist item field edits via admin POST after the window."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    item = Item.objects.create(
        inventory_number="INV-ITEM-POST-WIN",
        device=device,
        serial_number="SN-OLD",
    )
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )

    admin_user = get_user_model().objects.create_superuser(
        username="admin-item-post",
        email="admin-item-post@example.com",
        password="password",
    )
    client = Client()
    client.force_login(admin_user)
    url = reverse("admin:inventory_item_change", args=[item.pk])
    response = client.post(
        url,
        {
            "inventory_number": "INV-ITEM-POST-WIN",
            "device": str(device.pk),
            "serial_number": "SN-NEW",
            "notes": "item post after window",
            "_save": "Save",
        },
    )
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.serial_number == "SN-NEW"
    assert "item post after window" in item.notes


@pytest.mark.django_db
def test_item_admin_get_fieldsets_add_form_skips_item_lock_branch() -> None:
    """``obj`` is ``None`` on add: ``ItemAdmin`` returns base fieldsets without lock."""

    site = AdminSite()
    admin_obj = ItemAdmin(Item, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-item-add-fs",
        email="admin-item-add-fs@example.com",
        password="password",
    )
    fieldsets = admin_obj.get_fieldsets(request, None)
    assert isinstance(fieldsets, list)
    assert len(fieldsets) >= 1


@pytest.mark.django_db
def test_operation_admin_get_fieldsets_add_form_skips_operation_lock_branch() -> None:
    """``obj`` is ``None`` on add: ``OperationAdmin`` skips lock fieldset logic."""

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-op-add-fs",
        email="admin-op-add-fs@example.com",
        password="password",
    )
    fieldsets = admin_obj.get_fieldsets(request, None)
    assert isinstance(fieldsets, list)


@pytest.mark.django_db
def test_operation_admin_form_skips_window_bypass_for_non_latest_operation() -> None:
    """
    Superuser bypass applies only on the latest operation row for the item
    (``OperationAdminForm`` early exit).
    """

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    item = Item.objects.create(inventory_number="INV-OP-FORM-OLD", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-op-form-old",
        email="admin-op-form-old@example.com",
        password="password",
    )
    form_class = admin_obj.get_form(request, obj=op1, change=True)
    form = form_class(instance=op1)
    assert getattr(form.instance, "_bypass_operation_correction_window", False) is False


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_operation_admin_lock_message_for_non_latest_operation_row() -> None:
    """``_operation_correction_window_lock_user_message`` surfaces append-only copy."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    item = Item.objects.create(inventory_number="INV-OP-LOCK-MSG", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    op2 = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_operation_admin_permissions("staff-op-lock-msg")

    msg = admin_obj._operation_correction_window_lock_user_message(
        request,
        op1,
        latest_operation_pk=op2.pk,
    )
    assert msg is not None
    assert "Only the latest operation" in msg


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_lock_message_none_when_latest_id_unresolved() -> None:
    """Admin lock helper returns ``None`` when the journal head cannot be resolved."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    item = Item.objects.create(inventory_number="INV-OP-LOCK-NONE", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_operation_admin_permissions("staff-op-lock-none")

    with patch.object(Operation, "latest_operation_id_for_item", return_value=None):
        msg = admin_obj._operation_correction_window_lock_user_message(request, op)
    assert msg is None


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_lock_message_staff_latest_past_correction_window() -> None:
    """Non-superusers on the latest row past the window see expiry copy."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    item = Item.objects.create(inventory_number="INV-OP-LOCK-STAFF", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=30),
    )
    op.refresh_from_db()

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_operation_admin_permissions("staff-op-lock-exp")

    msg = admin_obj._operation_correction_window_lock_user_message(request, op)
    assert msg is not None
    assert Operation.correction_window_expired_user_message() in msg


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_lock_message_none_inside_window_for_staff() -> None:
    """Latest row still inside the window: no restriction copy for non-superusers."""

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    item = Item.objects.create(inventory_number="INV-OP-LOCK-WIN", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_user_with_operation_admin_permissions("staff-op-lock-win")

    msg = admin_obj._operation_correction_window_lock_user_message(request, op)
    assert msg is None


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_admin_lock_message_none_for_superuser_on_latest_row() -> None:
    site = AdminSite()
    admin_obj = OperationAdmin(Operation, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = get_user_model().objects.create_superuser(
        username="admin-op-lock-su",
        email="admin-op-lock-su@example.com",
        password="password",
    )

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")
    item = Item.objects.create(inventory_number="INV-OP-LOCK-SU", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )
    op.refresh_from_db()

    msg = admin_obj._operation_correction_window_lock_user_message(request, op)
    assert msg is None


# PendingTransfer admin is read-only (no create/edit/delete). Any tests for add-form
# initial values or auxiliary JSON endpoints are intentionally omitted.
