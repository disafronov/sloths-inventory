"""Management command: supervised launcher for qcluster + runserver (dev only)."""

import subprocess  # nosec B404 — fixed args, no shell, no user input
import sys

from django.core.management.base import BaseCommand

from common.management.commands.start import _supervise


class Command(BaseCommand):
    """Spawn qcluster and runserver as supervised children (development only)."""

    help = "Start qcluster and runserver together for local development"

    def handle(self, *args: object, **options: object) -> None:  # pragma: no cover
        """Launch child processes and hand off to the supervisor loop."""
        _supervise(
            [
                subprocess.Popen(  # nosec B603 — fixed args, no user input
                    [sys.executable, "manage.py", "qcluster"]
                ),
                subprocess.Popen(  # nosec B603 — fixed args, no user input
                    [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"]
                ),
            ]
        )
