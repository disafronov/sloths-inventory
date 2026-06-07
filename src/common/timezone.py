"""Timezone handling utilities and middleware.

This module provides middleware to activate timezones based on a cookie
and a context processor to expose timezone detection status to templates.
"""

from collections.abc import Callable
from urllib.parse import unquote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone


class TimezoneMiddleware:
    """Middleware to activate the user's preferred timezone from a cookie.

    The timezone name is expected to be stored in a 'timezone' cookie,
    URL-encoded. If the cookie is present and valid, the timezone is activated
    for the duration of the request.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        tzname = unquote(request.COOKIES.get("timezone", ""))
        if tzname:
            try:
                timezone.activate(ZoneInfo(tzname))
                # We attach this attribute dynamically to the request object
                # to communicate detection status to the context processor.
                request.timezone_detected = True  # type: ignore[attr-defined]
            except ZoneInfoNotFoundError, KeyError:
                # Fallback to server default if the provided timezone is invalid.
                timezone.deactivate()
                request.timezone_detected = False  # type: ignore[attr-defined]
        else:
            timezone.deactivate()
            request.timezone_detected = False  # type: ignore[attr-defined]
        return self.get_response(request)


def timezone_context(request: HttpRequest) -> dict[str, object]:
    """Context processor to expose timezone detection status to templates.

    Returns:
        A dictionary containing:
        - timezone_detected: Boolean indicating if a valid timezone cookie was found.
        - server_timezone: The default server timezone from settings.
    """
    return {
        "timezone_detected": getattr(request, "timezone_detected", False),
        "server_timezone": settings.TIME_ZONE,
    }
