"""Tests for manage.py."""

import importlib
import os
import sys
import types
from unittest.mock import patch

import pytest


def test_manage_py_import_and_main():
    """Test that manage.py can be imported and main() function exists."""
    manage = importlib.import_module('manage')
    assert hasattr(manage, 'main')
    assert callable(manage.main)


def test_main_function_raises_import_error():
    """Test that main() raises ImportError when Django is not installed."""
    with patch('builtins.__import__', side_effect=ImportError):
        with pytest.raises(ImportError) as exc_info:
            importlib.import_module('manage').main()
        assert "Couldn't import Django" in str(exc_info.value)


def test_main_function_calls_execute_from_command_line():
    """Test that main() calls execute_from_command_line with sys.argv."""
    with patch('django.core.management.execute_from_command_line') as mock_execute:
        with patch('sys.argv', ['manage.py', 'test']):
            importlib.import_module('manage').main()
            mock_execute.assert_called_once_with(['manage.py', 'test'])


def test_manage_py_environment():
    """Test environment variables setup."""
    with patch.dict(os.environ, clear=True):
        with patch('sys.argv', ['manage.py', 'nonexistentcommand']):
            import manage
            with pytest.raises(SystemExit):
                manage.main()
            assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'sloths_inventory.settings' 