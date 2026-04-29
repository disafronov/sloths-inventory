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
