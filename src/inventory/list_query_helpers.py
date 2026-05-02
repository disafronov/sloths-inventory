"""
Reusable ORM fragments for inventory list pages.

Centralizes correlated subqueries for "latest operation per item" so My items,
Previously held, and transfer cards stay aligned and do not duplicate ordering
logic (``-created_at``, ``-id`` tiebreaker matches :class:`~inventory.models.Item`
journal semantics).

Imports of concrete models are deferred inside callables to keep Django app
loading order predictable when this module is imported from page builders.
"""

from __future__ import annotations

from django.db.models import OuterRef, Subquery


def _latest_operation_subquery(*, item_ref: str, field: str) -> Subquery:
    from inventory.models.operation import Operation

    return Subquery(
        Operation.objects.filter(item_id=OuterRef(item_ref))
        .order_by("-created_at", "-id")
        .values(field)[:1]
    )


def latest_operation_location_name_subquery(*, item_ref: str) -> Subquery:
    """
    Return a subquery yielding the latest operation's location name for ``item_ref``.

    ``item_ref`` is the :class:`~django.db.models.OuterRef` lookup name on the
    outer queryset (``\"pk\"`` for :class:`~inventory.models.Item` rows,
    ``\"item_id\"`` for :class:`~inventory.models.PendingTransfer` rows).
    """

    return _latest_operation_subquery(item_ref=item_ref, field="location__name")


def latest_operation_status_name_subquery(*, item_ref: str) -> Subquery:
    """
    Return a subquery yielding the latest operation's status name for ``item_ref``.

    See :func:`latest_operation_location_name_subquery` for ``item_ref`` meaning.
    """

    return _latest_operation_subquery(item_ref=item_ref, field="status__name")
