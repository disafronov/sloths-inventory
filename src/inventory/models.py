from datetime import datetime, timedelta
from typing import Any, Optional, overload

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from catalogs.models import Location, Responsible, Status
from common.edit_window import (
    catalog_entry_correction_window_expired_user_message,
    inventory_correction_window_minutes,
    is_within_inventory_correction_window,
)
from common.models import BaseModel
from devices.models import Device


class Item(BaseModel):
    """
    Inventory unit (device instance).

    Item field edits are time-bounded by the correction window once an accountable
    party exists (see ``has_assigned_responsible()`` and ``clean()``). Until the
    first ``Operation`` is recorded, the item has no responsible person in the
    journal and the row stays editable regardless of ``updated_at``.

    The admin sets ``_bypass_item_correction_window`` on the instance for
    superusers only so support can repair rows after the window; do not set that
    flag from other code paths.
    """

    inventory_number = models.CharField(
        max_length=50, unique=True, verbose_name=_("Inventory number")
    )
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, verbose_name=_("Device")
    )
    serial_number = models.CharField(
        max_length=50, blank=True, verbose_name=_("Serial number")
    )

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ["inventory_number"]

    def __str__(self) -> str:
        return self.get_display_name()

    def get_display_name(self) -> str:
        return f"{self.inventory_number} - {self.device}"

    def has_assigned_responsible(self) -> bool:
        """
        Return True when this item has at least one ``Operation``.

        The append-only operation stream defines who is accountable for the unit.
        With zero operations there is no responsible party yet, so item field
        edits are not subject to the ``updated_at`` correction window (see ``clean()``).
        """

        if self._state.adding:
            return False
        return self.operation_set.exists()

    @classmethod
    def item_correction_window_expired_user_message(cls) -> str:
        """
        Return the user-visible message when the item correction window has expired.

        Uses ``INVENTORY_CORRECTION_WINDOW_MINUTES`` like operation corrections,
        but the anchor timestamp is this row's ``updated_at`` (see ``Item.clean()``).

        Wording is shared with ``CatalogCorrectionWindowMixin`` via
        ``common.edit_window.catalog_entry_correction_window_expired_user_message``.
        """

        return catalog_entry_correction_window_expired_user_message()

    def clean(self) -> None:
        """
        Validate the model and enforce the item correction window.

        Once a responsible party exists (at least one ``Operation``), any update
        while the row's previous ``updated_at`` falls outside the configured window
        is rejected. This matches ``Operation`` semantics (same minute cap) and
        prevents ``save()`` from silently refreshing ``updated_at`` after the
        window should have closed. Items with no operations skip the window check.
        """

        super().clean()
        if not self.inventory_number:
            raise ValidationError(
                {"inventory_number": _("Inventory number cannot be empty")}
            )
        if self._state.adding:
            return

        # Set only by ``ItemAdmin`` ModelForm for superusers (trusted repair path).
        if getattr(self, "_bypass_item_correction_window", False):
            return

        if not self.has_assigned_responsible():
            return

        original_updated_at = Item.objects.only("updated_at").get(pk=self.pk).updated_at
        if not is_within_inventory_correction_window(original_updated_at):
            raise ValidationError(
                type(self).item_correction_window_expired_user_message(),
                code="item_correction_window_expired",
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Persist after validation.

        Takes a row lock on updates so concurrent saves cannot race past ``clean()``
        window checks (same pattern as ``Operation.save``).
        """

        with transaction.atomic():
            if not self._state.adding:
                Item.objects.select_for_update().only("id").get(pk=self.pk)
            self.full_clean()
            return super().save(*args, **kwargs)

    @property
    def current_operation(self) -> Optional["Operation"]:
        return self.operation_set.order_by("-created_at", "-id").first()

    class CurrentOperationValue:
        def __init__(self, attr_name: str) -> None:
            self.attr_name = attr_name

        @overload
        def __get__(
            self, instance: None, owner: type["Item"]
        ) -> "Item.CurrentOperationValue": ...

        @overload
        def __get__(self, instance: "Item", owner: type["Item"]) -> Optional[str]: ...

        def __get__(self, instance: Optional["Item"], owner: type["Item"]) -> Any:
            if instance is None:
                return self
            operation = instance.current_operation
            if not operation:
                return None

            value = getattr(operation, self.attr_name, None)
            if value is not None and hasattr(value, "name"):
                return value.name
            if value is None:
                return None
            return str(value)

    current_status = CurrentOperationValue("status")
    current_location = CurrentOperationValue("location")
    current_responsible = CurrentOperationValue("responsible")

    def change_location(
        self, *, responsible: Responsible, location: Location, notes: str = ""
    ) -> "Operation":
        """
        Append a location-changing operation for this item.

        The inventory state is derived from append-only `Operation` records. Changing
        an item's location is represented by appending a new operation that keeps
        the current status and responsible person while updating the location.
        """

        current_op = self.current_operation
        if current_op is None:
            raise ValidationError(
                _("Cannot change location for an item without operations")
            )

        if location.pk == current_op.location_id:
            raise ValidationError(
                _("New location must be different from current location.")
            )

        op = Operation.objects.create(
            item=self,
            status=current_op.status,
            responsible=responsible,
            location=location,
            notes=notes,
        )
        return op


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


class PendingTransfer(BaseModel):
    """
    Pending item transfer that requires receiver confirmation.

    The inventory uses an append-only stream of `Operation` records to derive the
    current owner. A transfer must not be a unilateral state change, so we store
    a separate pending entity and only create a new `Operation` when the
    receiver confirms the handoff.
    """

    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    from_responsible = models.ForeignKey(
        Responsible,
        on_delete=models.PROTECT,
        related_name="outgoing_transfers",
        verbose_name=_("From"),
    )
    to_responsible = models.ForeignKey(
        Responsible,
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
        verbose_name=_("To"),
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires at"),
        help_text=_("Optional. Transfers are ignored after expiration."),
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Accepted at"),
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Cancelled at"),
    )

    class Meta:
        verbose_name = _("Pending transfer")
        verbose_name_plural = _("Pending transfers")
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["item", "accepted_at", "cancelled_at", "-created_at", "-id"],
                name="inv_pend_xfer_item_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.item} -> {self.to_responsible}"

    def clean(self) -> None:
        """
        Validate pending transfer invariants.

        - Only one active transfer may exist per item.
        - Transfers cannot be accepted and cancelled at the same time.
        """

        super().clean()

        if self.from_responsible_id == self.to_responsible_id:
            raise ValidationError(
                {"to_responsible": _("Transfer receiver must be different")}
            )

        if self.accepted_at and self.cancelled_at:
            raise ValidationError(_("Transfer cannot be accepted and cancelled"))

        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError({"expires_at": _("Expiration must be in the future")})

        if self._state.adding and self.item_id:
            active_exists = (
                PendingTransfer.objects.filter(item_id=self.item_id)
                .filter(accepted_at__isnull=True, cancelled_at__isnull=True)
                .exists()
            )
            if active_exists:
                raise ValidationError(
                    _("An active transfer already exists for this item")
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the transfer with per-item serialization.

        We lock the related Item row to avoid creating multiple concurrent
        pending transfers for the same item under race conditions.
        """

        with transaction.atomic():
            Item.objects.select_for_update().only("id").get(pk=self.item_id)
            self.full_clean()
            return super().save(*args, **kwargs)

    @classmethod
    def create_offer(
        cls,
        *,
        item: Item,
        from_responsible: Responsible,
        to_responsible: Responsible,
        expires_at: datetime | None,
        notes: str = "",
    ) -> "PendingTransfer":
        """
        Create a transfer offer and accept it automatically when required.

        If the receiver `Responsible` has no linked Django user, they cannot confirm
        the offer in the UI. In that case we accept the transfer automatically to
        avoid leaving an un-accept-able pending offer.
        """

        transfer = cls.objects.create(
            item=item,
            from_responsible=from_responsible,
            to_responsible=to_responsible,
            expires_at=expires_at,
            notes=notes,
        )
        if to_responsible.user_id is None:
            transfer.accept()
        return transfer

    def accept(self) -> None:
        """
        Accept the transfer and append an ownership-changing operation.

        This is the authoritative confirmation path that changes the current owner
        (via a new `Operation`). It is used both by the user-facing "Accept" action
        and by the automatic acceptance path when the receiver has no linked user.
        """

        with transaction.atomic():
            # Serialize per-item to avoid races with other operations/transfers.
            Item.objects.select_for_update().only("id").get(pk=self.item_id)
            transfer = PendingTransfer.objects.select_for_update().get(pk=self.pk)
            if not transfer.is_active:
                raise ValidationError(_("Transfer is not active"))

            item = Item.objects.get(pk=transfer.item_id)
            current_op = item.current_operation
            if current_op is None:
                raise ValidationError(
                    _("Cannot accept transfer for an item without operations")
                )

            Operation.objects.create(
                item=item,
                status=current_op.status,
                responsible=transfer.to_responsible,
                location=current_op.location,
                notes=transfer.notes,
            )
            transfer.accepted_at = timezone.now()
            transfer.save(update_fields=["accepted_at", "updated_at"])

    def cancel(self) -> None:
        """
        Cancel the transfer offer.

        This is used both by the sender ("Cancel") and by the receiver ("Decline").
        """

        with transaction.atomic():
            Item.objects.select_for_update().only("id").get(pk=self.item_id)
            transfer = PendingTransfer.objects.select_for_update().get(pk=self.pk)
            if not transfer.is_active:
                raise ValidationError(_("Transfer is not active"))

            transfer.cancelled_at = timezone.now()
            transfer.save(update_fields=["cancelled_at", "updated_at"])

    def update_offer(
        self,
        *,
        actor: Responsible,
        to_responsible: Responsible,
        notes: str,
        auto_expiration_hours: int,
    ) -> None:
        """
        Update an active transfer offer.

        This is the sender-side edit flow for the user-facing UI. We keep the
        same per-item serialization guarantees as `accept()` / `cancel()`.

        Offer edits are limited only by ``PendingTransfer.is_active`` (including
        ``expires_at`` when set), not by the operation correction window.

        If the new receiver has no linked Django user, we call `accept()` after
        persisting the update, matching `create_offer` so the item cannot remain
        stuck in a pending offer nobody can confirm in the UI.
        """

        if auto_expiration_hours < 0:
            raise ValidationError(_("Expiration window must be non-negative"))

        with transaction.atomic():
            Item.objects.select_for_update().only("id").get(pk=self.item_id)
            transfer = PendingTransfer.objects.select_for_update().get(pk=self.pk)

            if not transfer.is_active:
                raise ValidationError(_("Transfer is not active"))
            if transfer.from_responsible_id != actor.pk:
                raise ValidationError(_("Only the sender may update the transfer"))

            receiver_changed = transfer.to_responsible_id != to_responsible.pk

            transfer.to_responsible = to_responsible
            transfer.notes = notes
            if receiver_changed:
                if auto_expiration_hours > 0:
                    transfer.expires_at = timezone.now() + timedelta(
                        hours=auto_expiration_hours
                    )
                else:
                    transfer.expires_at = None

            transfer.save(
                update_fields=["to_responsible", "notes", "expires_at", "updated_at"]
            )

            if to_responsible.user_id is None:
                transfer.accept()

    @property
    def is_active(self) -> bool:
        """Return True when the transfer is pending and not expired."""

        if self.accepted_at or self.cancelled_at:
            return False
        if self.expires_at is not None and timezone.now() >= self.expires_at:
            return False
        return True

    def deadline_edge_gradient_t(self) -> str:
        """
        Return a ratio in ``[0, 1]`` as a CSS string for the ``--transfer-t`` property.

        The value tracks elapsed time from ``created_at`` toward ``expires_at``:
        ``0`` means the offer was just created, ``1`` means the deadline has been
        reached or passed. When ``expires_at`` is unset, returns ``0`` so transfer
        cards keep their default wide gradient (no deadline-driven edge emphasis).
        """

        if self.expires_at is None:
            return "0"
        start = self.created_at
        end = self.expires_at
        now = timezone.now()
        if now <= start:
            return "0"
        if now >= end:
            return "1"
        span_seconds = (end - start).total_seconds()
        # Defensive guard: given the comparisons above (now < end and now > start),
        # a non-positive span is practically unreachable, but we keep it for safety
        # against inconsistent timestamps or future refactors.
        if span_seconds <= 0:  # pragma: no cover
            return "1"
        ratio = (now - start).total_seconds() / span_seconds
        ratio = min(1.0, max(0.0, ratio))
        text = f"{ratio:.6f}".rstrip("0").rstrip(".")
        return text if text else "0"
