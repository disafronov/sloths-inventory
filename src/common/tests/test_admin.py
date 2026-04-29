import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from common.admin import BaseAdmin
from inventory.models import Item


@pytest.mark.django_db
def test_base_admin_format_empty_value() -> None:
    site = AdminSite()
    admin_obj = BaseAdmin(Item, site)

    assert admin_obj._format_empty_value("") == "-"
    assert admin_obj._format_empty_value(None) == "-"
    assert admin_obj._format_empty_value("x") == "x"


@pytest.mark.django_db
def test_base_admin_fieldsets_main_fields_injected() -> None:
    site = AdminSite()
    admin_obj = BaseAdmin(Item, site)
    rf = RequestFactory()

    request = rf.get("/")
    fieldsets = admin_obj.get_fieldsets(request)

    assert isinstance(fieldsets, list)
    assert fieldsets[0][0] is None
    assert "fields" in fieldsets[0][1]
