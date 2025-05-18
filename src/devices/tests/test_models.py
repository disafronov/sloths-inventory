"""
Тесты для моделей приложения devices.
"""
import pytest
from django.db import models
from django.db.utils import IntegrityError
from django.utils import timezone
from ..models import Category, Manufacturer, Model, Type, BaseModelMixin
from .factories import CategoryFactory, ManufacturerFactory, ModelFactory, TypeFactory


@pytest.mark.django_db
def test_base_model_mixin_str():
    class TestModel(BaseModelMixin):
        class Meta:
            app_label = "devices"
    test_model = TestModel(name="Test Name")
    assert str(test_model) == "Test Name"


@pytest.mark.django_db
class TestCategory:
    """Тесты для модели Category."""

    def test_creation(self):
        """Тест создания категории."""
        category = CategoryFactory()
        assert category.name
        assert category.created_at
        assert category.updated_at
        assert hasattr(category, 'notes')
        assert isinstance(category.created_at, timezone.datetime)
        assert isinstance(category.updated_at, timezone.datetime)

    def test_str_representation(self, category):
        """Тест строкового представления категории."""
        assert str(category) == category.name

    def test_unique_name(self, category):
        """Тест уникальности имени категории."""
        with pytest.raises(IntegrityError):
            Category.objects.create(name=category.name, notes="Другие примечания")

    def test_meta_verbose_names(self):
        """Тест verbose_name и verbose_name_plural."""
        assert Category._meta.verbose_name == "Категория"
        assert Category._meta.verbose_name_plural == "Категории"


@pytest.mark.django_db
class TestManufacturer:
    """Тесты для модели Manufacturer."""

    def test_creation(self):
        """Тест создания производителя."""
        manufacturer = ManufacturerFactory()
        assert manufacturer.name
        assert manufacturer.notes
        assert manufacturer.created_at
        assert manufacturer.updated_at
        assert isinstance(manufacturer.created_at, timezone.datetime)
        assert isinstance(manufacturer.updated_at, timezone.datetime)

    def test_str_representation(self, manufacturer):
        """Тест строкового представления производителя."""
        assert str(manufacturer) == manufacturer.name

    def test_unique_name(self, manufacturer):
        """Тест уникальности имени производителя."""
        with pytest.raises(IntegrityError):
            Manufacturer.objects.create(
                name=manufacturer.name,
                notes="Другие примечания"
            )

    def test_meta_verbose_names(self):
        """Тест verbose_name и verbose_name_plural."""
        assert Manufacturer._meta.verbose_name == "Производитель"
        assert Manufacturer._meta.verbose_name_plural == "Производители"


@pytest.mark.django_db
class TestModel:
    """Тесты для модели Model."""

    def test_creation(self):
        """Тест создания модели."""
        model = ModelFactory()
        assert model.name
        assert model.notes
        assert model.created_at
        assert model.updated_at
        assert isinstance(model.created_at, timezone.datetime)
        assert isinstance(model.updated_at, timezone.datetime)

    def test_str_representation(self, model):
        """Тест строкового представления модели."""
        assert str(model) == model.name

    def test_unique_name(self, model):
        """Тест уникальности имени модели."""
        with pytest.raises(IntegrityError):
            Model.objects.create(
                name=model.name,
                notes="Другие примечания"
            )

    def test_meta_verbose_names(self):
        """Тест verbose_name и verbose_name_plural."""
        assert Model._meta.verbose_name == "Модель"
        assert Model._meta.verbose_name_plural == "Модели"


@pytest.mark.django_db
class TestType:
    """Тесты для модели Type."""

    def test_creation(self):
        """Тест создания типа."""
        device_type = TypeFactory()
        assert device_type.name
        assert device_type.notes
        assert device_type.created_at
        assert device_type.updated_at
        assert isinstance(device_type.created_at, timezone.datetime)
        assert isinstance(device_type.updated_at, timezone.datetime)

    def test_str_representation(self, device_type):
        """Тест строкового представления типа."""
        assert str(device_type) == device_type.name

    def test_unique_name(self, device_type):
        """Тест уникальности имени типа."""
        with pytest.raises(IntegrityError):
            Type.objects.create(
                name=device_type.name,
                notes="Другие примечания"
            )

    def test_meta_verbose_names(self):
        """Тест verbose_name и verbose_name_plural."""
        assert Type._meta.verbose_name == "Тип"
        assert Type._meta.verbose_name_plural == "Типы" 