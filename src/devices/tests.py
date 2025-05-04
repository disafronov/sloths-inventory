from django.test import TestCase
from django.db.utils import IntegrityError
from .models import Category, Manufacturer, Model, Type


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Тестовая категория", notes="Примечания тестовой категории"
        )

    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.name, "Тестовая категория")
        self.assertEqual(self.category.notes, "Примечания тестовой категории")
        self.assertTrue(self.category.created_at)
        self.assertTrue(self.category.updated_at)

    def test_category_str_representation(self):
        self.assertEqual(str(self.category), "Тестовая категория")

    def test_category_unique_name(self):
        """Тест уникальности имени категории"""
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name="Тестовая категория", notes="Другие примечания"
            )


class ManufacturerModelTest(TestCase):
    def setUp(self):
        self.manufacturer = Manufacturer.objects.create(
            name="Тестовый производитель",
            notes="Примечания тестового производителя",
        )

    def test_manufacturer_creation(self):
        """Тест создания производителя"""
        self.assertEqual(self.manufacturer.name, "Тестовый производитель")
        self.assertEqual(
            self.manufacturer.notes, "Примечания тестового производителя"
        )
        self.assertTrue(self.manufacturer.created_at)
        self.assertTrue(self.manufacturer.updated_at)

    def test_manufacturer_str_representation(self):
        self.assertEqual(str(self.manufacturer), "Тестовый производитель")

    def test_manufacturer_unique_name(self):
        """Тест уникальности имени производителя"""
        with self.assertRaises(IntegrityError):
            Manufacturer.objects.create(
                name="Тестовый производитель",
                notes="Другие примечания",
            )


class ModelModelTest(TestCase):
    def setUp(self):
        self.model = Model.objects.create(
            name="Тестовая модель", notes="Примечания тестовой модели"
        )

    def test_model_creation(self):
        """Тест создания модели"""
        self.assertEqual(self.model.name, "Тестовая модель")
        self.assertEqual(self.model.notes, "Примечания тестовой модели")
        self.assertTrue(self.model.created_at)
        self.assertTrue(self.model.updated_at)

    def test_model_str_representation(self):
        self.assertEqual(str(self.model), "Тестовая модель")

    def test_model_unique_name(self):
        """Тест уникальности имени модели"""
        with self.assertRaises(IntegrityError):
            Model.objects.create(
                name="Тестовая модель", notes="Другие примечания"
            )


class TypeModelTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(
            name="Тестовый тип", notes="Примечания тестового типа"
        )

    def test_type_creation(self):
        """Тест создания типа"""
        self.assertEqual(self.type.name, "Тестовый тип")
        self.assertEqual(self.type.notes, "Примечания тестового типа")
        self.assertTrue(self.type.created_at)
        self.assertTrue(self.type.updated_at)

    def test_type_str_representation(self):
        self.assertEqual(str(self.type), "Тестовый тип")

    def test_type_unique_name(self):
        """Тест уникальности имени типа"""
        with self.assertRaises(IntegrityError):
            Type.objects.create(
                name="Тестовый тип", notes="Другие примечания"
            )
