"""
Тесты для админки приложения inventory.
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from ..admin import ItemAdmin, OperationAdmin
from ..models import Item, Operation
from .factories import ItemFactory, OperationFactory
from django.contrib import admin
from django.urls import reverse
from django.test import Client


@pytest.mark.django_db
class TestItemAdmin:
    """Тесты для админки модели Item."""

    def setup_method(self):
        """Подготовка тестового окружения."""
        self.site = AdminSite()
        self.admin = ItemAdmin(Item, self.site)
        self.factory = RequestFactory()
        self.item = ItemFactory()

    def test_current_status(self):
        """Тест метода current_status."""
        assert self.admin.current_status(self.item) == "-"
        operation = OperationFactory(item=self.item)
        assert self.admin.current_status(self.item) == operation.status.name

    def test_current_location(self):
        """Тест метода current_location."""
        assert self.admin.current_location(self.item) == "-"
        operation = OperationFactory(item=self.item)
        assert self.admin.current_location(self.item) == operation.location.name

    def test_current_responsible(self):
        """Тест метода current_responsible."""
        assert self.admin.current_responsible(self.item) == "-"
        operation = OperationFactory(item=self.item)
        assert self.admin.current_responsible(self.item) == operation.responsible


@pytest.mark.django_db
class TestOperationAdmin:
    """Тесты для админки модели Operation."""

    def setup_method(self):
        """Подготовка тестового окружения."""
        self.site = AdminSite()
        self.admin = OperationAdmin(Operation, self.site)
        self.factory = RequestFactory()
        self.operation = OperationFactory()

    def test_get_responsible_display(self):
        """Тест метода get_responsible_display."""
        expected_name = f"{self.operation.responsible.last_name} {self.operation.responsible.first_name} {self.operation.responsible.middle_name}"
        assert self.admin.get_responsible_display(self.operation) == expected_name 

@pytest.mark.django_db
def test_admin_registration():
    site = admin.site
    assert isinstance(site._registry[Item], ItemAdmin)
    assert isinstance(site._registry[Operation], OperationAdmin)

@pytest.mark.django_db
def test_admin_smoke(client, django_user_model):
    username = "admin"
    password = "password"
    user = django_user_model.objects.create_superuser(username=username, password=password, email="admin@example.com")
    client = Client()
    client.login(username=username, password=password)
    for model, name in [
        (Item, "item"),
        (Operation, "operation"),
    ]:
        url = reverse(f"admin:inventory_{name}_changelist")
        resp = client.get(url)
        assert resp.status_code == 200

@pytest.mark.django_db
def test_item_admin_settings():
    admin_obj = ItemAdmin(Item, admin.site)
    assert admin_obj.list_display == (
        "inventory_number",
        "device",
        "serial_number",
        "updated_at",
        "created_at",
    )
    assert admin_obj.list_display_links == ("inventory_number", "device", "serial_number")
    assert admin_obj.readonly_fields == ("updated_at", "created_at", "current_status", "current_location", "current_responsible")
    assert admin_obj.autocomplete_fields == ["device"]
    assert admin_obj.fieldsets[0][1]["fields"] == (
        "inventory_number",
        "device",
        "serial_number",
        "notes",
        "updated_at",
        "created_at",
    )
    assert admin_obj.fieldsets[1][0] == "Эксплуатация"
    assert set(admin_obj.fieldsets[1][1]["fields"]) == {"current_status", "current_responsible", "current_location"}

@pytest.mark.django_db
def test_item_admin_methods():
    admin_obj = ItemAdmin(Item, admin.site)
    item = ItemFactory()
    assert admin_obj.current_status(item) == (item.current_status or "-")
    assert admin_obj.current_location(item) == (item.current_location or "-")
    assert admin_obj.current_responsible(item) == (item.current_responsible or "-")
    assert admin_obj.current_status.short_description == "Статус"
    assert admin_obj.current_location.short_description == "Местоположение"
    assert admin_obj.current_responsible.short_description == "Ответственный"

@pytest.mark.django_db
def test_operation_admin_settings():
    admin_obj = OperationAdmin(Operation, admin.site)
    assert admin_obj.list_display == (
        "item",
        "status",
        "responsible",
        "location",
        "updated_at",
        "created_at",
    )
    assert admin_obj.list_display_links == ("item", "status", "location", "responsible")
    assert admin_obj.readonly_fields == ("created_at", "updated_at")
    assert set(admin_obj.autocomplete_fields) == {"item", "status", "location", "responsible"}
    assert admin_obj.fieldsets[0][1]["fields"] == (
        "item",
        "status",
        "responsible",
        "location",
        "notes",
        "updated_at",
        "created_at",
    )

@pytest.mark.django_db
def test_operation_admin_methods():
    admin_obj = OperationAdmin(Operation, admin.site)
    operation = OperationFactory()
    assert admin_obj.get_responsible_display(operation) == operation.responsible.get_full_name()
    assert admin_obj.get_responsible_display.short_description == "Ответственный"

@pytest.mark.django_db
def test_item_admin_search(client, django_user_model):
    """Тест поиска в админке Item."""
    # Создаем суперпользователя
    username = "admin"
    password = "password"
    user = django_user_model.objects.create_superuser(
        username=username, password=password, email="admin@example.com"
    )
    client.login(username=username, password=password)

    # Создаем тестовые данные
    item = ItemFactory()
    url = reverse("admin:inventory_item_changelist")

    # Тестируем поиск по инвентарному номеру
    resp = client.get(url, {"q": item.inventory_number})
    assert resp.status_code == 200
    assert item.inventory_number in resp.content.decode()

    # Тестируем поиск по серийному номеру
    resp = client.get(url, {"q": item.serial_number})
    assert resp.status_code == 200
    assert item.serial_number in resp.content.decode()

    # Тестируем поиск по категории устройства
    resp = client.get(url, {"q": item.device.category.name})
    assert resp.status_code == 200
    assert item.inventory_number in resp.content.decode()


@pytest.mark.django_db
def test_item_admin_filters(client, django_user_model):
    """Тест фильтров в админке Item."""
    # Создаем суперпользователя
    username = "admin"
    password = "password"
    user = django_user_model.objects.create_superuser(
        username=username, password=password, email="admin@example.com"
    )
    client.login(username=username, password=password)

    # Создаем тестовые данные
    item = ItemFactory()
    url = reverse("admin:inventory_item_changelist")

    # Тестируем фильтр по категории устройства
    resp = client.get(url, {"device__category__id__exact": item.device.category.id})
    assert resp.status_code == 200
    assert item.inventory_number in resp.content.decode()

    # Тестируем фильтр по дате создания
    resp = client.get(url, {"created_at__year": str(item.created_at.year)})
    assert resp.status_code == 200
    assert item.inventory_number in resp.content.decode()


@pytest.mark.django_db
def test_operation_admin_search(client, django_user_model):
    """Тест поиска в админке Operation."""
    # Создаем суперпользователя
    username = "admin"
    password = "password"
    user = django_user_model.objects.create_superuser(
        username=username, password=password, email="admin@example.com"
    )
    client.login(username=username, password=password)

    # Создаем тестовые данные
    operation = OperationFactory()
    url = reverse("admin:inventory_operation_changelist")

    # Тестируем поиск по инвентарному номеру
    resp = client.get(url, {"q": operation.item.inventory_number})
    assert resp.status_code == 200
    assert operation.item.inventory_number in resp.content.decode()

    # Тестируем поиск по статусу
    resp = client.get(url, {"q": operation.status.name})
    assert resp.status_code == 200
    assert operation.status.name in resp.content.decode()

    # Тестируем поиск по ответственному
    resp = client.get(url, {"q": operation.responsible.last_name})
    assert resp.status_code == 200
    assert operation.responsible.last_name in resp.content.decode()


@pytest.mark.django_db
def test_operation_admin_filters(client, django_user_model):
    """Тест фильтров в админке Operation."""
    # Создаем суперпользователя
    username = "admin"
    password = "password"
    user = django_user_model.objects.create_superuser(
        username=username, password=password, email="admin@example.com"
    )
    client.login(username=username, password=password)

    # Создаем тестовые данные
    operation = OperationFactory()
    url = reverse("admin:inventory_operation_changelist")

    # Тестируем фильтр по статусу
    resp = client.get(url, {"status__id__exact": operation.status.id})
    assert resp.status_code == 200
    assert operation.item.inventory_number in resp.content.decode()

    # Тестируем фильтр по ответственному
    resp = client.get(url, {"responsible__id__exact": operation.responsible.id})
    assert resp.status_code == 200
    assert operation.item.inventory_number in resp.content.decode()

    # Тестируем фильтр по дате создания
    resp = client.get(url, {"created_at__year": str(operation.created_at.year)})
    assert resp.status_code == 200
    assert operation.item.inventory_number in resp.content.decode()


@pytest.mark.django_db
def test_admin_permissions(client, django_user_model):
    """Тест прав доступа к админке."""
    # Создаем обычного пользователя
    username = "user"
    password = "password"
    user = django_user_model.objects.create_user(
        username=username, password=password, email="user@example.com"
    )
    client.login(username=username, password=password)

    # Проверяем, что обычный пользователь не имеет доступа
    for model, name in [
        (Item, "item"),
        (Operation, "operation"),
    ]:
        url = reverse(f"admin:inventory_{name}_changelist")
        resp = client.get(url)
        assert resp.status_code == 302  # Редирект на страницу входа

    # Создаем суперпользователя
    admin_username = "admin"
    admin_password = "password"
    admin_user = django_user_model.objects.create_superuser(
        username=admin_username, password=admin_password, email="admin@example.com"
    )
    client.login(username=admin_username, password=admin_password)

    # Проверяем, что суперпользователь имеет доступ
    for model, name in [
        (Item, "item"),
        (Operation, "operation"),
    ]:
        url = reverse(f"admin:inventory_{name}_changelist")
        resp = client.get(url)
        assert resp.status_code == 200 