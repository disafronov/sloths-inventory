import pytest
from django.contrib.auth.models import User
from django.core import mail

from catalogs.models import Responsible
from inventory.models import Item, Operation


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
def test_create_operation_same_responsible_as_prev_sends_only_assigned(
    inventory_test_device, inventory_test_status_location
) -> None:
    """Second operation with the same responsible does not send unassigned."""
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
