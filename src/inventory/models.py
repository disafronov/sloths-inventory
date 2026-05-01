from datetime import timedelta
from typing import Any, Optional, overload

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from catalogs.models import Location, Responsible, Status
from common.models import BaseModel
from devices.models import Device


class Item(BaseModel):
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

    def clean(self) -> None:
        """Validate the model."""
        if not self.inventory_number:
            raise ValidationError(
                {"inventory_number": _("Inventory number cannot be empty")}
            )

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


class Operation(BaseModel):
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

    def clean(self) -> None:
        """
        Enforce append-only semantics for operations.

        Only the latest operation for a given item may be edited, and only to
        correct its state fields. This keeps the history stable while allowing
        a human error to be fixed without rewriting older events.
        """

        super().clean()

        if self._state.adding:
            return

        # Editing operations is a "correction" path only. The goal is to prevent
        # silent history rewrites while still allowing quick fixes for recent typos.
        # The actual limit is configurable because different teams have different
        # operational workflows.
        edit_window_minutes = getattr(
            settings, "INVENTORY_OPERATION_EDIT_WINDOW_MINUTES", 10
        )
        edit_window = timedelta(minutes=edit_window_minutes)

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

        if timezone.now() - original.created_at > edit_window:
            message = ngettext(
                "This operation can no longer be edited "
                "(the %(minutes)d minute correction window has expired)",
                "This operation can no longer be edited "
                "(the %(minutes)d minutes correction window has expired)",
                edit_window_minutes,
            ) % {"minutes": edit_window_minutes}
            raise ValidationError(
                message,
                # Keep a stable error code for tests and possible UI handling.
                code="correction_window_expired",
            )

        latest_id = (
            Operation.objects.filter(item_id=self.item_id)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
            .first()
        )
        if latest_id is None:
            raise AssertionError(
                "Invariant violation: operation exists but no operations found for item"
            )
        if latest_id != self.pk:
            raise ValidationError(
                _("Only the latest operation for this item can be edited")
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
