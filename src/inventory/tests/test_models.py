from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation, PendingTransfer


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
    with pytest.raises(ValidationError) as exc_info:
        op.save()
    assert exc_info.value.error_dict["__all__"][0].code == "correction_window_expired"


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
    Switching the receiver from one Responsible without a linked user to another
    must still auto-accept.

    Normal `create_offer` never leaves a pending row for an offline receiver, so
    we seed with `objects.create` (same pattern as expiry tests). This guards the
    `to_responsible.user_id is None` branch when the receiver changes but remains
    offline-only.
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
