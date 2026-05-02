"""Pending transfer create / accept / cancel views."""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from catalogs.models import Responsible
from inventory.models import Item, PendingTransfer, pending_transfer_expiration_hours
from inventory.presentation import validation_error_user_message

from .http_helpers import parse_transfer_receiver_or_render_error, render_transfer_form


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

    Only the transfer receiver may accept.
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
    if not transfer.is_active:
        raise Http404
    if transfer.to_responsible_id != responsible.pk:
        raise Http404

    try:
        transfer.accept()
    except ValidationError:
        raise Http404

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
    if not transfer.is_active:
        raise Http404
    if responsible.pk not in {
        transfer.from_responsible_id,
        transfer.to_responsible_id,
    }:
        raise Http404

    try:
        transfer.cancel()
    except ValidationError:
        raise Http404
    return redirect("inventory:item-history", item_id=transfer.item_id)
