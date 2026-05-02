"""
Shared correction-window timing for inventory master data.

``INVENTORY_CORRECTION_WINDOW_MINUTES`` applies to operations, items, and catalog
rows once they participate in live data (see each model's ``clean()``).
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.translation import ngettext


def catalog_entry_correction_window_expired_user_message() -> str:
    """
    Return the message when a referenced catalog-style row is in use and its
    ``updated_at`` correction window has closed.

    Used by ``CatalogCorrectionWindowMixin`` and ``Item`` so gettext keeps a single
    msgid (translations live under ``common/locale`` only).
    """

    minutes = inventory_correction_window_minutes()
    return str(
        ngettext(
            "This catalog entry is in use. "
            "The correction window (%(minutes)d minute) has expired. "
            "To make changes, contact an administrator.",
            "This catalog entry is in use. "
            "The correction window (%(minutes)d minutes) has expired. "
            "To make changes, contact an administrator.",
            minutes,
        )
        % {"minutes": minutes}
    )


def inventory_correction_window_minutes() -> int:
    """Return the configured correction window length in minutes (default 10)."""

    return int(getattr(settings, "INVENTORY_CORRECTION_WINDOW_MINUTES", 10))


def is_within_inventory_correction_window(
    anchor_at: datetime,
    *,
    reference_time: datetime | None = None,
) -> bool:
    """
    Return whether ``anchor_at`` is still inside the correction window relative to
    ``reference_time`` (defaults to ``timezone.now()``).
    """

    if reference_time is None:
        reference_time = timezone.now()
    correction_window = timedelta(minutes=inventory_correction_window_minutes())
    return reference_time - anchor_at <= correction_window
