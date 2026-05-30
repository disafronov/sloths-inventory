from typing import Any

from django.contrib import admin
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from common.admin import (
    BaseAdmin,
    CatalogReferenceAdminMixin,
    CatalogReferenceRow,
    NamedModelAdmin,
    auth_has_change_permission,
)

from .models import Location, Responsible, Status


@admin.register(Location)
class LocationAdmin(NamedModelAdmin):
    list_display = [
        "location_display_name",
        "responsible_display",
        "updated_at",
        "created_at",
    ]
    list_display_links = ["location_display_name"]
    list_filter = ["responsible", "updated_at", "created_at"]
    search_fields = [
        "name",
        "responsible__last_name",
        "responsible__first_name",
        "responsible__middle_name",
        "created_at",
        "updated_at",
        "notes",
    ]
    autocomplete_fields = ["responsible"]
    main_fields = ("name", "responsible")

    @admin.display(description=_("Location"), ordering="name")
    def location_display_name(self, obj: Location) -> str:
        return obj.display_name

    @admin.display(description=_("Responsible"), ordering="responsible")
    def responsible_display(self, obj: Location) -> str:
        if obj.responsible_id is None:
            return _("Global: %(key)s") % {"key": obj.name}
        return str(obj.responsible)

    def get_readonly_fields(
        self, request: HttpRequest, obj: Model | None = None
    ) -> list[str]:
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None and not self.has_change_permission(request, obj):
            fields.append("location_display_name")
            fields.append("responsible_display")
        return fields

    def _catalog_correction_window_lock_user_message(
        self, request: HttpRequest, obj: CatalogReferenceRow
    ) -> str | None:
        if isinstance(obj, Location) and obj.is_system_location:
            return None
        return super()._catalog_correction_window_lock_user_message(request, obj)

    def system_location_lock_message(self, obj: Model | None) -> str | None:
        if isinstance(obj, Location) and obj.is_system_location:
            return str(
                _(
                    "This system location is required for transfers and cannot be "
                    "changed or deleted."
                )
            )
        return None

    def has_change_permission(
        self, request: HttpRequest, obj: Model | None = None
    ) -> bool:
        allowed = super().has_change_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self.system_location_lock_message(obj) is None

    def has_delete_permission(
        self, request: HttpRequest, obj: Model | None = None
    ) -> bool:
        allowed = super().has_delete_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self.system_location_lock_message(obj) is None

    def get_fieldsets(self, request: HttpRequest, obj: Model | None = None) -> Any:
        fieldsets = list(super().get_fieldsets(request, obj))
        if obj is not None and not self.has_change_permission(request, obj):
            main_fields = list(fieldsets[0][1]["fields"])
            display_map = {
                "name": "location_display_name",
                "responsible": "responsible_display",
            }
            main_fields = [display_map.get(f, f) for f in main_fields]
            fieldsets[0] = (fieldsets[0][0], {"fields": main_fields})
        message = self.system_location_lock_message(obj)
        if message is None:
            return fieldsets
        if not auth_has_change_permission(self, request, obj):
            return fieldsets
        desc = format_html('<p class="catalog-correction-window-lock">{}</p>', message)
        lock_panel = (
            _("Editing restrictions"),
            {"fields": (), "description": desc},
        )
        return [*fieldsets, lock_panel]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Location]:
        qs = super().get_queryset(request)
        return qs.select_related("responsible")


@admin.register(Responsible)
class ResponsibleAdmin(CatalogReferenceAdminMixin, BaseAdmin):
    list_display = [
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user",
        "updated_at",
        "created_at",
    ]
    list_display_links = [
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user",
    ]
    list_filter = ["last_name", "first_name", "user", "updated_at", "created_at"]
    search_fields = [
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user__username",
        "user__email",
    ]
    autocomplete_fields = ["user"]
    main_fields = (
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Responsible]:
        """
        Avoid N+1 queries in admin list pages by preloading the related user.
        """

        qs = super().get_queryset(request)
        return qs.select_related("user")


@admin.register(Status)
class StatusAdmin(NamedModelAdmin):
    pass
