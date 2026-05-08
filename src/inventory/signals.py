import logging
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from catalogs.models import Responsible
from common.email_utils import send_transfer_email
from inventory.models.item import Item
from inventory.models.operation import Operation
from inventory.models.pending_transfer import PendingTransfer

logger = logging.getLogger(__name__)


def _responsible_email(responsible: Responsible) -> str:
    """Return the email address of the user associated with the responsible person."""
    return responsible.user.email if responsible.user_id and responsible.user else ""


def _notify(
    template_name: str,
    responsible: Responsible,
    item: Item,
    operation: Operation,
) -> None:
    """Send an email notification related to an inventory operation."""
    send_transfer_email(
        f"emails/operation_{template_name}_subject.txt",
        f"emails/operation_{template_name}_body.txt",
        {"item": item, "operation": operation, "responsible": responsible},
        _responsible_email(responsible),
        html_template=f"emails/operation_{template_name}_body.html",
    )


def _notify_transfer(
    template_name: str,
    item: Item,
    from_responsible: Responsible,
    to_responsible: Responsible,
    recipients: list[str],
) -> None:
    """Send an email notification related to a pending item transfer."""
    send_transfer_email(
        f"emails/transfer_{template_name}_subject.txt",
        f"emails/transfer_{template_name}_body.txt",
        {"item": item, "sender": from_responsible, "receiver": to_responsible},
        recipients,
        html_template=f"emails/transfer_{template_name}_body.html",
    )


@receiver(post_save, sender=Operation)
def notify_operation_saved(
    sender: type[Operation],
    instance: Operation,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Handle post-save signal for Operation to send notifications.
    Notifies responsible persons when they are assigned or unassigned from an item,
    or when operation details are updated.
    """
    pre_responsible_id: int | None = getattr(instance, "_pre_save_responsible_id", None)
    responsible_changed = (
        pre_responsible_id is not None and pre_responsible_id != instance.responsible_id
    )

    try:
        item = Item.objects.select_related("device__manufacturer", "device__model").get(
            pk=instance.item_id
        )
        new_responsible = Responsible.objects.select_related("user").get(
            pk=instance.responsible_id
        )

        if created and responsible_changed and pre_responsible_id is not None:
            _notify("assigned", new_responsible, item, instance)
            prev_responsible = Responsible.objects.select_related("user").get(
                pk=pre_responsible_id
            )
            _notify("unassigned", prev_responsible, item, instance)
        elif created and pre_responsible_id is None:
            _notify("assigned", new_responsible, item, instance)
        elif created:
            _notify("updated", new_responsible, item, instance)
        elif responsible_changed and pre_responsible_id is not None:
            _notify("assigned", new_responsible, item, instance)
            prev_responsible = Responsible.objects.select_related("user").get(
                pk=pre_responsible_id
            )
            _notify("unassigned", prev_responsible, item, instance)
        else:
            _notify("updated", new_responsible, item, instance)
    except Exception:
        logger.exception(
            "Failed to send operation notification for operation %s", instance.pk
        )


@receiver(post_save, sender=PendingTransfer)
def notify_transfer_saved(
    sender: type[PendingTransfer],
    instance: PendingTransfer,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Handle post-save signal for PendingTransfer to send notifications.
    Notifies both parties when a transfer is created, accepted, or cancelled.
    """
    pre_to_responsible_id: int | None = getattr(
        instance, "_pre_save_to_responsible_id", None
    )
    pre_accepted_at = getattr(instance, "_pre_save_accepted_at", None)
    pre_cancelled_at = getattr(instance, "_pre_save_cancelled_at", None)

    receiver_changed = (
        pre_to_responsible_id is not None
        and pre_to_responsible_id != instance.to_responsible_id
    )
    just_accepted = bool(instance.accepted_at and not pre_accepted_at)
    just_cancelled = bool(instance.cancelled_at and not pre_cancelled_at)

    if not (created or just_accepted or just_cancelled or receiver_changed):
        return

    try:
        item = Item.objects.select_related("device__manufacturer", "device__model").get(
            pk=instance.item_id
        )
        from_responsible = Responsible.objects.select_related("user").get(
            pk=instance.from_responsible_id
        )
        to_responsible = Responsible.objects.select_related("user").get(
            pk=instance.to_responsible_id
        )
        from_email = _responsible_email(from_responsible)
        to_email = _responsible_email(to_responsible)

        if created:
            _notify_transfer(
                "created", item, from_responsible, to_responsible, [to_email]
            )
        elif receiver_changed and pre_to_responsible_id is not None:
            old_receiver = Responsible.objects.select_related("user").get(
                pk=pre_to_responsible_id
            )
            _notify_transfer(
                "cancelled",
                item,
                from_responsible,
                old_receiver,
                [_responsible_email(old_receiver)],
            )
            _notify_transfer(
                "created", item, from_responsible, to_responsible, [to_email]
            )
        elif just_accepted:
            _notify_transfer(
                "accepted",
                item,
                from_responsible,
                to_responsible,
                [from_email, to_email],
            )
        else:
            _notify_transfer(
                "cancelled",
                item,
                from_responsible,
                to_responsible,
                [from_email, to_email],
            )
    except Exception:
        logger.exception(
            "Failed to send transfer notification for transfer %s", instance.pk
        )
