from django.http import JsonResponse, HttpResponseForbidden
from django.db import connection

def check_database():
    """Проверка базы данных"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True, "Database connection OK"
    except Exception as e:
        return False, f"Database error: {str(e)}"

def is_local_request(request):
    return request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1')

def liveness(request):
    """
    Liveness probe проверяет, что процесс приложения работает.
    """
    if not is_local_request(request):
        return HttpResponseForbidden('Access allowed only from localhost')
    return JsonResponse({'status': 'ok'})

def readiness(request):
    """
    Readiness probe проверяет, что приложение готово принимать трафик.
    Проверяет доступность критических компонентов.
    """
    if not is_local_request(request):
        return HttpResponseForbidden('Access allowed only from localhost')
    checks = {
        'database': check_database()
    }
    
    all_ok = all(status for status, _ in checks.values())
    
    if not all_ok:
        return JsonResponse({
            'status': 'error',
            'checks': {k: v[1] for k, v in checks.items()}
        }, status=503)
    
    return JsonResponse({
        'status': 'ok',
        'checks': {k: v[1] for k, v in checks.items()}
    })
