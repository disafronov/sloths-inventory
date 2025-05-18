from django.db import models
from catalogs.models import Device, Location, Responsible, Status
from common.models import BaseModel


class Item(BaseModel):
    inventory_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Инвентарный номер"
    )
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, verbose_name="Устройство"
    )
    serial_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Серийный номер"
    )

    class Meta:
        verbose_name = "Экземпляр"
        verbose_name_plural = "Экземпляры"
        ordering = ["inventory_number"]

    def __str__(self):
        return self.get_display_name()

    def get_display_name(self):
        return f"{self.inventory_number} - {self.device}"

    @property
    def current_operation(self):
        return self.operation_set.order_by("-created_at").first()

    class CurrentOperationValue:
        def __init__(self, attr_name, display_attr=None):
            self.attr_name = attr_name
            self.display_attr = display_attr or attr_name

        def __get__(self, instance, owner):
            if instance is None:
                return self
            operation = instance.current_operation
            if not operation:
                return None
            
            value = getattr(operation, self.attr_name, None)
            if value and hasattr(value, 'name'):
                return value.name
            return value

    current_status = CurrentOperationValue('status')
    current_location = CurrentOperationValue('location')
    current_responsible = CurrentOperationValue('responsible')


class Operation(BaseModel):
    item = models.ForeignKey("Item", on_delete=models.CASCADE, verbose_name="Экземпляр")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name="Статус")
    responsible = models.ForeignKey(
        Responsible, on_delete=models.PROTECT, verbose_name="Ответственный"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, verbose_name="Расположение"
    )

    class Meta:
        verbose_name = "Эксплуатация"
        verbose_name_plural = "Эксплуатация"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.item} - {self.status} ({self.location})"
