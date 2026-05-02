from django.db import models
from django.utils.translation import gettext_lazy as _

from common.catalog_correction_window import CatalogCorrectionWindowMixin
from common.models import BaseModel

from .attributes import Category, Manufacturer, Model, Type


class Device(CatalogCorrectionWindowMixin, BaseModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, verbose_name=_("Category")
    )
    type = models.ForeignKey(Type, on_delete=models.PROTECT, verbose_name=_("Type"))
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, verbose_name=_("Manufacturer")
    )
    model = models.ForeignKey(Model, on_delete=models.PROTECT, verbose_name=_("Model"))

    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        ordering = ["category", "type", "manufacturer", "model"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "type", "manufacturer", "model"],
                name="devices_device_cat_type_mfr_model_uniq",
            )
        ]

    def is_catalog_reference_in_use(self) -> bool:
        """True when any ``Item`` references this device definition."""

        if self._state.adding:
            return False
        from inventory.models import Item

        return bool(Item.objects.filter(device_id=self.pk).exists())

    def __str__(self) -> str:
        return f"{self.category} | {self.type} | {self.manufacturer} | {self.model}"
