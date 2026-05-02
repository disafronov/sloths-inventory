from typing import Optional, Union

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from common.catalog_correction_window import CatalogCorrectionWindowMixin
from common.models import BaseModel, NamedModel


class Location(CatalogCorrectionWindowMixin, NamedModel):
    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
        ordering = ["name"]

    def is_catalog_reference_in_use(self) -> bool:
        """True when any ``Operation`` references this location."""

        if self._state.adding:
            return False
        from inventory.models import Operation

        return Operation.objects.filter(location_id=self.pk).exists()


class Responsible(CatalogCorrectionWindowMixin, BaseModel):
    last_name = models.CharField(max_length=150, verbose_name=_("Last name"))
    first_name = models.CharField(max_length=150, verbose_name=_("First name"))
    middle_name = models.CharField(
        max_length=150, null=True, blank=True, verbose_name=_("Middle name")
    )
    employee_id = models.CharField(
        max_length=50, blank=True, verbose_name=_("Employee ID")
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
    )

    class Meta:
        verbose_name = _("Responsible")
        verbose_name_plural = _("Responsibles")
        ordering = ["last_name", "first_name", "middle_name"]

    def is_catalog_reference_in_use(self) -> bool:
        """True when referenced by an ``Operation`` or a ``PendingTransfer``."""

        if self._state.adding:
            return False
        from django.db.models import Q

        from inventory.models import Operation, PendingTransfer

        if Operation.objects.filter(responsible_id=self.pk).exists():
            return True
        return bool(
            PendingTransfer.objects.filter(
                Q(from_responsible_id=self.pk) | Q(to_responsible_id=self.pk)
            ).exists()
        )

    def __str__(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def get_full_name(self) -> str:
        return str(self)

    @classmethod
    def linked_profile_for_user(
        cls, user: Union[AbstractBaseUser, AnonymousUser]
    ) -> Optional["Responsible"]:
        """
        Return the ``Responsible`` row linked to this Django user, if any.

        Anonymous or unlinked accounts return ``None`` so callers can show an
        empty inventory UI without raising.
        """

        if not getattr(user, "is_authenticated", False):
            return None
        return cls.objects.filter(user=user).first()

    @classmethod
    def transfer_receiver_candidates(
        cls, sender: "Responsible"
    ) -> QuerySet["Responsible"]:
        """
        Return possible transfer receivers for ``sender``, stable ordering.

        Used by the inventory transfer form so GET and POST paths stay aligned.
        """

        return (
            cls.objects.exclude(pk=sender.pk)
            .order_by("last_name", "first_name", "middle_name")
            .all()
        )

    @classmethod
    def resolve_transfer_receiver_from_form(
        cls, raw_to_responsible_id: str | None, *, sender: "Responsible"
    ) -> "Responsible":
        """
        Parse POST ``to_responsible_id`` for a transfer and validate against ``sender``.

        Raises ``ValidationError`` with user-visible messages (same strings the
        inventory UI expects) when the value is missing, invalid, or equal to the
        sender.
        """

        if not raw_to_responsible_id:
            raise ValidationError(gettext("New responsible is required."))
        try:
            to_responsible_id = int(raw_to_responsible_id)
            receiver = cls.objects.get(pk=to_responsible_id)
        except (cls.DoesNotExist, ValueError):
            raise ValidationError(gettext("New responsible is invalid."))
        if receiver.pk == sender.pk:
            raise ValidationError(gettext("New responsible must be different."))
        return receiver


class Status(CatalogCorrectionWindowMixin, NamedModel):
    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Statuses")
        ordering = ["name"]

    def is_catalog_reference_in_use(self) -> bool:
        """True when any ``Operation`` references this status."""

        if self._state.adding:
            return False
        from inventory.models import Operation

        return Operation.objects.filter(status_id=self.pk).exists()
