"""
Фабрики для тестов приложения inventory.
"""
import factory
from factory.django import DjangoModelFactory
from ..models import Item, Operation
from catalogs.tests.factories import DeviceFactory, StatusFactory, LocationFactory, ResponsibleFactory


class ItemFactory(DjangoModelFactory):
    """Фабрика для создания тестовых экземпляров."""
    class Meta:
        model = Item

    inventory_number = factory.Sequence(lambda n: f"INV{n:06d}")
    device = factory.SubFactory(DeviceFactory)
    serial_number = factory.Sequence(lambda n: f"SN{n:08d}")
    notes = "Test notes"


class OperationFactory(DjangoModelFactory):
    """Фабрика для создания тестовых операций."""
    class Meta:
        model = Operation

    item = factory.SubFactory(ItemFactory)
    status = factory.SubFactory(StatusFactory)
    responsible = factory.SubFactory(ResponsibleFactory)
    location = factory.SubFactory(LocationFactory)
    notes = "Test operation notes" 