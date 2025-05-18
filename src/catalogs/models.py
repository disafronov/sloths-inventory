from django.db import models
from django.contrib.auth.models import User
from common.models import BaseModel, NamedModel


class Location(NamedModel):
    class Meta:
        verbose_name = "Расположение"
        verbose_name_plural = "Расположения"


class Responsible(BaseModel):
    last_name = models.CharField(max_length=150, verbose_name="Фамилия")
    first_name = models.CharField(max_length=150, verbose_name="Имя")
    middle_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Отчество")
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


class Status(NamedModel):
    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"
