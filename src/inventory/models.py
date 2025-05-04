from django.db import models
from catalogs.models import Device

class Item(models.Model):
    inventory_number = models.CharField(max_length=255, unique=True, verbose_name="Инвентарный номер")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, verbose_name="Устройство")
    serial_number = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name="Серийный номер")
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
    location = models.CharField(max_length=255, blank=True, verbose_name="Местоположение")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Экземпляр"
        verbose_name_plural = "Экземпляры"
        ordering = ['inventory_number']

    def __str__(self):
        return f"{self.inventory_number} - {self.device}"
