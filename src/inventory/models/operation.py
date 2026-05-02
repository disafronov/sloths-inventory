from __future__ import annotations

from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from catalogs.models import Location, Responsible, Status
from common.edit_window import (
    inventory_correction_window_minutes,
    is_within_inventory_correction_window,
)
from common.models import BaseModel
from inventory.models.item import Item


class Operation(BaseModel):
    """
    Journal row for item state (append-only stream).

    ``OperationAdmin`` sets ``_bypass_operation_correction_window`` on the instance
    for superusers on the **latest** row only so ``clean()`` skips the correction
    window; the head-row rule is never bypassed.
    """

    item = models.ForeignKey("Item", on_delete=models.CASCADE, verbose_name=_("Item"))
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, verbose_name=_("Status")
    )
    responsible = models.ForeignKey(
        Responsible, on_delete=models.PROTECT, verbose_name=_("Responsible")
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, verbose_name=_("Location")
    )

    class Meta:
        verbose_name = _("Operation")
        verbose_name_plural = _("Operations")
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["item", "-created_at", "-id"],
                name="inventory_op_item_latest_idx",
            ),
            # Supports filters and subqueries keyed by responsible then latest
            # rows per item (see docs/inventory-list-query-profiling.md).
            models.Index(
                fields=["responsible", "item", "-created_at", "-id"],
                name="inventory_op_resp_item_idx",
            ),
        ]

    @classmethod
    def is_within_operation_correction_window(
        cls,
        operation_created_at: datetime,
        *,
        reference_time: datetime | None = None,
    ) -> bool:
        """
        Return whether an operation created at ``operation_created_at`` may still be
        corrected under ``INVENTORY_CORRECTION_WINDOW_MINUTES``.

        Delegates to ``common.edit_window.is_within_inventory_correction_window`` so
        admin checks and ``Operation.clean()`` stay aligned with ``save()``.
        """

        return is_within_inventory_correction_window(
            operation_created_at, reference_time=reference_time
        )

    @classmethod
    def latest_operation_id_for_item(cls, item_id: int) -> int | None:
        """Return the PK of the latest ``Operation`` for ``item_id``, if any."""

        return (
            cls.objects.filter(item_id=item_id)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
            .first()
        )

    @classmethod
    def only_latest_operation_may_be_edited_user_message(cls) -> str:
        """
        Return the user-visible message when a non-latest operation cannot be edited.

        Shared by ``Operation.clean()`` and the admin lock panel so operators see the
        same wording the model enforces on save (append-only head rule).
        """

        return str(_("Only the latest operation for this item can be edited"))

    @classmethod
    def correction_window_expired_user_message(cls) -> str:
        """
        Return the user-visible message when the correction window has expired.

        Shared by ``Operation.clean()`` and the admin lock panel so operators see
        the same wording the model enforces on save (correction window expiry only).
        """

        minutes = inventory_correction_window_minutes()
        return str(
            ngettext(
                "The correction window (%(minutes)d minute) has expired. "
                "To make changes, contact an administrator.",
                "The correction window (%(minutes)d minutes) has expired. "
                "To make changes, contact an administrator.",
                minutes,
            )
            % {"minutes": minutes}
        )

    def clean(self) -> None:
        """
        Enforce append-only semantics for operations.

        Only the latest operation for a given item may be edited, and only to
        correct its state fields. This keeps the history stable while allowing
        a human error to be fixed without rewriting older events.

        The latest-row check runs before the correction window so non-head rows
        surface the append-only reason (aligned with ``OperationAdmin``), not a
        misleading window-expired message when ``created_at`` is historical.

        Superusers in ``OperationAdmin`` set ``_bypass_operation_correction_window`` so
        the time cap is skipped on the head row only (see ``clean()`` order).
        """

        super().clean()

        if self._state.adding:
            return

        # Always re-fetch authoritative column values from the database. A stale
        # in-memory instance must not weaken append-only or window checks.
        original = Operation.objects.only(
            "item_id",
            "status_id",
            "responsible_id",
            "location_id",
            "notes",
            "created_at",
        ).get(pk=self.pk)

        if self.item_id != original.item_id:
            raise ValidationError({"item": _("Operation item cannot be changed")})

        # Append-only head rule first so the failure reason matches the admin UI and
        # does not claim the correction window expired for historical non-head rows.
        latest_id = type(self).latest_operation_id_for_item(self.item_id)
        if latest_id is None:
            raise AssertionError(
                "Invariant violation: operation exists but no operations found for item"
            )
        if latest_id != self.pk:
            raise ValidationError(
                type(self).only_latest_operation_may_be_edited_user_message(),
                code="operation_not_latest_for_item",
            )

        # Set only by ``OperationAdmin`` ModelForm for superusers on the latest row
        # (trusted repair path); never bypasses the append-only head rule above.
        if getattr(self, "_bypass_operation_correction_window", False):
            return

        # Correction edits are time-bounded; the cap is intentionally small by default
        # and configurable per deployment (see INVENTORY_CORRECTION_WINDOW_MINUTES).
        if not self.is_within_operation_correction_window(original.created_at):
            raise ValidationError(
                type(self).correction_window_expired_user_message(),
                # Keep a stable error code for tests and possible UI handling.
                code="correction_window_expired",
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the operation with concurrency-safe append-only enforcement.

        We serialize all operation writes per item by taking a row-level lock on
        the related Item inside a transaction. This makes the "only the latest
        operation may be edited" rule deterministic even under concurrent inserts
        and edits.
        """

        with transaction.atomic():
            # Lock the item row to serialize concurrent updates for the same item.
            Item.objects.select_for_update().only("id").get(pk=self.item_id)

            # Ensure `clean()` runs on updates as well (admin and any other code path).
            self.full_clean()
            return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.item} - {self.status} ({self.location})"

    def get_responsible_display(self) -> str:
        """Return a human-readable representation of the responsible person."""
        return str(self.responsible)
