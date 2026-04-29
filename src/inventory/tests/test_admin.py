import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

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
    assert admin_obj.current_responsible(item) == responsible
    assert str(admin_obj.current_responsible(item)) == str(responsible)

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
