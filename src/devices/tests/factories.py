"""
Фабрики для тестов приложения devices.
"""
import factory
from ..models import Category, Manufacturer, Model, Type


class CategoryFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания категорий."""
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class ManufacturerFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания производителей."""
    class Meta:
        model = Manufacturer

    name = factory.Sequence(lambda n: f'Manufacturer {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class ModelFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания моделей."""
    class Meta:
        model = Model

    name = factory.Sequence(lambda n: f'Model {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class TypeFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания типов."""
    class Meta:
        model = Type

    name = factory.Sequence(lambda n: f'Type {n}')
    notes = factory.Faker('text', max_nb_chars=200) 