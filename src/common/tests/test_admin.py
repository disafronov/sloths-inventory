import pytest
from django.contrib import admin
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


@pytest.mark.django_db
def test_base_admin_fieldsets_empty_super_result_is_handled(monkeypatch) -> None:
    site = AdminSite()
    admin_obj = BaseAdmin(Item, site)
    rf = RequestFactory()

    def _empty_fieldsets(_self, request, obj=None):
        return ()

    monkeypatch.setattr(admin.ModelAdmin, "get_fieldsets", _empty_fieldsets)

    request = rf.get("/")
    fieldsets = admin_obj.get_fieldsets(request)

    assert isinstance(fieldsets, list)
    assert len(fieldsets) == 1
    assert fieldsets[0][0] is None
