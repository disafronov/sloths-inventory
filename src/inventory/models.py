from django.db import models
from django.contrib.auth.models import User
from catalogs.models import Device

class Operation(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name="Экземпляр")
    status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Доступен'),
            ('in_use', 'В использовании'),
            ('maintenance', 'На обслуживании'),
            ('retired', 'Списан'),
        ],
        default='available',
        verbose_name="Статус"
    )
    responsible = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Ответственный")
    location = models.CharField(max_length=255, blank=True, verbose_name="Местоположение")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Эксплуатация"
        verbose_name_plural = "Эксплуатация"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item} - {self.get_status_display()}"

class Item(models.Model):
    inventory_number = models.CharField(max_length=255, unique=True, verbose_name="Инвентарный номер")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, verbose_name="Устройство")
    serial_number = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name="Серийный номер")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Экземпляр"
        verbose_name_plural = "Экземпляры"
        ordering = ['inventory_number']

    def __str__(self):
        return f"{self.inventory_number} - {self.device}"

    @property
    def current_operation(self):
        return self.operation_set.order_by('-created_at').first()

    @property
    def status(self):
        operation = self.current_operation
        return operation.status if operation else 'available'

    @property
    def location(self):
        operation = self.current_operation
        return operation.location if operation else ''

    @property
    def responsible(self):
        operation = self.current_operation
        return operation.responsible if operation else None
