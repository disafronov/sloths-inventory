from typing import Any

from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["updated_at", "created_at"]
    search_fields = ["created_at", "updated_at", "notes"]
    fieldsets = (
        (None, {"fields": ()}),  # Будет переопределено в дочерних классах
        (
            _("Additional information"),
            {"fields": ("notes", "updated_at", "created_at")},
        ),
    )
    main_fields: list[str] = []  # Will be overridden in subclasses

    def get_main_fields(self) -> tuple[str, ...]:
        return tuple(self.main_fields)

    def get_fieldsets(self, request: HttpRequest, obj: Model | None = None) -> Any:
        fieldsets = list(super().get_fieldsets(request, obj))
        if not fieldsets:
            fieldsets = [(None, {"fields": self.get_main_fields()})]
        else:
            fieldsets[0] = (None, {"fields": self.get_main_fields()})
        return fieldsets

    def _format_empty_value(self, value: Any) -> str:
        return value or "-"


class NamedModelAdmin(BaseAdmin):
    list_display = ["name", "updated_at", "created_at"]
    search_fields = ["name", "created_at", "updated_at", "notes"]
    main_fields = ["name"]
