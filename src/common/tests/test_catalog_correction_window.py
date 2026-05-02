"""Catalog correction window (``CatalogCorrectionWindowMixin`` + admin)."""

from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import RequestFactory, override_settings
from django.utils import timezone
from django.utils.translation import gettext as _

from catalogs.admin import LocationAdmin
from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation


def _staff_with_location_perms(username: str):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="password",
        is_staff=True,
    )
    content_type = ContentType.objects.get_for_model(Location)
    for codename in ("change_location", "delete_location", "view_location"):
        user.user_permissions.add(
            Permission.objects.get(content_type=content_type, codename=codename)
        )
    return user


def _staff_view_only_location(username: str):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="password",
        is_staff=True,
    )
    content_type = ContentType.objects.get_for_model(Location)
    user.user_permissions.add(
        Permission.objects.get(content_type=content_type, codename="view_location")
    )
    return user


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_location_clean_allows_stale_window_when_unused() -> None:
    loc = Location.objects.create(name="Loc-unused")
    Location.objects.filter(pk=loc.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    loc.refresh_from_db()
    loc.name = "Loc-unused-renamed"
    loc.full_clean()
    loc.save()
    loc.refresh_from_db()
    assert loc.name == "Loc-unused-renamed"


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_location_clean_rejects_stale_window_when_referenced() -> None:
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
    item = Item.objects.create(inventory_number="INV-CAT-LOC", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    loc = Location.objects.create(name="Loc-used")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=loc,
    )
    Location.objects.filter(pk=loc.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    loc.refresh_from_db()
    loc.name = "Loc-should-fail"

    with pytest.raises(ValidationError) as exc:
        loc.full_clean()

    assert (
        exc.value.error_dict["__all__"][0].code == "catalog_correction_window_expired"
    )


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_location_admin_staff_denies_change_when_used_and_stale() -> None:
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
    item = Item.objects.create(inventory_number="INV-CAT-LOC-ADM", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    loc = Location.objects.create(name="Loc-adm")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=loc,
    )
    Location.objects.filter(pk=loc.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    loc.refresh_from_db()

    site = AdminSite()
    admin_obj = LocationAdmin(Location, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_with_location_perms("staff-loc-win")

    assert admin_obj.has_change_permission(request, obj=loc) is False
    assert admin_obj.has_delete_permission(request, obj=loc) is False


@pytest.mark.django_db
@override_settings(LANGUAGE_CODE="en", INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_location_admin_omits_lock_fieldset_without_model_change_permission() -> None:
    """View-only staff must not see catalog correction-window copy."""

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
    item = Item.objects.create(inventory_number="INV-CAT-LOC-VIEW", device=device)
    status = Status.objects.create(name="In stock")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    loc = Location.objects.create(name="Loc-view-only")
    Operation.objects.create(
        item=item,
        status=status,
        responsible=responsible,
        location=loc,
    )
    Location.objects.filter(pk=loc.pk).update(
        updated_at=timezone.now() - timedelta(minutes=11),
    )
    loc.refresh_from_db()

    site = AdminSite()
    admin_obj = LocationAdmin(Location, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = _staff_view_only_location("staff-loc-view-only")
    lock_title = str(_("Editing restrictions"))
    fieldsets = admin_obj.get_fieldsets(request, loc)
    assert not any(fs[0] is not None and str(fs[0]) == lock_title for fs in fieldsets)
