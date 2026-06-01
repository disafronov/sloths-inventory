"""Tests for user-facing catalog views (location management)."""

from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from catalogs.models import Location, Responsible


@pytest.fixture
def linked_user(db: object) -> tuple[User, Responsible]:
    """Return a (user, responsible) pair with a linked profile."""
    user = User.objects.create_user(username="u", password="pw", email="u@example.com")
    resp = Responsible.objects.create(last_name="Test", first_name="User", user=user)
    return user, resp


@pytest.fixture
def other_responsible(db: object) -> Responsible:
    """Return an unrelated Responsible (no linked user)."""
    return Responsible.objects.create(last_name="Other", first_name="Person")


# --- location_list ---


def test_location_list_redirects_anonymous() -> None:
    client = Client()
    response = client.get(reverse("catalogs:location-list"))
    assert response.status_code == 302
    assert response.url.startswith("/login/")


def test_location_list_shows_unlinked_message(db: object) -> None:
    user = User.objects.create_user(
        username="nolink", password="pw", email="nolink@example.com"
    )
    client = Client()
    client.force_login(user)
    response = client.get(reverse("catalogs:location-list"))
    assert response.status_code == 200
    assert "not linked" in response.content.decode().lower()


def test_location_list_empty(db: object, linked_user: tuple[User, Responsible]) -> None:
    user, _ = linked_user
    client = Client()
    client.force_login(user)
    response = client.get(reverse("catalogs:location-list"))
    assert response.status_code == 200
    assert "no personal locations" in response.content.decode().lower()


def test_location_list_shows_personal_locations(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    Location.objects.create(name="Desk-1", responsible=resp)
    Location.objects.create(name="Cabinet-A", responsible=resp)

    client = Client()
    client.force_login(user)
    response = client.get(reverse("catalogs:location-list"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "Desk-1" in content
    assert "Cabinet-A" in content


def test_location_list_does_not_show_other_locations(
    db: object, linked_user: tuple[User, Responsible], other_responsible: Responsible
) -> None:
    user, resp = linked_user
    Location.objects.create(name="My-Desk", responsible=resp)
    Location.objects.create(name="Other-Desk", responsible=other_responsible)

    client = Client()
    client.force_login(user)
    response = client.get(reverse("catalogs:location-list"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "My-Desk" in content
    assert "Other-Desk" not in content


def test_location_list_search_filters_by_name(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    Location.objects.create(name="Desk-001", responsible=resp)
    Location.objects.create(name="Cabinet-002", responsible=resp)
    Location.objects.create(name="Rack-003", responsible=resp)

    client = Client()
    client.force_login(user)

    response = client.get(reverse("catalogs:location-list"), {"q": "Rack"})
    content = response.content.decode()
    assert "Rack-003" in content
    assert "Desk-001" not in content
    assert "Cabinet-002" not in content
    assert "no locations found" not in content

    response = client.get(reverse("catalogs:location-list"), {"q": "NonExistent"})
    content = response.content.decode()
    assert "no locations found" in content.lower()

    response = client.get(reverse("catalogs:location-list"), {"q": ""})
    content = response.content.decode()
    assert "Desk-001" in content
    assert "Cabinet-002" in content
    assert "Rack-003" in content


# --- location_create ---


def test_location_create_get_returns_form(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, _ = linked_user
    client = Client()
    client.force_login(user)
    response = client.get(reverse("catalogs:location-create"))
    assert response.status_code == 200


def test_location_create_post_creates_location(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("catalogs:location-create"), {"name": "My Safe"}, follow=True
    )
    assert response.status_code == 200
    assert Location.objects.filter(name="My Safe", responsible=resp).exists()


def test_location_create_post_empty_name_shows_error(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, _ = linked_user
    client = Client()
    client.force_login(user)
    response = client.post(reverse("catalogs:location-create"), {"name": ""})
    assert response.status_code == 400
    assert "required" in response.content.decode().lower()


def test_location_create_unlinked_redirects_with_error(db: object) -> None:
    user = User.objects.create_user(
        username="nolink", password="pw", email="nolink@example.com"
    )
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("catalogs:location-create"), {"name": "My Desk"}, follow=True
    )
    assert response.status_code == 200
    assert "not linked" in response.content.decode().lower()


# --- location_edit ---


def test_location_edit_get_returns_form(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    location = Location.objects.create(name="Old Name", responsible=resp)
    client = Client()
    client.force_login(user)
    response = client.get(
        reverse("catalogs:location-edit", kwargs={"location_id": location.pk})
    )
    assert response.status_code == 200
    assert "Old Name" in response.content.decode()


def test_location_edit_post_updates_name(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    location = Location.objects.create(name="Old Name", responsible=resp)
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("catalogs:location-edit", kwargs={"location_id": location.pk}),
        {"name": "New Name"},
        follow=True,
    )
    assert response.status_code == 200
    location.refresh_from_db()
    assert location.name == "New Name"


def test_location_edit_correction_window_expired_shows_error(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    location = Location.objects.create(name="In Use Loc", responsible=resp)

    from catalogs.models import Status
    from devices.attributes import Category, Manufacturer, Model, Type
    from devices.models import Device
    from inventory.models import Item, Operation

    status = Status.objects.create(name="Active")
    category = Category.objects.create(name="C")
    device_type = Type.objects.create(name="T")
    manufacturer = Manufacturer.objects.create(name="M")
    device_model = Model.objects.create(name="M")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    item = Item.objects.create(inventory_number="INV-EDIT-LOCK", device=device)
    Operation.objects.create(
        item=item,
        responsible=resp,
        location=location,
        status=status,
    )

    Location.objects.filter(pk=location.pk).update(
        created_at=timezone.now() - timedelta(minutes=11),
    )

    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("catalogs:location-edit", kwargs={"location_id": location.pk}),
        {"name": "Renamed"},
        follow=True,
    )
    assert response.status_code == 200
    assert "10" in response.content.decode()
    location.refresh_from_db()
    assert location.name == "In Use Loc"


def test_location_edit_not_own_returns_404(
    db: object, linked_user: tuple[User, Responsible], other_responsible: Responsible
) -> None:
    user, _ = linked_user
    location = Location.objects.create(name="Their Desk", responsible=other_responsible)
    client = Client()
    client.force_login(user)
    response = client.get(
        reverse("catalogs:location-edit", kwargs={"location_id": location.pk})
    )
    assert response.status_code == 404


def test_location_edit_empty_name_shows_error(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    location = Location.objects.create(name="Test", responsible=resp)
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("catalogs:location-edit", kwargs={"location_id": location.pk}),
        {"name": ""},
    )
    assert response.status_code == 400
    assert "required" in response.content.decode().lower()


def test_location_edit_unlinked_redirects_with_error(db: object) -> None:
    user = User.objects.create_user(
        username="nolink", password="pw", email="nolink@example.com"
    )
    another_resp = Responsible.objects.create(last_name="Other", first_name="O")
    location = Location.objects.create(name="Some", responsible=another_resp)
    client = Client()
    client.force_login(user)
    response = client.get(
        reverse("catalogs:location-edit", kwargs={"location_id": location.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert "not linked" in response.content.decode().lower()


# --- location_delete ---


def test_location_delete_unlinked_redirects_with_error(db: object) -> None:
    user = User.objects.create_user(
        username="nolink", password="pw", email="nolink@example.com"
    )
    another_resp = Responsible.objects.create(last_name="Other", first_name="O")
    location = Location.objects.create(name="Some", responsible=another_resp)
    client = Client()
    client.force_login(user)
    response = client.get(
        reverse("catalogs:location-delete", kwargs={"location_id": location.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert "not linked" in response.content.decode().lower()


def test_location_delete_get_returns_confirmation(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    location = Location.objects.create(name="To Delete", responsible=resp)
    client = Client()
    client.force_login(user)
    response = client.get(
        reverse("catalogs:location-delete", kwargs={"location_id": location.pk})
    )
    assert response.status_code == 200
    assert "To Delete" in response.content.decode()


def test_location_delete_post_deletes_location(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    location = Location.objects.create(name="To Delete", responsible=resp)
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("catalogs:location-delete", kwargs={"location_id": location.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert not Location.objects.filter(pk=location.pk).exists()


def test_location_delete_not_own_returns_404(
    db: object, linked_user: tuple[User, Responsible], other_responsible: Responsible
) -> None:
    user, _ = linked_user
    location = Location.objects.create(name="Their Desk", responsible=other_responsible)
    client = Client()
    client.force_login(user)
    response = client.get(
        reverse("catalogs:location-delete", kwargs={"location_id": location.pk})
    )
    assert response.status_code == 404


def test_location_delete_in_use_shows_error(
    db: object, linked_user: tuple[User, Responsible]
) -> None:
    user, resp = linked_user
    location = Location.objects.create(name="In Use", responsible=resp)

    # Create a reference via the inventory fixtures
    from catalogs.models import Status
    from devices.attributes import Category, Manufacturer, Model, Type
    from devices.models import Device
    from inventory.models import Item, Operation

    status = Status.objects.create(name="Active")
    category = Category.objects.create(name="C")
    device_type = Type.objects.create(name="T")
    manufacturer = Manufacturer.objects.create(name="M")
    device_model = Model.objects.create(name="M")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )
    item = Item.objects.create(inventory_number="INV-LOC-USE", device=device)
    Operation.objects.create(
        item=item,
        responsible=resp,
        location=location,
        status=status,
    )

    client = Client()
    client.force_login(user)

    # GET confirmation should redirect with error
    response = client.get(
        reverse("catalogs:location-delete", kwargs={"location_id": location.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert "in use" in response.content.decode().lower()

    # POST should not delete
    response = client.post(
        reverse("catalogs:location-delete", kwargs={"location_id": location.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert Location.objects.filter(pk=location.pk).exists()
