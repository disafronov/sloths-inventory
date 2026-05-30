import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.test import RequestFactory, override_settings

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation, PendingTransfer


@pytest.mark.django_db
def test_responsible_clean_rejects_user_without_email() -> None:
    user = User.objects.create_user(username="noemail", password="pw", email="")
    resp = Responsible(last_name="A", first_name="B", user=user)
    with pytest.raises(ValidationError) as exc_info:
        resp.clean()
    assert "user" in exc_info.value.message_dict


@pytest.mark.django_db
def test_responsible_clean_accepts_user_with_email() -> None:
    user = User.objects.create_user(
        username="hasemail", password="pw", email="u@example.com"
    )
    resp = Responsible(last_name="A", first_name="B", user=user)
    resp.clean()  # should not raise


@pytest.mark.django_db
def test_responsible_clean_accepts_no_user() -> None:
    resp = Responsible(last_name="A", first_name="B")
    resp.clean()  # should not raise


@pytest.mark.django_db
def test_responsible_linked_profile_for_user() -> None:
    user = User.objects.create_user(username="u", password="pw", email="u@example.com")
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
def test_responsible_reference_in_use_includes_personal_locations() -> None:
    responsible = Responsible.objects.create(last_name="Owner", first_name="User")
    assert responsible.is_catalog_reference_in_use() is False

    Location.objects.create(name="Desk", responsible=responsible)

    assert responsible.is_catalog_reference_in_use() is True


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_location_global_on_hand_display_name() -> None:
    location = Location.on_hand()

    assert location.name == Location.ON_HAND
    assert location.responsible_id is None
    assert location.display_name == "On hand"
    assert location.scope_label == "System"
    assert location.scope_css_class == "system"
    assert location.display_name_with_scope == "On hand (System)"
    assert str(location) == "On hand (System)"


@pytest.mark.django_db
def test_location_system_location_protects_on_save_against_name_change() -> None:
    location = Location.on_hand()
    location.name = "hacked"
    with pytest.raises(ValidationError):
        location.save()


@pytest.mark.django_db
def test_location_system_location_protects_on_save_against_responsible_change() -> None:
    location = Location.on_hand()
    responsible = Responsible.objects.create(last_name="A", first_name="B")
    location.responsible = responsible
    with pytest.raises(ValidationError):
        location.save()


@pytest.mark.django_db
def test_location_system_location_protects_clean_against_name_change() -> None:
    location = Location.on_hand()
    location.name = "hacked"
    with pytest.raises(ValidationError):
        location.clean()


@pytest.mark.django_db
def test_location_system_location_protects_on_delete() -> None:
    location = Location.on_hand()
    with pytest.raises(ValidationError):
        location.delete()


@pytest.mark.django_db
def test_location_system_location_allows_creation() -> None:
    """Creation via get_or_create should still work."""
    location = Location.on_hand()
    assert location.pk is not None
    assert location.name == Location.ON_HAND


@pytest.mark.django_db
def test_location_regular_location_allows_save_and_delete() -> None:
    location = Location.objects.create(name="Office")
    pk = location.pk
    location.name = "Renamed"
    location.save()
    assert Location.objects.get(pk=pk).name == "Renamed"

    deleted_count, _ = location.delete()
    assert deleted_count == 1
    assert Location.objects.filter(pk=pk).count() == 0


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en")
def test_location_scope_labels_distinguish_global_and_personal() -> None:
    responsible = Responsible.objects.create(last_name="Owner", first_name="User")
    global_location = Location.objects.create(name="Office")
    personal_location = Location.objects.create(name="Desk", responsible=responsible)

    assert global_location.scope_label == "Common"
    assert global_location.scope_css_class == "common"
    assert global_location.display_name_with_scope == "Office (Common)"
    assert personal_location.scope_label == "Personal"
    assert personal_location.scope_css_class == "personal"
    assert personal_location.display_name_with_scope == "Desk (Personal)"


@pytest.mark.django_db
def test_location_allows_same_personal_name_for_different_responsibles() -> None:
    responsible_one = Responsible.objects.create(last_name="One", first_name="User")
    responsible_two = Responsible.objects.create(last_name="Two", first_name="User")

    Location.objects.create(name="Desk", responsible=responsible_one)
    Location.objects.create(name="Desk", responsible=responsible_two)

    duplicate = Location(name="Desk", responsible=responsible_one)
    with pytest.raises(ValidationError):
        duplicate.full_clean()


@pytest.mark.django_db
def test_location_available_for_responsible_returns_global_and_own_only() -> None:
    owner = Responsible.objects.create(last_name="Owner", first_name="User")
    other = Responsible.objects.create(last_name="Other", first_name="User")
    global_location = Location.objects.create(name="Office")
    own_location = Location.objects.create(name="Home", responsible=owner)
    other_location = Location.objects.create(name="Other home", responsible=other)

    owner_locations = list(Location.available_for_responsible(owner).order_by("pk"))
    global_locations = list(Location.available_for_responsible(None).order_by("pk"))

    assert global_location in owner_locations
    assert own_location in owner_locations
    assert Location.on_hand() in owner_locations
    assert other_location not in owner_locations
    assert global_location in global_locations
    assert own_location not in global_locations


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
