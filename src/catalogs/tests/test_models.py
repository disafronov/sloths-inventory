import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation, PendingTransfer


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


@pytest.mark.django_db
def test_location_is_catalog_reference_in_use_adding_vs_saved() -> None:
    """Unsaved rows short-circuit; saved rows query ``Operation`` references."""

    assert Location(name="X").is_catalog_reference_in_use() is False

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
    item = Item.objects.create(inventory_number="INV-LOC-USE", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="A", first_name="B")
    loc = Location.objects.create(name="Shelf")
    assert loc.is_catalog_reference_in_use() is False
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=loc,
    )
    assert loc.is_catalog_reference_in_use() is True


@pytest.mark.django_db
def test_status_is_catalog_reference_in_use_adding_vs_saved() -> None:
    assert Status(name="S").is_catalog_reference_in_use() is False

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
    item = Item.objects.create(inventory_number="INV-ST-USE", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="A", first_name="B")
    location = Location.objects.create(name="L")
    assert status.is_catalog_reference_in_use() is False
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    assert status.is_catalog_reference_in_use() is True


@pytest.mark.django_db
def test_responsible_is_catalog_reference_in_use_adding_instance() -> None:
    assert (
        Responsible(last_name="X", first_name="Y").is_catalog_reference_in_use()
        is False
    )


@pytest.mark.django_db
def test_responsible_is_catalog_reference_in_use_via_pending_receiver_only() -> None:
    """
    ``Operation`` filter can be false while ``PendingTransfer`` still references
    the receiver via ``to_responsible``.
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
    item = Item.objects.create(inventory_number="INV-RSP-PEND", device=device)
    status = Status.objects.create(name="In stock")
    owner = Responsible.objects.create(last_name="Own", first_name="Er")
    receiver = Responsible.objects.create(last_name="Recv", first_name="Er")
    location = Location.objects.create(name="L")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=owner,
        location=location,
    )
    assert receiver.is_catalog_reference_in_use() is False

    PendingTransfer.objects.create(
        item=item,
        from_responsible=owner,
        to_responsible=receiver,
        notes="",
    )
    assert receiver.is_catalog_reference_in_use() is True


@pytest.mark.django_db
def test_responsible_is_catalog_reference_in_use_via_operation() -> None:
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
    item = Item.objects.create(inventory_number="INV-RSP-OP", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Op", first_name="User")
    location = Location.objects.create(name="L")
    assert responsible.is_catalog_reference_in_use() is False
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=location,
    )
    assert responsible.is_catalog_reference_in_use() is True
