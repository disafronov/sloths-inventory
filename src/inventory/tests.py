from django.test import TestCase
from django.db.utils import IntegrityError
from .models import Item, Operation
from catalogs.models import Device, Location, Responsible, Status
from devices.models import Category, Manufacturer, Model, Type


class ItemModelTest(TestCase):
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
            notes="Примечания тестового устройства",
        )

        self.item = Item.objects.create(
            inventory_number="TEST-001",
            device=self.device,
            serial_number="SN123456",
            notes="Тестовые примечания",
        )

    def test_item_creation(self):
        """Тест создания экземпляра"""
        self.assertEqual(self.item.inventory_number, "TEST-001")
        self.assertEqual(self.item.device, self.device)
        self.assertEqual(self.item.serial_number, "SN123456")
        self.assertEqual(self.item.notes, "Тестовые примечания")
        self.assertTrue(self.item.created_at)
        self.assertTrue(self.item.updated_at)

    def test_item_unique_inventory_number(self):
        """Тест уникальности инвентарного номера"""
        with self.assertRaises(IntegrityError):
            Item.objects.create(inventory_number="TEST-001", device=self.device)

    def test_item_str_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.item), f"TEST-001 - {self.device}")


class OperationModelTest(TestCase):
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
            notes="Примечания тестового устройства",
        )

        self.item = Item.objects.create(inventory_number="TEST-001", device=self.device)
        self.status = Status.objects.create(
            name="В эксплуатации", notes="Устройство находится в эксплуатации"
        )
        self.responsible = Responsible.objects.create(
            last_name="Иванов",
            first_name="Иван",
            middle_name="Иванович",
            employee_id="12345",
        )
        self.location = Location.objects.create(
            name="Кабинет 101", notes="Тестовое расположение"
        )
        self.operation = Operation.objects.create(
            item=self.item,
            status=self.status,
            responsible=self.responsible,
            location=self.location,
            notes="Тестовые примечания",
        )

    def test_operation_creation(self):
        """Тест создания операции"""
        self.assertEqual(self.operation.item, self.item)
        self.assertEqual(self.operation.status, self.status)
        self.assertEqual(self.operation.responsible, self.responsible)
        self.assertEqual(self.operation.location, self.location)
        self.assertEqual(self.operation.notes, "Тестовые примечания")
        self.assertTrue(self.operation.created_at)
        self.assertTrue(self.operation.updated_at)

    def test_operation_str_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.operation), f"{self.item} - {self.status}")

    def test_operation_get_status_display(self):
        """Тест получения отображаемого статуса"""
        self.assertEqual(self.operation.get_status_display(), "В эксплуатации")

    def test_item_current_operation(self):
        """Тест получения текущей операции для экземпляра"""
        self.assertEqual(self.item.current_operation, self.operation)

    def test_item_current_status(self):
        """Тест получения текущего статуса для экземпляра"""
        self.assertEqual(self.item.current_status, "В эксплуатации")

    def test_item_current_location(self):
        """Тест получения текущего расположения для экземпляра"""
        self.assertEqual(self.item.current_location, self.location)

    def test_item_current_responsible(self):
        """Тест получения текущего ответственного для экземпляра"""
        self.assertEqual(self.item.current_responsible, self.responsible)
