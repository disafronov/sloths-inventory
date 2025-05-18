"""Тесты для фикстур в conftest.py."""
import pytest
from django.contrib.auth.models import User
from catalogs.models import Device, Location, Responsible, Status
from catalogs.tests.conftest import (
    UserFactory,
    DeviceFactory,
    LocationFactory,
    ResponsibleFactory,
    StatusFactory,
)


@pytest.mark.django_db
def test_user_factory():
    """Тест фабрики пользователей."""
    user = UserFactory()
    assert isinstance(user, User)
    assert user.username
    assert user.email
    assert user.password


@pytest.mark.django_db
def test_device_factory():
    """Тест фабрики устройств."""
    device = DeviceFactory()
    assert isinstance(device, Device)
    assert device.category
    assert device.type
    assert device.manufacturer
    assert device.model
    assert device.notes


@pytest.mark.django_db
def test_location_factory():
    """Тест фабрики расположений."""
    location = LocationFactory()
    assert isinstance(location, Location)
    assert location.name
    assert location.notes


@pytest.mark.django_db
def test_responsible_factory():
    """Тест фабрики ответственных."""
    responsible = ResponsibleFactory()
    assert isinstance(responsible, Responsible)
    assert responsible.last_name
    assert responsible.first_name
    assert responsible.middle_name
    assert responsible.employee_id
    assert responsible.user


@pytest.mark.django_db
def test_status_factory():
    """Тест фабрики статусов."""
    status = StatusFactory()
    assert isinstance(status, Status)
    assert status.name
    assert status.notes


@pytest.mark.django_db
def test_user_fixture(user):
    """Тест фикстуры пользователя."""
    assert isinstance(user, User)
    assert user.username
    assert user.email
    assert user.password


@pytest.mark.django_db
def test_device_fixture(device):
    """Тест фикстуры устройства."""
    assert isinstance(device, Device)
    assert device.category
    assert device.type
    assert device.manufacturer
    assert device.model
    assert device.notes


@pytest.mark.django_db
def test_location_fixture(location):
    """Тест фикстуры расположения."""
    assert isinstance(location, Location)
    assert location.name
    assert location.notes


@pytest.mark.django_db
def test_responsible_fixture(responsible):
    """Тест фикстуры ответственного."""
    assert isinstance(responsible, Responsible)
    assert responsible.last_name
    assert responsible.first_name
    assert responsible.middle_name
    assert responsible.employee_id
    assert responsible.user


@pytest.mark.django_db
def test_status_fixture(status):
    """Тест фикстуры статуса."""
    assert isinstance(status, Status)
    assert status.name
    assert status.notes 