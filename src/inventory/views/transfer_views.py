"""Pending transfer create / accept / cancel views."""

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

from .http_helpers import parse_transfer_receiver_or_render_error, render_transfer_form


def _redirect_after_inactive_transfer(
    request: HttpRequest,
    responsible: Responsible,
    transfer: PendingTransfer,
) -> HttpResponse:
    """Warn and send the user somewhere they can still navigate from."""

    messages.warning(
        request,
        _("This transfer offer is no longer active."),
    )
    if resolve_item_history_context(responsible, transfer.item_id) is not None:
        return redirect("inventory:item-history", item_id=transfer.item_id)
    return redirect("inventory:my-items")


def _redirect_journal_head_stale(
    request: HttpRequest,
    responsible: Responsible,
    *,
    item_id: int,
) -> HttpResponse:
    """The Accept form was built for an older journal head than the server sees now."""

    messages.error(
        request,
        _(
            "The inventory record changed since this page was loaded. "
            "Refresh the page and try again."
        ),
    )
    if resolve_item_history_context(responsible, item_id) is not None:
        return redirect("inventory:item-history", item_id=item_id)
    return redirect("inventory:my-items")


def _redirect_accept_without_journal_head(
    request: HttpRequest,
    _responsible: Responsible,
) -> HttpResponse:
    """
    Accept requires a journal head; without operations the item has none.

    The receiver branch in ``resolve_item_history_context`` returns ``None``
    when there are no operations while an offer is pending, so there is no
    item-history page to send them to—only the list view remains useful.
    """

    messages.error(
        request,
        validation_error_user_message(
            ValidationError(
                _("Cannot accept transfer for an item without operations"),
            ),
        ),
    )
    return redirect("inventory:my-items")


@login_required
def create_transfer(request: HttpRequest, *, item_id: int) -> HttpResponse:
    """
    Create a pending transfer offer for an item.

    Only the current owner may initiate a transfer. Ownership is changed only
    when the receiver confirms the handoff (see ``accept_transfer``).
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
        if pending_transfer is not None:
            if pending_transfer.from_responsible_id != responsible.pk:
                raise Http404

            notes = (request.POST.get("notes") or "").strip()
            to_responsible, error_response = parse_transfer_receiver_or_render_error(
                request,
                item=item,
                sender=responsible,
                pending_transfer=pending_transfer,
                transfer_expiration_hours=transfer_expiration_hours,
                notes=notes,
            )
            if error_response is not None:
                return error_response
            if to_responsible is None:
                # ``parse_transfer_receiver_or_render_error`` always returns a response
                # when the receiver is missing; this guards internal regressions.
                raise AssertionError("expected receiver or response")

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

        notes = (request.POST.get("notes") or "").strip()
        to_responsible, error_response = parse_transfer_receiver_or_render_error(
            request,
            item=item,
            sender=responsible,
            pending_transfer=None,
            transfer_expiration_hours=transfer_expiration_hours,
            notes=notes,
        )
        if error_response is not None:
            return error_response
        if to_responsible is None:
            # Same invariant as the pending-transfer branch above.
            raise AssertionError("expected receiver or response")

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
    Accept a pending transfer and append an ownership-changing operation.

    Only the transfer receiver may accept. POST must include
    ``journal_head_operation_id`` matching the latest ``Operation`` for the item
    (the item history template sets this when rendering Accept) so the server
    rejects submissions built from stale UI state.
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
        return _redirect_after_inactive_transfer(request, responsible, transfer)
    if transfer.to_responsible_id != responsible.pk:
        raise Http404

    latest_head = Operation.latest_operation_id_for_item(transfer.item_id)
    raw_baseline = (request.POST.get("journal_head_operation_id") or "").strip()
    try:
        posted_baseline = int(raw_baseline) if raw_baseline else None
    except ValueError:
        posted_baseline = None

    if latest_head is None:
        return _redirect_accept_without_journal_head(request, responsible)

    if posted_baseline is None or posted_baseline != latest_head:
        return _redirect_journal_head_stale(
            request, responsible, item_id=transfer.item_id
        )

    try:
        transfer.accept()
    except ValidationError as exc:
        messages.error(request, validation_error_user_message(exc))
        return redirect("inventory:item-history", item_id=transfer.item_id)

    messages.success(request, _("Transfer accepted."))
    return redirect("inventory:item-history", item_id=transfer.item_id)


@login_required
def cancel_transfer(request: HttpRequest, *, transfer_id: int) -> HttpResponse:
    """Cancel a pending transfer (sender) or decline it (receiver)."""

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
        return _redirect_after_inactive_transfer(request, responsible, transfer)

    try:
        transfer.cancel()
    except ValidationError as exc:
        messages.error(request, validation_error_user_message(exc))
        return redirect("inventory:item-history", item_id=transfer.item_id)
    messages.success(request, _("Transfer offer closed."))
    return redirect("inventory:item-history", item_id=transfer.item_id)
