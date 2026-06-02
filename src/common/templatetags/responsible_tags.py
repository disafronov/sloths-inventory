from __future__ import annotations

from typing import Optional

from django import template
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from catalogs.models import Responsible

register = template.Library()


@register.simple_tag
def current_responsible(
    user: AbstractBaseUser | AnonymousUser,
) -> Optional[Responsible]:
    """Return the Responsible linked to the given user, or None."""
    return Responsible.linked_profile_for_user(user)
