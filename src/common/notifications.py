"""Context processor that pushes persistent conditions to Django messages.

Replaces hard-coded banner divs in base.html with the standard
messages framework, so all on-page notifications use the same mechanism.
"""

from django.contrib import messages
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext


def persistent_notifications(request: HttpRequest) -> dict[str, object]:
    """Check per-request conditions and add messages when they apply.

    Conditions are mutually exclusive by descending severity:

    1. No email → ``messages.error`` (blocks responsible-linking and notifications).
    2. No linked responsible → ``messages.warning`` (most pages are empty).
    """
    user = request.user
    if not user.is_authenticated:
        return {}

    if not user.email:
        url = reverse("common:profile")
        msg = format_html(
            '{} <a href="{}#email">{}</a> — {}.',
            gettext("Your account has no email address yet."),
            url,
            gettext("Add one in your profile"),
            gettext(
                "it is required to link a responsible person and receive notifications"
            ),
        )
        messages.error(request, msg)
        return {}

    if not hasattr(user, "responsible") or user.responsible is None:
        if user.has_perm("catalogs.change_responsible"):
            no_responsible_msg = gettext(
                "Your account is not linked to a responsible person profile."
            )
        else:
            no_responsible_msg = gettext(
                "Your account is not linked to a responsible person profile yet. "
                "Please contact the administration."
            )
        messages.warning(request, no_responsible_msg)

    return {}
