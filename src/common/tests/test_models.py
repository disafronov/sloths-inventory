"""
Тесты для моделей приложения common.
"""
import pytest
from django.test import TestCase
from django.db import models
from django.utils import timezone
from common.models import BaseModel, NamedModel
from django.db.utils import IntegrityError


class BaseModelTest(BaseModel):
    """
    Тестовая модель для тестирования BaseModel.
    """
    class Meta:
        app_label = 'common'


class NamedModelTest(NamedModel):
    """
    Тестовая модель для тестирования NamedModel.
    """
    class Meta:
        app_label = 'common'


@pytest.mark.django_db
def test_base_model_notes(base_model):
    """Проверяем, что поле notes корректно сохраняется."""
    assert base_model.notes == "Test notes"


@pytest.mark.django_db
def test_named_model_ordering(named_model):
    """Проверяем, что сортировка по умолчанию работает корректно."""
    TestNamedModel = named_model.__class__
    TestNamedModel.objects.create(name="A Name")
    TestNamedModel.objects.create(name="B Name")
    TestNamedModel.objects.create(name="C Name")
    
    names = [obj.name for obj in TestNamedModel.objects.all()]
    assert names == ["Test Name", "A Name", "B Name", "C Name"]


@pytest.mark.django_db
def test_named_model_unique_name(named_model):
    """Проверяем, что имя должно быть уникальным."""
    TestNamedModel = named_model.__class__
    with pytest.raises(IntegrityError):
        TestNamedModel.objects.create(name="Test Name")


@pytest.mark.django_db
class TestBaseModel:
    """Тесты для базовой модели."""

    def test_abstract(self):
        """Тест, что модель является абстрактной."""
        assert BaseModel._meta.abstract is True

    def test_created_at(self, base_model):
        """Тест поля created_at."""
        assert base_model.created_at is not None
        assert isinstance(base_model.created_at, timezone.datetime)
        field = BaseModel._meta.get_field("created_at")
        assert field.auto_now_add is True
        assert field.verbose_name == "Дата создания"

    def test_updated_at(self, base_model):
        """Тест поля updated_at."""
        assert base_model.updated_at is not None
        assert isinstance(base_model.updated_at, timezone.datetime)
        field = BaseModel._meta.get_field("updated_at")
        assert field.auto_now is True
        assert field.verbose_name == "Дата обновления"

    def test_notes(self, base_model):
        """Тест поля notes."""
        assert base_model.notes == "Test notes"
        field = BaseModel._meta.get_field("notes")
        assert field.blank is True
        assert field.verbose_name == "Примечания"
        assert isinstance(field, models.TextField)


@pytest.mark.django_db
class TestNamedModel:
    """Тесты для именованной модели."""

    def test_abstract(self):
        """Тест, что модель является абстрактной."""
        assert NamedModel._meta.abstract is True

    def test_meta_ordering(self):
        """Тест, что модели сортируются по имени."""
        assert NamedModel._meta.ordering == ["name"]

    def test_name_field(self, named_model):
        """Тест поля name."""
        assert named_model.name == "Test Name"
        field = NamedModel._meta.get_field("name")
        assert field.max_length == 255
        assert field.unique is True
        assert field.verbose_name == "Название"
        assert isinstance(field, models.CharField)

    def test_str_representation(self, named_model):
        """Тест строкового представления."""
        assert str(named_model) == named_model.name

    def test_ordering(self, named_model):
        """Тест сортировки по умолчанию."""
        TestNamedModel = named_model.__class__
        TestNamedModel.objects.create(name="A Name")
        TestNamedModel.objects.create(name="B Name")
        TestNamedModel.objects.create(name="C Name")
        
        names = [obj.name for obj in TestNamedModel.objects.all()]
        assert names == ["Test Name", "A Name", "B Name", "C Name"]

    def test_unique_name(self, named_model):
        """Тест уникальности имени."""
        TestNamedModel = named_model.__class__
        with pytest.raises(IntegrityError):
            TestNamedModel.objects.create(name="Test Name")

    def test_inheritance(self, named_model):
        """Тест наследования от BaseModel."""
        assert isinstance(named_model, BaseModel)
        assert hasattr(named_model, 'created_at')
        assert hasattr(named_model, 'updated_at')
        assert hasattr(named_model, 'notes') 