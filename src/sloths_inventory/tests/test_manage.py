"""Тесты для manage.py."""
import os
import sys
import pytest
from unittest.mock import patch


def test_manage_py_import_and_main():
    """Тест импорта и функции main в manage.py."""
    import importlib
    manage = importlib.import_module('manage')
    assert hasattr(manage, 'main')
    
    # Проверяем, что main можно вызвать с несуществующей командой
    with patch('sys.argv', ['manage.py', 'nonexistentcommand']):
        with pytest.raises(SystemExit):
            manage.main()


def test_manage_py_environment():
    """Тест установки переменных окружения."""
    with patch.dict(os.environ, clear=True):
        with patch('sys.argv', ['manage.py', 'nonexistentcommand']):
            import manage
            with pytest.raises(SystemExit):
                manage.main()
            assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'sloths_inventory.settings' 