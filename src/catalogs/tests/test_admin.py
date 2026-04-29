import pytest
from django.contrib.admin.sites import AdminSite
from django.db.models import QuerySet
from django.test import RequestFactory

from catalogs.admin import ResponsibleAdmin
from catalogs.models import Responsible


@pytest.mark.django_db
def test_responsible_admin_queryset_is_select_related() -> None:
    site = AdminSite()
    admin_obj = ResponsibleAdmin(Responsible, site)
    rf = RequestFactory()
    request = rf.get("/")

    qs = admin_obj.get_queryset(request)
    assert isinstance(qs, QuerySet)
    assert "user" in qs.query.select_related
