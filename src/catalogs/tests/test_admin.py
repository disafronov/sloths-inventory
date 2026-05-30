import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.test import RequestFactory
from django.utils import translation
from django.utils.translation import gettext as _

from catalogs.admin import LocationAdmin, ResponsibleAdmin
from catalogs.models import Location, Responsible


@pytest.mark.django_db
def test_location_admin_displays_global_and_personal_location_values() -> None:
    global_location = Location.on_hand()
    responsible = Responsible.objects.create(last_name="Owner", first_name="User")
    personal_location = Location.objects.create(name="Desk", responsible=responsible)
    site = AdminSite()
    admin_obj = LocationAdmin(Location, site)
    rf = RequestFactory()
    request = rf.get("/")

    with translation.override("en"):
        assert admin_obj.location_display_name(global_location) == "On hand"
        assert admin_obj.responsible_display(global_location) == "Global: on_hand"
        assert admin_obj.responsible_display(personal_location) == str(responsible)
        assert admin_obj.get_queryset(request).query.select_related == {
            "responsible": {}
        }

    with translation.override("ru"):
        expected = _("Global: %(key)s") % {"key": global_location.name}
        assert admin_obj.responsible_display(global_location) == expected


@pytest.mark.django_db
def test_location_admin_blocks_system_location_editing_with_lock_panel() -> None:
    location = Location.on_hand()
    user = User.objects.create_user("editor", password="pw", is_staff=True)
    content_type = ContentType.objects.get_for_model(Location)
    permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=["change_location", "delete_location"],
    )
    user.user_permissions.set(permissions)
    site = AdminSite()
    admin_obj = LocationAdmin(Location, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user

    assert admin_obj.has_change_permission(request, location) is False
    assert admin_obj.has_delete_permission(request, location) is False

    fieldsets = admin_obj.get_fieldsets(request, location)
    lock_descriptions = [fieldset[1].get("description", "") for fieldset in fieldsets]
    lock_msg = admin_obj.system_location_lock_message(location)
    assert lock_msg is not None
    assert any(lock_msg in str(text) for text in lock_descriptions)

    view_only_user = User.objects.create_user("viewer", password="pw", is_staff=True)
    view_only_request = rf.get("/")
    view_only_request.user = view_only_user
    view_only_fieldsets = admin_obj.get_fieldsets(view_only_request, location)
    lock_descriptions = [
        fieldset[1].get("description", "") for fieldset in view_only_fieldsets
    ]
    assert not any(lock_msg in str(text) for text in lock_descriptions)
    main_fields = view_only_fieldsets[0][1]["fields"]
    assert "location_display_name" in main_fields
    assert "responsible_display" in main_fields
    assert "name" not in main_fields
    assert "responsible" not in main_fields


@pytest.mark.django_db
def test_location_admin_readonly_fields_for_system_location() -> None:
    location = Location.on_hand()
    user = User.objects.create_user("viewer", password="pw", is_staff=True)
    site = AdminSite()
    admin_obj = LocationAdmin(Location, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user

    readonly = admin_obj.get_readonly_fields(request, location)
    assert "location_display_name" in readonly
    assert "responsible_display" in readonly

    assert "location_display_name" not in admin_obj.get_readonly_fields(request)
    assert "responsible_display" not in admin_obj.get_readonly_fields(request)

    editor = User.objects.create_user("editor", password="pw", is_staff=True)
    ct = ContentType.objects.get_for_model(Location)
    editor.user_permissions.set(
        Permission.objects.filter(content_type=ct, codename__in=["change_location"])
    )
    req2 = rf.get("/")
    req2.user = editor
    regular = Location.objects.create(name="Office")
    readonly2 = admin_obj.get_readonly_fields(req2, regular)
    assert "location_display_name" not in readonly2
    assert "responsible_display" not in readonly2


@pytest.mark.django_db
def test_location_admin_allows_regular_location_editing() -> None:
    location = Location.objects.create(name="Office")
    user = User.objects.create_user("editor2", password="pw", is_staff=True)
    content_type = ContentType.objects.get_for_model(Location)
    permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=["change_location", "delete_location"],
    )
    user.user_permissions.set(permissions)
    site = AdminSite()
    admin_obj = LocationAdmin(Location, site)
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user

    assert admin_obj.has_change_permission(request, location) is True
    assert admin_obj.has_delete_permission(request, location) is True


@pytest.mark.django_db
def test_responsible_admin_queryset_is_select_related() -> None:
    site = AdminSite()
    admin_obj = ResponsibleAdmin(Responsible, site)
    rf = RequestFactory()
    request = rf.get("/")

    qs = admin_obj.get_queryset(request)
    assert isinstance(qs, QuerySet)
    assert "user" in qs.query.select_related
