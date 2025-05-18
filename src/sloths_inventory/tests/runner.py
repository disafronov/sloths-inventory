"""
Тестовый раннер для Django.
"""
from django.test.runner import DiscoverRunner


class PytestTestRunner(DiscoverRunner):
    """Тестовый раннер, который использует pytest для запуска тестов."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_loader = None
        self.test_runner = None

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Запускает тесты с помощью pytest."""
        import pytest
        import sys

        argv = []
        if test_labels:
            argv.extend(test_labels)
        if kwargs.get('keepdb'):
            argv.append('--reuse-db')
        if kwargs.get('failfast'):
            argv.append('--exitfirst')
        if kwargs.get('verbosity') == 0:
            argv.append('--quiet')
        elif kwargs.get('verbosity') == 2:
            argv.append('--verbose')
        elif kwargs.get('verbosity') == 3:
            argv.append('-vv')

        return pytest.main(argv) 