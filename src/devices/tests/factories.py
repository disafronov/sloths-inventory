"""
Фабрики для тестов приложения devices.
"""
import factory
from factory.django import DjangoModelFactory
from catalogs.models import Device, Category, Manufacturer, Model, Type


class CategoryFactory(DjangoModelFactory):
    """Фабрика для создания категорий."""
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class ManufacturerFactory(DjangoModelFactory):
    """Фабрика для создания производителей."""
    class Meta:
        model = Manufacturer

    name = factory.Sequence(lambda n: f'Manufacturer {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class ModelFactory(DjangoModelFactory):
    """Фабрика для создания моделей."""
    class Meta:
        model = Model

    name = factory.Sequence(lambda n: f'Model {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class TypeFactory(DjangoModelFactory):
    """Фабрика для создания типов."""
    class Meta:
        model = Type

    name = factory.Sequence(lambda n: f'Type {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class DeviceFactory(DjangoModelFactory):
    class Meta:
        model = Device

    category = factory.SubFactory(CategoryFactory)
    type = factory.SubFactory(TypeFactory)
    manufacturer = factory.SubFactory(ManufacturerFactory)
    model = factory.SubFactory(ModelFactory)
    notes = factory.Sequence(lambda n: f'Notes {n}') 