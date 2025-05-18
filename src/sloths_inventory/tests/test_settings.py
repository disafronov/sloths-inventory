"""Тесты настроек Django."""

import os
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def test_secret_key():
    """Тест наличия SECRET_KEY."""
    assert hasattr(settings, 'SECRET_KEY')
    assert settings.SECRET_KEY


def test_debug():
    """Тест настройки DEBUG."""
    assert hasattr(settings, 'DEBUG')
    assert isinstance(settings.DEBUG, bool)


def test_allowed_hosts():
    """Тест настройки ALLOWED_HOSTS."""
    assert hasattr(settings, 'ALLOWED_HOSTS')
    assert isinstance(settings.ALLOWED_HOSTS, list)


def test_csrf_trusted_origins():
    """Тест настройки CSRF_TRUSTED_ORIGINS."""
    assert hasattr(settings, 'CSRF_TRUSTED_ORIGINS')
    assert isinstance(settings.CSRF_TRUSTED_ORIGINS, list)


def test_installed_apps():
    """Тест установленных приложений."""
    assert hasattr(settings, 'INSTALLED_APPS')
    assert isinstance(settings.INSTALLED_APPS, list)
    required_apps = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'common',
        'catalogs',
        'devices',
        'inventory',
    ]
    for app in required_apps:
        assert app in settings.INSTALLED_APPS


def test_middleware():
    """Тест установленных middleware."""
    assert hasattr(settings, 'MIDDLEWARE')
    assert isinstance(settings.MIDDLEWARE, list)
    required_middleware = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
    for middleware in required_middleware:
        assert middleware in settings.MIDDLEWARE


def test_database():
    """Тест настроек базы данных."""
    assert hasattr(settings, 'DATABASES')
    assert isinstance(settings.DATABASES, dict)
    assert 'default' in settings.DATABASES
    assert settings.DATABASES['default']['ENGINE'].startswith('django.db.backends.postgresql')
    assert isinstance(settings.DATABASES['default']['NAME'], str)
    assert isinstance(settings.DATABASES['default']['USER'], str)
    assert isinstance(settings.DATABASES['default']['PASSWORD'], str)
    assert isinstance(settings.DATABASES['default']['HOST'], str)
    assert isinstance(settings.DATABASES['default']['PORT'], str)


def test_password_validators():
    """Тест настроек валидаторов паролей."""
    assert hasattr(settings, 'AUTH_PASSWORD_VALIDATORS')
    assert isinstance(settings.AUTH_PASSWORD_VALIDATORS, list)
    assert len(settings.AUTH_PASSWORD_VALIDATORS) > 0


def test_internationalization():
    """Тест настроек интернационализации."""
    assert hasattr(settings, 'LANGUAGE_CODE')
    assert hasattr(settings, 'TIME_ZONE')
    assert hasattr(settings, 'USE_I18N')
    assert hasattr(settings, 'USE_TZ')
    assert settings.LANGUAGE_CODE == 'en-us'
    assert settings.TIME_ZONE == 'UTC'
    assert settings.USE_I18N is True
    assert settings.USE_TZ is True


def test_static_files():
    """Тест настроек статических файлов."""
    assert hasattr(settings, 'STATIC_URL')
    assert settings.STATIC_URL == '/static/'


def test_default_auto_field():
    """Тест настройки DEFAULT_AUTO_FIELD."""
    assert hasattr(settings, 'DEFAULT_AUTO_FIELD')
    assert settings.DEFAULT_AUTO_FIELD == 'django.db.models.BigAutoField'


def test_test_runner():
    """Тест настройки тестового раннера."""
    assert hasattr(settings, 'TEST_RUNNER')
    assert settings.TEST_RUNNER == 'sloths_inventory.tests.runner.CustomTestRunner'


def test_templates():
    """Тест настроек шаблонов."""
    assert hasattr(settings, 'TEMPLATES')
    assert isinstance(settings.TEMPLATES, list)
    assert len(settings.TEMPLATES) > 0


def test_auth_password_validators():
    """Тест настройки валидаторов паролей."""
    required_validators = [
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "django.contrib.auth.password_validation.MinimumLengthValidator",
        "django.contrib.auth.password_validation.CommonPasswordValidator",
        "django.contrib.auth.password_validation.NumericPasswordValidator",
    ]
    for validator in required_validators:
        assert any(v["NAME"] == validator for v in settings.AUTH_PASSWORD_VALIDATORS)


def test_test_runner():
    """Тест настройки кастомного тестового раннера."""
    assert settings.TEST_RUNNER == "sloths_inventory.tests.runner.PytestTestRunner"


def test_templates():
    """Тест конфигурации шаблонов."""
    assert len(settings.TEMPLATES) == 1
    template_settings = settings.TEMPLATES[0]
    assert template_settings["BACKEND"] == "django.template.backends.django.DjangoTemplates"
    assert "templates" in template_settings["DIRS"]
    assert template_settings["APP_DIRS"] is True
    required_processors = [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]
    for processor in required_processors:
        assert processor in template_settings["OPTIONS"]["context_processors"] 