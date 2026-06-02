"""Pending transfer create / accept / cancel views."""

import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from catalogs.models import Responsible
from inventory.models import (
    Item,
    PendingTransfer,
    pending_transfer_expiration_hours,
    resolve_item_history_context,
)
from inventory.models.operation import Operation
from inventory.presentation import validation_error_user_message

from .http_helpers import CreateTransferForm, render_transfer_form

logger = logging.getLogger(__name__)


def _redirect_with_message(
    request: HttpRequest,
    responsible: Responsible,
    message: str,
    *,
    level: str = "error",
    item_id: int | None = None,
) -> HttpResponse:
    """Set a flash message and redirect to a page the user can navigate from."""
    getattr(messages, level)(request, message)
    if (
        item_id is not None
        and resolve_item_history_context(responsible, item_id) is not None
    ):
        return redirect("inventory:item-history", item_id=item_id)
    return redirect("inventory:my-items")


@login_required
def create_transfer(request: HttpRequest, *, item_id: int) -> HttpResponse:
    """
    Handle the creation or update of a pending transfer offer for an item.

    GET: Display the transfer creation form.
    POST: Create a new transfer offer or update an existing one.
    Only the current owner may initiate or update a transfer.
    """

    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        raise Http404

    item = Item.objects.owned_by(responsible).filter(pk=item_id).first()
    if item is None:
        raise Http404

    current_op = item.current_operation
    if current_op is None:
        raise Http404  # pragma: no cover

    transfer_expiration_hours = pending_transfer_expiration_hours()

    pending_transfer = PendingTransfer.objects.active_offer_for_item(item)

    if request.method == "POST":
        if (
            pending_transfer is not None
            and pending_transfer.from_responsible_id != responsible.pk
        ):
            raise Http404

        form = CreateTransferForm(request.POST, sender=responsible)
        if not form.is_valid():
            error = str(form.errors.get("to_responsible_id", [""])[0])
            return render_transfer_form(
                request,
                item=item,
                sender=responsible,
                pending_transfer=pending_transfer,
                transfer_expiration_hours=transfer_expiration_hours,
                error=error,
                notes=form.cleaned_data.get("notes", ""),
                selected_to_responsible_id=None,
                status=400,
            )

        to_responsible: Responsible = form.cleaned_data["to_responsible_id"]
        notes: str = form.cleaned_data["notes"]

        if pending_transfer is not None:
            try:
                pending_transfer.update_offer(
                    actor=responsible,
                    to_responsible=to_responsible,
                    notes=notes,
                    auto_expiration_hours=transfer_expiration_hours,
                )
            except ValidationError as exc:
                return render_transfer_form(
                    request,
                    item=item,
                    sender=responsible,
                    pending_transfer=pending_transfer,
                    transfer_expiration_hours=transfer_expiration_hours,
                    error=validation_error_user_message(exc),
                    notes=notes,
                    selected_to_responsible_id=to_responsible.pk,
                    status=400,
                )
            messages.success(request, _("Transfer offer updated."))
            return redirect("inventory:item-history", item_id=item.pk)

        expires_at = None
        if transfer_expiration_hours > 0:
            expires_at = timezone.now() + timedelta(hours=transfer_expiration_hours)

        try:
            PendingTransfer.create_offer(
                item=item,
                from_responsible=responsible,
                to_responsible=to_responsible,
                expires_at=expires_at,
                notes=notes,
            )
        except ValidationError as exc:
            return render_transfer_form(
                request,
                item=item,
                sender=responsible,
                pending_transfer=None,
                transfer_expiration_hours=transfer_expiration_hours,
                error=validation_error_user_message(exc),
                notes=notes,
                selected_to_responsible_id=to_responsible.pk,
                status=400,
            )
        messages.success(request, _("Transfer offer submitted."))
        return redirect("inventory:item-history", item_id=item.pk)

    if pending_transfer is not None:
        if pending_transfer.from_responsible_id != responsible.pk:
            return render(
                request,
                "inventory/transfer_create.html",
                {
                    "item": item,
                    "responsible": responsible,
                    "responsibles": [],
                    "pending_transfer": pending_transfer,
                    "transfer_expiration_hours": transfer_expiration_hours,
                    "notes": "",
                    "selected_to_responsible_id": None,
                },
            )

        return render_transfer_form(
            request,
            item=item,
            sender=responsible,
            pending_transfer=pending_transfer,
            transfer_expiration_hours=transfer_expiration_hours,
            notes=pending_transfer.notes or "",
            selected_to_responsible_id=pending_transfer.to_responsible_id,
        )

    return render_transfer_form(
        request,
        item=item,
        sender=responsible,
        pending_transfer=None,
        transfer_expiration_hours=transfer_expiration_hours,
        notes="",
        selected_to_responsible_id=None,
    )


@login_required
def accept_transfer(request: HttpRequest, *, transfer_id: int) -> HttpResponse:
    """
    Accept a pending transfer and record the ownership change.

    Only the receiver of the transfer may accept it.
    Requires a POST request and verification of the latest operation ID
    to prevent race conditions with stale UI state.
    """

    if request.method != "POST":
        raise Http404

    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        raise Http404

    transfer = get_object_or_404(
        PendingTransfer.objects.select_related(
            "item", "to_responsible", "from_responsible"
        ),
        pk=transfer_id,
    )
    if responsible.pk not in {
        transfer.from_responsible_id,
        transfer.to_responsible_id,
    }:
        raise Http404
    if not transfer.is_active:
        return _redirect_with_message(
            request,
            responsible,
            _("This transfer offer is no longer active."),
            level="warning",
            item_id=transfer.item_id,
        )
    if transfer.to_responsible_id != responsible.pk:
        raise Http404

    latest_head = Operation.latest_operation_id_for_item(transfer.item_id)
    raw_baseline = (request.POST.get("journal_head_operation_id") or "").strip()
    try:
        posted_baseline = int(raw_baseline) if raw_baseline else None
    except ValueError:
        posted_baseline = None

    if latest_head is None:
        messages.error(
            request,
            validation_error_user_message(
                ValidationError(
                    _("Cannot accept transfer for an item without operations"),
                ),
            ),
        )
        return redirect("inventory:my-items")

    if posted_baseline is None or posted_baseline != latest_head:
        return _redirect_with_message(
            request,
            responsible,
            _(
                "The inventory record changed since this page was loaded. "
                "Refresh the page and try again."
            ),
            item_id=transfer.item_id,
        )

    try:
        transfer.accept()
    except ValidationError as exc:
        error_msg = validation_error_user_message(exc)
        messages.error(request, error_msg)
        if getattr(exc, "code", None) == "transfer_inactive":
            logger.warning(
                "Transfer %s became inactive before accept could complete",
                transfer_id,
            )
        else:
            logger.exception(
                "ValidationError while accepting transfer id=%s", transfer_id
            )
        return redirect("inventory:item-history", item_id=transfer.item_id)
    messages.success(request, _("Transfer accepted."))
    return redirect("inventory:item-history", item_id=transfer.item_id)


@login_required
def cancel_transfer(request: HttpRequest, *, transfer_id: int) -> HttpResponse:
    """
    Cancel or decline a pending transfer offer.

    Both the sender (Cancel) and the receiver (Decline) may perform this action.
    Requires a POST request.
    """

    if request.method != "POST":
        raise Http404

    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        raise Http404

    transfer = get_object_or_404(
        PendingTransfer.objects.select_related(
            "item", "from_responsible", "to_responsible"
        ),
        pk=transfer_id,
    )
    if responsible.pk not in {
        transfer.from_responsible_id,
        transfer.to_responsible_id,
    }:
        raise Http404
    if not transfer.is_active:
        return _redirect_with_message(
            request,
            responsible,
            _("This transfer offer is no longer active."),
            level="warning",
            item_id=transfer.item_id,
        )

    try:
        transfer.cancel()
    except ValidationError as exc:
        messages.error(request, validation_error_user_message(exc))
        return redirect("inventory:item-history", item_id=transfer.item_id)
    messages.success(request, _("Transfer offer closed."))
    return redirect("inventory:item-history", item_id=transfer.item_id)
