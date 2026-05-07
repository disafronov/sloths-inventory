from typing import Any

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from catalogs.models import Responsible
from common.email_utils import send_transfer_email

User = get_user_model()


def _user_email(user: Any) -> str:
    return user.email if user.email else ""


def _notify_responsible(
    template_name: str, responsible: Responsible, user: Any
) -> None:
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
    pre_user_id: int | None = getattr(instance, "_pre_save_user_id", None)

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
