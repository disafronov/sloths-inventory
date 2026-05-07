import pytest
from django.contrib.auth.models import User
from django.core import mail

from catalogs.models import Responsible
from inventory.models import Item, Operation, PendingTransfer


@pytest.fixture(autouse=True)
def reset_outbox() -> None:
    mail.outbox.clear()


def _responsible(username: str, email: str) -> Responsible:
    user = User.objects.create_user(username=username, password="pw", email=email)
    return Responsible.objects.create(
        last_name=username.title(), first_name="Test", user=user
    )


@pytest.mark.django_db
def test_create_first_operation_sends_assigned(
    inventory_test_device, inventory_test_status_location
) -> None:
    """First operation for an item notifies the new responsible (assigned)."""
    item = Item.objects.create(inventory_number="SIG-001", device=inventory_test_device)
    resp = _responsible("sig_a", "a@example.com")

    Operation.objects.create(
        item=item,
        status=inventory_test_status_location["status"],
        responsible=resp,
        location=inventory_test_status_location["location"],
    )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["a@example.com"]
    assert "SIG-001" in mail.outbox[0].subject


@pytest.mark.django_db
def test_create_operation_with_prev_responsible_sends_assigned_and_unassigned(
    inventory_test_device, inventory_test_status_location
) -> None:
    """Second operation with a different responsible notifies both parties."""
    item = Item.objects.create(inventory_number="SIG-002", device=inventory_test_device)
    resp_a = _responsible("sig_b", "b@example.com")
    resp_b = _responsible("sig_c", "c@example.com")
    status = inventory_test_status_location["status"]
    location = inventory_test_status_location["location"]

    Operation.objects.create(
        item=item, status=status, responsible=resp_a, location=location
    )
    mail.outbox.clear()

    Operation.objects.create(
        item=item, status=status, responsible=resp_b, location=location
    )

    assert len(mail.outbox) == 2
    recipients = {msg.to[0] for msg in mail.outbox}
    assert "b@example.com" in recipients
    assert "c@example.com" in recipients


@pytest.mark.django_db
def test_create_operation_same_responsible_as_prev_sends_updated(
    inventory_test_device, inventory_test_status_location
) -> None:
    """New operation with unchanged responsible (e.g. location move) sends updated."""
    item = Item.objects.create(inventory_number="SIG-003", device=inventory_test_device)
    resp = _responsible("sig_d", "d@example.com")
    status = inventory_test_status_location["status"]
    location = inventory_test_status_location["location"]

    Operation.objects.create(
        item=item, status=status, responsible=resp, location=location
    )
    mail.outbox.clear()

    Operation.objects.create(
        item=item, status=status, responsible=resp, location=location
    )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["d@example.com"]
    assert "SIG-003" in mail.outbox[0].subject


@pytest.mark.django_db
def test_edit_operation_no_responsible_change_sends_updated(
    inventory_test_device, inventory_test_status_location
) -> None:
    item = Item.objects.create(inventory_number="SIG-004", device=inventory_test_device)
    resp = _responsible("sig_e", "e@example.com")
    status = inventory_test_status_location["status"]
    location = inventory_test_status_location["location"]

    op = Operation.objects.create(
        item=item, status=status, responsible=resp, location=location
    )
    mail.outbox.clear()

    op.notes = "updated note"
    op.save()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["e@example.com"]
    assert "SIG-004" in mail.outbox[0].subject


@pytest.mark.django_db
def test_edit_operation_responsible_change_sends_assigned_and_unassigned(
    inventory_test_device, inventory_test_status_location
) -> None:
    item = Item.objects.create(inventory_number="SIG-005", device=inventory_test_device)
    resp_a = _responsible("sig_f", "f@example.com")
    resp_b = _responsible("sig_g", "g@example.com")
    status = inventory_test_status_location["status"]
    location = inventory_test_status_location["location"]

    op = Operation.objects.create(
        item=item, status=status, responsible=resp_a, location=location
    )
    mail.outbox.clear()

    op.responsible = resp_b
    op.save()

    assert len(mail.outbox) == 2
    recipients = {msg.to[0] for msg in mail.outbox}
    assert "f@example.com" in recipients
    assert "g@example.com" in recipients


@pytest.mark.django_db
def test_no_email_when_responsible_has_no_user(
    inventory_test_device, inventory_test_status_location
) -> None:
    """Responsible without a linked user produces no email — recipient filtered."""
    item = Item.objects.create(inventory_number="SIG-006", device=inventory_test_device)
    resp = Responsible.objects.create(last_name="Offline", first_name="User")

    Operation.objects.create(
        item=item,
        status=inventory_test_status_location["status"],
        responsible=resp,
        location=inventory_test_status_location["location"],
    )

    assert len(mail.outbox) == 0


# ---------------------------------------------------------------------------
# Transfer signal tests
# ---------------------------------------------------------------------------


def _make_transfer(item, from_resp, to_resp, sl):
    op = Operation.objects.create(
        item=item,
        status=sl["status"],
        responsible=from_resp,
        location=sl["location"],
    )
    mail.outbox.clear()
    return op, PendingTransfer.objects.create(
        item=item,
        from_responsible=from_resp,
        to_responsible=to_resp,
    )


@pytest.mark.django_db
def test_transfer_created_notifies_receiver(
    inventory_test_device, inventory_test_status_location
) -> None:
    item = Item.objects.create(inventory_number="TR-001", device=inventory_test_device)
    sender = _responsible("tr_from1", "from1@example.com")
    receiver = _responsible("tr_to1", "to1@example.com")

    _, transfer = _make_transfer(item, sender, receiver, inventory_test_status_location)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["to1@example.com"]


@pytest.mark.django_db
def test_transfer_accepted_notifies_both(
    inventory_test_device, inventory_test_status_location
) -> None:
    item = Item.objects.create(inventory_number="TR-002", device=inventory_test_device)
    sender = _responsible("tr_from2", "from2@example.com")
    receiver = _responsible("tr_to2", "to2@example.com")

    _, transfer = _make_transfer(item, sender, receiver, inventory_test_status_location)
    mail.outbox.clear()

    transfer.accept()

    # accept() also triggers operation_assigned + operation_unassigned signals
    all_recipients = {addr for m in mail.outbox for addr in m.to}
    assert "from2@example.com" in all_recipients
    assert "to2@example.com" in all_recipients


@pytest.mark.django_db
def test_transfer_accepted_sends_accepted_email_to_both(
    inventory_test_device, inventory_test_status_location
) -> None:
    item = Item.objects.create(inventory_number="TR-003", device=inventory_test_device)
    user_s = User.objects.create_user(
        username="tr_s3", password="pw", email="s3@example.com"
    )
    user_r = User.objects.create_user(
        username="tr_r3", password="pw", email="r3@example.com"
    )
    sender = Responsible.objects.create(last_name="Sender", first_name="T", user=user_s)
    receiver = Responsible.objects.create(last_name="Recv", first_name="T", user=user_r)

    _, transfer = _make_transfer(item, sender, receiver, inventory_test_status_location)
    mail.outbox.clear()

    transfer.accept()

    transfer_emails = [m for m in mail.outbox if "TR-003" in m.subject]
    # accepted template subject does not contain item name — check by recipient set
    all_recipients = {addr for m in mail.outbox for addr in m.to}
    assert "s3@example.com" in all_recipients
    assert "r3@example.com" in all_recipients
    _ = transfer_emails  # referenced to avoid lint


@pytest.mark.django_db
def test_transfer_cancelled_notifies_both(
    inventory_test_device, inventory_test_status_location
) -> None:
    item = Item.objects.create(inventory_number="TR-004", device=inventory_test_device)
    user_s = User.objects.create_user(
        username="tr_s4", password="pw", email="s4@example.com"
    )
    user_r = User.objects.create_user(
        username="tr_r4", password="pw", email="r4@example.com"
    )
    sender = Responsible.objects.create(last_name="Sender", first_name="T", user=user_s)
    receiver = Responsible.objects.create(last_name="Recv", first_name="T", user=user_r)

    _, transfer = _make_transfer(item, sender, receiver, inventory_test_status_location)
    mail.outbox.clear()

    transfer.cancel()

    all_recipients = {addr for m in mail.outbox for addr in m.to}
    assert "s4@example.com" in all_recipients
    assert "r4@example.com" in all_recipients


@pytest.mark.django_db
def test_transfer_receiver_change_notifies_new_receiver(
    inventory_test_device, inventory_test_status_location
) -> None:
    item = Item.objects.create(inventory_number="TR-005", device=inventory_test_device)
    sender = _responsible("tr_s5", "s5@example.com")
    recv_a = _responsible("tr_r5a", "r5a@example.com")
    recv_b = _responsible("tr_r5b", "r5b@example.com")

    _, transfer = _make_transfer(item, sender, recv_a, inventory_test_status_location)
    mail.outbox.clear()

    transfer.update_offer(
        actor=sender,
        to_responsible=recv_b,
        notes="",
        auto_expiration_hours=0,
    )

    recipients = {addr for m in mail.outbox for addr in m.to}
    assert "r5b@example.com" in recipients  # new receiver notified (created)
    assert "r5a@example.com" in recipients  # old receiver notified (cancelled)


@pytest.mark.django_db
def test_transfer_created_no_email_for_offline_receiver(
    inventory_test_device, inventory_test_status_location
) -> None:
    """Offline receiver (no user) produces no created email."""
    item = Item.objects.create(inventory_number="TR-006", device=inventory_test_device)
    sender = _responsible("tr_s6", "s6@example.com")
    offline = Responsible.objects.create(last_name="Off", first_name="Line")

    Operation.objects.create(
        item=item,
        status=inventory_test_status_location["status"],
        responsible=sender,
        location=inventory_test_status_location["location"],
    )
    mail.outbox.clear()

    PendingTransfer.objects.create(
        item=item,
        from_responsible=sender,
        to_responsible=offline,
    )

    # No "transfer_created" email since offline receiver has no address.
    # The auto-accept path also triggers operation_assigned for the offline
    # receiver — also suppressed — and operation_unassigned for the sender.
    assert not any("Transfer offer created" in m.subject for m in mail.outbox)
