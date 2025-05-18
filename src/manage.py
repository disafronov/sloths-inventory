#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sloths_inventory.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


def test_manage_py_import_and_main():
    import importlib
    import sys
    import types
    manage = importlib.import_module('manage')
    assert hasattr(manage, 'main')
    # Проверяем, что main можно вызвать без аргументов (упадёт на execute_from_command_line, но не раньше)
    try:
        manage.main()
    except SystemExit:
        pass
    except Exception as e:
        # Ожидаем ImportError или SystemExit, но не AttributeError
        assert isinstance(e, (ImportError, SystemExit))


if __name__ == '__main__':
    main()
