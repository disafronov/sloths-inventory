"""
HTTP-only helpers shared by inventory view modules (forms, template rendering).
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from catalogs.models import Responsible
from inventory.models import Item, PendingTransfer
from inventory.presentation import validation_error_user_message


def render_transfer_form(
    request: HttpRequest,
    *,
    item: Item,
    sender: Responsible,
    pending_transfer: PendingTransfer | None,
    transfer_expiration_hours: int,
    notes: str,
    selected_to_responsible_id: int | None,
    error: str | None = None,
    status: int = 200,
) -> HttpResponse:
    """Render the transfer create/update template."""

    ctx: dict[str, object] = {
        "item": item,
        "responsible": sender,
        "responsibles": Responsible.transfer_receiver_candidates(sender),
        "pending_transfer": pending_transfer,
        "transfer_expiration_hours": transfer_expiration_hours,
        "notes": notes,
        "selected_to_responsible_id": selected_to_responsible_id,
    }
    if error is not None:
        ctx["error"] = error
    return render(request, "inventory/transfer_create.html", ctx, status=status)


def parse_transfer_receiver_or_render_error(
    request: HttpRequest,
    *,
    item: Item,
    sender: Responsible,
    pending_transfer: PendingTransfer | None,
    transfer_expiration_hours: int,
    notes: str,
) -> tuple[Responsible | None, HttpResponse | None]:
    """
    Parse POST ``to_responsible_id`` or return a 400 response with the form.

    Domain validation is delegated to
    :meth:`Responsible.resolve_transfer_receiver_from_form`.
    """

    from django.core.exceptions import ValidationError

    try:
        receiver = Responsible.resolve_transfer_receiver_from_form(
            request.POST.get("to_responsible_id"), sender=sender
        )
    except ValidationError as exc:
        return None, render_transfer_form(
            request,
            item=item,
            sender=sender,
            pending_transfer=pending_transfer,
            transfer_expiration_hours=transfer_expiration_hours,
            notes=notes,
            selected_to_responsible_id=None,
            error=validation_error_user_message(exc),
            status=400,
        )
    return receiver, None
