from django.contrib import admin
from .models import Item, Operation


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_number",
        "device",
        "serial_number",
        "updated_at",
        "created_at",
    )
    list_display_links = ("inventory_number", "device", "serial_number")
    list_filter = (
        "device__category",
        "device__type",
        "device__manufacturer",
        "device__model",
        "updated_at",
        "created_at",
    )
    search_fields = (
        "inventory_number",
        "device__category__name",
        "device__type__name",
        "device__manufacturer__name",
        "device__model__name",
        "serial_number",
    )
    readonly_fields = ("updated_at", "created_at", "current_status", "current_location", "current_responsible")
    autocomplete_fields = ["device"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "inventory_number",
                    "device",
                    "serial_number",
                    "notes",
                    "updated_at",
                    "created_at",
                )
            },
        ),
        (
            "Эксплуатация",
            {
                "fields": (
                    "current_status",
                    "current_responsible",
                    "current_location",
                )
            },
        ),
    )

    def current_status(self, obj):
        return obj.current_status or "-"

    current_status.short_description = "Статус"

    def current_location(self, obj):
        return obj.current_location or "-"

    current_location.short_description = "Местоположение"

    def current_responsible(self, obj):
        return obj.current_responsible or "-"

    current_responsible.short_description = "Ответственный"


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "status",
        "location",
        "responsible",
        "updated_at",
        "created_at",
    )
    list_display_links = ("item", "status", "location", "responsible")
    search_fields = (
        "item__inventory_number",
        "item__device__category__name",
        "item__device__type__name",
        "item__device__manufacturer__name",
        "item__device__model__name",
        "status__name",
        "location__name",
        "responsible__last_name",
        "responsible__first_name",
        "responsible__middle_name",
    )
    list_filter = (
        "status",
        "location",
        "responsible",
        "updated_at",
        "created_at",
    )
    autocomplete_fields = ["item", "status", "location", "responsible"]
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "item",
                    "status",
                    "location",
                    "responsible",
                    "notes",
                    "updated_at",
                    "created_at",
                )
            },
        ),
    )

    def get_responsible_display(self, obj):
        return obj.responsible.get_full_name()

    get_responsible_display.short_description = "Ответственный"
