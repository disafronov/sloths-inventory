from django.conf import settings
from django.db import models
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
        return PendingTransfer.objects.filter(
            Q(from_responsible_id=self.pk) | Q(to_responsible_id=self.pk)
        ).exists()

    def __str__(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def get_full_name(self) -> str:
        return str(self)


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
