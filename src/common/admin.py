from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[Model]
else:
    _ModelAdminBase = admin.ModelAdmin


class BaseAdmin(_ModelAdminBase):
    readonly_fields = ("created_at", "updated_at")
    list_display = ("updated_at", "created_at")
    search_fields = ("created_at", "updated_at", "notes")
    fieldsets = (
        (None, {"fields": ()}),  # Будет переопределено в дочерних классах
        (
            _("Additional information"),
            {"fields": ("notes", "updated_at", "created_at")},
        ),
    )
    main_fields = ()  # Будет переопределено в дочерних классах

    def get_main_fields(self) -> tuple[str, ...]:
        return self.main_fields

    def get_fieldsets(
        self, request: HttpRequest, obj: Model | None = None
    ) -> list[tuple[str | None, dict[str, Any]]]:
        fieldsets = list(super().get_fieldsets(request, obj))
        fieldsets[0] = (None, {"fields": self.get_main_fields()})
        return fieldsets

    def _format_empty_value(self, value: Any) -> str:
        return value or "-"


class NamedModelAdmin(BaseAdmin):
    list_display = ("name", "updated_at", "created_at")
    search_fields = ("name", "created_at", "updated_at", "notes")
    main_fields = ("name",)
