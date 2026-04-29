from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, QuerySet, Subquery
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from catalogs.models import Responsible

from .models import Item, Operation


def _get_responsible_for_user(request: HttpRequest) -> Responsible | None:
    """
    Resolve the domain \"Responsible\" profile for the authenticated user.

    The user-facing inventory UI is scoped by `Responsible.user`. If the account
    is not linked, the UI must not error: it should show a helpful message and
    no data.
    """

    if not request.user.is_authenticated:
        return None
    return Responsible.objects.filter(user=request.user).first()


def _items_owned_by(responsible: Responsible) -> QuerySet[Item]:
    latest_responsible_id = (
        Operation.objects.filter(item_id=OuterRef("pk"))
        .order_by("-created_at", "-id")
        .values("responsible_id")[:1]
    )

    return (
        Item.objects.annotate(_latest_responsible_id=Subquery(latest_responsible_id))
        .filter(_latest_responsible_id=responsible.pk)
        .select_related(
            "device",
            "device__category",
            "device__type",
            "device__manufacturer",
            "device__model",
        )
    )


@login_required
def my_items(request: HttpRequest) -> HttpResponse:
    responsible = _get_responsible_for_user(request)
    if responsible is None:
        return render(
            request,
            "inventory/my_items.html",
            {
                "responsible": None,
                "items": [],
            },
        )

    items = _items_owned_by(responsible)
    return render(
        request,
        "inventory/my_items.html",
        {
            "responsible": responsible,
            "items": items,
        },
    )


@login_required
def item_history(request: HttpRequest, *, item_id: int) -> HttpResponse:
    responsible = _get_responsible_for_user(request)
    if responsible is None:
        # Hide existence details for users without a linked Responsible profile.
        raise Http404  # pragma: no cover

    item = get_object_or_404(_items_owned_by(responsible), pk=item_id)

    operations = (
        Operation.objects.filter(item=item)
        .select_related("status", "responsible", "location")
        .order_by("-created_at", "-id")
    )
    return render(
        request,
        "inventory/item_history.html",
        {
            "item": item,
            "operations": operations,
        },
    )
