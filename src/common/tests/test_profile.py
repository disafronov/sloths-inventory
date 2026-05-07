"""Tests for profile and email change functionality."""

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from common.email_tokens import email_change_token_generator

User = get_user_model()


@pytest.mark.django_db
class TestNoEmailBanner:
    """Tests for the missing-email warning banner in base.html."""

    def test_banner_shown_when_user_has_no_email(
        self, client: Client, django_user_model
    ):
        django_user_model.objects.create_user(
            username="noemail", password="pw", email=""
        )
        client.login(username="noemail", password="pw")
        response = client.get(reverse("common:profile"))
        assert response.status_code == 200
        assert "Add one in your profile" in response.content.decode()

    def test_banner_hidden_when_user_has_email(self, client: Client, django_user_model):
        django_user_model.objects.create_user(
            username="hasemail", password="pw", email="u@example.com"
        )
        client.login(username="hasemail", password="pw")
        response = client.get(reverse("common:profile"))
        assert response.status_code == 200
        assert "Add one in your profile" not in response.content.decode()


@pytest.mark.django_db
class TestProfileView:
    """Tests for the profile view."""

    def test_profile_page_requires_login(self, client: Client):
        """Profile page should redirect to login if not authenticated."""
        response = client.get(reverse("common:profile"))
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_profile_page_accessible_when_logged_in(
        self, client: Client, django_user_model
    ):
        """Profile page should be accessible for authenticated users."""
        django_user_model.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        response = client.get(reverse("common:profile"))
        assert response.status_code == 200
        assert "test@example.com" in response.content.decode()

    def test_email_change_sends_confirmation_email(
        self, client: Client, django_user_model
    ):
        """Submitting email change form should send confirmation email."""
        django_user_model.objects.create_user(
            username="testuser", email="old@example.com", password="testpass123"
        )
        client.login(username="testuser", password="testpass123")

        response = client.post(
            reverse("common:profile"),
            {
                "email_submit": "1",
                "new_email": "new@example.com",
                "new_email_confirm": "new@example.com",
            },
        )

        assert response.status_code == 302
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["new@example.com"]
        assert "Confirm your email address change" in mail.outbox[0].subject

    def test_email_change_validation_same_email(
        self, client: Client, django_user_model
    ):
        """Cannot change to the same email address."""
        django_user_model.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        client.login(username="testuser", password="testpass123")

        response = client.post(
            reverse("common:profile"),
            {
                "email_submit": "1",
                "new_email": "test@example.com",
                "new_email_confirm": "test@example.com",
            },
        )

        assert response.status_code == 200
        assert "must be different from the current one" in response.content.decode()

    def test_email_change_validation_mismatch(self, client: Client, django_user_model):
        """Email addresses must match."""
        django_user_model.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        client.login(username="testuser", password="testpass123")

        response = client.post(
            reverse("common:profile"),
            {
                "email_submit": "1",
                "new_email": "new1@example.com",
                "new_email_confirm": "new2@example.com",
            },
        )

        assert response.status_code == 200
        assert "do not match" in response.content.decode()

    def test_email_change_validation_already_taken(
        self, client: Client, django_user_model
    ):
        """Cannot change to an email already used by another user."""
        django_user_model.objects.create_user(
            username="user1", email="taken@example.com", password="pass123"
        )
        django_user_model.objects.create_user(
            username="user2", email="user2@example.com", password="pass123"
        )
        client.login(username="user2", password="pass123")

        response = client.post(
            reverse("common:profile"),
            {
                "email_submit": "1",
                "new_email": "taken@example.com",
                "new_email_confirm": "taken@example.com",
            },
        )

        assert response.status_code == 200
        assert "already in use" in response.content.decode()

    def test_profile_view_post_no_submit_button(
        self, client: Client, django_user_model
    ):
        """Posting to profile without a submit button should just return the page."""
        django_user_model.objects.create_user(username="testuser", password="password")
        client.login(username="testuser", password="password")
        response = client.post(reverse("common:profile"), {})
        assert response.status_code == 200

    def test_profile_view_password_change_invalid(
        self, client: Client, django_user_model
    ):
        """Invalid password change submission should return the form with errors."""
        django_user_model.objects.create_user(
            username="testuser", password="oldpassword"
        )
        client.login(username="testuser", password="oldpassword")
        # Invalid password (mismatch)
        response = client.post(
            reverse("common:profile"),
            {
                "password_submit": "1",
                "old_password": "oldpassword",
                "new_password1": "newpassword1",
                "new_password2": "newpassword2",
            },
        )
        assert response.status_code == 200
        assert "password_form" in response.context

    def test_password_change_success(self, client: Client, django_user_model):
        """Password change should work and keep user logged in."""
        django_user_model.objects.create_user(
            username="testuser", email="test@example.com", password="oldpass123"
        )
        client.login(username="testuser", password="oldpass123")

        response = client.post(
            reverse("common:profile"),
            {
                "password_submit": "1",
                "old_password": "oldpass123",
                "new_password1": "newpass123!@#",
                "new_password2": "newpass123!@#",
            },
        )

        assert response.status_code == 302
        # User should still be logged in
        response = client.get(reverse("common:profile"))
        assert response.status_code == 200

        # Old password should not work
        client.logout()
        assert not client.login(username="testuser", password="oldpass123")
        # New password should work
        assert client.login(username="testuser", password="newpass123!@#")


@pytest.mark.django_db
class TestEmailChangeConfirmation:
    """Tests for email change confirmation."""

    def test_valid_token_changes_email(self, client: Client, django_user_model):
        """Valid confirmation token should change the email."""
        user = django_user_model.objects.create_user(
            username="testuser", email="old@example.com", password="testpass123"
        )

        new_email = "new@example.com"
        user._new_email_for_token = new_email
        token = email_change_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        new_email_encoded = urlsafe_base64_encode(force_bytes(new_email))

        client.login(username="testuser", password="testpass123")
        response = client.get(
            reverse(
                "common:email_change_confirm",
                kwargs={"uidb64": uid, "token": token, "new_email": new_email_encoded},
            )
        )

        assert response.status_code == 302
        user.refresh_from_db()
        assert user.email == new_email
        assert len(mail.outbox) == 1  # Notification to old email
        assert mail.outbox[0].to == ["old@example.com"]

    def test_invalid_token_does_not_change_email(
        self, client: Client, django_user_model
    ):
        """Invalid token should not change the email."""
        user = django_user_model.objects.create_user(
            username="testuser", email="old@example.com", password="testpass123"
        )

        new_email = "new@example.com"
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        new_email_encoded = urlsafe_base64_encode(force_bytes(new_email))

        client.login(username="testuser", password="testpass123")
        response = client.get(
            reverse(
                "common:email_change_confirm",
                kwargs={
                    "uidb64": uid,
                    "token": "invalid-token",
                    "new_email": new_email_encoded,
                },
            )
        )

        assert response.status_code == 302
        user.refresh_from_db()
        assert user.email == "old@example.com"  # Email unchanged

    def test_email_change_confirm_invalid_uid(self, client: Client):
        """Invalid UID in email change confirmation should redirect to profile."""
        response = client.get(
            reverse(
                "common:email_change_confirm",
                kwargs={
                    "uidb64": "invalid",
                    "token": "token",
                    "new_email": "bmV3QGV4YW1wbGUuY29t",  # new@example.com
                },
            )
        )
        assert response.status_code == 302
        assert response.url == reverse("common:profile")

    def test_email_change_confirm_user_does_not_exist(self, client: Client):
        """If user does not exist for UID, confirmation should redirect."""
        # uidb64 for ID 99999
        response = client.get(
            reverse(
                "common:email_change_confirm",
                kwargs={
                    "uidb64": "OTk5OTk",
                    "token": "token",
                    "new_email": "bmV3QGV4YW1wbGUuY29t",
                },
            )
        )
        assert response.status_code == 302

    def test_email_taken_by_another_user_during_confirmation(
        self, client: Client, django_user_model
    ):
        """If email is taken by another user during confirmation, change should fail."""
        user1 = django_user_model.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )

        new_email = "new@example.com"
        user1._new_email_for_token = new_email
        token = email_change_token_generator.make_token(user1)
        uid = urlsafe_base64_encode(force_bytes(user1.pk))
        new_email_encoded = urlsafe_base64_encode(force_bytes(new_email))

        # Another user takes the email before confirmation
        django_user_model.objects.create_user(
            username="user2", email=new_email, password="pass123"
        )

        client.login(username="user1", password="pass123")
        response = client.get(
            reverse(
                "common:email_change_confirm",
                kwargs={"uidb64": uid, "token": token, "new_email": new_email_encoded},
            )
        )

        assert response.status_code == 302
        user1.refresh_from_db()
        assert user1.email == "user1@example.com"  # Email unchanged
