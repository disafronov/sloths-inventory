"""
Inventory domain models and UI queryset builders.

Submodules split the former monolith for maintainability; import from
``inventory.models`` remains the public API (Django discovers models via this
package).
"""

from inventory.models.item import Item, ItemManager, ItemQuerySet
from inventory.models.operation import Operation
from inventory.models.pages import (
    MY_ITEMS_LIST_KINDS,
    ItemHistoryContext,
    MyItemsPageData,
    PreviousItemsPageData,
    build_my_items_page_data,
    build_previous_items_page_data,
    parse_my_items_list_kind,
    pending_transfer_expiration_hours,
    resolve_item_history_context,
)
from inventory.models.pending_transfer import (
    PendingTransfer,
    PendingTransferManager,
    PendingTransferQuerySet,
)

__all__ = [
    "MY_ITEMS_LIST_KINDS",
    "Item",
    "ItemHistoryContext",
    "ItemManager",
    "ItemQuerySet",
    "MyItemsPageData",
    "Operation",
    "PendingTransfer",
    "PendingTransferManager",
    "PendingTransferQuerySet",
    "PreviousItemsPageData",
    "build_my_items_page_data",
    "build_previous_items_page_data",
    "parse_my_items_list_kind",
    "pending_transfer_expiration_hours",
    "resolve_item_history_context",
]
