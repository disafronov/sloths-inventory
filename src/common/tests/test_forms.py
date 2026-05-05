"""Tests for common forms."""

import pytest
from django.contrib.auth import get_user_model

from common.forms import EmailChangeForm

User = get_user_model()


@pytest.mark.django_db
def test_email_change_form_clean_none_data():
    """Form clean should handle missing cleaned_data."""
    form = EmailChangeForm(user=User())
    form.cleaned_data = None
    assert form.clean() == {}
