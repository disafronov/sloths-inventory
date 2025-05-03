from django.db import models

class Vendor(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
        ordering = ['name']

    def __str__(self):
        return self.name

class Model(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Модель"
        verbose_name_plural = "Модели"
        ordering = ['name']

    def __str__(self):
        return self.name

class Device(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, verbose_name="Поставщик")
    model = models.ForeignKey(Model, on_delete=models.CASCADE, verbose_name="Модель")
    serial_number = models.CharField(max_length=255, unique=True, verbose_name="Серийный номер")
    description = models.TextField(blank=True, verbose_name="Описание")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Устройство"
        verbose_name_plural = "Устройства"
        ordering = ['vendor', 'model', 'serial_number']

    def __str__(self):
        return f"{self.vendor} {self.model} {self.serial_number}"
