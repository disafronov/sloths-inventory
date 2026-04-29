from django.test import Client


def test_home_and_health_routes_are_wired(monkeypatch) -> None:
    # Avoid touching the database in this wiring/smoke test.
    from health import health

    monkeypatch.setattr(health, "check_database", lambda: (True, "ok"))

    client = Client()

    assert client.get("/").status_code == 200

    health_index = client.get("/health/")
    assert health_index.status_code == 200
    assert b"liveness" in health_index.content
    assert b"readiness" in health_index.content

    assert client.get("/health/liveness/").status_code == 200
    assert client.get("/health/readiness/").status_code == 200
