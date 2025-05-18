"""
Фикстуры для тестов приложения devices.
"""
import pytest
from factory import Faker
from factory.django import DjangoModelFactory
from ..models import Category, Manufacturer, Model, Type


class CategoryFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых категорий.
    """
    class Meta:
        model = Category

    name = Faker('word')
    notes = Faker('sentence')


class ManufacturerFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых производителей.
    """
    class Meta:
        model = Manufacturer

    name = Faker('company')
    notes = Faker('sentence')


class ModelFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых моделей.
    """
    class Meta:
        model = Model

    name = Faker('word')
    notes = Faker('sentence')


class TypeFactory(DjangoModelFactory):
    """
    Фабрика для создания тестовых типов.
    """
    class Meta:
        model = Type

    name = Faker('word')
    notes = Faker('sentence')


@pytest.fixture
def category():
    """
    Фикстура для создания тестовой категории.
    """
    return CategoryFactory()


@pytest.fixture
def manufacturer():
    """
    Фикстура для создания тестового производителя.
    """
    return ManufacturerFactory()


@pytest.fixture
def model():
    """
    Фикстура для создания тестовой модели.
    """
    return ModelFactory()


@pytest.fixture
def device_type():
    """
    Фикстура для создания тестового типа.
    """
    return TypeFactory() 