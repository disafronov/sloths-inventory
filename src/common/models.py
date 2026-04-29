from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Base class for all models with common fields.

    Provides timestamps for creation/update and a free-form notes field.
    """

    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        abstract = True


class NamedModel(BaseModel):
    """
    Base class for models that have a `name` field.

    Extends `BaseModel` with a unique `name` and default ordering by name.
    """

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
