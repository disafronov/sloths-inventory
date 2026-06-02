"""Management command to launch Gunicorn via manage.py."""

import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Start the Gunicorn WSGI server."""

    help = "Start Gunicorn (replaces direct gunicorn invocation)"

    def handle(self, *args: object, **options: object) -> None:
        """Replace the current process with Gunicorn."""
        os.execvp(
            "gunicorn", ["gunicorn", "sloths_inventory.wsgi"]
        )  # nosec B606 B607 — fixed executable from venv, no user input
