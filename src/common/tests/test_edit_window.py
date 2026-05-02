"""Tests for ``common.edit_window`` timing helpers."""

from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from common.edit_window import is_within_inventory_correction_window


@pytest.mark.django_db
@override_settings(INVENTORY_CORRECTION_WINDOW_MINUTES=10)
def test_is_within_inventory_correction_window_uses_explicit_reference_time() -> None:
    """Branch where ``reference_time`` is provided (not ``None``)."""

    anchor = timezone.now() - timedelta(minutes=5)
    ref = timezone.now()
    assert is_within_inventory_correction_window(anchor, reference_time=ref) is True
