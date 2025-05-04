from django.contrib import admin
from .models import Device, Location, Responsible, Status


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "category",
        "type",
        "manufacturer",
        "model",
        "description",
        "updated_at",
        "created_at",
    )
    list_display_links = ("category", "type", "manufacturer", "model", "description")
    search_fields = (
        "description",
        "category__name",
        "type__name",
        "manufacturer__name",
        "model__name",
    )
    list_filter = (
        "category",
        "type",
        "manufacturer",
        "model",
        "updated_at",
        "created_at",
    )
    autocomplete_fields = ["category", "type", "manufacturer", "model"]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "type",
                    "manufacturer",
                    "model",
                    "description",
                    "updated_at",
                    "created_at",
                )
            },
        ),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    list_display_links = ("name",)
    search_fields = ("name", "description")
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ["name"]
    fieldsets = (
        (None, {"fields": ("name", "description", "updated_at", "created_at")}),
    )


@admin.register(Responsible)
class ResponsibleAdmin(admin.ModelAdmin):
    list_display = ("get_full_name", "employee_id", "user", "updated_at", "created_at")
    list_display_links = ("get_full_name",)
    search_fields = (
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user__username",
    )
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ["user"]
    ordering = ["last_name", "first_name", "middle_name"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "last_name",
                    "first_name",
                    "middle_name",
                    "employee_id",
                    "user",
                    "updated_at",
                    "created_at",
                )
            },
        ),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = "Полное имя"
    get_full_name.admin_order_field = "last_name"


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    list_display_links = ("name",)
    search_fields = ("name", "description")
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ["name"]
    fieldsets = (
        (None, {"fields": ("name", "description", "updated_at", "created_at")}),
    )
