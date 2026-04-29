from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, QuerySet, Subquery
from django.db.models.query_utils import Q
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


def _items_with_device_relations() -> QuerySet[Item]:
    """
    Shared base queryset for item list/detail views.

    Keeping this centralized avoids subtle N+1 regressions when templates render
    `item.device` (which touches multiple FK relations).
    """

    return Item.objects.select_related(
        "device",
        "device__category",
        "device__type",
        "device__manufacturer",
        "device__model",
    )


def _items_owned_by(responsible: Responsible) -> QuerySet[Item]:
    latest_responsible_id = (
        Operation.objects.filter(item_id=OuterRef("pk"))
        .order_by("-created_at", "-id")
        .values("responsible_id")[:1]
    )

    return (
        _items_with_device_relations()
        .annotate(_latest_responsible_id=Subquery(latest_responsible_id))
        .filter(_latest_responsible_id=responsible.pk)
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
def previous_items(request: HttpRequest) -> HttpResponse:
    responsible = _get_responsible_for_user(request)
    if responsible is None:
        return render(
            request,
            "inventory/previous_items.html",
            {
                "responsible": None,
                "items": [],
            },
        )

    last_on_me_created_at = (
        Operation.objects.filter(item_id=OuterRef("pk"), responsible=responsible)
        .order_by("-created_at", "-id")
        .values("created_at")[:1]
    )

    current_items = _items_owned_by(responsible).values("pk")
    items = (
        _items_with_device_relations()
        .filter(operation__responsible=responsible)
        .exclude(pk__in=current_items)
        .distinct()
        .annotate(last_on_me_created_at=Subquery(last_on_me_created_at))
        .order_by("-last_on_me_created_at", "inventory_number")
    )

    return render(
        request,
        "inventory/previous_items.html",
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

    # Current owner sees the entire history.
    item_qs = _items_owned_by(responsible)
    item = item_qs.filter(pk=item_id).first()
    if item is None:
        # Former owners may only see the history up to their last responsibility,
        # plus one "handoff" operation after they transferred the item away.
        #
        # Rationale: this gives the former owner enough context to understand when
        # and to whom the item was handed off, while limiting how much of the
        # subsequent history is exposed.
        last_mine = (
            Operation.objects.filter(item_id=item_id, responsible=responsible)
            .order_by("-created_at", "-id")
            .first()
        )
        if last_mine is None:
            raise Http404

        item = get_object_or_404(_items_with_device_relations(), pk=item_id)

        handoff = (
            Operation.objects.filter(item_id=item_id)
            .filter(
                Q(created_at__gt=last_mine.created_at)
                | Q(created_at=last_mine.created_at, id__gt=last_mine.id)
            )
            .order_by("created_at", "id")
            .first()
        )
        if handoff is None:
            raise AssertionError(
                "Invariant violation: former-owner flow requires a handoff operation"
            )
        ops_filter = Q(created_at__lt=last_mine.created_at) | Q(
            created_at=last_mine.created_at, id__lte=last_mine.id
        )
        ops_filter |= Q(pk=handoff.pk)

        operations = (
            Operation.objects.filter(item=item)
            .filter(ops_filter)
            .select_related("status", "responsible", "location")
            .order_by("-created_at", "-id")
        )
    else:
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
