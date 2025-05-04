from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Category, Manufacturer, Model, Type


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Тестовая категория", description="Описание тестовой категории"
        )

    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.name, "Тестовая категория")
        self.assertEqual(self.category.description, "Описание тестовой категории")
        self.assertTrue(self.category.created_at)
        self.assertTrue(self.category.updated_at)

    def test_category_unique_name(self):
        """Тест уникальности имени категории"""
        with self.assertRaises(ValidationError):
            Category.objects.create(name="Тестовая категория")


class ManufacturerModelTest(TestCase):
    def setUp(self):
        self.manufacturer = Manufacturer.objects.create(
            name="Тестовый производитель",
            description="Описание тестового производителя",
        )

    def test_manufacturer_creation(self):
        """Тест создания производителя"""
        self.assertEqual(self.manufacturer.name, "Тестовый производитель")
        self.assertEqual(
            self.manufacturer.description, "Описание тестового производителя"
        )
        self.assertTrue(self.manufacturer.created_at)
        self.assertTrue(self.manufacturer.updated_at)

    def test_manufacturer_unique_name(self):
        """Тест уникальности имени производителя"""
        with self.assertRaises(ValidationError):
            Manufacturer.objects.create(name="Тестовый производитель")


class ModelModelTest(TestCase):
    def setUp(self):
        self.model = Model.objects.create(
            name="Тестовая модель", description="Описание тестовой модели"
        )

    def test_model_creation(self):
        """Тест создания модели"""
        self.assertEqual(self.model.name, "Тестовая модель")
        self.assertEqual(self.model.description, "Описание тестовой модели")
        self.assertTrue(self.model.created_at)
        self.assertTrue(self.model.updated_at)

    def test_model_unique_name(self):
        """Тест уникальности имени модели"""
        with self.assertRaises(ValidationError):
            Model.objects.create(name="Тестовая модель")


class TypeModelTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(
            name="Тестовый тип", description="Описание тестового типа"
        )

    def test_type_creation(self):
        """Тест создания типа"""
        self.assertEqual(self.type.name, "Тестовый тип")
        self.assertEqual(self.type.description, "Описание тестового типа")
        self.assertTrue(self.type.created_at)
        self.assertTrue(self.type.updated_at)

    def test_type_unique_name(self):
        """Тест уникальности имени типа"""
        with self.assertRaises(ValidationError):
            Type.objects.create(name="Тестовый тип")
