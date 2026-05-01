from datetime import timedelta
from typing import Any, Protocol, cast

from django.conf import settings
from django.contrib import admin
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.admin import BaseAdmin

from .models import Item, Operation, PendingTransfer


class _EmptyValueFormatter(Protocol):
    def _format_empty_value(self, value: Any) -> str: ...


class CurrentFieldMixin:
    def get_current_field(self, obj: Item, field_name: str) -> str:
        formatter = cast(_EmptyValueFormatter, self)
        return formatter._format_empty_value(getattr(obj, f"current_{field_name}"))

    @admin.display(description=_("Status"))
    def current_status(self, obj: Item) -> str:
        return self.get_current_field(obj, "status")

    @admin.display(description=_("Location"))
    def current_location(self, obj: Item) -> str:
        return self.get_current_field(obj, "location")

    @admin.display(description=_("Responsible Person"))
    def current_responsible(self, obj: Item) -> str:
        return self.get_current_field(obj, "responsible")


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
    list_display = [
        "inventory_number",
        "device",
        "serial_number",
        "updated_at",
        "created_at",
    ]
    list_display_links = ["inventory_number", "device", "serial_number"]
    list_filter = [
        *list(DeviceFieldsMixin.device_list_filter),
        "updated_at",
        "created_at",
    ]
    search_fields = [
        "inventory_number",
        *list(DeviceFieldsMixin.device_search_fields),
        "serial_number",
        "notes",
    ]
    readonly_fields = list(BaseAdmin.readonly_fields) + [
        "current_responsible",
        "current_location",
        "current_status",
    ]
    autocomplete_fields = ["device"]
    main_fields = (
        "inventory_number",
        "device",
        "serial_number",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Item]:
        """
        Avoid N+1 queries in admin list pages by preloading device relations.

        `Item.__str__` renders `Device`, which touches multiple FK relations.
        """

        qs = super().get_queryset(request)
        return qs.select_related(
            "device",
            "device__category",
            "device__type",
            "device__manufacturer",
            "device__model",
        )

    def get_fieldsets(self, request: HttpRequest, obj: Model | None = None) -> Any:
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = list(fieldsets)
        # Move "Additional Information" section to the beginning
        additional_info = fieldsets.pop(1)
        fieldsets.insert(1, additional_info)
        # Add "Operation" section after
        fieldsets.insert(
            2,
            (
                _("Operation"),
                {
                    "fields": (
                        "current_responsible",
                        "current_location",
                        "current_status",
                    )
                },
            ),
        )
        return fieldsets


@admin.register(Operation)
class OperationAdmin(BaseAdmin, DeviceFieldsMixin):
    list_display = [
        "item",
        "responsible",
        "location",
        "status",
        "updated_at",
        "created_at",
    ]
    list_display_links = ["item", "responsible", "location", "status"]
    search_fields = [
        "item__inventory_number",
        *list(DeviceFieldsMixin.device_search_fields),
        "item__serial_number",
        "responsible__last_name",
        "responsible__first_name",
        "responsible__middle_name",
        "status__name",
        "location__name",
        "notes",
    ]
    list_filter = [
        "responsible",
        "location",
        "status",
        "updated_at",
        "created_at",
    ]
    autocomplete_fields = ["item", "responsible", "status", "location"]
    main_fields = (
        "item",
        "responsible",
        "location",
        "status",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Operation]:
        """
        Avoid N+1 queries in admin list pages by preloading common relations.
        """

        qs = super().get_queryset(request)
        return qs.select_related(
            "item",
            "item__device",
            "item__device__category",
            "item__device__type",
            "item__device__manufacturer",
            "item__device__model",
            "status",
            "responsible",
            "location",
        )

    def _get_latest_operation_id_for_item(
        self, request: HttpRequest, *, item_id: int
    ) -> int | None:
        """
        Return the latest operation id for the given item, cached per request.

        Admin permission checks may call this multiple times while rendering a
        changelist. Caching keeps the behavior correct while avoiding repetitive
        queries.
        """

        cache_attr = "_inventory_latest_operation_id_by_item"
        cache = cast(dict[int, int | None] | None, getattr(request, cache_attr, None))
        if cache is None:
            cache = {}
            setattr(request, cache_attr, cache)

        if item_id in cache:
            return cache[item_id]

        latest_id: int | None = (
            Operation.objects.filter(item_id=item_id)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
            .first()
        )
        cache[item_id] = latest_id
        return latest_id

    def _is_latest_for_item(self, request: HttpRequest, obj: Operation) -> bool:
        latest_id = self._get_latest_operation_id_for_item(request, item_id=obj.item_id)
        return latest_id == obj.pk

    def has_change_permission(
        self, request: HttpRequest, obj: Operation | None = None
    ) -> bool:
        allowed = super().has_change_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self._is_latest_for_item(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: Operation | None = None
    ) -> bool:
        allowed = super().has_delete_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self._is_latest_for_item(request, obj)

    @admin.display(description=_("Responsible Person"))
    def get_responsible_display(self, obj: Operation) -> str:
        return obj.responsible.get_full_name()


@admin.register(PendingTransfer)
class PendingTransferAdmin(BaseAdmin):
    readonly_fields = list(BaseAdmin.readonly_fields) + [
        "accepted_at",
        "cancelled_at",
    ]
    list_display = [
        "item",
        "from_responsible",
        "to_responsible",
        "expires_at",
        "accepted_at",
        "cancelled_at",
        "updated_at",
        "created_at",
    ]
    list_display_links = ["item", "from_responsible", "to_responsible"]
    search_fields = [
        "item__inventory_number",
        "from_responsible__last_name",
        "from_responsible__first_name",
        "from_responsible__middle_name",
        "to_responsible__last_name",
        "to_responsible__first_name",
        "to_responsible__middle_name",
        "notes",
    ]
    list_filter = [
        "from_responsible",
        "to_responsible",
        "accepted_at",
        "cancelled_at",
        "updated_at",
        "created_at",
    ]
    autocomplete_fields = ["item", "from_responsible", "to_responsible"]
    main_fields = (
        "item",
        "from_responsible",
        "to_responsible",
        "expires_at",
    )

    def get_changeform_initial_data(
        self, request: HttpRequest
    ) -> dict[str, str | list[str]]:
        initial = super().get_changeform_initial_data(request)
        hours = max(
            0,
            int(getattr(settings, "INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS", 168)),
        )
        if hours > 0 and "expires_at" not in initial:
            # Django admin's default type for initial data is string-based, but
            # datetime values are accepted by form fields. We keep the public type
            # signature compatible with stubs and cast locally.
            initial_any = cast(dict[str, Any], initial)
            initial_any["expires_at"] = timezone.now() + timedelta(hours=hours)

        if "from_responsible" not in initial and "item" in initial:
            raw_item: str | list[str] = initial["item"]
            if isinstance(raw_item, list):
                raw_item = raw_item[0] if raw_item else ""
            try:
                item_id = int(raw_item)
            except (TypeError, ValueError):
                item_id = 0

            if item_id:
                responsible_id = (
                    Operation.objects.filter(item_id=item_id)
                    .order_by("-created_at", "-id")
                    .values_list("responsible_id", flat=True)
                    .first()
                )
                if responsible_id is not None:
                    initial_any = cast(dict[str, Any], initial)
                    initial_any["from_responsible"] = responsible_id
        return initial
