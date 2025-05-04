from django.db import models
from django.contrib.auth.models import User
from catalogs.models import Device

class Responsible(models.Model):
    last_name = models.CharField(max_length=150, verbose_name="Фамилия")
    first_name = models.CharField(max_length=150, verbose_name="Имя")
    middle_name = models.CharField(max_length=150, blank=True, verbose_name="Отчество")
    employee_id = models.CharField(max_length=50, blank=True, verbose_name="Табельный номер")
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Ответственный"
        verbose_name_plural = "Ответственные"
        ordering = ['last_name', 'first_name', 'middle_name']

    def __str__(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    def get_full_name(self):
        return str(self)

class Status(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"
        ordering = ['name']

    def __str__(self):
        return self.name

class Operation(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name="Экземпляр")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name="Статус")
    responsible = models.ForeignKey(Responsible, on_delete=models.PROTECT, verbose_name="Ответственный")
    location = models.CharField(max_length=255, verbose_name="Местоположение")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Эксплуатация"
        verbose_name_plural = "Эксплуатация"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.item} - {self.status}"

    def get_status_display(self):
        return self.status.name

class Item(models.Model):
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name="Инвентарный номер")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, verbose_name="Устройство")
    serial_number = models.CharField(max_length=50, blank=True, verbose_name="Серийный номер")
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
