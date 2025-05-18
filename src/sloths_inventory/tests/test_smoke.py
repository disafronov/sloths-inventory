def test_asgi_import():
    import importlib
    asgi = importlib.import_module('sloths_inventory.asgi')
    assert hasattr(asgi, 'application')

def test_wsgi_import():
    import importlib
    wsgi = importlib.import_module('sloths_inventory.wsgi')
    assert hasattr(wsgi, 'application')

def test_urls_import():
    import importlib
    urls = importlib.import_module('sloths_inventory.urls')
    assert hasattr(urls, 'urlpatterns')

def test_settings_import():
    import importlib
    settings = importlib.import_module('sloths_inventory.settings')
    assert hasattr(settings, 'INSTALLED_APPS')
    assert hasattr(settings, 'DATABASES')
    assert hasattr(settings, 'SECRET_KEY') 