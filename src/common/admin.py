from typing import Any, Protocol, cast

from django import forms
from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from common.edit_window import is_within_inventory_correction_window


class CatalogReferenceRow(Protocol):
    """
    Structural type for models using ``CatalogCorrectionWindowMixin``.

    Mypy cannot infer this from the abstract mixin on ``Model`` subclasses.
    """

    updated_at: Any
    pk: Any

    def is_catalog_reference_in_use(self) -> bool: ...

    @classmethod
    def catalog_correction_window_expired_user_message(cls) -> str: ...


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["updated_at", "created_at"]
    search_fields = ["created_at", "updated_at", "notes"]
    fieldsets = (
        (None, {"fields": ()}),  # Will be overridden in subclasses
        (
            _("Additional information"),
            {"fields": ("notes", "updated_at", "created_at")},
        ),
    )
    main_fields: tuple[str, ...] = ()  # Will be overridden in subclasses

    def get_main_fields(self) -> tuple[str, ...]:
        return self.main_fields

    def get_fieldsets(self, request: HttpRequest, obj: Model | None = None) -> Any:
        fieldsets = list(super().get_fieldsets(request, obj))
        if not fieldsets:
            fieldsets = [(None, {"fields": self.get_main_fields()})]
        else:
            fieldsets[0] = (None, {"fields": self.get_main_fields()})
        return fieldsets

    def _format_empty_value(self, value: Any) -> str:
        if value is None or value == "":
            return "-"
        return str(value)


class CatalogReferenceAdminMixin(admin.ModelAdmin):
    """
    Admin for models using ``CatalogCorrectionWindowMixin``.

    Superusers may always edit. Rows not referenced by inventory data may always
    edit. Referenced rows are bound by ``INVENTORY_CORRECTION_WINDOW_MINUTES``
    from ``updated_at``.
    """

    def _is_catalog_reference_editable(
        self, request: HttpRequest, obj: CatalogReferenceRow
    ) -> bool:
        user = getattr(request, "user", None)
        if getattr(user, "is_superuser", False):
            return True
        if not obj.is_catalog_reference_in_use():
            return True
        return is_within_inventory_correction_window(obj.updated_at)

    def _catalog_correction_window_lock_user_message(
        self, request: HttpRequest, obj: CatalogReferenceRow
    ) -> str | None:
        user = getattr(request, "user", None)
        if getattr(user, "is_superuser", False):
            return None
        if not obj.is_catalog_reference_in_use():
            return None
        if is_within_inventory_correction_window(obj.updated_at):
            return None
        model_cls = type(obj)
        return model_cls.catalog_correction_window_expired_user_message()

    def has_change_permission(
        self, request: HttpRequest, obj: Model | None = None
    ) -> bool:
        allowed = super().has_change_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self._is_catalog_reference_editable(
            request, cast(CatalogReferenceRow, obj)
        )

    def has_delete_permission(
        self, request: HttpRequest, obj: Model | None = None
    ) -> bool:
        allowed = super().has_delete_permission(request, obj)
        if not allowed or obj is None:
            return allowed
        return self._is_catalog_reference_editable(
            request, cast(CatalogReferenceRow, obj)
        )

    def get_form(
        self,
        request: HttpRequest,
        obj: Model | None = None,
        change: bool = False,
        **kwargs: Any,
    ) -> type[forms.ModelForm]:
        """
        For superusers, set the bypass flag so ``CatalogCorrectionWindowMixin.clean()``
        runs before ``form.is_valid()`` calls ``full_clean()`` on the instance.
        """

        form_class = super().get_form(request, obj, change=change, **kwargs)
        user = getattr(request, "user", None)

        class CatalogAdminForm(form_class):  # type: ignore[misc, valid-type]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                if getattr(user, "is_superuser", False) and self.instance.pk:
                    setattr(self.instance, "_bypass_catalog_correction_window", True)

        return CatalogAdminForm

    def get_fieldsets(self, request: HttpRequest, obj: Model | None = None) -> Any:
        fieldsets = list(super().get_fieldsets(request, obj))
        if obj is None:
            return fieldsets
        message = self._catalog_correction_window_lock_user_message(
            request, cast(CatalogReferenceRow, obj)
        )
        if message is None:
            return fieldsets
        desc = format_html('<p class="catalog-correction-window-lock">{}</p>', message)
        lock_panel = (
            _("Editing restrictions"),
            {"fields": (), "description": desc},
        )
        return [*fieldsets, lock_panel]


class NamedModelAdmin(CatalogReferenceAdminMixin, BaseAdmin):
    list_display = ["name", "updated_at", "created_at"]
    search_fields = ["name", "created_at", "updated_at", "notes"]
    main_fields = ("name",)
