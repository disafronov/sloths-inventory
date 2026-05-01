from __future__ import annotations

from datetime import timedelta
from typing import TypeVar

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import OuterRef, QuerySet, Subquery
from django.db.models.query_utils import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from catalogs.models import Location, Responsible

from .models import Item, Operation, PendingTransfer

TItem = TypeVar("TItem", bound=Item)


def _apply_item_search(qs: QuerySet[TItem], *, query: str) -> QuerySet[TItem]:
    """
    Apply a user-facing search query to an item queryset.

    The UI needs a lightweight search that works without introducing additional
    entities (e.g. dedicated search indexes). We scope it to the most useful
    identifying fields.
    """

    query = query.strip()
    if not query:
        return qs

    return qs.filter(
        Q(inventory_number__icontains=query)
        | Q(serial_number__icontains=query)
        | Q(device__manufacturer__name__icontains=query)
        | Q(device__model__name__icontains=query)
    )


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


_MY_ITEMS_LIST_KINDS = frozenset({"all", "incoming", "owned", "outgoing"})


def _parse_my_items_list_kind(request: HttpRequest) -> str:
    """
    Parse the optional `kind` query parameter for the "My items" list.

    Values: ``all`` (default), ``incoming``, ``owned``, ``outgoing``.
    Unknown values fall back to ``all`` so bookmarked URLs stay safe.
    """

    raw = (request.GET.get("kind") or "").strip().lower()
    if raw in _MY_ITEMS_LIST_KINDS:
        return raw
    return "all"


def _get_active_transfer_for_item(item: Item) -> PendingTransfer | None:
    """
    Return the active pending transfer for an item, if any.

    Transfers are separate from `Operation` history and only become part of the
    inventory state when accepted (at which point a new `Operation` is created).
    """

    return (
        PendingTransfer.objects.filter(item=item)
        .filter(accepted_at__isnull=True, cancelled_at__isnull=True)
        .select_related("from_responsible", "to_responsible")
        .order_by("-created_at", "-id")
        .first()
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
                "incoming_transfers": [],
                "outgoing_transfers": [],
                "query": "",
                "list_kind": "all",
            },
        )

    query = request.GET.get("q", "")
    list_kind = _parse_my_items_list_kind(request)
    items = _apply_item_search(_items_owned_by(responsible), query=query)

    latest_location_name = (
        Operation.objects.filter(item_id=OuterRef("item_id"))
        .order_by("-created_at", "-id")
        .values("location__name")[:1]
    )
    latest_status_name = (
        Operation.objects.filter(item_id=OuterRef("item_id"))
        .order_by("-created_at", "-id")
        .values("status__name")[:1]
    )

    base_transfers_qs = PendingTransfer.objects.filter(
        accepted_at__isnull=True,
        cancelled_at__isnull=True,
    ).select_related(
        "item",
        "item__device",
        "item__device__category",
        "item__device__type",
        "item__device__manufacturer",
        "item__device__model",
        "from_responsible",
        "to_responsible",
    )
    base_transfers_qs = base_transfers_qs.annotate(
        current_location=Subquery(latest_location_name),
        current_status=Subquery(latest_status_name),
    )
    incoming_transfers = base_transfers_qs.filter(to_responsible=responsible).order_by(
        "-created_at", "-id"
    )
    outgoing_transfers = base_transfers_qs.filter(
        from_responsible=responsible
    ).order_by("-created_at", "-id")

    # If an item has an active transfer offer, it must not appear both as a
    # regular "owned" card and as a transfer card on the same page.
    #
    # NOTE: Avoid QuerySet.union() here: SQLite forbids ORDER BY in subqueries of
    # compound statements, and `incoming_transfers` / `outgoing_transfers` are
    # ordered for UI rendering.
    transfer_item_ids = (
        PendingTransfer.objects.filter(
            accepted_at__isnull=True,
            cancelled_at__isnull=True,
        )
        .filter(Q(to_responsible=responsible) | Q(from_responsible=responsible))
        .values_list("item_id", flat=True)
        .distinct()
    )
    items = items.exclude(id__in=transfer_item_ids)

    if list_kind == "incoming":
        items = items.none()
        outgoing_transfers = outgoing_transfers.none()
    elif list_kind == "owned":
        incoming_transfers = incoming_transfers.none()
        outgoing_transfers = outgoing_transfers.none()
    elif list_kind == "outgoing":
        items = items.none()
        incoming_transfers = incoming_transfers.none()

    return render(
        request,
        "inventory/my_items.html",
        {
            "responsible": responsible,
            "items": items,
            "query": query,
            "list_kind": list_kind,
            "incoming_transfers": incoming_transfers,
            "outgoing_transfers": outgoing_transfers,
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
                "incoming_transfers": [],
                "outgoing_transfers": [],
                "query": "",
            },
        )

    last_on_me_created_at = (
        Operation.objects.filter(item_id=OuterRef("pk"), responsible=responsible)
        .order_by("-created_at", "-id")
        .values("created_at")[:1]
    )

    current_items = _items_owned_by(responsible).values("pk")
    query = request.GET.get("q", "")
    items = (
        _items_with_device_relations()
        .filter(operation__responsible=responsible)
        .exclude(pk__in=current_items)
        .distinct()
        .annotate(last_on_me_created_at=Subquery(last_on_me_created_at))
        .order_by("-last_on_me_created_at", "inventory_number")
    )
    items = _apply_item_search(items, query=query)

    # Active offers for items on this page: same cards as "My items" (gradient,
    # party plaque). Typical case is an incoming offer back to a former owner.
    latest_location_name = (
        Operation.objects.filter(item_id=OuterRef("item_id"))
        .order_by("-created_at", "-id")
        .values("location__name")[:1]
    )
    latest_status_name = (
        Operation.objects.filter(item_id=OuterRef("item_id"))
        .order_by("-created_at", "-id")
        .values("status__name")[:1]
    )
    base_transfers_qs = (
        PendingTransfer.objects.filter(
            accepted_at__isnull=True,
            cancelled_at__isnull=True,
        )
        .filter(item_id__in=Subquery(items.values("pk")))
        .filter(Q(to_responsible=responsible) | Q(from_responsible=responsible))
        .select_related(
            "item",
            "item__device",
            "item__device__category",
            "item__device__type",
            "item__device__manufacturer",
            "item__device__model",
            "from_responsible",
            "to_responsible",
        )
    )
    base_transfers_qs = base_transfers_qs.annotate(
        current_location=Subquery(latest_location_name),
        current_status=Subquery(latest_status_name),
    )
    incoming_transfers = base_transfers_qs.filter(to_responsible=responsible).order_by(
        "-created_at", "-id"
    )
    outgoing_transfers = base_transfers_qs.filter(
        from_responsible=responsible
    ).order_by("-created_at", "-id")
    transfer_item_ids = base_transfers_qs.values_list("item_id", flat=True).distinct()
    items = items.exclude(id__in=transfer_item_ids)

    return render(
        request,
        "inventory/previous_items.html",
        {
            "responsible": responsible,
            "items": items,
            "query": query,
            "incoming_transfers": incoming_transfers,
            "outgoing_transfers": outgoing_transfers,
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
    is_owner = item is not None
    if item is None:
        # The receiver of an active transfer offer may open the item page to review
        # the offer and accept it. They are not an owner yet.
        pending_for_me = (
            PendingTransfer.objects.filter(
                item_id=item_id,
                to_responsible=responsible,
                accepted_at__isnull=True,
                cancelled_at__isnull=True,
            )
            .order_by("-created_at", "-id")
            .first()
        )
        if pending_for_me is not None and pending_for_me.is_active:
            item = get_object_or_404(_items_with_device_relations(), pk=item_id)
            operations = (
                Operation.objects.filter(item=item)
                .select_related("status", "responsible", "location")
                .order_by("-created_at", "-id")
            )
            if not operations.exists():
                raise Http404  # pragma: no cover
        else:
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
                    "Invariant violation: former-owner flow requires "
                    "a handoff operation"
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

    pending_transfer = _get_active_transfer_for_item(item)
    can_see_transfer = False
    if pending_transfer is not None:
        can_see_transfer = (
            is_owner or pending_transfer.to_responsible_id == responsible.pk
        )
        if not can_see_transfer:
            pending_transfer = None

    return render(
        request,
        "inventory/item_history.html",
        {
            "item": item,
            "operations": operations,
            "is_owner": is_owner,
            "pending_transfer": pending_transfer,
        },
    )


@login_required
def change_location(request: HttpRequest, *, item_id: int) -> HttpResponse:
    responsible = _get_responsible_for_user(request)
    if responsible is None:
        raise Http404

    item = _items_owned_by(responsible).filter(pk=item_id).first()
    if item is None:
        raise Http404

    current_op = item.current_operation
    if current_op is None:
        raise Http404  # pragma: no cover

    if request.method == "POST":
        location_id = request.POST.get("location_id")
        if not location_id:
            raise Http404
        try:
            location = Location.objects.get(pk=location_id)
        except Location.DoesNotExist:
            raise Http404

        if location.pk == current_op.location_id:
            locations = Location.objects.order_by("name")
            return render(
                request,
                "inventory/change_location.html",
                {
                    "item": item,
                    "locations": locations,
                    "current_location": current_op.location,
                    "error": _("New location must be different from current location."),
                },
                status=400,
            )

        Operation.objects.create(
            item=item,
            status=current_op.status,
            responsible=responsible,
            location=location,
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
        },
    )


@login_required
def create_transfer(request: HttpRequest, *, item_id: int) -> HttpResponse:
    """
    Create a pending transfer offer for an item.

    Only the current owner may initiate a transfer. Ownership is changed only
    when the receiver confirms the handoff (see `accept_transfer`).
    """

    responsible = _get_responsible_for_user(request)
    if responsible is None:
        raise Http404

    item = _items_owned_by(responsible).filter(pk=item_id).first()
    if item is None:
        raise Http404

    current_op = item.current_operation
    if current_op is None:
        raise Http404  # pragma: no cover

    transfer_expiration_hours = max(
        0,
        int(getattr(settings, "INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS", 168)),
    )

    pending_transfer = _get_active_transfer_for_item(item)
    if pending_transfer is not None:
        return render(
            request,
            "inventory/transfer_create.html",
            {
                "item": item,
                "responsible": responsible,
                "responsibles": [],
                "pending_transfer": pending_transfer,
                "transfer_expiration_hours": transfer_expiration_hours,
            },
        )

    if request.method == "POST":
        to_id = request.POST.get("to_responsible_id")
        if not to_id:
            raise Http404
        try:
            to_responsible = Responsible.objects.get(pk=int(to_id))
        except (Responsible.DoesNotExist, ValueError):
            raise Http404
        if to_responsible.pk == responsible.pk:
            raise Http404

        expires_at = None
        if transfer_expiration_hours > 0:
            expires_at = timezone.now() + timedelta(hours=transfer_expiration_hours)

        PendingTransfer.objects.create(
            item=item,
            from_responsible=responsible,
            to_responsible=to_responsible,
            expires_at=expires_at,
        )
        return redirect("inventory:item-history", item_id=item.pk)

    responsibles = (
        Responsible.objects.exclude(pk=responsible.pk)
        .order_by("last_name", "first_name", "middle_name")
        .all()
    )
    return render(
        request,
        "inventory/transfer_create.html",
        {
            "item": item,
            "responsible": responsible,
            "responsibles": responsibles,
            "pending_transfer": None,
            "transfer_expiration_hours": transfer_expiration_hours,
        },
    )


@login_required
def accept_transfer(request: HttpRequest, *, transfer_id: int) -> HttpResponse:
    """
    Accept a pending transfer and append an ownership-changing operation.

    Only the transfer receiver may accept. This is the authoritative confirmation
    path that changes the current owner (via a new `Operation`).

    The new operation keeps `notes` empty: the handoff is implied by the new
    responsible and by `PendingTransfer.accepted_at`, without duplicating prose
    in the operation timeline.
    """

    if request.method != "POST":
        raise Http404

    responsible = _get_responsible_for_user(request)
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

    with transaction.atomic():
        Item.objects.select_for_update().only("id").get(pk=transfer.item_id)
        transfer = PendingTransfer.objects.select_for_update().get(pk=transfer.pk)
        if not transfer.is_active:
            raise Http404

        item = Item.objects.get(pk=transfer.item_id)
        current_op = item.current_operation
        if current_op is None:
            raise Http404  # pragma: no cover

        Operation.objects.create(
            item=item,
            status=current_op.status,
            responsible=transfer.to_responsible,
            location=current_op.location,
            notes="",
        )
        transfer.accepted_at = timezone.now()
        transfer.save()

    return redirect("inventory:item-history", item_id=transfer.item_id)


@login_required
def cancel_transfer(request: HttpRequest, *, transfer_id: int) -> HttpResponse:
    """
    Cancel a pending transfer.

    The sender may cancel their offer; the receiver may decline it.
    """

    if request.method != "POST":
        raise Http404

    responsible = _get_responsible_for_user(request)
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
    if responsible.pk not in {transfer.from_responsible_id, transfer.to_responsible_id}:
        raise Http404

    transfer.cancelled_at = timezone.now()
    transfer.save()
    return redirect("inventory:item-history", item_id=transfer.item_id)
