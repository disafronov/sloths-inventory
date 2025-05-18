from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import BaseModel
from .attributes import Category, Manufacturer, Model, Type


class Device(BaseModel):
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
        unique_together = ["category", "type", "manufacturer", "model"]

    def __str__(self):
        return f"{self.category} | {self.type} | {self.manufacturer} | {self.model}"
 