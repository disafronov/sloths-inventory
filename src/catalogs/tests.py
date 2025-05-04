from django.test import TestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from .models import Device, Location, Responsible, Status
from devices.models import Category, Manufacturer, Model, Type


class DeviceModelTest(TestCase):
    def setUp(self):
        # Создаем необходимые объекты для тестов
        self.category = Category.objects.create(name="Тестовая категория")
        self.type = Type.objects.create(name="Тестовый тип")
        self.manufacturer = Manufacturer.objects.create(name="Тестовый производитель")
        self.model = Model.objects.create(name="Тестовая модель")

        self.device = Device.objects.create(
            category=self.category,
            type=self.type,
            manufacturer=self.manufacturer,
            model=self.model,
            notes="Тестовые примечания",
        )

    def test_device_creation(self):
        """Тест создания устройства"""
        self.assertEqual(self.device.category, self.category)
        self.assertEqual(self.device.type, self.type)
        self.assertEqual(self.device.manufacturer, self.manufacturer)
        self.assertEqual(self.device.model, self.model)
        self.assertEqual(self.device.notes, "Тестовые примечания")
        self.assertTrue(self.device.created_at)
        self.assertTrue(self.device.updated_at)

    def test_device_unique_together(self):
        """Тест уникальности комбинации полей"""
        with self.assertRaises(IntegrityError):
            Device.objects.create(
                category=self.category,
                type=self.type,
                manufacturer=self.manufacturer,
                model=self.model,
                notes="Другие примечания",
            )

    def test_device_str_representation(self):
        """Тест строкового представления"""
        expected_str = (
            f"{self.category} | {self.type} | {self.manufacturer} | {self.model}"
        )
        self.assertEqual(str(self.device), expected_str)


class LocationModelTest(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            name="Тестовое расположение", notes="Тестовые примечания"
        )

    def test_location_creation(self):
        """Тест создания расположения"""
        self.assertEqual(self.location.name, "Тестовое расположение")
        self.assertEqual(self.location.notes, "Тестовые примечания")
        self.assertTrue(self.location.created_at)
        self.assertTrue(self.location.updated_at)

    def test_location_str_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.location), "Тестовое расположение")


class ResponsibleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.responsible = Responsible.objects.create(
            last_name="Иванов",
            first_name="Иван",
            middle_name="Иванович",
            employee_id="12345",
            user=self.user,
        )

    def test_responsible_creation(self):
        """Тест создания ответственного"""
        self.assertEqual(self.responsible.last_name, "Иванов")
        self.assertEqual(self.responsible.first_name, "Иван")
        self.assertEqual(self.responsible.middle_name, "Иванович")
        self.assertEqual(self.responsible.employee_id, "12345")
        self.assertEqual(self.responsible.user, self.user)
        self.assertTrue(self.responsible.created_at)
        self.assertTrue(self.responsible.updated_at)

    def test_responsible_str_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.responsible), "Иванов Иван Иванович")

    def test_responsible_get_full_name(self):
        """Тест получения полного имени"""
        self.assertEqual(self.responsible.get_full_name(), "Иванов Иван Иванович")

    def test_responsible_without_middle_name(self):
        """Тест создания ответственного без отчества"""
        responsible = Responsible.objects.create(last_name="Петров", first_name="Петр")
        self.assertEqual(str(responsible), "Петров Петр")


class StatusModelTest(TestCase):
    def setUp(self):
        self.status = Status.objects.create(
            name="Тестовый статус", notes="Тестовые примечания"
        )

    def test_status_creation(self):
        """Тест создания статуса"""
        self.assertEqual(self.status.name, "Тестовый статус")
        self.assertEqual(self.status.notes, "Тестовые примечания")
        self.assertTrue(self.status.created_at)
        self.assertTrue(self.status.updated_at)

    def test_status_str_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.status), "Тестовый статус")
