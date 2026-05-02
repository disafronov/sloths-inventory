"""Item detail and location change views."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from catalogs.models import Location, Responsible
from inventory.models import Item, resolve_item_history_context
from inventory.presentation import validation_error_user_message


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
        location_id = request.POST.get("location_id")
        notes = (request.POST.get("notes") or "").strip()
        if not location_id:
            locations = Location.objects.order_by("name")
            return render(
                request,
                "inventory/change_location.html",
                {
                    "item": item,
                    "locations": locations,
                    "current_location": current_op.location,
                    "error": _("New location is required."),
                    "notes": notes,
                },
                status=400,
            )
        try:
            location = Location.objects.get(pk=location_id)
        except Location.DoesNotExist:
            raise Http404

        try:
            item.change_location(
                responsible=responsible, location=location, notes=notes
            )
        except ValidationError as exc:
            locations = Location.objects.order_by("name")
            return render(
                request,
                "inventory/change_location.html",
                {
                    "item": item,
                    "locations": locations,
                    "current_location": current_op.location,
                    "error": validation_error_user_message(exc),
                    "notes": notes,
                },
                status=400,
            )

        return redirect("inventory:item-history", item_id=item.pk)

    locations = Location.objects.order_by("name")
    return render(
        request,
        "inventory/change_location.html",
        {
            "item": item,
            "locations": locations,
            "current_location": current_op.location,
            "notes": "",
        },
    )
