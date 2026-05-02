"""
Inventory UI page queryset builders and related helpers.

Keeps HTTP views thin: list views import builders from this module while domain
rules stay on models.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import OuterRef, Q, QuerySet, Subquery

from catalogs.models import Responsible
from inventory.list_query_helpers import (
    latest_operation_location_name_subquery,
    latest_operation_status_name_subquery,
)
from inventory.models.item import Item
from inventory.models.operation import Operation
from inventory.models.pending_transfer import PendingTransfer

MY_ITEMS_LIST_KINDS = frozenset({"all", "incoming", "owned", "outgoing"})


def parse_my_items_list_kind(raw: str) -> str:
    """
    Parse the optional ``kind`` query parameter for the "My items" list.

    Values: ``all`` (default), ``incoming``, ``owned``, ``outgoing``. Unknown
    values fall back to ``all`` so bookmarked URLs stay safe.
    """

    value = (raw or "").strip().lower()
    if value in MY_ITEMS_LIST_KINDS:
        return value
    return "all"


def pending_transfer_expiration_hours() -> int:
    """Return configured pending-transfer auto-expiration window in hours."""

    from django.conf import settings

    return max(
        0,
        int(getattr(settings, "INVENTORY_PENDING_TRANSFER_EXPIRATION_HOURS", 168)),
    )


@dataclass(frozen=True)
class MyItemsPageData:
    """Querysets and metadata for the "My items" inventory page."""

    items: QuerySet[Item]
    incoming_transfers: QuerySet[PendingTransfer]
    outgoing_transfers: QuerySet[PendingTransfer]


@dataclass(frozen=True)
class PreviousItemsPageData:
    """Querysets for the "Previously held" inventory page."""

    items: QuerySet[Item]
    incoming_transfers: QuerySet[PendingTransfer]
    outgoing_transfers: QuerySet[PendingTransfer]


@dataclass(frozen=True)
class ItemHistoryContext:
    """Authorized item history payload for a ``Responsible`` viewer."""

    item: Item
    operations: QuerySet[Operation]
    is_owner: bool
    pending_transfer: PendingTransfer | None


def build_my_items_page_data(
    responsible: Responsible, *, query: str, list_kind: str
) -> MyItemsPageData:
    """
    Build querysets for the "My items" page (owned items and transfer cards).

    Applies the same exclusion rules as the user-facing UI: items with an active
    transfer offer involving this responsible are listed only as transfer cards,
    not as duplicate owned rows.

    Owned ``Item`` rows are annotated with ``current_location`` and ``current_status``
    (latest operation display strings) so list templates do not trigger one query
    per row via :class:`~inventory.models.item.Item` descriptors.
    """

    items = Item.objects.apply_search(query).owned_by(responsible)

    latest_location_name = latest_operation_location_name_subquery(item_ref="item_id")
    latest_status_name = latest_operation_status_name_subquery(item_ref="item_id")

    base_transfers_qs = (
        PendingTransfer.offers_visible_in_ui()
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
        .annotate(
            current_location=latest_location_name,
            current_status=latest_status_name,
        )
    )
    incoming_transfers = base_transfers_qs.filter(to_responsible=responsible).order_by(
        "-created_at", "-id"
    )
    outgoing_transfers = base_transfers_qs.filter(
        from_responsible=responsible
    ).order_by("-created_at", "-id")

    transfer_item_ids = (
        PendingTransfer.offers_visible_in_ui()
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

    # Annotate like transfer cards so ``my_items.html`` does not N+1 on descriptors.
    item_loc = latest_operation_location_name_subquery(item_ref="pk")
    item_stat = latest_operation_status_name_subquery(item_ref="pk")
    items = items.annotate(current_location=item_loc, current_status=item_stat)

    return MyItemsPageData(
        items=items,
        incoming_transfers=incoming_transfers,
        outgoing_transfers=outgoing_transfers,
    )


def build_previous_items_page_data(
    responsible: Responsible, *, query: str
) -> PreviousItemsPageData:
    """
    Build querysets for items this responsible once held but no longer owns.

    Includes the same transfer-card annotations as :func:`build_my_items_page_data`
    for items on this page.
    """

    last_on_me_created_at = (
        Operation.objects.filter(item_id=OuterRef("pk"), responsible=responsible)
        .order_by("-created_at", "-id")
        .values("created_at")[:1]
    )

    current_items = Item.objects.owned_by(responsible).values("pk")
    items = (
        Item.objects.with_device_relations()
        .filter(operation__responsible=responsible)
        .exclude(pk__in=current_items)
        .distinct()
        .annotate(last_on_me_created_at=Subquery(last_on_me_created_at))
        .order_by("-last_on_me_created_at", "inventory_number")
    )
    items = items.apply_search(query)

    latest_location_name = latest_operation_location_name_subquery(item_ref="item_id")
    latest_status_name = latest_operation_status_name_subquery(item_ref="item_id")
    base_transfers_qs = (
        PendingTransfer.offers_visible_in_ui()
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
        current_location=latest_location_name,
        current_status=latest_status_name,
    )
    incoming_transfers = base_transfers_qs.filter(to_responsible=responsible).order_by(
        "-created_at", "-id"
    )
    outgoing_transfers = base_transfers_qs.filter(
        from_responsible=responsible
    ).order_by("-created_at", "-id")
    transfer_item_ids = base_transfers_qs.values_list("item_id", flat=True).distinct()
    items = items.exclude(id__in=transfer_item_ids)

    return PreviousItemsPageData(
        items=items,
        incoming_transfers=incoming_transfers,
        outgoing_transfers=outgoing_transfers,
    )


def resolve_item_history_context(
    responsible: Responsible, item_id: int
) -> ItemHistoryContext | None:
    """
    Resolve item, operations, and optional pending transfer for the history page.

    Returns ``None`` when the viewer must not see this item (caller maps to
    HTTP 404). Implements owner, incoming-offer receiver, and former-owner slice
    rules in one place so views and other entry points stay aligned.
    """

    item_qs = Item.objects.owned_by(responsible)
    item = item_qs.filter(pk=item_id).first()
    is_owner = item is not None

    if item is None:
        pending_for_me = (
            PendingTransfer.offers_visible_in_ui()
            .filter(
                item_id=item_id,
                to_responsible=responsible,
            )
            .order_by("-created_at", "-id")
            .first()
        )
        if pending_for_me is not None and pending_for_me.is_active:
            try:
                item = Item.objects.with_device_relations().get(pk=item_id)
            except Item.DoesNotExist:  # pragma: no cover
                # Defensive: ``item_id`` may race with concurrent deletions.
                return None
            operations = (
                Operation.objects.filter(item=item)
                .select_related("status", "responsible", "location")
                .order_by("-created_at", "-id")
            )
            if not operations.exists():
                return None
        else:
            last_mine = (
                Operation.objects.filter(item_id=item_id, responsible=responsible)
                .order_by("-created_at", "-id")
                .first()
            )
            if last_mine is None:
                return None

            try:
                item = Item.objects.with_device_relations().get(pk=item_id)
            except Item.DoesNotExist:  # pragma: no cover
                # Defensive: same race window as the pending-receiver branch.
                return None

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

    pending_transfer = PendingTransfer.objects.active_offer_for_item(item)
    if pending_transfer is not None:
        can_see_transfer = (
            is_owner or pending_transfer.to_responsible_id == responsible.pk
        )
        if not can_see_transfer:
            pending_transfer = None

    return ItemHistoryContext(
        item=item,
        operations=operations,
        is_owner=is_owner,
        pending_transfer=pending_transfer,
    )
