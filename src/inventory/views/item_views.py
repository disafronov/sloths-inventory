"""Item detail and location change views."""

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from catalogs.models import Location, Responsible
from inventory.models import Item, resolve_item_history_context
from inventory.presentation import validation_error_user_message


class ChangeLocationForm(forms.Form):
    location_id = forms.IntegerField(
        error_messages={"required": _("New location is required.")}
    )
    notes = forms.CharField(required=False, strip=True)


def _render_change_location(
    request: HttpRequest,
    item: Item,
    current_location: Location,
    *,
    error: str = "",
    notes: str = "",
    status: int = 200,
) -> HttpResponse:
    return render(
        request,
        "inventory/change_location.html",
        {
            "item": item,
            "locations": Location.objects.order_by("name"),
            "current_location": current_location,
            "error": error,
            "notes": notes,
        },
        status=status,
    )


@login_required
def item_history(request: HttpRequest, *, item_id: int) -> HttpResponse:
    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        raise Http404  # pragma: no cover

    ctx = resolve_item_history_context(responsible, item_id)
    if ctx is None:
        raise Http404

    return render(
        request,
        "inventory/item_history.html",
        {
            "item": ctx.item,
            "responsible": responsible,
            "operations": ctx.operations,
            "is_owner": ctx.is_owner,
            "pending_transfer": ctx.pending_transfer,
            "accept_journal_head_operation_id": ctx.accept_journal_head_operation_id,
        },
    )


@login_required
def change_location(request: HttpRequest, *, item_id: int) -> HttpResponse:
    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        raise Http404

    item = Item.objects.owned_by(responsible).filter(pk=item_id).first()
    if item is None:
        raise Http404

    current_op = item.current_operation
    if current_op is None:
        raise Http404  # pragma: no cover

    if request.method == "POST":
        form = ChangeLocationForm(request.POST)
        if not form.is_valid():
            error = str(form.errors.get("location_id", [""])[0])
            return _render_change_location(
                request,
                item,
                current_op.location,
                error=error,
                notes=(request.POST.get("notes") or "").strip(),
                status=400,
            )

        location_id: int = form.cleaned_data["location_id"]
        notes: str = form.cleaned_data["notes"]

        try:
            location = Location.objects.get(pk=location_id)
        except Location.DoesNotExist:
            raise Http404

        try:
            item.change_location(
                responsible=responsible, location=location, notes=notes
            )
        except ValidationError as exc:
            return _render_change_location(
                request,
                item,
                current_op.location,
                error=validation_error_user_message(exc),
                notes=notes,
                status=400,
            )

        return redirect("inventory:item-history", item_id=item.pk)

    return _render_change_location(request, item, current_op.location, notes="")
