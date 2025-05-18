"""
Тесты для моделей приложения inventory.
"""
import pytest
import time
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.db import models
from ..models import Item, Operation, Status, Location, Responsible, Device
from .factories import ItemFactory, OperationFactory, StatusFactory, LocationFactory, ResponsibleFactory


@pytest.mark.django_db
def test_item_creation(item):
    """Тест создания экземпляра"""
    assert item.inventory_number
    assert item.device
    assert item.serial_number
    assert item.notes
    assert item.created_at
    assert item.updated_at


@pytest.mark.django_db
def test_item_str_representation(item):
    """Тест строкового представления экземпляра"""
    expected_str = f"{item.inventory_number} - {item.device}"
    assert str(item) == expected_str


@pytest.mark.django_db
def test_item_unique_inventory_number(item):
    """Тест уникальности инвентарного номера"""
    with pytest.raises(IntegrityError):
        Item.objects.create(
            inventory_number=item.inventory_number,
            device=item.device
        )


@pytest.mark.django_db
def test_item_empty_values():
    """Тест пустых значений полей"""
    item = ItemFactory(serial_number="", notes="")
    assert item.serial_number == ""
    assert item.notes == ""


@pytest.mark.django_db
def test_item_max_values():
    """Тест максимальной длины полей"""
    long_inventory = "A" * 51
    long_serial = "B" * 51
    long_notes = "C" * 1001

    item = ItemFactory(
        inventory_number=long_inventory[:50],
        serial_number=long_serial[:50],
        notes=long_notes[:1000]
    )
    assert len(item.inventory_number) == 50
    assert len(item.serial_number) == 50
    assert len(item.notes) == 1000


@pytest.mark.django_db
def test_operation_creation(operation):
    """Тест создания операции"""
    assert operation.item
    assert operation.status
    assert operation.responsible
    assert operation.location
    assert operation.notes
    assert operation.created_at
    assert operation.updated_at


@pytest.mark.django_db
def test_operation_str_representation(operation):
    """Тест строкового представления операции"""
    expected_str = f"{operation.item} - {operation.status} ({operation.location})"
    assert str(operation) == expected_str


@pytest.mark.django_db
def test_item_current_state(operation):
    """Тест получения текущего состояния экземпляра"""
    item = operation.item
    assert item.current_operation == operation
    assert item.current_status == operation.status.name
    assert item.current_location == operation.location.name
    assert item.current_responsible == operation.responsible


@pytest.mark.django_db
def test_operation_delete(operation):
    """Тест удаления операций"""
    # Проверка каскадного удаления
    item_id = operation.item.id
    operation.item.delete()
    assert not Operation.objects.filter(item_id=item_id).exists()

    # Проверка защиты от удаления
    new_item = ItemFactory()
    new_operation = OperationFactory(item=new_item, status=operation.status)
    with pytest.raises(ProtectedError):
        operation.status.delete()


@pytest.mark.django_db
class TestItem:
    """Тесты для модели Item."""

    def test_meta(self):
        """Тест метаданных модели."""
        assert Item._meta.verbose_name == "Экземпляр"
        assert Item._meta.verbose_name_plural == "Экземпляры"
        assert Item._meta.ordering == ["inventory_number"]

    def test_inventory_number_field(self):
        """Тест поля inventory_number."""
        field = Item._meta.get_field("inventory_number")
        assert field.max_length == 50
        assert field.unique is True
        assert field.verbose_name == "Инвентарный номер"
        assert isinstance(field, models.CharField)

    def test_device_field(self):
        """Тест поля device."""
        field = Item._meta.get_field("device")
        assert field.verbose_name == "Устройство"
        assert field.remote_field.on_delete == models.PROTECT
        assert isinstance(field, models.ForeignKey)

    def test_serial_number_field(self):
        """Тест поля serial_number."""
        field = Item._meta.get_field("serial_number")
        assert field.max_length == 50
        assert field.blank is True
        assert field.verbose_name == "Серийный номер"
        assert isinstance(field, models.CharField)

    def test_str(self):
        """Тест метода __str__."""
        item = ItemFactory()
        expected_str = f"{item.inventory_number} - {item.device}"
        assert str(item) == expected_str
        assert item.get_display_name() == expected_str

    def test_current_operation(self):
        """Тест свойства current_operation."""
        item = ItemFactory()
        assert item.current_operation is None
        operation = OperationFactory(item=item)
        assert item.current_operation == operation

    def test_current_status(self):
        """Тест свойства current_status."""
        item = ItemFactory()
        assert item.current_status is None
        operation = OperationFactory(item=item)
        assert item.current_status == operation.status.name

    def test_current_location(self):
        """Тест свойства current_location."""
        item = ItemFactory()
        assert item.current_location is None
        operation = OperationFactory(item=item)
        assert item.current_location == operation.location.name

    def test_current_responsible(self):
        """Тест свойства current_responsible."""
        item = ItemFactory()
        assert item.current_responsible is None
        operation = OperationFactory(item=item)
        assert item.current_responsible == operation.responsible

    def test_current_operation_value_none_instance(self):
        """Тест CurrentOperationValue.__get__ с None instance."""
        item = ItemFactory()
        assert Item.current_status.__get__(None, Item) is Item.current_status
        assert Item.current_location.__get__(None, Item) is Item.current_location
        assert Item.current_responsible.__get__(None, Item) is Item.current_responsible

    def test_current_operation_value_with_different_types(self):
        """Тест CurrentOperationValue с разными типами значений."""
        item = ItemFactory()
        
        # Тест с None значением
        assert item.current_status is None
        assert item.current_location is None
        assert item.current_responsible is None

        # Тест с объектом без атрибута name
        operation = OperationFactory(item=item)
        operation.status.name = ""
        operation.status.save()
        operation.save()
        item.refresh_from_db()
        assert item.current_status == ""

        # Тест с объектом с атрибутом name
        operation.status.name = "Test Status"
        operation.status.save()
        operation.save()
        item.refresh_from_db()
        assert item.current_status == "Test Status"

        # Тест с несуществующим атрибутом
        operation.delete()
        item.refresh_from_db()
        assert item.current_status is None

    def test_current_operation_value_with_custom_display_attr(self):
        """Тест CurrentOperationValue с пользовательским display_attr."""
        class CustomOperationValue(Item.CurrentOperationValue):
            def __init__(self, attr_name, display_attr=None):
                super().__init__(attr_name, display_attr or f"custom_{attr_name}")

        # Используем существующую модель Item
        item = ItemFactory()
        status = StatusFactory()
        location = LocationFactory()
        responsible = ResponsibleFactory()

        operation = OperationFactory(
            item=item,
            status=status,
            location=location,
            responsible=responsible
        )

        # Проверяем стандартное поведение
        assert item.current_status == status.name
        assert item.current_location == location.name
        assert item.current_responsible == responsible

        # Проверяем пользовательский атрибут отображения
        custom_value = CustomOperationValue('status', 'custom_status')
        assert custom_value.display_attr == 'custom_status'
        assert custom_value.attr_name == 'status'

    def test_current_operation_value_with_invalid_attr(self):
        """Тест CurrentOperationValue с несуществующим атрибутом."""
        item = ItemFactory()
        operation = OperationFactory(item=item)

        # Тест с несуществующим атрибутом операции
        assert getattr(item, 'current_invalid_attr', None) is None

    def test_current_operation_value_with_deleted_related(self):
        """Тест CurrentOperationValue при удалении связанных объектов."""
        item = ItemFactory()
        operation = OperationFactory(item=item)
        
        # Удаляем операцию
        operation.delete()
        item.refresh_from_db()
        
        # Проверяем, что значения стали None
        assert item.current_status is None
        assert item.current_location is None
        assert item.current_responsible is None

    def test_device_relationship(self):
        """Тест связи с моделью Device."""
        item = ItemFactory()
        
        # Проверка, что нельзя удалить устройство, если есть связанные экземпляры
        with pytest.raises(ProtectedError):
            item.device.delete()

    def test_operation_relationship(self):
        """Тест связи с моделью Operation."""
        item = ItemFactory()
        operation = OperationFactory(item=item)

        # Проверка, что операция связана с экземпляром
        assert operation.item == item
        assert item.operation_set.first() == operation

        # Проверка, что при удалении экземпляра удаляются все связанные операции
        item_id = item.id
        item.delete()
        assert not Operation.objects.filter(item_id=item_id).exists()

    def test_current_operation_with_multiple_operations(self):
        """Тест получения текущей операции при наличии нескольких операций."""
        item = ItemFactory()
        operation1 = OperationFactory(item=item)
        operation2 = OperationFactory(item=item)
        operation3 = OperationFactory(item=item)

        # Проверяем, что возвращается последняя операция
        assert item.current_operation == operation3
        assert item.current_status == operation3.status.name
        assert item.current_location == operation3.location.name
        assert item.current_responsible == operation3.responsible

    def test_current_operation_with_deleted_operation(self):
        """Тест получения текущей операции при удалении последней операции."""
        item = ItemFactory()
        operation1 = OperationFactory(item=item)
        operation2 = OperationFactory(item=item)
        operation3 = OperationFactory(item=item)

        # Удаляем последнюю операцию
        operation3.delete()

        # Проверяем, что возвращается предыдущая операция
        assert item.current_operation == operation2
        assert item.current_status == operation2.status.name
        assert item.current_location == operation2.location.name
        assert item.current_responsible == operation2.responsible

    def test_current_operation_with_empty_name(self):
        """Тест получения текущей операции с пустым именем."""
        item = ItemFactory()
        status = Status.objects.create(name="")
        operation = OperationFactory(item=item, status=status)

        # Проверяем, что возвращается пустая строка для имени
        assert item.current_status == ""

    def test_current_operation_with_none_value(self):
        """Тест получения текущей операции с None значением."""
        item = ItemFactory()
        assert item.current_status is None
        assert item.current_location is None
        assert item.current_responsible is None

    def test_inventory_number_case_sensitivity(self):
        """Тест регистронезависимости инвентарного номера."""
        item = ItemFactory(inventory_number="INV-123")
        
        # Проверяем, что можно создать экземпляр с тем же номером в другом регистре
        new_item = ItemFactory(inventory_number="inv-123")
        assert new_item.inventory_number == "inv-123"

    def test_serial_number_case_sensitivity(self):
        """Тест регистронезависимости серийного номера."""
        item = ItemFactory(serial_number="SN-123")
        
        # Проверяем, что можно создать экземпляр с тем же номером в другом регистре
        new_item = ItemFactory(serial_number="sn-123")
        assert new_item.serial_number == "sn-123"

    def test_operation_with_same_timestamp(self):
        """Тест операций с одинаковым временем создания."""
        item = ItemFactory()
        timestamp = timezone.now()
        
        # Создаем операции с одинаковым временем по одной
        operation1 = OperationFactory(item=item)
        operation1.created_at = timestamp
        operation1.save()
        operation2 = OperationFactory(item=item)
        operation2.created_at = timestamp
        operation2.save()

        # Проверяем, что возвращается одна из операций (порядок не гарантирован)
        assert item.current_operation in (operation1, operation2)

    def test_current_responsible_with_deleted_operation(self):
        """Тест current_responsible при удалении операции."""
        item = ItemFactory()
        operation = OperationFactory(item=item)
        responsible = operation.responsible
        
        # Удаляем операцию
        operation.delete()
        item.refresh_from_db()
        assert item.current_responsible is None

    def test_current_responsible_with_multiple_operations(self):
        """Тест current_responsible при наличии нескольких операций."""
        item = ItemFactory()
        responsible1 = ResponsibleFactory()
        responsible2 = ResponsibleFactory()
        
        # Создаем операции с разными ответственными
        operation1 = OperationFactory(item=item, responsible=responsible1)
        operation2 = OperationFactory(item=item, responsible=responsible2)
        
        # Проверяем, что возвращается ответственный из последней операции
        assert item.current_responsible == responsible2

    def test_current_responsible_with_same_responsible(self):
        """Тест current_responsible при одинаковых ответственных."""
        item = ItemFactory()
        responsible = ResponsibleFactory()
        
        # Создаем операции с одинаковым ответственным
        operation1 = OperationFactory(item=item, responsible=responsible)
        operation2 = OperationFactory(item=item, responsible=responsible)
        
        # Проверяем, что возвращается тот же объект ответственного
        assert item.current_responsible == responsible

    def test_current_operation_value_with_none_related(self):
        """Тест CurrentOperationValue, когда операция отсутствует."""
        item = ItemFactory()
        # Проверяем, что current_status возвращает None, когда нет операций
        assert item.current_status is None
        assert item.current_location is None
        assert item.current_responsible is None

    def test_inventory_number_validation(self):
        """Тест базовых ограничений инвентарного номера."""
        # Тест на максимальную длину
        item = ItemFactory(inventory_number="A" * 50)
        assert len(item.inventory_number) == 50

        # Тест на уникальность
        with pytest.raises(IntegrityError):
            ItemFactory(inventory_number=item.inventory_number)

    def test_serial_number_validation(self):
        """Тест базовых ограничений серийного номера."""
        # Тест на пустое значение
        item = ItemFactory(serial_number="")
        assert item.serial_number == ""

        # Тест на максимальную длину
        item = ItemFactory(serial_number="B" * 50)
        assert len(item.serial_number) == 50

    def test_device_protection(self):
        """Тест защиты от удаления устройства."""
        item = ItemFactory()
        device = item.device

        # Попытка удалить устройство должна вызвать ProtectedError
        with pytest.raises(ProtectedError):
            device.delete()

        # После удаления экземпляра устройство можно удалить
        item.delete()
        device.delete()
        assert not Device.objects.filter(id=device.id).exists()

    def test_cascade_delete(self):
        """Тест каскадного удаления."""
        item = ItemFactory()
        operation = OperationFactory(item=item)
        
        # Удаляем Item
        item.delete()
        
        # Проверяем, что Operation тоже удалился
        assert not Operation.objects.filter(id=operation.id).exists()
        
        # Проверяем, что связанные объекты остались
        assert Status.objects.filter(id=operation.status.id).exists()
        assert Location.objects.filter(id=operation.location.id).exists()
        assert Responsible.objects.filter(id=operation.responsible.id).exists()

    def test_protected_delete(self):
        """Тест защиты от удаления."""
        item = ItemFactory()
        operation = OperationFactory(item=item)
        
        # Пытаемся удалить связанные объекты
        with pytest.raises(ProtectedError):
            operation.status.delete()
        with pytest.raises(ProtectedError):
            operation.location.delete()
        with pytest.raises(ProtectedError):
            operation.responsible.delete()
        
        # Проверяем, что объекты остались
        assert Status.objects.filter(id=operation.status.id).exists()
        assert Location.objects.filter(id=operation.location.id).exists()
        assert Responsible.objects.filter(id=operation.responsible.id).exists()

    def test_operation_ordering(self):
        """Тест сортировки операций."""
        item = ItemFactory()
        
        # Создаем операции с разными временными метками
        operation1 = OperationFactory(item=item)
        time.sleep(0.1)  # Небольшая задержка
        operation2 = OperationFactory(item=item)
        time.sleep(0.1)  # Небольшая задержка
        operation3 = OperationFactory(item=item)
        
        # Проверяем сортировку
        operations = item.operation_set.all()
        assert operations[0] == operation3  # Самая новая
        assert operations[1] == operation2
        assert operations[2] == operation1  # Самая старая

    def test_status_transition(self):
        """Тест перехода между статусами."""
        item = ItemFactory()
        
        # Создаем первую операцию
        status1 = StatusFactory()
        operation1 = OperationFactory(item=item, status=status1)
        
        # Проверяем текущий статус
        assert item.current_status == status1.name
        
        # Создаем вторую операцию с другим статусом
        status2 = StatusFactory()
        operation2 = OperationFactory(item=item, status=status2)
        
        # Проверяем, что статус обновился
        assert item.current_status == status2.name
        
        # Проверяем, что обе операции сохранились в истории
        assert item.operation_set.count() == 2
        assert item.operation_set.filter(status=status1).exists()
        assert item.operation_set.filter(status=status2).exists()

    def test_location_transition(self):
        """Тест перехода между местоположениями."""
        item = ItemFactory()
        
        # Создаем первую операцию
        location1 = LocationFactory()
        operation1 = OperationFactory(item=item, location=location1)
        
        # Проверяем текущее местоположение
        assert item.current_location == location1.name
        
        # Создаем вторую операцию с другим местоположением
        location2 = LocationFactory()
        operation2 = OperationFactory(item=item, location=location2)
        
        # Проверяем, что местоположение обновилось
        assert item.current_location == location2.name
        
        # Проверяем, что обе операции сохранились в истории
        assert item.operation_set.count() == 2
        assert item.operation_set.filter(location=location1).exists()
        assert item.operation_set.filter(location=location2).exists()

    def test_responsible_transition(self):
        """Тест перехода между ответственными."""
        item = ItemFactory()
        
        # Создаем первую операцию
        responsible1 = ResponsibleFactory()
        operation1 = OperationFactory(item=item, responsible=responsible1)
        
        # Проверяем текущего ответственного
        assert item.current_responsible == responsible1
        
        # Создаем вторую операцию с другим ответственным
        responsible2 = ResponsibleFactory()
        operation2 = OperationFactory(item=item, responsible=responsible2)
        
        # Проверяем, что ответственный обновился
        assert item.current_responsible == responsible2
        
        # Проверяем, что обе операции сохранились в истории
        assert item.operation_set.count() == 2
        assert item.operation_set.filter(responsible=responsible1).exists()
        assert item.operation_set.filter(responsible=responsible2).exists()

    def test_current_operation_value_with_multiple_operations(self):
        """Тест CurrentOperationValue при наличии нескольких операций."""
        item = ItemFactory()
        
        # Создаем несколько операций с разными значениями
        status1 = StatusFactory()
        location1 = LocationFactory()
        responsible1 = ResponsibleFactory()
        operation1 = OperationFactory(
            item=item,
            status=status1,
            location=location1,
            responsible=responsible1
        )
        
        status2 = StatusFactory()
        location2 = LocationFactory()
        responsible2 = ResponsibleFactory()
        operation2 = OperationFactory(
            item=item,
            status=status2,
            location=location2,
            responsible=responsible2
        )
        
        # Проверяем, что возвращаются значения из последней операции
        assert item.current_status == status2.name
        assert item.current_location == location2.name
        assert item.current_responsible == responsible2
        
        # Удаляем последнюю операцию
        operation2.delete()
        item.refresh_from_db()
        
        # Проверяем, что вернулись значения из предыдущей операции
        assert item.current_status == status1.name
        assert item.current_location == location1.name
        assert item.current_responsible == responsible1

    def test_current_operation_value_with_bulk_operations(self):
        """Тест CurrentOperationValue при массовом создании операций."""
        item = ItemFactory()
        operations = []
        
        # Создаем несколько операций в цикле
        for i in range(5):
            operation = OperationFactory(item=item)
            operations.append(operation)
            time.sleep(0.1)  # Небольшая задержка для разных временных меток
        
        # Проверяем, что возвращаются значения из последней операции
        assert item.current_status == operations[-1].status.name
        assert item.current_location == operations[-1].location.name
        assert item.current_responsible == operations[-1].responsible
        
        # Удаляем все операции кроме первой
        for operation in operations[1:]:
            operation.delete()
        item.refresh_from_db()
        
        # Проверяем, что вернулись значения из первой операции
        assert item.current_status == operations[0].status.name
        assert item.current_location == operations[0].location.name
        assert item.current_responsible == operations[0].responsible

    def test_current_operation_value_with_concurrent_operations(self):
        """Тест CurrentOperationValue при одновременном создании операций."""
        item = ItemFactory()
        timestamp = timezone.now()
        
        # Создаем операции с одинаковым временем создания
        status1 = StatusFactory()
        location1 = LocationFactory()
        responsible1 = ResponsibleFactory()
        operation1 = OperationFactory(
            item=item,
            status=status1,
            location=location1,
            responsible=responsible1
        )
        operation1.created_at = timestamp
        operation1.save()
        
        status2 = StatusFactory()
        location2 = LocationFactory()
        responsible2 = ResponsibleFactory()
        operation2 = OperationFactory(
            item=item,
            status=status2,
            location=location2,
            responsible=responsible2
        )
        operation2.created_at = timestamp
        operation2.save()
        
        # Проверяем, что возвращаются значения из одной из операций
        # (порядок не гарантирован при одинаковом времени)
        assert item.current_status in (status1.name, status2.name)
        assert item.current_location in (location1.name, location2.name)
        assert item.current_responsible in (responsible1, responsible2)

    def test_current_operation_value_with_empty_related(self):
        """Тест CurrentOperationValue с пустыми связанными объектами."""
        item = ItemFactory()
        
        # Создаем операцию с пустыми значениями
        status = StatusFactory(name="")
        location = LocationFactory(name="")
        responsible = ResponsibleFactory()
        operation = OperationFactory(
            item=item,
            status=status,
            location=location,
            responsible=responsible
        )
        
        # Проверяем, что возвращаются пустые строки для name
        assert item.current_status == ""
        assert item.current_location == ""
        assert item.current_responsible == responsible

    def test_current_operation_value_with_invalid_operation(self):
        """Тест CurrentOperationValue при отсутствии операции."""
        item = ItemFactory()
        
        # Проверяем, что значения None при отсутствии операций
        assert item.current_status is None
        assert item.current_location is None
        assert item.current_responsible is None
        
        # Создаем и сразу удаляем операцию
        operation = OperationFactory(item=item)
        operation.delete()
        item.refresh_from_db()
        
        # Проверяем, что значения снова стали None
        assert item.current_status is None
        assert item.current_location is None
        assert item.current_responsible is None

    def test_current_operation_value_with_corrupted_data(self):
        """Тест CurrentOperationValue при удалении операции."""
        item = ItemFactory()
        
        # Создаем операцию
        operation = OperationFactory(item=item)
        
        # Сохраняем значения для проверки
        status_name = operation.status.name
        location_name = operation.location.name
        responsible = operation.responsible
        
        # Удаляем операцию
        operation.delete()
        item.refresh_from_db()
        
        # Проверяем, что значения стали None
        assert item.current_status is None
        assert item.current_location is None
        assert item.current_responsible is None
        
        # Проверяем, что связанные объекты остались
        assert Status.objects.filter(name=status_name).exists()
        assert Location.objects.filter(name=location_name).exists()
        assert Responsible.objects.filter(id=responsible.id).exists()

    def test_current_operation_value_with_deleted_item(self):
        """Тест CurrentOperationValue при удалении экземпляра."""
        item = ItemFactory()
        operation = OperationFactory(item=item)
        
        # Удаляем экземпляр
        item_id = item.id
        item.delete()
        
        # Пытаемся получить значения для удаленного экземпляра
        with pytest.raises(Item.DoesNotExist):
            Item.objects.get(id=item_id).current_status

    def test_current_operation_value_with_invalid_attr_name(self):
        """Тест CurrentOperationValue с некорректным именем атрибута."""
        class InvalidOperationValue(Item.CurrentOperationValue):
            def __init__(self):
                super().__init__("invalid_attr")
        
        item = ItemFactory()
        operation = OperationFactory(item=item)
        
        # Создаем дескриптор с некорректным именем атрибута
        invalid_value = InvalidOperationValue()
        
        # Проверяем, что при обращении к несуществующему атрибуту возвращается None
        assert getattr(item, 'invalid_attr', None) is None


@pytest.mark.django_db
class TestOperation:
    """Тесты для модели Operation."""

    def test_meta(self):
        """Тест метаданных модели."""
        assert Operation._meta.verbose_name == "Эксплуатация"
        assert Operation._meta.verbose_name_plural == "Эксплуатация"
        assert Operation._meta.ordering == ["-updated_at"]

    def test_item_field(self):
        """Тест поля item."""
        field = Operation._meta.get_field("item")
        assert field.verbose_name == "Экземпляр"
        assert field.remote_field.on_delete == models.CASCADE
        assert isinstance(field, models.ForeignKey)

    def test_status_field(self):
        """Тест поля status."""
        field = Operation._meta.get_field("status")
        assert field.verbose_name == "Статус"
        assert field.remote_field.on_delete == models.PROTECT
        assert isinstance(field, models.ForeignKey)

    def test_responsible_field(self):
        """Тест поля responsible."""
        field = Operation._meta.get_field("responsible")
        assert field.verbose_name == "Ответственный"
        assert field.remote_field.on_delete == models.PROTECT
        assert isinstance(field, models.ForeignKey)

    def test_location_field(self):
        """Тест поля location."""
        field = Operation._meta.get_field("location")
        assert field.verbose_name == "Расположение"
        assert field.remote_field.on_delete == models.PROTECT
        assert isinstance(field, models.ForeignKey)

    def test_str(self):
        """Тест метода __str__."""
        operation = OperationFactory()
        expected = f"{operation.item} - {operation.status} ({operation.location})"
        assert str(operation) == expected

    def test_get_responsible_display(self):
        """Тест метода get_responsible_display."""
        operation = OperationFactory()
        expected = f"{operation.responsible.last_name} {operation.responsible.first_name} {operation.responsible.middle_name}"
        assert str(operation.responsible) == expected

    def test_delete(self):
        """Тест удаления операций."""
        operation = OperationFactory()
        
        # Проверка каскадного удаления
        item_id = operation.item.id
        operation.item.delete()
        assert not Operation.objects.filter(item_id=item_id).exists()

        # Проверка защиты от удаления
        new_item = ItemFactory()
        new_operation = OperationFactory(item=new_item, status=operation.status)
        with pytest.raises(ProtectedError):
            operation.status.delete()

    def test_cascade_delete(self):
        """Тест каскадного удаления связанных объектов."""
        item = ItemFactory()
        operation = OperationFactory(item=item)
        status = operation.status
        location = operation.location
        responsible = operation.responsible

        # Удаляем экземпляр
        item.delete()

        # Проверяем, что операция удалена
        assert not Operation.objects.filter(id=operation.id).exists()

        # Проверяем, что связанные объекты не удалены
        assert Status.objects.filter(id=status.id).exists()
        assert Location.objects.filter(id=location.id).exists()
        assert Responsible.objects.filter(id=responsible.id).exists()

    def test_protected_delete(self):
        """Тест защиты от удаления связанных объектов."""
        item = ItemFactory()
        operation = OperationFactory(item=item)
        status = operation.status
        location = operation.location
        responsible = operation.responsible

        # Проверяем, что нельзя удалить статус
        with pytest.raises(ProtectedError):
            status.delete()

        # Проверяем, что нельзя удалить локацию
        with pytest.raises(ProtectedError):
            location.delete()

        # Проверяем, что нельзя удалить ответственного
        with pytest.raises(ProtectedError):
            responsible.delete()

        # Проверяем, что объекты не удалены
        assert Status.objects.filter(id=status.id).exists()
        assert Location.objects.filter(id=location.id).exists()
        assert Responsible.objects.filter(id=responsible.id).exists()

    def test_operation_ordering(self):
        """Тест сортировки операций."""
        item = ItemFactory()
        operations = []
        
        # Создаем операции с разными временными метками
        for i in range(3):
            operation = OperationFactory(item=item)
            operations.append(operation)
            time.sleep(1)  # Добавляем задержку для разных временных меток

        # Проверяем, что операции отсортированы по убыванию updated_at
        sorted_operations = Operation.objects.filter(item=item)
        assert list(sorted_operations) == list(reversed(operations))

    def test_status_transition(self):
        """Тест перехода между статусами."""
        item = ItemFactory()
        status1 = StatusFactory()
        status2 = StatusFactory()

        # Создаем первую операцию
        operation1 = OperationFactory(item=item, status=status1)
        assert item.current_status == status1.name

        # Создаем вторую операцию с другим статусом
        operation2 = OperationFactory(item=item, status=status2)
        assert item.current_status == status2.name

        # Проверяем, что первая операция осталась в истории
        assert Operation.objects.filter(id=operation1.id).exists()
        assert Operation.objects.filter(id=operation2.id).exists()

    def test_location_transition(self):
        """Тест перехода между локациями."""
        item = ItemFactory()
        location1 = LocationFactory()
        location2 = LocationFactory()

        # Создаем первую операцию
        operation1 = OperationFactory(item=item, location=location1)
        assert item.current_location == location1.name

        # Создаем вторую операцию с другой локацией
        operation2 = OperationFactory(item=item, location=location2)
        assert item.current_location == location2.name

        # Проверяем, что первая операция осталась в истории
        assert Operation.objects.filter(id=operation1.id).exists()
        assert Operation.objects.filter(id=operation2.id).exists()

    def test_responsible_transition(self):
        """Тест перехода между ответственными."""
        item = ItemFactory()
        responsible1 = ResponsibleFactory()
        responsible2 = ResponsibleFactory()

        # Создаем первую операцию
        operation1 = OperationFactory(item=item, responsible=responsible1)
        assert item.current_responsible == responsible1

        # Создаем вторую операцию с другим ответственным
        operation2 = OperationFactory(item=item, responsible=responsible2)
        assert item.current_responsible == responsible2

        # Проверяем, что первая операция осталась в истории
        assert Operation.objects.filter(id=operation1.id).exists()
        assert Operation.objects.filter(id=operation2.id).exists()

    def test_operation_history(self):
        """Тест истории операций."""
        item = ItemFactory()
        status1 = StatusFactory()
        status2 = StatusFactory()
        status3 = StatusFactory()

        # Создаем последовательность операций
        operation1 = OperationFactory(item=item, status=status1)
        operation2 = OperationFactory(item=item, status=status2)
        operation3 = OperationFactory(item=item, status=status3)

        # Проверяем историю операций
        operations = Operation.objects.filter(item=item)
        assert len(operations) == 3
        assert operations[0] == operation3
        assert operations[1] == operation2
        assert operations[2] == operation1

        # Проверяем текущее состояние
        assert item.current_status == status3.name
        assert item.current_operation == operation3

    def test_operation_with_same_status(self):
        """Тест операций с одинаковым статусом."""
        item = ItemFactory()
        status = StatusFactory()
        
        # Создаем операции с одинаковым статусом
        operation1 = OperationFactory(item=item, status=status)
        operation2 = OperationFactory(item=item, status=status)

        # Проверяем, что статус обновился
        assert item.current_status == status.name
        assert item.current_operation == operation2

    def test_operation_with_same_location(self):
        """Тест операций с одинаковой локацией."""
        item = ItemFactory()
        location = LocationFactory()
        
        # Создаем операции с одинаковой локацией
        operation1 = OperationFactory(item=item, location=location)
        operation2 = OperationFactory(item=item, location=location)

        # Проверяем, что локация обновилась
        assert item.current_location == location.name
        assert item.current_operation == operation2

    def test_operation_with_same_responsible(self):
        """Тест операций с одинаковым ответственным."""
        item = ItemFactory()
        responsible = ResponsibleFactory()
        
        # Создаем операции с одинаковым ответственным
        operation1 = OperationFactory(item=item, responsible=responsible)
        operation2 = OperationFactory(item=item, responsible=responsible)

        # Проверяем, что ответственный обновился
        assert item.current_responsible == responsible
        assert item.current_operation == operation2

    def test_operation_with_all_same_values(self):
        """Тест операций с одинаковыми значениями всех полей."""
        item = ItemFactory()
        status = StatusFactory()
        location = LocationFactory()
        responsible = ResponsibleFactory()
        
        # Создаем операции с одинаковыми значениями
        operation1 = OperationFactory(
            item=item,
            status=status,
            location=location,
            responsible=responsible
        )
        operation2 = OperationFactory(
            item=item,
            status=status,
            location=location,
            responsible=responsible
        )

        # Проверяем, что все значения обновились
        assert item.current_status == status.name
        assert item.current_location == location.name
        assert item.current_responsible == responsible
        assert item.current_operation == operation2

    def test_operation_with_empty_values(self):
        """Тест операций с пустыми значениями."""
        item = ItemFactory()
        status = StatusFactory(name="")
        location = LocationFactory(name="")
        responsible = ResponsibleFactory()
        
        # Создаем операцию с пустыми значениями
        operation = OperationFactory(
            item=item,
            status=status,
            location=location,
            responsible=responsible
        )

        # Проверяем, что все значения пустые
        assert item.current_status == ""
        assert item.current_location == ""
        assert item.current_responsible == responsible 