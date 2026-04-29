import pytest
from django.contrib.admin.sites import AdminSite
from django.db.models import QuerySet
from django.test import RequestFactory

from devices.admin import DeviceAdmin
from devices.models import Device


@pytest.mark.django_db
def test_device_admin_queryset_is_select_related() -> None:
    site = AdminSite()
    admin_obj = DeviceAdmin(Device, site)
    rf = RequestFactory()
    request = rf.get("/")

    qs = admin_obj.get_queryset(request)
    assert isinstance(qs, QuerySet)
    assert "category" in qs.query.select_related
    assert "type" in qs.query.select_related
    assert "manufacturer" in qs.query.select_related
    assert "model" in qs.query.select_related
