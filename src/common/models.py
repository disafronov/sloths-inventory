from django.db import models


class BaseModel(models.Model):
    """
    Базовый класс для всех моделей с общими полями.
    Предоставляет поля для отслеживания времени создания/обновления и заметок.
    """
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    class Meta:
        abstract = True


class NamedModel(BaseModel):
    """
    Базовый класс для моделей с полем name.
    Предоставляет общие поля и поведение для именованных моделей.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name 