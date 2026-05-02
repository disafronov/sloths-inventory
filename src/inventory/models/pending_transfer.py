from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from catalogs.models import Responsible
from common.models import BaseModel
from inventory.models.item import Item


class PendingTransferQuerySet(models.QuerySet):
    """
    QuerySet helpers for pending transfer offers shown in the inventory UI.

    Matches ``PendingTransfer.is_active`` semantics without relying on per-row
    property checks in Python for list views.
    """

    def offers_visible_in_ui(self) -> "PendingTransferQuerySet":
        """Exclude finished or expired offers."""

        now = timezone.now()
        return self.filter(
            accepted_at__isnull=True,
            cancelled_at__isnull=True,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))

    def active_offer_for_item(self, item: Item) -> PendingTransfer | None:
        """Return the newest visible pending transfer for ``item``, if any."""

        return (
            self.offers_visible_in_ui()
            .filter(item=item)
            .select_related("from_responsible", "to_responsible")
            .order_by("-created_at", "-id")
            .first()
        )


class PendingTransferManager(models.Manager):
    """
    Manager for :class:`PendingTransfer` returning :class:`PendingTransferQuerySet`.
    """

    def get_queryset(self) -> PendingTransferQuerySet:
        return PendingTransferQuerySet(self.model, using=self._db)

    def offers_visible_in_ui(self) -> PendingTransferQuerySet:
        return self.get_queryset().offers_visible_in_ui()

    def active_offer_for_item(self, item: Item) -> PendingTransfer | None:
        return self.get_queryset().active_offer_for_item(item)


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

    objects = PendingTransferManager()

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

    @classmethod
    def offers_visible_in_ui(cls) -> PendingTransferQuerySet:
        """
        Pending transfers the inventory UI treats as visible offers.

        Delegates to :meth:`PendingTransferQuerySet.offers_visible_in_ui` so
        filter rules stay centralized; call sites can reference the model class.
        """

        return cls.objects.offers_visible_in_ui()

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

        The latest journal operation must still name ``from_responsible``; otherwise
        the offer is stale and acceptance is rejected.
        """

        from inventory.models.operation import Operation

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
            # The offer is valid only while the journal head still names the sender.
            # Ownership may move while a stale PendingTransfer row stays active (e.g.
            # admin repair); we must not copy state from a non-sender head for the
            # receiver.
            if current_op.responsible_id != transfer.from_responsible_id:
                raise ValidationError(
                    _("Cannot accept transfer: sender no longer holds the item.")
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
