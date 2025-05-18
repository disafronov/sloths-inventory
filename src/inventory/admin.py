from django.contrib import admin
from common.admin import BaseAdmin
from .models import Item, Operation


@admin.register(Item)
class ItemAdmin(BaseAdmin):
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
        "notes",
    )
    readonly_fields = list(BaseAdmin.readonly_fields) + ["current_status", "current_location", "current_responsible"]
    autocomplete_fields = ["device"]
    main_fields = (
        "inventory_number",
        "device",
        "serial_number",
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = list(fieldsets)
        # Перемещаем секцию "Дополнительная информация" в начало
        additional_info = fieldsets.pop(1)
        fieldsets.insert(1, additional_info)
        # Добавляем секцию "Эксплуатация" после
        fieldsets.insert(2, (
            "Эксплуатация",
            {
                "fields": (
                    "current_status",
                    "current_responsible",
                    "current_location",
                )
            },
        ))
        return fieldsets

    def _format_empty_value(self, value):
        return value or "-"

    def current_status(self, obj):
        return self._format_empty_value(obj.current_status)
    current_status.short_description = "Статус"

    def current_location(self, obj):
        return self._format_empty_value(obj.current_location)
    current_location.short_description = "Местоположение"

    def current_responsible(self, obj):
        return self._format_empty_value(obj.current_responsible)
    current_responsible.short_description = "Ответственный"


@admin.register(Operation)
class OperationAdmin(BaseAdmin):
    list_display = (
        "item",
        "status",
        "responsible",
        "location",
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
        "item__serial_number",
        "status__name",
        "responsible__last_name",
        "responsible__first_name",
        "responsible__middle_name",
        "location__name",
        "notes",
    )
    list_filter = (
        "status",
        "responsible",
        "location",
        "updated_at",
        "created_at",
    )
    autocomplete_fields = ["item", "status", "location", "responsible"]
    main_fields = (
        "item",
        "status",
        "responsible",
        "location",
    )

    def get_responsible_display(self, obj):
        return obj.responsible.get_full_name()
    get_responsible_display.short_description = "Ответственный"
