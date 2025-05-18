import pytest
from django.contrib import admin
from django.urls import reverse
from django.test import Client
from catalogs.models import Category, Manufacturer, Model, Type
from devices.admin import CategoryAdmin, ManufacturerAdmin, ModelAdmin, TypeAdmin
from devices.tests.factories import CategoryFactory, ManufacturerFactory, ModelFactory, TypeFactory

@pytest.mark.django_db
def test_admin_registration():
    site = admin.site
    assert isinstance(site._registry[Category], CategoryAdmin)
    assert isinstance(site._registry[Manufacturer], ManufacturerAdmin)
    assert isinstance(site._registry[Model], ModelAdmin)
    assert isinstance(site._registry[Type], TypeAdmin)

@pytest.mark.django_db
def test_admin_smoke(client, django_user_model):
    username = "admin"
    password = "password"
    user = django_user_model.objects.create_superuser(username=username, password=password, email="admin@example.com")
    client = Client()
    client.login(username=username, password=password)
    for model, name in [
        (Category, "category"),
        (Manufacturer, "manufacturer"),
        (Model, "model"),
        (Type, "type"),
    ]:
        url = reverse(f"admin:devices_{name}_changelist")
        resp = client.get(url)
        assert resp.status_code == 200

@pytest.mark.django_db
def test_category_admin_settings():
    admin_obj = CategoryAdmin(Category, admin.site)
    assert admin_obj.list_display == ("name", "updated_at", "created_at")
    assert admin_obj.list_display_links == ("name",)
    assert admin_obj.search_fields == ("name",)
    assert admin_obj.list_filter == ("updated_at", "created_at")
    assert admin_obj.readonly_fields == ("created_at", "updated_at")
    assert admin_obj.fieldsets[0][1]["fields"] == ("name", "notes", "updated_at", "created_at")

@pytest.mark.django_db
def test_manufacturer_admin_settings():
    admin_obj = ManufacturerAdmin(Manufacturer, admin.site)
    assert admin_obj.list_display == ("name", "updated_at", "created_at")
    assert admin_obj.list_display_links == ("name",)
    assert admin_obj.search_fields == ("name",)
    assert admin_obj.list_filter == ("updated_at", "created_at")
    assert admin_obj.readonly_fields == ("created_at", "updated_at")
    assert admin_obj.fieldsets[0][1]["fields"] == ("name", "notes", "updated_at", "created_at")

@pytest.mark.django_db
def test_model_admin_settings():
    admin_obj = ModelAdmin(Model, admin.site)
    assert admin_obj.list_display == ("name", "updated_at", "created_at")
    assert admin_obj.list_display_links == ("name",)
    assert admin_obj.search_fields == ("name",)
    assert admin_obj.list_filter == ("updated_at", "created_at")
    assert admin_obj.readonly_fields == ("created_at", "updated_at")
    assert admin_obj.fieldsets[0][1]["fields"] == ("name", "notes", "updated_at", "created_at")

@pytest.mark.django_db
def test_type_admin_settings():
    admin_obj = TypeAdmin(Type, admin.site)
    assert admin_obj.list_display == ("name", "updated_at", "created_at")
    assert admin_obj.list_display_links == ("name",)
    assert admin_obj.search_fields == ("name",)
    assert admin_obj.list_filter == ("updated_at", "created_at")
    assert admin_obj.readonly_fields == ("created_at", "updated_at")
    assert admin_obj.fieldsets[0][1]["fields"] == ("name", "notes", "updated_at", "created_at") 