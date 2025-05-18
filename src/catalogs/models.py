from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from common.models import BaseModel, NamedModel


class Location(NamedModel):
    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")


class Responsible(BaseModel):
    last_name = models.CharField(max_length=150, verbose_name=_("Last name"))
    first_name = models.CharField(max_length=150, verbose_name=_("First name"))
    middle_name = models.CharField(max_length=150, null=True, blank=True, verbose_name=_("Middle name"))
    employee_id = models.CharField(
        max_length=50, blank=True, verbose_name=_("Employee ID")
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
    )

    class Meta:
        verbose_name = _("Responsible")
        verbose_name_plural = _("Responsibles")
        ordering = ["last_name", "first_name", "middle_name"]

    def __str__(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def get_full_name(self):
        return str(self)


class Status(NamedModel):
    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Statuses")
