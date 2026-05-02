import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from catalogs.models import Responsible


@pytest.mark.django_db
def test_responsible_linked_profile_for_user() -> None:
    user = User.objects.create_user(username="u", password="pw")
    resp = Responsible.objects.create(last_name="A", first_name="B", user=user)
    assert Responsible.linked_profile_for_user(user) == resp
    rf = RequestFactory()
    req = rf.get("/")
    req.user = AnonymousUser()
    assert Responsible.linked_profile_for_user(req.user) is None


@pytest.mark.django_db
def test_responsible_resolve_transfer_receiver_from_form() -> None:
    sender = Responsible.objects.create(last_name="S", first_name="A")
    receiver = Responsible.objects.create(last_name="R", first_name="B")
    assert (
        Responsible.resolve_transfer_receiver_from_form(str(receiver.pk), sender=sender)
        == receiver
    )
    with pytest.raises(ValidationError):
        Responsible.resolve_transfer_receiver_from_form(None, sender=sender)
    with pytest.raises(ValidationError):
        Responsible.resolve_transfer_receiver_from_form(str(sender.pk), sender=sender)


def test_responsible_full_name_formatting() -> None:
    responsible = Responsible(
        last_name="Ivanov",
        first_name="Ivan",
        middle_name="Ivanovich",
    )

    assert str(responsible) == "Ivanov Ivan Ivanovich"
    assert responsible.get_full_name() == "Ivanov Ivan Ivanovich"


def test_responsible_full_name_without_middle_name() -> None:
    responsible = Responsible(
        last_name="Ivanov",
        first_name="Ivan",
        middle_name=None,
    )

    assert str(responsible) == "Ivanov Ivan"
