"""Email utilities: template rendering helpers for common email types."""

import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)


def send_transfer_email(
    subject_template: str,
    body_template: str,
    context: dict,
    recipient: str | list[str],
    html_template: str | None = None,
) -> None:
    """Render templates and send email for inventory transfer notifications.

    Filters out empty recipient strings before sending.
    """
    recipients = [recipient] if isinstance(recipient, str) else list(recipient)
    recipients = [r for r in recipients if r]
    if not recipients:
        return
    subject = render_to_string(subject_template, context).strip()
    message = render_to_string(body_template, context)
    html_message = render_to_string(html_template, context) if html_template else None
    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=recipients,
        html_message=html_message,
    )


def send_email_change_confirmation(user: Any, new_email: str) -> None:
    """Send email change confirmation link to the new email address.

    Generates a signed token and sends a confirmation URL to the new email.
    The user must click the link to complete the email change.
    """
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
    send_mail(
        subject=subject,
        message=text_body,
        from_email=None,
        recipient_list=[new_email],
        html_message=html_body,
    )


def send_email_changed_notification(user: Any, old_email: str, new_email: str) -> None:
    """Notify the old email address that the user's email has been changed.

    Sent after successful email change confirmation as a security measure.
    """
    context = {"user": user, "old_email": old_email, "new_email": new_email}
    subject = render_to_string(
        "emails/email_changed_notification_subject.txt", {"user": user}
    ).strip()
    text_body = render_to_string("emails/email_changed_notification_body.txt", context)
    html_body = render_to_string("emails/email_changed_notification_body.html", context)
    send_mail(
        subject=subject,
        message=text_body,
        from_email=None,
        recipient_list=[old_email],
        html_message=html_body,
    )
