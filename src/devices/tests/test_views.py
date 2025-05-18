import pytest
from django.urls import reverse
from django.test import Client
from catalogs.models import Device
from devices.tests.factories import DeviceFactory


@pytest.mark.django_db
def test_device_list_view_anonymous(client):
    """Тест доступа к списку устройств для неавторизованного пользователя."""
    url = reverse('devices:device-list')
    response = client.get(url)
    assert response.status_code == 302  # Редирект на страницу входа


@pytest.mark.django_db
def test_device_list_view_authenticated(client, django_user_model):
    """Тест доступа к списку устройств для авторизованного пользователя."""
    # Создаем пользователя
    username = "user"
    password = "password"
    user = django_user_model.objects.create_user(
        username=username, password=password, email="user@example.com"
    )
    client.login(username=username, password=password)

    # Создаем тестовые данные
    device = DeviceFactory()

    # Проверяем доступ к списку
    url = reverse('devices:device-list')
    response = client.get(url)
    assert response.status_code == 200
    assert device.model.name in response.content.decode()


@pytest.mark.django_db
def test_device_create_view_anonymous(client):
    """Тест доступа к созданию устройства для неавторизованного пользователя."""
    url = reverse('devices:device-create')
    response = client.get(url)
    assert response.status_code == 302  # Редирект на страницу входа


@pytest.mark.django_db
def test_device_create_view_authenticated(client, django_user_model):
    """Тест создания устройства авторизованным пользователем."""
    # Создаем пользователя
    username = "user"
    password = "password"
    user = django_user_model.objects.create_user(
        username=username, password=password, email="user@example.com"
    )
    client.login(username=username, password=password)

    # Проверяем доступ к форме создания
    url = reverse('devices:device-create')
    response = client.get(url)
    assert response.status_code == 200

    # Создаем устройство
    device_data = {
        'category': DeviceFactory().category.id,
        'type': DeviceFactory().type.id,
        'manufacturer': DeviceFactory().manufacturer.id,
        'model': DeviceFactory().model.id,
        'notes': 'Test notes'
    }
    response = client.post(url, device_data)
    assert response.status_code == 302  # Редирект после успешного создания
    assert Device.objects.filter(notes='Test notes').exists()


@pytest.mark.django_db
def test_device_update_view_anonymous(client):
    """Тест доступа к изменению устройства для неавторизованного пользователя."""
    device = DeviceFactory()
    url = reverse('devices:device-update', kwargs={'pk': device.pk})
    response = client.get(url)
    assert response.status_code == 302  # Редирект на страницу входа


@pytest.mark.django_db
def test_device_update_view_authenticated(client, django_user_model):
    """Тест изменения устройства авторизованным пользователем."""
    # Создаем пользователя
    username = "user"
    password = "password"
    user = django_user_model.objects.create_user(
        username=username, password=password, email="user@example.com"
    )
    client.login(username=username, password=password)

    # Создаем тестовые данные
    device = DeviceFactory()
    url = reverse('devices:device-update', kwargs={'pk': device.pk})

    # Проверяем доступ к форме изменения
    response = client.get(url)
    assert response.status_code == 200

    # Изменяем устройство
    device_data = {
        'category': device.category.id,
        'type': device.type.id,
        'manufacturer': device.manufacturer.id,
        'model': device.model.id,
        'notes': 'Updated notes'
    }
    response = client.post(url, device_data)
    assert response.status_code == 302  # Редирект после успешного изменения
    assert Device.objects.get(pk=device.pk).notes == 'Updated notes'


@pytest.mark.django_db
def test_device_delete_view_anonymous(client):
    """Тест доступа к удалению устройства для неавторизованного пользователя."""
    device = DeviceFactory()
    url = reverse('devices:device-delete', kwargs={'pk': device.pk})
    response = client.get(url)
    assert response.status_code == 302  # Редирект на страницу входа


@pytest.mark.django_db
def test_device_delete_view_authenticated(client, django_user_model):
    """Тест удаления устройства авторизованным пользователем."""
    # Создаем пользователя
    username = "user"
    password = "password"
    user = django_user_model.objects.create_user(
        username=username, password=password, email="user@example.com"
    )
    client.login(username=username, password=password)

    # Создаем тестовые данные
    device = DeviceFactory()
    url = reverse('devices:device-delete', kwargs={'pk': device.pk})

    # Проверяем доступ к форме удаления
    response = client.get(url)
    assert response.status_code == 200

    # Удаляем устройство
    response = client.post(url)
    assert response.status_code == 302  # Редирект после успешного удаления
    assert not Device.objects.filter(pk=device.pk).exists() 