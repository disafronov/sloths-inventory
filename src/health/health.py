import logging

from django.db import connection
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)


def check_database() -> tuple[bool, str]:
    """Проверка базы данных"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True, "Database connection OK"
    except Exception:
        logger.exception("Database readiness check failed")
        return False, "Database connection failed"


def liveness(request: HttpRequest) -> JsonResponse:
    """
    Liveness probe проверяет, что процесс приложения работает.
    """
    return JsonResponse({"status": "ok"})


def readiness(request: HttpRequest) -> JsonResponse:
    """
    Readiness probe проверяет, что приложение готово принимать трафик.
    Проверяет доступность критических компонентов.
    """
    checks = {"database": check_database()}

    all_ok = all(status for status, _ in checks.values())

    if not all_ok:
        return JsonResponse(
            {"status": "error", "checks": {k: v[1] for k, v in checks.items()}},
            status=503,
        )

    return JsonResponse(
        {"status": "ok", "checks": {k: v[1] for k, v in checks.items()}}
    )
