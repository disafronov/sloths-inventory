"""
Фикстуры для тестов приложения common.
"""
import pytest
from factory import Faker
from factory.django import DjangoModelFactory
from common.models import BaseModel, NamedModel


class TestBaseModel(BaseModel):
    """
    Тестовая модель для фикстур.
    """
    class Meta:
        app_label = 'common'


class TestNamedModel(NamedModel):
    """
    Тестовая модель для фикстур.
    """
    class Meta:
        app_label = 'common'


@pytest.fixture
def base_model():
    """
    Фикстура для создания тестовой модели BaseModel.
    """
    return TestBaseModel.objects.create(notes="Test notes")


@pytest.fixture
def named_model():
    """
    Фикстура для создания тестовой модели NamedModel.
    """
    return TestNamedModel.objects.create(name="Test Name") 