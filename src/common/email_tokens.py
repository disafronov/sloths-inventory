"""Token generation and validation for email change confirmation."""

import contextvars
from typing import TYPE_CHECKING

from django.contrib.auth.tokens import PasswordResetTokenGenerator

if TYPE_CHECKING:
    from django.contrib.auth.models import User

_pending_new_email: contextvars.ContextVar[str] = contextvars.ContextVar(
    "pending_new_email", default=""
)


class EmailChangeTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email change confirmation.

    Includes the target email in the hash so the token is only valid for the
    specific email change request. The target email is passed via a
    ``ContextVar`` — safe for threaded and async workers alike.
    """

    def make_token_for_email(self, user: "User", new_email: str) -> str:
        ctx = _pending_new_email.set(new_email)
        try:
            return self.make_token(user)
        finally:
            _pending_new_email.reset(ctx)

    def check_token_for_email(self, user: "User", token: str, new_email: str) -> bool:
        ctx = _pending_new_email.set(new_email)
        try:
            return self.check_token(user, token)
        finally:
            _pending_new_email.reset(ctx)

    def _make_hash_value(self, user: "User", timestamp: int) -> str:
        return f"{user.pk}{user.email}{timestamp}{_pending_new_email.get()}"


email_change_token_generator = EmailChangeTokenGenerator()
