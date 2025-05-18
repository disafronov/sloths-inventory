from django.test import TestCase, RequestFactory
from django.db import connection
from unittest.mock import patch
import json
from common.health import check_database, liveness, readiness

class HealthCheckTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_check_database_success(self):
        """Тест успешной проверки базы данных"""
        status, message = check_database()
        self.assertTrue(status)
        self.assertEqual(message, "Database connection OK")

    @patch('django.db.connection.cursor')
    def test_check_database_failure(self, mock_cursor):
        """Тест ошибки при проверке базы данных"""
        mock_cursor.side_effect = Exception("Connection failed")
        status, message = check_database()
        self.assertFalse(status)
        self.assertEqual(message, "Database error: Connection failed")

    def test_liveness(self):
        """Тест проверки работоспособности приложения"""
        request = self.factory.get('/health/liveness')
        response = liveness(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'ok'})

    def test_readiness_success(self):
        """Тест успешной проверки готовности приложения"""
        request = self.factory.get('/health/readiness')
        response = readiness(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'status': 'ok',
            'checks': {'database': 'Database connection OK'}
        })

    @patch('django.db.connection.cursor')
    def test_readiness_failure(self, mock_cursor):
        """Тест ошибки при проверке готовности приложения"""
        mock_cursor.side_effect = Exception("Connection failed")
        request = self.factory.get('/health/readiness')
        response = readiness(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.content), {
            'status': 'error',
            'checks': {'database': 'Database error: Connection failed'}
        }) 