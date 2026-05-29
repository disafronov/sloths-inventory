import pytest
from django.contrib.admin.sites import AdminSite
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
def test_responsible_admin_queryset_is_select_related() -> None:
    site = AdminSite()
    admin_obj = ResponsibleAdmin(Responsible, site)
    rf = RequestFactory()
    request = rf.get("/")

    qs = admin_obj.get_queryset(request)
    assert isinstance(qs, QuerySet)
    assert "user" in qs.query.select_related
