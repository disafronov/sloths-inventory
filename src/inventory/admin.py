from django.contrib import admin
from django.utils.translation import gettext as _
from common.admin import BaseAdmin
from .models import Item, Operation


class CurrentFieldMixin:
    def get_current_field(self, obj, field_name):
        return self._format_empty_value(getattr(obj, f'current_{field_name}'))

    def current_status(self, obj):
        return self.get_current_field(obj, 'status')
    current_status.short_description = _("Status")

    def current_location(self, obj):
        return self.get_current_field(obj, 'location')
    current_location.short_description = _("Location")

    def current_responsible(self, obj):
        return self.get_current_field(obj, 'responsible')
    current_responsible.short_description = _("Responsible Person")


class DeviceFieldsMixin:
    device_search_fields = (
        "device__category__name",
        "device__type__name",
        "device__manufacturer__name",
        "device__model__name",
    )
    device_list_filter = (
        "device__category",
        "device__type",
        "device__manufacturer",
        "device__model",
    )


@admin.register(Item)
class ItemAdmin(BaseAdmin, CurrentFieldMixin, DeviceFieldsMixin):
    list_display = (
        "inventory_number",
        "device",
        "serial_number",
        "updated_at",
        "created_at",
    )
    list_display_links = ("inventory_number", "device", "serial_number")
    list_filter = (
        *DeviceFieldsMixin.device_list_filter,
        "updated_at",
        "created_at",
    )
    search_fields = (
        "inventory_number",
        *DeviceFieldsMixin.device_search_fields,
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
        # Move "Additional Information" section to the beginning
        additional_info = fieldsets.pop(1)
        fieldsets.insert(1, additional_info)
        # Add "Operation" section after
        fieldsets.insert(2, (
            _("Operation"),
            {
                "fields": (
                    "current_status",
                    "current_responsible",
                    "current_location",
                )
            },
        ))
        return fieldsets


@admin.register(Operation)
class OperationAdmin(BaseAdmin, DeviceFieldsMixin):
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
        *DeviceFieldsMixin.device_search_fields,
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
    get_responsible_display.short_description = _("Responsible Person")
