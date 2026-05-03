"""Token generation and validation for email change confirmation."""

from typing import TYPE_CHECKING

from django.contrib.auth.tokens import PasswordResetTokenGenerator

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class EmailChangeTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email change confirmation.

    Similar to password reset tokens but includes the new email in the hash
    to ensure the token is only valid for the specific email change request.
    """

    def _make_hash_value(self, user: "User", timestamp: int) -> str:
        """
        Hash the user's primary key, email, timestamp, and new email.

        The new email is stored in a temporary attribute on the user object
        when generating the token.
        """
        email_field = getattr(user, "_new_email_for_token", "")
        return f"{user.pk}{user.email}{timestamp}{email_field}"


email_change_token_generator = EmailChangeTokenGenerator()
