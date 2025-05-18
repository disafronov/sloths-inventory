from django.test import TestCase
from django.db import models
from django.utils import timezone
from .models import BaseModel, NamedModel


class TestBaseModel(BaseModel):
    """
    Тестовая модель для проверки BaseModel.
    """
    pass


class TestNamedModel(NamedModel):
    """
    Тестовая модель для проверки NamedModel.
    """
    pass


class BaseModelTest(TestCase):
    def setUp(self):
        self.model = TestBaseModel.objects.create(notes="Test notes")

    def test_notes(self):
        """Проверяем, что поле notes корректно сохраняется."""
        self.assertEqual(self.model.notes, "Test notes")


class NamedModelTest(TestCase):
    def setUp(self):
        self.model = TestNamedModel.objects.create(name="Test Name")

    def test_ordering(self):
        """Проверяем, что сортировка по умолчанию работает корректно."""
        TestNamedModel.objects.create(name="A Name")
        TestNamedModel.objects.create(name="B Name")
        TestNamedModel.objects.create(name="C Name")
        
        names = [obj.name for obj in TestNamedModel.objects.all()]
        self.assertEqual(names, ["A Name", "B Name", "C Name", "Test Name"])

    def test_unique_name(self):
        """Проверяем, что имя должно быть уникальным."""
        with self.assertRaises(Exception):
            TestNamedModel.objects.create(name="Test Name") 