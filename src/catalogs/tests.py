from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from .models import Category, Manufacturer, Model, Type, Device


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Тестовая категория", description="Описание тестовой категории"
        )

    def test_category_creation(self):
        """Проверка создания категории"""
        self.assertEqual(self.category.name, "Тестовая категория")
        self.assertEqual(self.category.description, "Описание тестовой категории")
        self.assertTrue(isinstance(self.category, Category))
        self.assertEqual(str(self.category), "Тестовая категория")

    def test_category_unique_name(self):
        """Проверка уникальности названия категории"""
        category = Category(name="Тестовая категория", description="Другое описание")
        with self.assertRaises(ValidationError):
            category.full_clean()


class ManufacturerModelTest(TestCase):
    def setUp(self):
        self.manufacturer = Manufacturer.objects.create(
            name="Тестовый производитель",
            description="Описание тестового производителя",
        )

    def test_manufacturer_creation(self):
        """Проверка создания производителя"""
        self.assertEqual(self.manufacturer.name, "Тестовый производитель")
        self.assertEqual(
            self.manufacturer.description, "Описание тестового производителя"
        )
        self.assertTrue(isinstance(self.manufacturer, Manufacturer))
        self.assertEqual(str(self.manufacturer), "Тестовый производитель")

    def test_manufacturer_unique_name(self):
        """Проверка уникальности названия производителя"""
        manufacturer = Manufacturer(
            name="Тестовый производитель", description="Другое описание"
        )
        with self.assertRaises(ValidationError):
            manufacturer.full_clean()


class ModelModelTest(TestCase):
    def setUp(self):
        self.model = Model.objects.create(
            name="Тестовая модель", description="Описание тестовой модели"
        )

    def test_model_creation(self):
        """Проверка создания модели"""
        self.assertEqual(self.model.name, "Тестовая модель")
        self.assertEqual(self.model.description, "Описание тестовой модели")
        self.assertTrue(isinstance(self.model, Model))
        self.assertEqual(str(self.model), "Тестовая модель")

    def test_model_unique_name(self):
        """Проверка уникальности названия модели"""
        model = Model(name="Тестовая модель", description="Другое описание")
        with self.assertRaises(ValidationError):
            model.full_clean()


class TypeModelTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(
            name="Тестовый тип", description="Описание тестового типа"
        )

    def test_type_creation(self):
        """Проверка создания типа"""
        self.assertEqual(self.type.name, "Тестовый тип")
        self.assertEqual(self.type.description, "Описание тестового типа")
        self.assertTrue(isinstance(self.type, Type))
        self.assertEqual(str(self.type), "Тестовый тип")

    def test_type_unique_name(self):
        """Проверка уникальности названия типа"""
        type_obj = Type(name="Тестовый тип", description="Другое описание")
        with self.assertRaises(ValidationError):
            type_obj.full_clean()


class DeviceModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Категория для устройства", description="Описание категории"
        )
        self.type = Type.objects.create(
            name="Тип для устройства", description="Описание типа"
        )
        self.manufacturer = Manufacturer.objects.create(
            name="Производитель для устройства", description="Описание производителя"
        )
        self.model = Model.objects.create(
            name="Модель для устройства", description="Описание модели"
        )
        self.device = Device.objects.create(
            category=self.category,
            type=self.type,
            manufacturer=self.manufacturer,
            model=self.model,
            description="Описание устройства",
        )

    def test_device_creation(self):
        """Проверка создания устройства"""
        self.assertEqual(self.device.category, self.category)
        self.assertEqual(self.device.type, self.type)
        self.assertEqual(self.device.manufacturer, self.manufacturer)
        self.assertEqual(self.device.model, self.model)
        self.assertEqual(self.device.description, "Описание устройства")
        self.assertTrue(isinstance(self.device, Device))
        self.assertEqual(
            str(self.device),
            f"{self.category} | {self.type} | {self.manufacturer} | {self.model}",
        )

    def test_device_unique_together(self):
        """Проверка уникальности сочетания полей устройства"""
        device = Device(
            category=self.category,
            type=self.type,
            manufacturer=self.manufacturer,
            model=self.model,
            description="Другое описание",
        )
        with self.assertRaises(ValidationError):
            device.full_clean()

    def test_device_cascade_protection(self):
        """Проверка защиты от каскадного удаления"""
        with self.assertRaises(ProtectedError):
            self.category.delete()

        with self.assertRaises(ProtectedError):
            self.type.delete()

        with self.assertRaises(ProtectedError):
            self.manufacturer.delete()

        with self.assertRaises(ProtectedError):
            self.model.delete()
