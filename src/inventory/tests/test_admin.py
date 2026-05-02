from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
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
@override_settings(INVENTORY_OPERATION_EDIT_WINDOW_MINUTES=10)
def test_operation_admin_denies_change_after_correction_window() -> None:
    """Admin must hide edit/delete once the operation correction window ends."""

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
    user = get_user_model().objects.create_superuser(
        username="admin-win", email="admin-win@example.com", password="password"
    )
    request.user = user

    assert admin_obj.has_change_permission(request, obj=op) is False
    assert admin_obj.has_delete_permission(request, obj=op) is False


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
@override_settings(LANGUAGE_CODE="en", INVENTORY_OPERATION_EDIT_WINDOW_MINUTES=10)
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
    request.user = get_user_model().objects.create_superuser(
        username="admin-fs2", email="admin-fs2@example.com", password="password"
    )
    text = str(admin_obj.get_fieldsets(request, op)[-1][1]["description"])
    assert "correction window" in text.lower()


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_OPERATION_EDIT_WINDOW_MINUTES=10)
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

    admin_user = get_user_model().objects.create_superuser(
        username="admin-banner", email="admin-banner@example.com", password="password"
    )
    client = Client()
    client.force_login(admin_user)
    url = reverse("admin:inventory_operation_change", args=[op.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert b"correction window" in response.content.lower()


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


# PendingTransfer admin is read-only (no create/edit/delete). Any tests for add-form
# initial values or auxiliary JSON endpoints are intentionally omitted.
