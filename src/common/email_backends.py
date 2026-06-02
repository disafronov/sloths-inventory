"""Custom Django email backend providing async delivery via django-q2."""

import logging
import smtplib
import time
from typing import Sequence

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
from django_q.tasks import async_task

logger = logging.getLogger(__name__)

# Errors that warrant retry (transient network/connection issues).
_RECOVERABLE_ERRORS = (
    smtplib.SMTPConnectError,
    smtplib.SMTPServerDisconnected,
    ConnectionError,
    TimeoutError,
)


def _deliver_messages(messages: list[EmailMessage]) -> int:
    """django-q2 task: deliver messages via SMTP with exponential backoff retry."""
    max_retries: int = settings.EMAIL_RETRY_MAX_RETRIES
    base_delay: float = settings.EMAIL_RETRY_BASE_DELAY_SECONDS
    backoff_factor: float = settings.EMAIL_RETRY_BACKOFF_FACTOR

    delay = base_delay
    for attempt in range(max_retries + 1):
        try:
            with SmtpBackend() as backend:
                return backend.send_messages(messages)
        except _RECOVERABLE_ERRORS as exc:
            if attempt < max_retries:
                logger.warning(
                    "Email attempt %d/%d failed (%s), retrying in %.0fs",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    "Email failed after %d attempts: %s",
                    max_retries + 1,
                    exc,
                )
        except Exception:
            logger.exception("Email send failed (non-recoverable)")
            return 0
    return 0


class AsyncEmailBackend(BaseEmailBackend):
    """Email backend that enqueues messages to django-q2 for async delivery.

    Respects EMAIL_SEND_ASYNC: when False, delivers synchronously (useful
    for local dev without a running qcluster).
    """

    def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """Enqueue messages for async delivery, or deliver synchronously."""
        messages = list(email_messages)
        if not messages:
            return 0
        if settings.EMAIL_SEND_ASYNC:
            async_task("common.email_backends._deliver_messages", messages)
            return len(messages)
        return _deliver_messages(messages)
