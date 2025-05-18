"""Тесты для PytestTestRunner."""
import pytest
from unittest.mock import patch, MagicMock
from ..tests.runner import PytestTestRunner


def test_pytest_test_runner_init():
    """Тест инициализации PytestTestRunner."""
    runner = PytestTestRunner()
    assert runner.test_loader is None
    assert runner.test_runner is None


@pytest.mark.parametrize('test_labels,keepdb,failfast,verbosity,expected_argv', [
    ([], False, False, 1, []),
    (['app1', 'app2'], False, False, 1, ['app1', 'app2']),
    ([], True, False, 1, ['--reuse-db']),
    ([], False, True, 1, ['--exitfirst']),
    ([], False, False, 0, ['--quiet']),
    ([], False, False, 2, ['--verbose']),
    ([], False, False, 3, ['-vv']),
    (['app1'], True, True, 2, ['app1', '--reuse-db', '--exitfirst', '--verbose']),
])
def test_pytest_test_runner_run_tests(test_labels, keepdb, failfast, verbosity, expected_argv):
    """Тест метода run_tests с различными параметрами."""
    runner = PytestTestRunner()
    
    with patch('pytest.main') as mock_pytest_main:
        mock_pytest_main.return_value = 0
        result = runner.run_tests(
            test_labels=test_labels,
            keepdb=keepdb,
            failfast=failfast,
            verbosity=verbosity
        )
        
        mock_pytest_main.assert_called_once_with(expected_argv)
        assert result == 0 