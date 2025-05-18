from django.db import models
from common.models import NamedModel


class BaseModelMixin(models.Model):
    """
    Базовый миксин для моделей каталогов.
    Предоставляет общие поля и поведение для всех моделей каталогов.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(NamedModel):
    """
    Модель категории устройства.
    Используется для классификации устройств по их назначению или типу.
    """
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Manufacturer(NamedModel):
    """
    Модель производителя устройства.
    Содержит информацию о компаниях-производителях оборудования.
    """
    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"


class Model(NamedModel):
    """
    Модель устройства.
    Представляет конкретную модель устройства от производителя.
    """
    class Meta:
        verbose_name = "Модель"
        verbose_name_plural = "Модели"


class Type(NamedModel):
    """
    Модель типа устройства.
    Используется для дополнительной классификации устройств.
    """
    class Meta:
        verbose_name = "Тип"
        verbose_name_plural = "Типы"
