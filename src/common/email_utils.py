import logging
import smtplib
import threading
import time
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)

_RECOVERABLE_ERRORS = (
    smtplib.SMTPConnectError,
    smtplib.SMTPServerDisconnected,
    ConnectionError,
    TimeoutError,
)


def _send_with_retry(
    subject: str,
    message: str,
    recipients: list[str],
    html_message: str | None,
) -> None:
    max_retries: int = settings.EMAIL_RETRY_MAX_RETRIES
    base_delay: float = settings.EMAIL_RETRY_BASE_DELAY_SECONDS
    backoff_factor: float = settings.EMAIL_RETRY_BACKOFF_FACTOR

    delay = base_delay
    for attempt in range(max_retries + 1):
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=recipients,
                html_message=html_message,
            )
            return
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
            logger.exception("Email send failed (non-recoverable) to %s", recipients)
            return


def send_email_async(
    subject: str,
    message: str,
    recipient: str | list[str],
    html_message: str | None = None,
) -> None:
    recipients = [recipient] if isinstance(recipient, str) else list(recipient)
    recipients = [r for r in recipients if r]
    if not recipients:
        return

    if settings.EMAIL_SEND_ASYNC:
        threading.Thread(
            target=_send_with_retry,
            args=(subject, message, recipients, html_message),
            daemon=True,
        ).start()
    else:
        _send_with_retry(subject, message, recipients, html_message)


def send_transfer_email(
    subject_template: str,
    body_template: str,
    context: dict,
    recipient: str | list[str],
    html_template: str | None = None,
) -> None:
    subject = render_to_string(subject_template, context).strip()
    message = render_to_string(body_template, context)
    html_message = render_to_string(html_template, context) if html_template else None
    send_email_async(subject, message, recipient, html_message)


def send_email_change_confirmation(user: Any, new_email: str) -> None:
    from common.email_tokens import email_change_token_generator

    token = email_change_token_generator.make_token_for_email(user, new_email)
    path = reverse(
        "common:email_change_confirm",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": token,
            "new_email": urlsafe_base64_encode(force_bytes(new_email)),
        },
    )
    confirmation_url = f"{settings.SITE_URL}{path}"
    context = {
        "user": user,
        "new_email": new_email,
        "confirmation_url": confirmation_url,
    }
    subject = render_to_string(
        "emails/email_change_subject.txt", {"user": user}
    ).strip()
    text_body = render_to_string("emails/email_change_body.txt", context)
    html_body = render_to_string("emails/email_change_body.html", context)
    send_email_async(subject, text_body, new_email, html_body)


def send_email_changed_notification(user: Any, old_email: str, new_email: str) -> None:
    context = {"user": user, "old_email": old_email, "new_email": new_email}
    subject = render_to_string(
        "emails/email_changed_notification_subject.txt", {"user": user}
    ).strip()
    text_body = render_to_string("emails/email_changed_notification_body.txt", context)
    html_body = render_to_string("emails/email_changed_notification_body.html", context)
    send_email_async(subject, text_body, old_email, html_body)
