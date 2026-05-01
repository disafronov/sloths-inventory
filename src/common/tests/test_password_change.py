import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.mark.django_db
def test_password_change_requires_login() -> None:
    client = Client()
    response = client.get("/password/change/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


@pytest.mark.django_db
def test_password_change_get_renders_form_for_authenticated_user() -> None:
    user = User.objects.create_user(username="alice", password="old")

    client = Client()
    client.force_login(user)

    response = client.get("/password/change/")
    assert response.status_code == 200

    # Form fields from Django's PasswordChangeForm.
    assert b'name="old_password"' in response.content
    assert b'name="new_password1"' in response.content
    assert b'name="new_password2"' in response.content


@pytest.mark.django_db
def test_password_change_link_is_visible_for_authenticated_user_before_logout() -> None:
    user = User.objects.create_user(username="alice", password="pw", is_staff=True)

    client = Client()
    client.force_login(user)

    response = client.get("/")
    assert response.status_code == 200

    body = response.content
    idx_change = body.find(b"/password/change/")
    idx_logout = body.find(b'action="/logout/')

    assert idx_change != -1
    assert idx_logout != -1
    assert idx_change < idx_logout
