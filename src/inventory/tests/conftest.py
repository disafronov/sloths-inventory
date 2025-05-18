"""
Фикстуры для тестов приложения inventory.
"""
import pytest
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from inventory.models import Item, Operation
from catalogs.models import Device, Location, Responsible, Status
from catalogs.tests.conftest import (
    DeviceFactory,
    LocationFactory,
    ResponsibleFactory,
    StatusFactory,
)


class ItemFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых экземпляров.
    """
    class Meta:
        model = Item

    inventory_number = Faker('numerify', text='TEST-###')
    device = SubFactory(DeviceFactory)
    serial_number = Faker('numerify', text='SN######')
    notes = Faker('sentence')


class OperationFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых операций.
    """
    class Meta:
        model = Operation

    item = SubFactory(ItemFactory)
    status = SubFactory(StatusFactory)
    responsible = SubFactory(ResponsibleFactory)
    location = SubFactory(LocationFactory)
    notes = Faker('sentence')


@pytest.fixture
def item():
    """
    Фикстура для создания тестового экземпляра.
    """
    return ItemFactory()


@pytest.fixture
def operation():
    """
    Фикстура для создания тестовой операции.
    """
    return OperationFactory() 