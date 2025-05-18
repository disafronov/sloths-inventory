"""
Тесты для админ-панели приложения catalogs.
"""
import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from catalogs.admin import (
    DeviceAdmin,
    LocationAdmin,
    ResponsibleAdmin,
    StatusAdmin,
    CustomUserAdmin,
    ResponsibleInline,
)
from catalogs.models import Device, Location, Responsible, Status
from catalogs.tests.factories import (
    DeviceFactory,
    LocationFactory,
    ResponsibleFactory,
    StatusFactory,
    UserFactory,
)


class MockRequest:
    pass


class MockSuperUser:
    def has_perm(self, perm):
        return True


@pytest.mark.django_db
class TestDeviceAdmin:
    def test_list_display(self):
        admin = DeviceAdmin(Device, AdminSite())
        assert admin.list_display == (
            "category",
            "type",
            "manufacturer",
            "model",
            "updated_at",
            "created_at",
        )

    def test_list_display_links(self):
        admin = DeviceAdmin(Device, AdminSite())
        assert admin.list_display_links == ("category", "type", "manufacturer", "model")

    def test_list_filter(self):
        admin = DeviceAdmin(Device, AdminSite())
        assert admin.list_filter == (
            "category",
            "type",
            "manufacturer",
            "model",
            "updated_at",
            "created_at",
        )

    def test_search_fields(self):
        admin = DeviceAdmin(Device, AdminSite())
        assert admin.search_fields == (
            "category__name",
            "type__name",
            "manufacturer__name",
            "model__name",
        )

    def test_readonly_fields(self):
        admin = DeviceAdmin(Device, AdminSite())
        assert admin.readonly_fields == ("updated_at", "created_at")

    def test_autocomplete_fields(self):
        admin = DeviceAdmin(Device, AdminSite())
        assert admin.autocomplete_fields == ["category", "type", "manufacturer", "model"]

    def test_fieldsets(self):
        admin = DeviceAdmin(Device, AdminSite())
        assert len(admin.fieldsets) == 1
        assert admin.fieldsets[0][0] is None
        assert admin.fieldsets[0][1]["fields"] == (
            "category",
            "type",
            "manufacturer",
            "model",
            "notes",
            "updated_at",
            "created_at",
        )


@pytest.mark.django_db
class TestLocationAdmin:
    def test_list_display(self):
        admin = LocationAdmin(Location, AdminSite())
        assert admin.list_display == ("name", "updated_at", "created_at")

    def test_list_display_links(self):
        admin = LocationAdmin(Location, AdminSite())
        assert admin.list_display_links == ("name",)

    def test_list_filter(self):
        admin = LocationAdmin(Location, AdminSite())
        assert admin.list_filter == ("updated_at", "created_at")

    def test_search_fields(self):
        admin = LocationAdmin(Location, AdminSite())
        assert admin.search_fields == ("name",)

    def test_ordering(self):
        admin = LocationAdmin(Location, AdminSite())
        assert admin.ordering == ["name"]

    def test_readonly_fields(self):
        admin = LocationAdmin(Location, AdminSite())
        assert admin.readonly_fields == ("created_at", "updated_at")

    def test_fieldsets(self):
        admin = LocationAdmin(Location, AdminSite())
        assert len(admin.fieldsets) == 1
        assert admin.fieldsets[0][0] is None
        assert admin.fieldsets[0][1]["fields"] == ("name", "notes", "updated_at", "created_at")


@pytest.mark.django_db
class TestResponsibleAdmin:
    def test_list_display(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert admin.list_display == (
            "get_full_name",
            "employee_id",
            "user",
            "updated_at",
            "created_at",
        )

    def test_list_display_links(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert admin.list_display_links == ("get_full_name",)

    def test_list_filter(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert admin.list_filter == ("updated_at", "created_at")

    def test_search_fields(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert admin.search_fields == (
            "last_name",
            "first_name",
            "middle_name",
            "employee_id",
            "user__username",
        )

    def test_ordering(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert admin.ordering == ["last_name", "first_name", "middle_name"]

    def test_get_full_name(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        responsible = ResponsibleFactory()
        assert admin.get_full_name(responsible) == responsible.get_full_name()
        assert admin.get_full_name.short_description == "Полное имя"
        assert admin.get_full_name.admin_order_field == "last_name"

    def test_readonly_fields(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert admin.readonly_fields == ("created_at", "updated_at")

    def test_autocomplete_fields(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert admin.autocomplete_fields == ["user"]

    def test_fieldsets(self):
        admin = ResponsibleAdmin(Responsible, AdminSite())
        assert len(admin.fieldsets) == 1
        assert admin.fieldsets[0][0] is None
        assert admin.fieldsets[0][1]["fields"] == (
            "last_name",
            "first_name",
            "middle_name",
            "employee_id",
            "user",
            "notes",
            "updated_at",
            "created_at",
        )


@pytest.mark.django_db
class TestStatusAdmin:
    def test_list_display(self):
        admin = StatusAdmin(Status, AdminSite())
        assert admin.list_display == ("name", "updated_at", "created_at")

    def test_list_display_links(self):
        admin = StatusAdmin(Status, AdminSite())
        assert admin.list_display_links == ("name",)

    def test_list_filter(self):
        admin = StatusAdmin(Status, AdminSite())
        assert admin.list_filter == ("updated_at", "created_at")

    def test_search_fields(self):
        admin = StatusAdmin(Status, AdminSite())
        assert admin.search_fields == ("name",)

    def test_ordering(self):
        admin = StatusAdmin(Status, AdminSite())
        assert admin.ordering == ["name"]

    def test_readonly_fields(self):
        admin = StatusAdmin(Status, AdminSite())
        assert admin.readonly_fields == ("created_at", "updated_at")

    def test_fieldsets(self):
        admin = StatusAdmin(Status, AdminSite())
        assert len(admin.fieldsets) == 1
        assert admin.fieldsets[0][0] is None
        assert admin.fieldsets[0][1]["fields"] == ("name", "notes", "updated_at", "created_at")


@pytest.mark.django_db
class TestResponsibleInline:
    def test_model(self):
        inline = ResponsibleInline(Responsible, AdminSite())
        assert inline.model == Responsible
        assert not inline.can_delete
        assert inline.verbose_name_plural == "Ответственный"
        assert inline.fk_name == "user"


@pytest.mark.django_db
class TestCustomUserAdmin:
    def test_inlines(self):
        admin = CustomUserAdmin(User, AdminSite())
        assert admin.inlines == (ResponsibleInline,)

    def test_get_full_name_with_responsible(self):
        admin = CustomUserAdmin(User, AdminSite())
        user = UserFactory()
        responsible = ResponsibleFactory(user=user)
        assert admin.get_full_name(user) == responsible.get_full_name()

    def test_get_full_name_without_responsible(self):
        admin = CustomUserAdmin(User, AdminSite())
        user = UserFactory()
        assert admin.get_full_name(user) == user.get_full_name()
        assert admin.get_full_name.short_description == "Полное имя"


@pytest.mark.django_db
def test_admin_registration():
    # Проверяем, что модели зарегистрированы в админке
    site = admin.site
    assert isinstance(site._registry[Device], DeviceAdmin)
    assert isinstance(site._registry[Location], LocationAdmin)
    assert isinstance(site._registry[Responsible], ResponsibleAdmin)
    assert isinstance(site._registry[Status], StatusAdmin)
    assert isinstance(site._registry[User], CustomUserAdmin)


@pytest.mark.django_db
def test_admin_smoke(client, django_user_model):
    # Smoke-тесты для страниц админки
    username = "admin"
    password = "password"
    user = django_user_model.objects.create_superuser(username=username, password=password, email="admin@example.com")
    client = Client()
    client.login(username=username, password=password)
    for model, name in [
        (Device, "device"),
        (Location, "location"),
        (Responsible, "responsible"),
        (Status, "status"),
        (User, "user"),
    ]:
        url = reverse(f"admin:catalogs_{name}_changelist") if model != User else reverse("admin:auth_user_changelist")
        resp = client.get(url)
        assert resp.status_code == 200


@pytest.mark.django_db
def test_responsible_admin_get_full_name():
    obj = ResponsibleFactory()
    admin_obj = ResponsibleAdmin(Responsible, admin.site)
    assert admin_obj.get_full_name(obj) == obj.get_full_name()


@pytest.mark.django_db
def test_custom_user_admin_get_full_name():
    user = UserFactory()
    responsible = ResponsibleFactory(user=user)
    admin_obj = CustomUserAdmin(User, admin.site)
    assert admin_obj.get_full_name(user) == responsible.get_full_name()
    # Без responsible
    user2 = UserFactory()
    assert admin_obj.get_full_name(user2) == user2.get_full_name() 