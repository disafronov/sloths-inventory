from django.db import models
from common.models import BaseModel
from .attributes import Category, Manufacturer, Model, Type


class Device(BaseModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, verbose_name="Категория"
    )
    type = models.ForeignKey(Type, on_delete=models.PROTECT, verbose_name="Тип")
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, verbose_name="Производитель"
    )
    model = models.ForeignKey(Model, on_delete=models.PROTECT, verbose_name="Модель")

    class Meta:
        verbose_name = "Устройство"
        verbose_name_plural = "Устройства"
        ordering = ["category", "type", "manufacturer", "model"]
        unique_together = ["category", "type", "manufacturer", "model"]

    def __str__(self):
        return f"{self.category} | {self.type} | {self.manufacturer} | {self.model}" 