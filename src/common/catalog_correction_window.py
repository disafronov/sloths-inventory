"""
Catalog / reference models: time-bounded edits when a row is in use.

Superusers bypass via ``_bypass_catalog_correction_window`` (set by admin forms).
Rows not referenced by inventory data skip the window entirely.
"""

from typing import Any, cast

from django.core.exceptions import ValidationError

from common.edit_window import (
    catalog_entry_correction_window_expired_user_message,
    is_within_inventory_correction_window,
)
from common.models import SerializedSaveMixin


class CatalogCorrectionWindowMixin(SerializedSaveMixin):
    """
    Abstract mixin: enforce ``INVENTORY_CORRECTION_WINDOW_MINUTES`` on updates
    when ``is_catalog_reference_in_use()`` is true.

    The correction window is anchored on the row's ``created_at`` timestamp
    (immutable), not ``updated_at``, so the window does not reset on each save.

    Row-level save serialization comes from ``SerializedSaveMixin``.

    Subclasses must implement ``is_catalog_reference_in_use`` (no DB hits while
    ``_state.adding``).
    """

    class Meta:
        abstract = True

    def is_catalog_reference_in_use(self) -> bool:
        """Return True when this catalog row is referenced by inventory data."""

        raise NotImplementedError

    @classmethod
    def catalog_correction_window_expired_user_message(cls) -> str:
        """User-visible text when the catalog correction window has expired."""

        return catalog_entry_correction_window_expired_user_message()

    def clean(self) -> None:
        """Apply the correction window when the row is referenced elsewhere."""

        super().clean()
        if self._state.adding:
            return
        if getattr(self, "_bypass_catalog_correction_window", False):
            return
        if not self.is_catalog_reference_in_use():
            return

        # ``type(self)`` is a concrete model class; mypy cannot derive ``.objects`` from
        # the abstract mixin base.
        concrete_model_cls = cast(Any, type(self))
        original_created_at = (
            concrete_model_cls.objects.only("created_at").get(pk=self.pk).created_at
        )
        if not is_within_inventory_correction_window(original_created_at):
            raise ValidationError(
                type(self).catalog_correction_window_expired_user_message(),
                code="catalog_correction_window_expired",
            )
