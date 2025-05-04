from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Device, Location, Responsible, Status
from devices.models import Category, Manufacturer, Model, Type


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("category", "type", "manufacturer", "model", "updated_at", "created_at")
    list_display_links = ("category", "type", "manufacturer", "model")
    list_filter = ("category", "type", "manufacturer", "model", "updated_at", "created_at")
    search_fields = ("category__name", "type__name", "manufacturer__name", "model__name")
    readonly_fields = ("updated_at", "created_at")
    fieldsets = (
        (None, {"fields": ("category", "type", "manufacturer", "model", "updated_at", "created_at")}),
    )
    autocomplete_fields = ["category", "type", "manufacturer", "model"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    list_display_links = ("name",)
    search_fields = ("name",)
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ["name"]
    fieldsets = (
        (None, {"fields": ("name", "updated_at", "created_at")}),
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
    search_fields = ("name",)
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ["name"]
    fieldsets = (
        (None, {"fields": ("name", "updated_at", "created_at")}),
    )


class ResponsibleInline(admin.StackedInline):
    model = Responsible
    can_delete = False
    verbose_name_plural = "Ответственный"
    fk_name = "user"


class CustomUserAdmin(UserAdmin):
    inlines = (ResponsibleInline,)

    def get_full_name(self, obj):
        if hasattr(obj, "responsible"):
            return obj.responsible.get_full_name()
        return super().get_full_name(obj)

    get_full_name.short_description = "Полное имя"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
