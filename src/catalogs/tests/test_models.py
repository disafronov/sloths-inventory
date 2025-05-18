"""
Тесты для моделей приложения catalogs.
"""
import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db import models
from django.core.exceptions import ValidationError
from django.db.utils import DataError
from django.utils import timezone

from catalogs.models import Device, Location, Responsible, Status
from catalogs.tests.factories import (
    DeviceFactory,
    LocationFactory,
    ResponsibleFactory,
    StatusFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestDevice:
    def test_str(self):
        device = DeviceFactory()
        assert str(device) == f"{device.category} | {device.type} | {device.manufacturer} | {device.model}"

    def test_ordering(self):
        device1 = DeviceFactory()
        device2 = DeviceFactory()
        assert Device.objects.first() == device1
        assert Device.objects.last() == device2

    def test_unique_together(self):
        device = DeviceFactory()
        with pytest.raises(IntegrityError):
            DeviceFactory(
                category=device.category,
                type=device.type,
                manufacturer=device.manufacturer,
                model=device.model,
            )

    def test_verbose_names(self):
        assert Device._meta.verbose_name == "Устройство"
        assert Device._meta.verbose_name_plural == "Устройства"

    def test_foreign_keys(self):
        """Тест внешних ключей и их настроек."""
        device = DeviceFactory()
        
        # Проверяем category
        assert device.category._meta.model._meta.get_field("device").on_delete == models.PROTECT
        assert device.category._meta.verbose_name == "Категория"
        
        # Проверяем type
        assert device.type._meta.model._meta.get_field("device").on_delete == models.PROTECT
        assert device.type._meta.verbose_name == "Тип"
        
        # Проверяем manufacturer
        assert device.manufacturer._meta.model._meta.get_field("device").on_delete == models.PROTECT
        assert device.manufacturer._meta.verbose_name == "Производитель"
        
        # Проверяем model
        assert device.model._meta.model._meta.get_field("device").on_delete == models.PROTECT
        assert device.model._meta.verbose_name == "Модель"

    def test_device_requires_foreign_keys(self):
        with pytest.raises(IntegrityError):
            Device.objects.create()

    def test_device_protects_foreign_keys(self):
        device = DeviceFactory()
        category = device.category
        type = device.type
        manufacturer = device.manufacturer
        model = device.model

        with pytest.raises(models.ProtectedError):
            category.delete()
        with pytest.raises(models.ProtectedError):
            type.delete()
        with pytest.raises(models.ProtectedError):
            manufacturer.delete()
        with pytest.raises(models.ProtectedError):
            model.delete()


@pytest.mark.django_db
class TestLocation:
    def test_str(self):
        location = LocationFactory()
        assert str(location) == location.name

    def test_ordering(self):
        location1 = LocationFactory(name="A")
        location2 = LocationFactory(name="B")
        assert Location.objects.first() == location1
        assert Location.objects.last() == location2

    def test_verbose_names(self):
        assert Location._meta.verbose_name == "Расположение"
        assert Location._meta.verbose_name_plural == "Расположения"

    def test_name_field(self):
        field = Location._meta.get_field("name")
        assert field.max_length == 255
        assert field.unique is True
        assert field.verbose_name == "Название"

    def test_name_too_long(self):
        with pytest.raises(DataError):
            LocationFactory(name="A" * 256)

    def test_name_unique(self):
        name = "Test Location"
        LocationFactory(name=name)
        with pytest.raises(IntegrityError):
            LocationFactory(name=name)

    def test_name_empty(self):
        obj = LocationFactory.build(name="")
        with pytest.raises(ValidationError):
            obj.full_clean()


@pytest.mark.django_db
class TestResponsible:
    def test_str(self):
        responsible = ResponsibleFactory()
        assert str(responsible) == responsible.get_full_name()

    def test_get_full_name(self):
        responsible = ResponsibleFactory(
            last_name="Иванов",
            first_name="Иван",
            middle_name="Иванович",
        )
        assert responsible.get_full_name() == "Иванов Иван Иванович"

    def test_get_full_name_without_middle_name(self):
        responsible = ResponsibleFactory(
            last_name="Иванов",
            first_name="Иван",
            middle_name=None,
        )
        assert responsible.get_full_name() == "Иванов Иван"

    def test_ordering(self):
        responsible1 = ResponsibleFactory(last_name="A")
        responsible2 = ResponsibleFactory(last_name="B")
        assert Responsible.objects.first() == responsible1
        assert Responsible.objects.last() == responsible2

    def test_unique_user(self):
        user = UserFactory()
        ResponsibleFactory(user=user)
        with pytest.raises(IntegrityError):
            ResponsibleFactory(user=user)

    def test_verbose_names(self):
        assert Responsible._meta.verbose_name == "Ответственный"
        assert Responsible._meta.verbose_name_plural == "Ответственные"

    def test_user_foreign_key(self):
        responsible = ResponsibleFactory()
        assert responsible.user._meta.model._meta.get_field("responsible").on_delete == models.SET_NULL

    def test_name_fields(self):
        """Тест полей имени."""
        # Проверяем last_name
        field = Responsible._meta.get_field("last_name")
        assert field.max_length == 150
        assert field.verbose_name == "Фамилия"
        assert field.null is False
        assert field.blank is False

        # Проверяем first_name
        field = Responsible._meta.get_field("first_name")
        assert field.max_length == 150
        assert field.verbose_name == "Имя"
        assert field.null is False
        assert field.blank is False

        # Проверяем middle_name
        field = Responsible._meta.get_field("middle_name")
        assert field.max_length == 150
        assert field.verbose_name == "Отчество"
        assert field.null is True
        assert field.blank is True

    def test_employee_id_field(self):
        """Тест поля employee_id."""
        field = Responsible._meta.get_field("employee_id")
        assert field.max_length == 50
        assert field.verbose_name == "Табельный номер"
        assert field.null is False
        assert field.blank is True

    def test_last_name_too_long(self):
        with pytest.raises(DataError):
            ResponsibleFactory(last_name="A" * 151)

    def test_first_name_too_long(self):
        with pytest.raises(DataError):
            ResponsibleFactory(first_name="A" * 151)

    def test_middle_name_too_long(self):
        with pytest.raises(DataError):
            ResponsibleFactory(middle_name="A" * 151)

    def test_last_name_empty(self):
        obj = ResponsibleFactory.build(last_name="")
        with pytest.raises(ValidationError):
            obj.full_clean()

    def test_first_name_empty(self):
        obj = ResponsibleFactory.build(first_name="")
        with pytest.raises(ValidationError):
            obj.full_clean()


@pytest.mark.django_db
class TestStatus:
    def test_str(self):
        status = StatusFactory()
        assert str(status) == status.name

    def test_ordering(self):
        status1 = StatusFactory(name="A")
        status2 = StatusFactory(name="B")
        assert Status.objects.first() == status1
        assert Status.objects.last() == status2

    def test_verbose_names(self):
        assert Status._meta.verbose_name == "Статус"
        assert Status._meta.verbose_name_plural == "Статусы"

    def test_name_field(self):
        field = Status._meta.get_field("name")
        assert field.max_length == 255
        assert field.unique is True
        assert field.verbose_name == "Название"

    def test_status_name_too_long(self):
        with pytest.raises(DataError):
            StatusFactory(name="A" * 256)

    def test_status_name_unique(self):
        name = "Test Status"
        StatusFactory(name=name)
        with pytest.raises(IntegrityError):
            StatusFactory(name=name)

    def test_status_name_empty(self):
        obj = StatusFactory.build(name="")
        with pytest.raises(ValidationError):
            obj.full_clean() 