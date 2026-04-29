import pytest
from django.core.exceptions import ValidationError

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation


@pytest.mark.django_db
def test_item_display_name_and_str() -> None:
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
        inventory_number="INV-001",
        device=device,
        serial_number="SN-001",
    )

    assert item.get_display_name() == "INV-001 - " + str(device)
    assert str(item) == item.get_display_name()


@pytest.mark.django_db
def test_item_clean_requires_inventory_number() -> None:
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

    item = Item(inventory_number="", device=device)

    with pytest.raises(ValidationError):
        item.clean()


@pytest.mark.django_db
def test_item_clean_valid_inventory_number() -> None:
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

    item = Item(inventory_number="INV-VALID", device=device)
    item.clean()


@pytest.mark.django_db
def test_item_current_operation_and_current_fields() -> None:
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

    item = Item.objects.create(inventory_number="INV-002", device=device)

    # No operations yet.
    assert item.current_operation is None
    assert item.current_status is None
    assert item.current_location is None
    assert item.current_responsible is None

    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    assert item.current_operation is not None
    assert item.current_status == "In stock"
    assert item.current_location == "Moscow"
    assert item.current_responsible == responsible
    assert str(item.current_responsible) == "Ivanov Ivan"


@pytest.mark.django_db
def test_operation_str_and_responsible_display() -> None:
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

    item = Item.objects.create(inventory_number="INV-003", device=device)
    op = Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    assert op.get_responsible_display() == "Ivanov Ivan"
    assert str(op) == f"{item} - {status} ({location})"


def test_current_operation_value_descriptor_access_via_class_contract() -> None:
    # Descriptor protocol contract: access via the class must return the descriptor
    # itself (so admin/forms/introspection can read configuration without an instance).
    descriptor = Item.current_status
    assert isinstance(descriptor, Item.CurrentOperationValue)
    assert descriptor.attr_name == "status"
