from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    assert item.current_responsible == "Ivanov Ivan"


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


@pytest.mark.django_db
def test_operation_only_latest_can_be_edited_and_item_cannot_change() -> None:
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

    item1 = Item.objects.create(inventory_number="INV-100", device=device)
    item2 = Item.objects.create(inventory_number="INV-101", device=device)

    op1 = Operation.objects.create(
        item=item1,
        status=status1,
        responsible=responsible,
        location=location,
    )
    op2 = Operation.objects.create(
        item=item1,
        status=status1,
        responsible=responsible,
        location=location,
    )

    # Old operations are append-only: cannot edit.
    op1.status = status2
    with pytest.raises(ValidationError):
        op1.save()

    # The latest operation may be corrected.
    op2.status = status2
    op2.notes = "typo fix"
    op2.save()

    # Changing item is forbidden even for the latest operation.
    op2.item = item2
    with pytest.raises(ValidationError):
        op2.save()


@pytest.mark.django_db
def test_operation_latest_edit_is_blocked_after_correction_window() -> None:
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

    item = Item.objects.create(inventory_number="INV-WINDOW-001", device=device)
    op = Operation.objects.create(
        item=item,
        status=status1,
        responsible=responsible,
        location=location,
        notes="init",
    )

    # Simulate an old operation by moving created_at to the past.
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    op.refresh_from_db()

    op.status = status2
    with pytest.raises(ValidationError, match="correction window"):
        op.save()


@pytest.mark.django_db
def test_operation_default_ordering_and_current_operation_tiebreaker() -> None:
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

    status = Status.objects.create(name="S1")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-200", device=device)
    op1 = Operation.objects.create(
        item=item, status=status, responsible=responsible, location=location
    )
    op2 = Operation.objects.create(
        item=item, status=status, responsible=responsible, location=location
    )

    # Simulate identical created_at to validate deterministic tiebreaker by id.
    created_at = timezone.now()
    Operation.objects.filter(pk__in=[op1.pk, op2.pk]).update(created_at=created_at)
    op1.refresh_from_db()
    op2.refresh_from_db()

    assert Operation.objects.filter(item=item).first() == op2
    assert item.current_operation == op2


def test_current_operation_value_is_introspectable_via_class_access() -> None:
    """
    Descriptor contract: accessing the attribute via the class returns the descriptor.

    This matters for Django/admin introspection and for safe refactoring: if the
    descriptor stops being accessible at class level, it's easy to accidentally
    break dynamic attribute usage patterns.
    """

    descriptor = Item.current_status
    assert isinstance(descriptor, Item.CurrentOperationValue)
    assert descriptor.attr_name == "status"


@pytest.mark.django_db
def test_current_operation_value_missing_attr_returns_none() -> None:
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

    item = Item.objects.create(inventory_number="INV-404", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )

    descriptor = Item.CurrentOperationValue("missing_field")
    assert descriptor.__get__(item, Item) is None
