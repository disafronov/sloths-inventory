"""
Фабрики для тестов приложения catalogs.
"""
import factory
from django.contrib.auth import get_user_model
from ..models import Device, Location, Responsible, Status
from devices.tests.factories import CategoryFactory, TypeFactory, ManufacturerFactory, ModelFactory

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания пользователей."""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password')


class LocationFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания расположений."""
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f'Location {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class StatusFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания статусов."""
    class Meta:
        model = Status

    name = factory.Sequence(lambda n: f'Status {n}')
    notes = factory.Faker('text', max_nb_chars=200)


class ResponsibleFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания ответственных."""
    class Meta:
        model = Responsible

    last_name = factory.Faker('last_name')
    first_name = factory.Faker('first_name')
    middle_name = factory.Faker('first_name')
    employee_id = factory.Sequence(lambda n: f'EMP{n:04d}')
    user = factory.SubFactory(UserFactory)


class DeviceFactory(factory.django.DjangoModelFactory):
    """Фабрика для создания устройств."""
    class Meta:
        model = Device

    category = factory.SubFactory(CategoryFactory)
    type = factory.SubFactory(TypeFactory)
    manufacturer = factory.SubFactory(ManufacturerFactory)
    model = factory.SubFactory(ModelFactory)
    notes = factory.Faker('text', max_nb_chars=200) 