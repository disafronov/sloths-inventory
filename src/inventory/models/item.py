from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, cast, overload

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import OuterRef, Q, Subquery
from django.utils.translation import gettext_lazy as _

from catalogs.models import Location, Responsible
from common.edit_window import (
    catalog_entry_correction_window_expired_user_message,
    is_within_inventory_correction_window,
)
from common.models import BaseModel
from devices.models import Device

if TYPE_CHECKING:
    from inventory.models.operation import Operation


class ItemQuerySet(models.QuerySet):
    """
    QuerySet helpers for inventory UI lists.

    Centralizes ``select_related`` for device relations so list/detail templates
    do not regress into N+1 queries.
    """

    def with_device_relations(self) -> "ItemQuerySet":
        """Prefetch device and its catalog FKs for template rendering."""

        return self.select_related(
            "device",
            "device__category",
            "device__type",
            "device__manufacturer",
            "device__model",
        )

    def apply_search(self, query: str) -> "ItemQuerySet":
        """
        Apply a user-facing search string to inventory number, serial, and device
        identifying fields.
        """

        text = query.strip()
        if not text:
            return self
        return self.filter(
            Q(inventory_number__icontains=text)
            | Q(serial_number__icontains=text)
            | Q(device__manufacturer__name__icontains=text)
            | Q(device__model__name__icontains=text)
        )

    def owned_by(self, responsible: Responsible) -> "ItemQuerySet":
        """
        Return items whose latest operation names ``responsible``.

        Reflects journal semantics: the latest ``Operation`` per item defines the
        current responsible person.
        """

        from inventory.models.operation import Operation

        latest_responsible_id = (
            Operation.objects.filter(item_id=OuterRef("pk"))
            .order_by("-created_at", "-id")
            .values("responsible_id")[:1]
        )
        # cast: django-stubs widen ``annotate().filter()`` on a typed QuerySet to Any.
        return cast(
            ItemQuerySet,
            self.with_device_relations()
            .annotate(_latest_responsible_id=Subquery(latest_responsible_id))
            .filter(_latest_responsible_id=responsible.pk),
        )


class ItemManager(models.Manager):
    """Manager for :class:`Item` returning :class:`ItemQuerySet`."""

    def get_queryset(self) -> ItemQuerySet:
        return ItemQuerySet(self.model, using=self._db)

    def with_device_relations(self) -> ItemQuerySet:
        return self.get_queryset().with_device_relations()

    def apply_search(self, query: str) -> ItemQuerySet:
        return self.get_queryset().apply_search(query)

    def owned_by(self, responsible: Responsible) -> ItemQuerySet:
        return self.get_queryset().owned_by(responsible)


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

    objects = ItemManager()

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
        """Descriptor that reads display strings from the latest ``Operation``."""

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

        from inventory.models.operation import Operation

        current_op = self.current_operation
        if current_op is None:
            raise ValidationError(
                _("Cannot change location for an item without operations")
            )

        if location.pk == current_op.location_id:
            raise ValidationError(
                _("New location must be different from current location.")
            )

        # Align with transfer acceptance: the journal head defines the accountable
        # party; callers must not append a location move under another identity.
        if responsible.pk != current_op.responsible_id:
            raise ValidationError(
                _(
                    "Location changes must be recorded by the current "
                    "accountable person."
                )
            )

        op = Operation.objects.create(
            item=self,
            status=current_op.status,
            responsible=responsible,
            location=location,
            notes=notes,
        )
        return op
