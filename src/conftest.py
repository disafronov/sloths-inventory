"""
Общие фикстуры для всех тестов.
"""
import pytest
from django.conf import settings


def pytest_configure():
    """
    Настройка pytest для работы с Django.
    """
    settings.DEBUG = False 