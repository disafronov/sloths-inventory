from django.db import models
from common.models import NamedModel


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