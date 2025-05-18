"""Дымовые тесты для проверки базовой функциональности."""

def test_asgi_import():
    """Тест импорта ASGI приложения."""
    import importlib
    asgi = importlib.import_module('sloths_inventory.asgi')
    assert hasattr(asgi, 'application')

def test_wsgi_import():
    """Тест импорта WSGI приложения."""
    import importlib
    wsgi = importlib.import_module('sloths_inventory.wsgi')
    assert hasattr(wsgi, 'application')

def test_urls_import():
    """Тест импорта URL-конфигурации."""
    import importlib
    urls = importlib.import_module('sloths_inventory.urls')
    assert hasattr(urls, 'urlpatterns')
    assert len(urls.urlpatterns) > 0

def test_settings_import():
    """Тест импорта настроек."""
    import importlib
    settings = importlib.import_module('sloths_inventory.settings')
    assert hasattr(settings, 'INSTALLED_APPS')
    assert hasattr(settings, 'DATABASES')
    assert hasattr(settings, 'SECRET_KEY')
    assert hasattr(settings, 'DEBUG')
    assert hasattr(settings, 'ALLOWED_HOSTS') 