"""
Фикстуры для тестов приложения catalogs.
"""
import pytest
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from catalogs.models import Device, Location, Responsible, Status
from devices.models import Category, Manufacturer, Model, Type
from devices.tests.conftest import (
    CategoryFactory,
    ManufacturerFactory,
    ModelFactory,
    TypeFactory,
)


class UserFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых пользователей.
    """
    class Meta:
        model = User

    username = Faker('user_name')
    email = Faker('email')
    password = Faker('password')


class DeviceFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых устройств.
    """
    class Meta:
        model = Device

    category = SubFactory(CategoryFactory)
    type = SubFactory(TypeFactory)
    manufacturer = SubFactory(ManufacturerFactory)
    model = SubFactory(ModelFactory)
    notes = Faker('sentence')


class LocationFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых расположений.
    """
    class Meta:
        model = Location

    name = Faker('word')
    notes = Faker('sentence')


class ResponsibleFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых ответственных.
    """
    class Meta:
        model = Responsible

    last_name = Faker('last_name')
    first_name = Faker('first_name')
    middle_name = Faker('first_name')
    employee_id = Faker('numerify', text='#####')
    user = SubFactory(UserFactory)


class StatusFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых статусов.
    """
    class Meta:
        model = Status

    name = Faker('word')
    notes = Faker('sentence')


@pytest.fixture
def user():
    """
    Фикстура для создания тестового пользователя.
    """
    return UserFactory()


@pytest.fixture
def device():
    """
    Фикстура для создания тестового устройства.
    """
    return DeviceFactory()


@pytest.fixture
def location():
    """
    Фикстура для создания тестового расположения.
    """
    return LocationFactory()


@pytest.fixture
def responsible():
    """
    Фикстура для создания тестового ответственного.
    """
    return ResponsibleFactory()


@pytest.fixture
def status():
    """
    Фикстура для создания тестового статуса.
    """
    return StatusFactory() 