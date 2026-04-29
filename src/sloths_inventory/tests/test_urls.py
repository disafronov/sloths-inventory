import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.mark.django_db
def test_home_and_health_routes_are_wired(monkeypatch) -> None:
    # Avoid touching the database in this wiring/smoke test.
    from health import health

    monkeypatch.setattr(health, "check_database", lambda: (True, "ok"))

    client = Client()

    # Anonymous user is redirected to login (root is "My items").
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]

    # Authenticated user is redirected to "My items".
    user = User.objects.create_user(username="smoke", password="pw")
    client.force_login(user)
    assert client.get("/").status_code == 200

    health_index = client.get("/health/")
    assert health_index.status_code == 200
    assert b"liveness" in health_index.content
    assert b"readiness" in health_index.content

    assert client.get("/health/liveness/").status_code == 200
    assert client.get("/health/readiness/").status_code == 200
