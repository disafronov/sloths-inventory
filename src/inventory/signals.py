from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from catalogs.models import Responsible
from common.email_utils import send_transfer_email
from inventory.models.item import Item
from inventory.models.operation import Operation


def _responsible_email(responsible: Responsible) -> str:
    return responsible.user.email if responsible.user_id and responsible.user else ""


def _notify(
    template_name: str,
    responsible: Responsible,
    item: Item,
    operation: Operation,
) -> None:
    send_transfer_email(
        f"emails/operation_{template_name}_subject.txt",
        f"emails/operation_{template_name}_body.txt",
        {"item": item, "operation": operation, "responsible": responsible},
        _responsible_email(responsible),
        html_template=f"emails/operation_{template_name}_body.html",
    )


@receiver(post_save, sender=Operation)
def notify_operation_saved(
    sender: type[Operation],
    instance: Operation,
    created: bool,
    **kwargs: Any,
) -> None:
    pre_responsible_id: int | None = getattr(instance, "_pre_save_responsible_id", None)
    responsible_changed = (
        pre_responsible_id is not None and pre_responsible_id != instance.responsible_id
    )

    item = Item.objects.select_related("device__manufacturer", "device__model").get(
        pk=instance.item_id
    )
    new_responsible = Responsible.objects.select_related("user").get(
        pk=instance.responsible_id
    )

    if created:
        _notify("assigned", new_responsible, item, instance)
        if responsible_changed and pre_responsible_id is not None:
            prev_responsible = Responsible.objects.select_related("user").get(
                pk=pre_responsible_id
            )
            _notify("unassigned", prev_responsible, item, instance)
    elif responsible_changed and pre_responsible_id is not None:
        _notify("assigned", new_responsible, item, instance)
        prev_responsible = Responsible.objects.select_related("user").get(
            pk=pre_responsible_id
        )
        _notify("unassigned", prev_responsible, item, instance)
    else:
        _notify("updated", new_responsible, item, instance)
