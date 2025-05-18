from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import NamedModel


class Category(NamedModel):
    """
    Модель категории устройства.
    Используется для классификации устройств по их назначению или типу.
    """
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class Manufacturer(NamedModel):
    """
    Модель производителя устройства.
    Содержит информацию о компаниях-производителях оборудования.
    """
    class Meta:
        verbose_name = _("Manufacturer")
        verbose_name_plural = _("Manufacturers")


class Model(NamedModel):
    """
    Модель устройства.
    Представляет конкретную модель устройства от производителя.
    """
    class Meta:
        verbose_name = _("Model")
        verbose_name_plural = _("Models")


class Type(NamedModel):
    """
    Модель типа устройства.
    Используется для дополнительной классификации устройств.
    """
    class Meta:
        verbose_name = _("Type")
        verbose_name_plural = _("Types") 