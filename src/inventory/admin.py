from typing import Any, Protocol, cast

from django import forms
from django.contrib import admin
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
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
    """
    Item master data edits use ``INVENTORY_OPERATION_EDIT_WINDOW_MINUTES`` from the
    row's ``updated_at`` (same setting as operation corrections, different anchor).

    The admin mirrors ``Item.clean()`` for change/delete permissions for non-super
    users and appends a restriction panel when the window has expired.

    Items with no operations yet (no responsible in the journal) stay editable
    regardless of ``updated_at``.

    Superusers keep full change/delete and get a ModelForm that sets
    ``Item._bypass_item_master_edit_window`` so ``clean()`` allows repairs after
    the window.
    """

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

    def _is_item_master_editable(self, obj: Item) -> bool:
        """
        Return True when ``Item.clean()`` still allows an update save.

        Without this check, Django admin would show edit/delete until ``save()``
        raised ``ValidationError`` after the window closed.
        """

        if not obj.has_assigned_responsible():
            return True
        return Operation.is_within_operation_edit_window(obj.updated_at)

    def _item_edit_lock_user_message(
        self, request: HttpRequest, obj: Item
    ) -> str | None:
        """Return restriction HTML source text, or None when edits are allowed."""

        user = getattr(request, "user", None)
        if getattr(user, "is_superuser", False):
            return None
        if self._is_item_master_editable(obj):
            return None
        return Item.master_record_edit_window_expired_user_message()

    def has_change_permission(
        self, request: HttpRequest, obj: Item | None = None
    ) -> bool:
        allowed = super().has_change_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        user = getattr(request, "user", None)
        if getattr(user, "is_superuser", False):
            return True
        return self._is_item_master_editable(obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: Item | None = None
    ) -> bool:
        allowed = super().has_delete_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        user = getattr(request, "user", None)
        if getattr(user, "is_superuser", False):
            return True
        return self._is_item_master_editable(obj)

    def get_form(
        self,
        request: HttpRequest,
        obj: Model | None = None,
        change: bool = False,
        **kwargs: Any,
    ) -> type[forms.ModelForm]:
        """
        For superusers, mark the instance so ``Item.clean()`` skips the edit window.

        The flag must be present before ``form.is_valid()`` runs (which calls
        ``full_clean()`` on the model).
        """

        form_class = super().get_form(request, obj, change=change, **kwargs)
        user = getattr(request, "user", None)

        class ItemAdminForm(form_class):  # type: ignore[misc, valid-type]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                if getattr(user, "is_superuser", False) and self.instance.pk:
                    setattr(
                        self.instance,
                        "_bypass_item_master_edit_window",
                        True,
                    )

        return ItemAdminForm

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
        if obj is None:
            return fieldsets
        item = cast(Item, obj)
        message = self._item_edit_lock_user_message(request, item)
        if message is None:
            return fieldsets
        desc = format_html('<p class="item-master-edit-lock">{}</p>', message)
        lock_panel = (
            _("Editing restrictions"),
            {"fields": (), "description": desc},
        )
        return [*fieldsets, lock_panel]


@admin.register(Operation)
class OperationAdmin(BaseAdmin, DeviceFieldsMixin):
    """
    Operations are append-only: only the latest row per item may be corrected,
    and only inside ``INVENTORY_OPERATION_EDIT_WINDOW_MINUTES``.

    The admin mirrors ``Operation.clean()`` for permissions. When a row cannot be
    corrected, a trailing fieldset with only a ``description`` (no form rows)
    states why; it is omitted entirely while edits are still allowed.
    """

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

    def get_fieldsets(self, request: HttpRequest, obj: Model | None = None) -> Any:
        """
        On change/view, optionally append a restriction summary (fieldset description).

        The panel is shown only when ``_operation_edit_lock_user_message`` returns a
        reason the row cannot be edited. If corrections are still allowed, there is
        nothing to warn about, so no extra fieldset is added.

        Using ``fields: ()`` avoids the default two-column label/value row. The add
        form is unchanged: there is nothing to describe until the row exists.
        """

        fieldsets = list(super().get_fieldsets(request, obj))
        if obj is None:
            return fieldsets
        op = cast(Operation, obj)
        message = self._operation_edit_lock_user_message(
            obj=op, latest_operation_pk=None
        )
        if message is None:
            return fieldsets
        desc = format_html('<p class="operation-edit-lock">{}</p>', message)
        lock_panel = (
            _("Editing restrictions"),
            {"fields": (), "description": desc},
        )
        return [*fieldsets, lock_panel]

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

    def _is_editable_latest_operation(
        self, request: HttpRequest, obj: Operation
    ) -> bool:
        """
        True only when this row is the latest operation for its item and the
        correction window from ``Operation.clean()`` has not expired.

        Without the window check, the admin would still show change/delete controls
        until ``save()`` raised ``ValidationError`` — which matches reports of the
        "lock after window" rule not applying in the UI.
        """

        if not self._is_latest_for_item(request, obj):
            return False
        return Operation.is_within_operation_edit_window(obj.created_at)

    def _operation_edit_lock_user_message(
        self,
        *,
        obj: Operation,
        latest_operation_pk: int | None,
    ) -> str | None:
        """
        Return a short user-visible reason when this operation cannot be edited,
        or None when edits are allowed.

        Text stays aligned with ``Operation.clean()`` so operators see the same story
        the model enforces on save (including pluralisation for the minutes window).
        """

        if latest_operation_pk is None:
            latest_operation_pk = (
                Operation.objects.filter(item_id=obj.item_id)
                .order_by("-created_at", "-id")
                .values_list("id", flat=True)
                .first()
            )
        if latest_operation_pk is None:
            return None
        if obj.pk != latest_operation_pk:
            return str(_("Only the latest operation for this item can be edited"))
        if Operation.is_within_operation_edit_window(obj.created_at):
            return None
        return Operation.correction_window_expired_user_message()

    def has_change_permission(
        self, request: HttpRequest, obj: Operation | None = None
    ) -> bool:
        allowed = super().has_change_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self._is_editable_latest_operation(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: Operation | None = None
    ) -> bool:
        allowed = super().has_delete_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self._is_editable_latest_operation(request, obj)

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

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: PendingTransfer | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: PendingTransfer | None = None
    ) -> bool:
        return False
