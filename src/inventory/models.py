from django.db import models
from catalogs.models import Device, Location, Responsible, Status


class Operation(models.Model):
    item = models.ForeignKey("Item", on_delete=models.CASCADE, verbose_name="Экземпляр")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name="Статус")
    responsible = models.ForeignKey(
        Responsible, on_delete=models.PROTECT, verbose_name="Ответственный"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, verbose_name="Расположение"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Эксплуатация"
        verbose_name_plural = "Эксплуатация"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.item} - {self.status}"

    def get_status_display(self):
        return self.status.name


class Item(models.Model):
    inventory_number = models.CharField(
        max_length=50, unique=True, verbose_name="Инвентарный номер"
    )
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, verbose_name="Устройство"
    )
    serial_number = models.CharField(
        max_length=50, blank=True, verbose_name="Серийный номер"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Экземпляр"
        verbose_name_plural = "Экземпляры"
        ordering = ["inventory_number"]

    def __str__(self):
        return f"{self.inventory_number} - {self.device}"

    @property
    def current_operation(self):
        return self.operation_set.order_by("-created_at").first()

    @property
    def current_status(self):
        operation = self.current_operation
        if operation:
            return operation.get_status_display()
        return None

    @property
    def current_location(self):
        operation = self.current_operation
        if operation:
            return operation.location
        return None

    @property
    def current_responsible(self):
        operation = self.current_operation
        if operation and operation.responsible:
            return operation.responsible
        return None
