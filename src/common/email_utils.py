import logging
import smtplib
import threading
import time

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

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
