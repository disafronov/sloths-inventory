from django.db import models
from django.contrib.auth.models import User
from devices.models import Category, Manufacturer, Model, Type


class Device(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, verbose_name="Категория"
    )
    type = models.ForeignKey(Type, on_delete=models.PROTECT, verbose_name="Тип")
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, verbose_name="Производитель"
    )
    model = models.ForeignKey(Model, on_delete=models.PROTECT, verbose_name="Модель")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Устройство"
        verbose_name_plural = "Устройства"
        ordering = ["category", "type", "manufacturer", "model"]
        unique_together = ["category", "type", "manufacturer", "model"]

    def __str__(self):
        return f"{self.category} | {self.type} | {self.manufacturer} | {self.model}"


class Location(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Расположение"
        verbose_name_plural = "Расположения"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Responsible(models.Model):
    last_name = models.CharField(max_length=150, verbose_name="Фамилия")
    first_name = models.CharField(max_length=150, verbose_name="Имя")
    middle_name = models.CharField(max_length=150, blank=True, verbose_name="Отчество")
    employee_id = models.CharField(
        max_length=50, blank=True, verbose_name="Табельный номер"
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Ответственный"
        verbose_name_plural = "Ответственные"
        ordering = ["last_name", "first_name", "middle_name"]

    def __str__(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def get_full_name(self):
        return str(self)


class Status(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"
        ordering = ["name"]

    def __str__(self):
        return self.name
