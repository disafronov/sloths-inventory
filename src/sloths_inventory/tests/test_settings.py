"""Tests for Django settings."""

import os
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def test_secret_key():
    """Test that SECRET_KEY is set."""
    assert settings.SECRET_KEY is not None
    assert isinstance(settings.SECRET_KEY, str)
    assert len(settings.SECRET_KEY) > 0


def test_debug():
    """Test that DEBUG is set."""
    assert isinstance(settings.DEBUG, bool)


def test_allowed_hosts():
    """Test that ALLOWED_HOSTS is set."""
    assert isinstance(settings.ALLOWED_HOSTS, list)


def test_csrf_trusted_origins():
    """Test that CSRF_TRUSTED_ORIGINS is set."""
    assert isinstance(settings.CSRF_TRUSTED_ORIGINS, list)


def test_installed_apps():
    """Test that all required apps are installed."""
    required_apps = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "common",
        "devices",
        "catalogs",
        "inventory",
    ]
    for app in required_apps:
        assert app in settings.INSTALLED_APPS


def test_middleware():
    """Test that all required middleware is installed."""
    required_middleware = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]
    for middleware in required_middleware:
        assert middleware in settings.MIDDLEWARE


def test_database_settings():
    """Test that database settings are properly configured."""
    assert "default" in settings.DATABASES
    db_settings = settings.DATABASES["default"]
    assert db_settings["ENGINE"] == "django.db.backends.postgresql_psycopg2"
    assert isinstance(db_settings["NAME"], str)
    assert isinstance(db_settings["USER"], str)
    assert isinstance(db_settings["PASSWORD"], str)
    assert isinstance(db_settings["HOST"], str)
    assert isinstance(db_settings["PORT"], str)


def test_auth_password_validators():
    """Test that password validators are configured."""
    required_validators = [
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "django.contrib.auth.password_validation.MinimumLengthValidator",
        "django.contrib.auth.password_validation.CommonPasswordValidator",
        "django.contrib.auth.password_validation.NumericPasswordValidator",
    ]
    for validator in required_validators:
        assert any(v["NAME"] == validator for v in settings.AUTH_PASSWORD_VALIDATORS)


def test_internationalization():
    """Test internationalization settings."""
    assert settings.LANGUAGE_CODE == "en-us"
    assert settings.TIME_ZONE == "UTC"
    assert settings.USE_I18N is True
    assert settings.USE_TZ is True


def test_static_files():
    """Test static files settings."""
    assert settings.STATIC_URL == "/static/"


def test_default_auto_field():
    """Test default auto field setting."""
    assert settings.DEFAULT_AUTO_FIELD == "django.db.models.BigAutoField"


def test_test_runner():
    """Test that custom test runner is configured."""
    assert settings.TEST_RUNNER == "sloths_inventory.tests.runner.PytestTestRunner"


def test_templates():
    """Test templates configuration."""
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