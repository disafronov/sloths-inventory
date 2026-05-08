"""Signal handlers for catalog model changes.

This module handles email notifications when a Responsible record's
linked user changes. The _pre_save_user_id attribute is set by
Responsible.save() to track the previous user assignment.
"""

import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from catalogs.models import Responsible
from common.email_utils import send_transfer_email

logger = logging.getLogger(__name__)
User = get_user_model()


def _user_email(user: Any) -> str:
    """Extract email address from user, returning empty string if not set."""
    return user.email if user.email else ""


def _notify_responsible(
    template_name: str, responsible: Responsible, user: Any
) -> None:
    """Send email notification about responsible assignment change.

    Args:
        template_name: Base name for email templates
            (e.g., 'linked', 'unlinked', 'updated')
        responsible: The Responsible instance that changed
        user: The user to notify (either newly assigned or previously assigned)
    """
    send_transfer_email(
        f"emails/responsible_{template_name}_subject.txt",
        f"emails/responsible_{template_name}_body.txt",
        {"responsible": responsible, "user": user},
        _user_email(user),
        html_template=f"emails/responsible_{template_name}_body.html",
    )


@receiver(post_save, sender=Responsible)
def notify_responsible_user_changed(
    sender: type[Responsible],
    instance: Responsible,
    created: bool,
    **kwargs: Any,
) -> None:
    """Send email notifications when a Responsible's linked user changes.

    Compares the current user_id with _pre_save_user_id (set by Responsible.save())
    to detect assignment changes and send appropriate notifications:
    - 'linked': Notify the newly assigned user
    - 'unlinked': Notify the previously assigned user
    - 'updated': Notify the current user if other fields changed but assignment didn't

    Args:
        sender: The Responsible model class
        instance: The Responsible instance that was saved
        created: Whether this is a new record
        **kwargs: Additional signal arguments
    """
    # _pre_save_user_id is set by Responsible.save() before the actual save
    # to track the previous user assignment for comparison.
    pre_user_id: int | None = getattr(instance, "_pre_save_user_id", None)

    try:
        if pre_user_id == instance.user_id:
            if instance.user_id:
                user = User.objects.get(pk=instance.user_id)
                _notify_responsible("updated", instance, user)
            return

        if instance.user_id:
            new_user = User.objects.get(pk=instance.user_id)
            _notify_responsible("linked", instance, new_user)

        if pre_user_id:
            old_user = User.objects.get(pk=pre_user_id)
            _notify_responsible("unlinked", instance, old_user)
    except Exception:
        logger.exception(
            "Failed to send responsible notification for responsible %s", instance.pk
        )
