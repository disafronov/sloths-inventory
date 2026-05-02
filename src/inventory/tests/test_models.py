from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation, PendingTransfer, parse_my_items_list_kind


def test_parse_my_items_list_kind_defaults_and_unknown() -> None:
    assert parse_my_items_list_kind("") == "all"
    assert parse_my_items_list_kind("  OWNED  ") == "owned"
    assert parse_my_items_list_kind("bogus") == "all"


@pytest.mark.django_db
def test_item_display_name_and_str(inventory_test_device) -> None:
    item = Item.objects.create(
        inventory_number="INV-001",
        device=inventory_test_device,
        serial_number="SN-001",
    )

    assert item.get_display_name() == "INV-001 - " + str(inventory_test_device)
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
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_clean_rejects_update_after_correction_window() -> None:
    """Reject updates past the window once an operation assigns a responsible party."""

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

    item = Item.objects.create(inventory_number="INV-WINDOW", device=device)
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
    item.serial_number = "SN-NEW"

    with pytest.raises(ValidationError) as exc:
        item.full_clean()

    assert exc.value.error_dict["__all__"][0].code == "item_correction_window_expired"


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_clean_allows_update_after_window_without_responsible() -> None:
    """No operations yet: master data stays editable past ``updated_at`` window."""

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

    item = Item.objects.create(inventory_number="INV-NO-RESP", device=device)
    Item.objects.filter(pk=item.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    item.refresh_from_db()
    item.serial_number = "SN-DRAFT"
    item.full_clean()
    item.save()
    item.refresh_from_db()
    assert item.serial_number == "SN-DRAFT"


@pytest.mark.django_db
def test_item_has_assigned_responsible_tracks_operations() -> None:
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

    item = Item.objects.create(inventory_number="INV-HAS-R", device=device)
    assert item.has_assigned_responsible() is False

    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    item.refresh_from_db()
    assert item.has_assigned_responsible() is True


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_save_allows_update_inside_correction_window() -> None:
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

    item = Item.objects.create(inventory_number="INV-WINDOW-OK", device=device)
    item.serial_number = "SN-NEW"
    item.save()
    item.refresh_from_db()
    assert item.serial_number == "SN-NEW"


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_save_after_correction_window_with_admin_bypass_flag() -> None:
    """Trusted admin sets ``_bypass_item_correction_window`` so repairs can save."""

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

    item = Item.objects.create(inventory_number="INV-BYPASS", device=device)
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
    item.serial_number = "SN-FIX"
    setattr(item, "_bypass_item_correction_window", True)
    item.save()
    item.refresh_from_db()
    assert item.serial_number == "SN-FIX"


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
    with pytest.raises(ValidationError) as exc_info:
        op1.save()
    assert (
        exc_info.value.error_dict["__all__"][0].code == "operation_not_latest_for_item"
    )

    # The latest operation may be corrected.
    op2.status = status2
    op2.notes = "typo fix"
    op2.save()

    # Changing item is forbidden even for the latest operation.
    op2.item = item2
    with pytest.raises(ValidationError):
        op2.save()


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_operation_stale_non_latest_reports_append_only_not_window() -> None:
    """
    Non-head rows must fail with the append-only reason, not the correction window.

    If ``clean()`` checked the time window before the latest-row rule, a historical
    non-latest row would incorrectly surface ``correction_window_expired``.
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

    status1 = Status.objects.create(name="S1")
    status2 = Status.objects.create(name="S2")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-NONHEAD-STALE", device=device)
    op1 = Operation.objects.create(
        item=item,
        status=status1,
        responsible=responsible,
        location=location,
    )
    Operation.objects.create(
        item=item,
        status=status1,
        responsible=responsible,
        location=location,
    )
    Operation.objects.filter(pk=op1.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    op1.refresh_from_db()

    op1.status = status2
    with pytest.raises(ValidationError) as exc_info:
        op1.save()
    assert (
        exc_info.value.error_dict["__all__"][0].code == "operation_not_latest_for_item"
    )


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
    with pytest.raises(ValidationError) as exc_info:
        op.save()
    assert exc_info.value.error_dict["__all__"][0].code == "correction_window_expired"


@pytest.mark.django_db
def test_operation_save_after_window_with_admin_bypass_flag() -> None:
    """Trusted admin path: bypass flag skips the correction window on the latest row."""

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

    item = Item.objects.create(inventory_number="INV-OP-BYPASS", device=device)
    op = Operation.objects.create(
        item=item,
        status=status1,
        responsible=responsible,
        location=location,
        notes="init",
    )
    Operation.objects.filter(pk=op.pk).update(
        created_at=timezone.now() - timedelta(days=1),
    )
    op.refresh_from_db()

    op.status = status2
    setattr(op, "_bypass_operation_correction_window", True)
    op.save()
    op.refresh_from_db()
    assert op.status_id == status2.pk


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


@pytest.mark.django_db
def test_pending_transfer_str_and_is_active() -> None:
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
    location = Location.objects.create(name="Moscow")

    sender = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    receiver = Responsible.objects.create(last_name="Petrov", first_name="Petr")

    item = Item.objects.create(inventory_number="INV-XFER-ACTIVE", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=sender, location=location, notes="init"
    )

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
    )
    assert str(item.inventory_number) in str(transfer)
    assert transfer.is_active is True

    transfer.accepted_at = timezone.now()
    transfer.save()
    assert transfer.is_active is False


@pytest.mark.django_db
def test_pending_transfer_clean_rejects_self_transfer() -> None:
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
    location = Location.objects.create(name="Moscow")
    person = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")

    item = Item.objects.create(inventory_number="INV-XFER-SELF", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=person, location=location
    )

    transfer = PendingTransfer(
        item=item, from_responsible=person, to_responsible=person
    )
    with pytest.raises(ValidationError):
        transfer.full_clean()


@pytest.mark.django_db
def test_pending_transfer_clean_rejects_accepted_and_cancelled() -> None:
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
    location = Location.objects.create(name="Moscow")
    sender = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    receiver = Responsible.objects.create(last_name="Petrov", first_name="Petr")

    item = Item.objects.create(inventory_number="INV-XFER-BADSTATE", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=sender, location=location
    )

    transfer = PendingTransfer(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        accepted_at=timezone.now(),
        cancelled_at=timezone.now(),
    )
    with pytest.raises(ValidationError):
        transfer.full_clean()


@pytest.mark.django_db
def test_pending_transfer_clean_rejects_expired_expires_at() -> None:
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
    location = Location.objects.create(name="Moscow")
    sender = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    receiver = Responsible.objects.create(last_name="Petrov", first_name="Petr")

    item = Item.objects.create(inventory_number="INV-XFER-EXPIRED", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=sender, location=location
    )

    transfer = PendingTransfer(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    with pytest.raises(ValidationError):
        transfer.full_clean()


@pytest.mark.django_db
def test_pending_transfer_clean_rejects_second_active_transfer_for_item() -> None:
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
    location = Location.objects.create(name="Moscow")
    sender = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    receiver1 = Responsible.objects.create(last_name="Petrov", first_name="Petr")
    receiver2 = Responsible.objects.create(last_name="Sidorov", first_name="Sid")

    item = Item.objects.create(inventory_number="INV-XFER-UNIQ", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=sender, location=location
    )

    PendingTransfer.objects.create(
        item=item, from_responsible=sender, to_responsible=receiver1
    )
    another = PendingTransfer(
        item=item, from_responsible=sender, to_responsible=receiver2
    )
    with pytest.raises(ValidationError):
        another.full_clean()


@pytest.mark.django_db
def test_pending_transfer_deadline_edge_gradient_t() -> None:
    """CSS pressure ratio follows elapsed time between created_at and expires_at."""

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
    location = Location.objects.create(name="Moscow")
    sender = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    receiver = Responsible.objects.create(last_name="Petrov", first_name="Petr")

    item = Item.objects.create(inventory_number="INV-XFER-GRAD", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=sender, location=location
    )

    item_ne = Item.objects.create(inventory_number="INV-XFER-GRAD-NE", device=device)
    Operation.objects.create(
        item=item_ne, status=status, responsible=sender, location=location, notes="ne"
    )
    no_deadline = PendingTransfer.objects.create(
        item=item_ne,
        from_responsible=sender,
        to_responsible=receiver,
    )
    assert no_deadline.deadline_edge_gradient_t() == "0"

    frozen_now = timezone.now()
    with patch("django.utils.timezone.now", return_value=frozen_now):
        transfer = PendingTransfer.objects.create(
            item=item,
            from_responsible=sender,
            to_responsible=receiver,
            expires_at=frozen_now + timedelta(hours=2),
        )

    PendingTransfer.objects.filter(pk=transfer.pk).update(
        created_at=frozen_now - timedelta(hours=2)
    )
    transfer.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=frozen_now):
        assert transfer.deadline_edge_gradient_t() == "0.5"

    with patch(
        "django.utils.timezone.now", return_value=frozen_now + timedelta(hours=2)
    ):
        assert transfer.deadline_edge_gradient_t() == "1"

    with patch(
        "django.utils.timezone.now", return_value=frozen_now + timedelta(hours=3)
    ):
        assert transfer.deadline_edge_gradient_t() == "1"


@pytest.mark.django_db
def test_pending_transfer_deadline_edge_gradient_t_clamps_before_created_at() -> None:
    """
    When the clock is behind created_at, the UI ratio should clamp to 0.

    This can happen due to clock skew or data fixes that move created_at forward.
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
    status = Status.objects.create(name="S1")
    location = Location.objects.create(name="Moscow")
    sender = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    receiver = Responsible.objects.create(last_name="Petrov", first_name="Petr")

    item = Item.objects.create(inventory_number="INV-XFER-GRAD-CLAMP0", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=sender, location=location
    )

    frozen_now = timezone.now()
    with patch("django.utils.timezone.now", return_value=frozen_now):
        transfer = PendingTransfer.objects.create(
            item=item,
            from_responsible=sender,
            to_responsible=receiver,
            expires_at=frozen_now + timedelta(hours=2),
        )

    PendingTransfer.objects.filter(pk=transfer.pk).update(
        created_at=frozen_now + timedelta(seconds=1)
    )
    transfer.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=frozen_now):
        assert transfer.deadline_edge_gradient_t() == "0"


@pytest.mark.django_db
def test_pending_transfer_deadline_edge_gradient_t_handles_non_positive_span() -> None:
    """
    When expires_at <= created_at, treat the deadline as reached (ratio 1).
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
    status = Status.objects.create(name="S1")
    location = Location.objects.create(name="Moscow")
    sender = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    receiver = Responsible.objects.create(last_name="Petrov", first_name="Petr")

    item = Item.objects.create(inventory_number="INV-XFER-GRAD-BADSPAN", device=device)
    Operation.objects.create(
        item=item, status=status, responsible=sender, location=location
    )

    frozen_now = timezone.now()
    with patch("django.utils.timezone.now", return_value=frozen_now):
        transfer = PendingTransfer.objects.create(
            item=item,
            from_responsible=sender,
            to_responsible=receiver,
            expires_at=frozen_now + timedelta(hours=2),
        )

    PendingTransfer.objects.filter(pk=transfer.pk).update(
        created_at=frozen_now + timedelta(hours=2),
        expires_at=frozen_now + timedelta(hours=2),
    )
    transfer.refresh_from_db()

    with patch(
        "django.utils.timezone.now", return_value=frozen_now + timedelta(hours=3)
    ):
        assert transfer.deadline_edge_gradient_t() == "1"


@pytest.mark.django_db
def test_pending_transfer_update_offer_resets_expires_at_when_receiver_changes() -> (
    None
):
    """
    When both receivers have linked users, `update_offer` must not auto-accept;
    only receiver, notes, and expiry window change (raw `objects.create` is used
    to seed a pending row without going through `create_offer`).
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

    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    user_from = User.objects.create_user(username="from-exp", password="pw")
    user_to1 = User.objects.create_user(username="to1-exp", password="pw")
    user_to2 = User.objects.create_user(username="to2-exp", password="pw")
    from_resp = Responsible.objects.create(
        last_name="From", first_name="User", user=user_from
    )
    to_resp1 = Responsible.objects.create(
        last_name="To", first_name="One", user=user_to1
    )
    to_resp2 = Responsible.objects.create(
        last_name="To", first_name="Two", user=user_to2
    )

    item = Item.objects.create(inventory_number="INV-XFER-UPD", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=from_resp,
        location=location,
    )

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=from_resp,
        to_responsible=to_resp1,
        expires_at=timezone.now() + timedelta(hours=100),
        notes="old",
    )

    before = timezone.now()
    transfer.update_offer(
        actor=from_resp,
        to_responsible=to_resp2,
        notes="new",
        auto_expiration_hours=72,
    )
    after = timezone.now()

    transfer.refresh_from_db()
    assert transfer.to_responsible_id == to_resp2.pk
    assert transfer.notes == "new"
    assert transfer.expires_at is not None
    assert (
        before + timedelta(hours=72)
        <= transfer.expires_at
        <= after + timedelta(hours=72)
    )
    assert transfer.accepted_at is None
    assert item.operation_set.count() == 1


@pytest.mark.django_db
def test_pending_transfer_update_offer_auto_accepts_no_user_receiver() -> None:
    """
    Changing the receiver to a Responsible without a linked user must auto-accept,
    matching `create_offer` behaviour so the offer cannot stay pending forever.
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

    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    user_sender = User.objects.create_user(username="snd", password="pw")
    user_recv = User.objects.create_user(username="rcv", password="pw")
    from_resp = Responsible.objects.create(
        last_name="From", first_name="User", user=user_sender
    )
    to_with_user = Responsible.objects.create(
        last_name="To", first_name="WithUser", user=user_recv
    )
    to_no_user = Responsible.objects.create(last_name="To", first_name="NoUser")

    item = Item.objects.create(inventory_number="INV-XFER-UPD-AUTO", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=from_resp,
        location=location,
    )

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=from_resp,
        to_responsible=to_with_user,
        notes="pending",
    )

    transfer.update_offer(
        actor=from_resp,
        to_responsible=to_no_user,
        notes="hand to offline profile",
        auto_expiration_hours=0,
    )

    transfer.refresh_from_db()
    assert transfer.to_responsible_id == to_no_user.pk
    assert transfer.notes == "hand to offline profile"
    assert transfer.accepted_at is not None
    latest = item.operation_set.order_by("-created_at", "-id").first()
    assert latest is not None
    assert latest.responsible_id == to_no_user.pk


@pytest.mark.django_db
def test_pending_transfer_update_offer_auto_accepts_offline_to_offline_receiver() -> (
    None
):
    """
    Model contract: `update_offer` must auto-accept when the new receiver has no
    linked user, even if the previous receiver also had none.

    This state is not reachable through the logged-in UI (`create_offer` accepts
    immediately for offline receivers). We seed a pending row with `objects.create`
    to exercise the branch defensively (migrations, admin, or future code paths).
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

    status = Status.objects.create(name="In use")
    location = Location.objects.create(name="Home")
    user_sender = User.objects.create_user(username="snd-off2off", password="pw")
    from_resp = Responsible.objects.create(
        last_name="From", first_name="User", user=user_sender
    )
    offline_a = Responsible.objects.create(last_name="Offline", first_name="Alpha")
    offline_b = Responsible.objects.create(last_name="Offline", first_name="Beta")
    assert offline_a.user_id is None and offline_b.user_id is None

    item = Item.objects.create(inventory_number="INV-XFER-OFF2OFF", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=from_resp,
        location=location,
    )

    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=from_resp,
        to_responsible=offline_a,
        notes="seed pending to offline A",
    )

    transfer.update_offer(
        actor=from_resp,
        to_responsible=offline_b,
        notes="reassign to offline B",
        auto_expiration_hours=48,
    )

    transfer.refresh_from_db()
    assert transfer.to_responsible_id == offline_b.pk
    assert transfer.notes == "reassign to offline B"
    assert transfer.accepted_at is not None
    assert item.operation_set.count() == 2
    latest = item.operation_set.order_by("-created_at", "-id").first()
    assert latest is not None
    assert latest.responsible_id == offline_b.pk


@pytest.mark.django_db
def test_item_has_assigned_responsible_false_while_adding() -> None:
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
    item = Item(inventory_number="INV-ADD-STATE", device=device)
    assert item.has_assigned_responsible() is False


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_item_clean_allows_update_inside_window_when_assigned() -> None:
    """``clean()`` allows updates while ``updated_at`` stays inside the window."""

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
    item = Item.objects.create(inventory_number="INV-ITEM-WIN", device=device)
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
        updated_at=timezone.now() - timedelta(minutes=2),
    )
    item.refresh_from_db()
    item.notes = "still inside window"
    item.full_clean()
    item.save()
    item.refresh_from_db()
    assert "still inside window" in item.notes


@pytest.mark.django_db
def test_item_change_location_requires_operations() -> None:
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
    item = Item.objects.create(inventory_number="INV-LOC-NOOP", device=device)
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    with pytest.raises(ValidationError):
        item.change_location(responsible=responsible, location=location)


@pytest.mark.django_db
def test_item_change_location_rejects_non_current_responsible() -> None:
    """Only the journal head's responsible person may append a location move."""

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
    item = Item.objects.create(inventory_number="INV-LOC-WRONG-R", device=device)
    owner = Responsible.objects.create(last_name="Owner", first_name="O")
    other = Responsible.objects.create(last_name="Other", first_name="X")
    status = Status.objects.create(name="In stock")
    loc_a = Location.objects.create(name="A")
    loc_b = Location.objects.create(name="B")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=owner,
        location=loc_a,
    )

    with pytest.raises(ValidationError):
        item.change_location(responsible=other, location=loc_b, notes="")


@pytest.mark.django_db
def test_pending_transfer_accept_raises_without_journal_head() -> None:
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
    item = Item.objects.create(inventory_number="INV-ACC-NOOP", device=device)
    status = Status.objects.create(name="In stock")
    sender = Responsible.objects.create(last_name="S", first_name="A")
    receiver = Responsible.objects.create(last_name="R", first_name="B")
    location = Location.objects.create(name="L")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        notes="",
    )
    Operation.objects.filter(item=item).delete()

    with pytest.raises(ValidationError):
        transfer.accept()


@pytest.mark.django_db
def test_pending_transfer_accept_raises_when_journal_head_not_sender() -> None:
    """
    ``accept()`` must reject offers once the append-only head no longer names
    ``from_responsible`` (stale row after the journal moved past the sender).
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
    item = Item.objects.create(inventory_number="INV-ACC-STALE-OWNER", device=device)
    status = Status.objects.create(name="In stock")
    sender = Responsible.objects.create(last_name="S", first_name="A")
    other = Responsible.objects.create(last_name="O", first_name="B")
    receiver = Responsible.objects.create(last_name="R", first_name="C")
    location = Location.objects.create(name="L")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        notes="",
    )
    Operation.objects.create(
        item=item,
        status=status,
        responsible=other,
        location=location,
    )

    with pytest.raises(ValidationError):
        transfer.accept()


@pytest.mark.django_db
def test_pending_transfer_cancel_raises_when_inactive() -> None:
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
    item = Item.objects.create(inventory_number="INV-CAN-INACT", device=device)
    status = Status.objects.create(name="In stock")
    sender = Responsible.objects.create(last_name="S", first_name="A")
    receiver = Responsible.objects.create(last_name="R", first_name="B")
    location = Location.objects.create(name="L")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        notes="",
    )
    transfer.cancel()

    with pytest.raises(ValidationError):
        transfer.cancel()


@pytest.mark.django_db
def test_pending_transfer_update_offer_rejects_negative_expiration() -> None:
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
    sender = Responsible.objects.create(last_name="S", first_name="A")
    receiver = Responsible.objects.create(last_name="R", first_name="B")
    location = Location.objects.create(name="L")
    item = Item.objects.create(inventory_number="INV-UPD-NEG", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        notes="",
    )
    with pytest.raises(ValidationError):
        transfer.update_offer(
            actor=sender,
            to_responsible=receiver,
            notes="x",
            auto_expiration_hours=-1,
        )


@pytest.mark.django_db
def test_pending_transfer_update_offer_rejects_wrong_actor() -> None:
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
    sender = Responsible.objects.create(last_name="S", first_name="A")
    receiver = Responsible.objects.create(last_name="R", first_name="B")
    other = Responsible.objects.create(last_name="O", first_name="T")
    location = Location.objects.create(name="L")
    item = Item.objects.create(inventory_number="INV-UPD-ACT", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        notes="",
    )
    with pytest.raises(ValidationError):
        transfer.update_offer(
            actor=other,
            to_responsible=receiver,
            notes="x",
            auto_expiration_hours=0,
        )


@pytest.mark.django_db
def test_pending_transfer_update_offer_receiver_change_zero_hours_clears_expiry() -> (
    None
):
    """
    When the receiver changes and ``auto_expiration_hours`` is ``0``, ``expires_at``
    is cleared (``else`` branch under ``receiver_changed``).
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
    sender = Responsible.objects.create(last_name="S", first_name="A")
    user_b = User.objects.create_user(username="ub", password="pw")
    user_c = User.objects.create_user(username="uc", password="pw")
    recv_b = Responsible.objects.create(last_name="B", first_name="One", user=user_b)
    recv_c = Responsible.objects.create(last_name="C", first_name="Two", user=user_c)
    location = Location.objects.create(name="L")
    item = Item.objects.create(inventory_number="INV-UPD-ZERO-EXP", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=recv_b,
        expires_at=timezone.now() + timedelta(hours=1),
        notes="",
    )
    transfer.update_offer(
        actor=sender,
        to_responsible=recv_c,
        notes="switch receiver",
        auto_expiration_hours=0,
    )
    transfer.refresh_from_db()
    assert transfer.expires_at is None
    assert transfer.to_responsible_id == recv_c.pk


@pytest.mark.django_db
def test_pending_transfer_update_offer_rejects_when_inactive() -> None:
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
    sender = Responsible.objects.create(last_name="S", first_name="A")
    receiver = Responsible.objects.create(last_name="R", first_name="B")
    location = Location.objects.create(name="L")
    item = Item.objects.create(inventory_number="INV-UPD-INACT", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        notes="",
    )
    transfer.cancel()

    with pytest.raises(ValidationError):
        transfer.update_offer(
            actor=sender,
            to_responsible=receiver,
            notes="too late",
            auto_expiration_hours=0,
        )


@pytest.mark.django_db
def test_pending_transfer_update_offer_same_receiver_skips_expiry_block() -> None:
    """Unchanged receiver leaves ``expires_at`` untouched (skip inner ``if`` body)."""

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
    sender = Responsible.objects.create(last_name="S", first_name="A")
    receiver = Responsible.objects.create(last_name="R", first_name="B")
    location = Location.objects.create(name="L")
    item = Item.objects.create(inventory_number="INV-UPD-SKIP-EXP", device=device)
    Operation.objects.create(
        item=item,
        status=status,
        responsible=sender,
        location=location,
    )
    exp = timezone.now() + timedelta(hours=5)
    transfer = PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=receiver,
        expires_at=exp,
        notes="seed",
    )
    transfer.update_offer(
        actor=sender,
        to_responsible=receiver,
        notes="same path",
        auto_expiration_hours=99,
    )
    transfer.refresh_from_db()
    assert transfer.expires_at == exp
    assert transfer.notes == "same path"
