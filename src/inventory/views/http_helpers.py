"""
HTTP-only helpers shared by inventory view modules (forms, template rendering).
"""

from typing import Any

from django import forms
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from catalogs.models import Responsible
from inventory.models import Item, PendingTransfer


class CreateTransferForm(forms.Form):
    to_responsible_id = forms.CharField(required=False)
    notes = forms.CharField(required=False, strip=True)

    def __init__(self, *args: Any, sender: Responsible, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._sender = sender

    def clean_to_responsible_id(self) -> Responsible:
        return Responsible.resolve_transfer_receiver_from_form(
            self.cleaned_data.get("to_responsible_id"), sender=self._sender
        )


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
