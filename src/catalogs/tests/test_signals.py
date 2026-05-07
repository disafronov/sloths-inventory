from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError

from catalogs.models import Responsible


@pytest.fixture(autouse=True)
def reset_outbox() -> None:
    mail.outbox.clear()


def _user(username: str, email: str) -> User:
    return User.objects.create_user(username=username, password="pw", email=email)


@pytest.mark.django_db
def test_linking_user_on_create_sends_linked_email() -> None:
    user = _user("new_u", "new@example.com")
    Responsible.objects.create(last_name="Test", first_name="A", user=user)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["new@example.com"]


@pytest.mark.django_db
def test_linking_user_on_update_sends_linked_email() -> None:
    user = _user("upd_u", "upd@example.com")
    resp = Responsible.objects.create(last_name="Test", first_name="B")
    mail.outbox.clear()

    resp.user = user
    resp.save()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["upd@example.com"]


@pytest.mark.django_db
def test_unlinking_user_sends_unlinked_email_to_old_user() -> None:
    user = _user("old_u", "old@example.com")
    resp = Responsible.objects.create(last_name="Test", first_name="C", user=user)
    mail.outbox.clear()

    resp.user = None
    resp.save()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["old@example.com"]


@pytest.mark.django_db
def test_changing_user_notifies_both_old_and_new() -> None:
    user_a = _user("ua", "a@example.com")
    user_b = _user("ub", "b@example.com")
    resp = Responsible.objects.create(last_name="Test", first_name="D", user=user_a)
    mail.outbox.clear()

    resp.user = user_b
    resp.save()

    assert len(mail.outbox) == 2
    recipients = {msg.to[0] for msg in mail.outbox}
    assert "a@example.com" in recipients
    assert "b@example.com" in recipients


@pytest.mark.django_db
def test_create_without_user_sends_no_email() -> None:
    Responsible.objects.create(last_name="Test", first_name="E")
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_update_without_user_sends_no_email() -> None:
    resp = Responsible.objects.create(last_name="Test", first_name="F")
    mail.outbox.clear()

    resp.notes = "changed"
    resp.save()

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_update_with_user_unchanged_sends_updated_email() -> None:
    user = _user("upd2_u", "upd2@example.com")
    resp = Responsible.objects.create(last_name="Test", first_name="H", user=user)
    mail.outbox.clear()

    resp.last_name = "Updated"
    resp.save()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["upd2@example.com"]


@pytest.mark.django_db
def test_linking_user_without_email_raises_validation_error() -> None:
    user = User.objects.create_user(username="noemail", password="pw", email="")
    resp = Responsible(last_name="Test", first_name="G", user=user)
    with pytest.raises(ValidationError):
        resp.save()
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_responsible_notification_failure_does_not_roll_back_save() -> None:
    """Email failure in notify_responsible_user_changed must not roll back the save."""
    user = _user("notify_err", "notify_err@example.com")

    with patch(
        "catalogs.signals.send_transfer_email", side_effect=RuntimeError("boom")
    ):
        resp = Responsible.objects.create(last_name="Test", first_name="Err", user=user)

    assert Responsible.objects.filter(pk=resp.pk).exists()
