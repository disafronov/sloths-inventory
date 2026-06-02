"""Management command: supervised launcher for qcluster + gunicorn."""

import os
import signal
import subprocess  # nosec B404 — fixed args, no shell, no user input
import sys
import time

from django.core.management.base import BaseCommand

# Seconds all children share before SIGKILL; override via GRACEFUL_TIMEOUT env var.
_GRACEFUL_TIMEOUT = int(os.environ.get("GRACEFUL_TIMEOUT", "25"))


def _stop(procs: list[subprocess.Popen[bytes]]) -> None:
    """SIGTERM all; shared _GRACEFUL_TIMEOUT window, then SIGKILL survivors."""
    for p in procs:
        p.terminate()
    deadline = time.monotonic() + _GRACEFUL_TIMEOUT
    for p in procs:
        remaining = max(0.0, deadline - time.monotonic())
        try:
            p.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            p.kill()


def _supervise(procs: list[subprocess.Popen[bytes]]) -> None:
    """Set up signal handlers and poll until a child exits, then stop survivors."""

    def _on_sigterm(signum: int, frame: object) -> None:
        """Planned stop (orchestrator/systemd): stop children gracefully, exit 0."""
        _stop(procs)
        sys.exit(0)

    def _on_sigint(signum: int, frame: object) -> None:
        """SIGINT: stop all children, then re-raise for correct exit code."""
        _stop(procs)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.raise_signal(signal.SIGINT)

    signal.signal(signal.SIGTERM, _on_sigterm)
    signal.signal(signal.SIGINT, _on_sigint)

    while True:
        for p in procs:
            rc = p.poll()
            if rc is not None:
                _stop([other for other in procs if other is not p])
                sys.exit(rc)
        time.sleep(0.5)


class Command(BaseCommand):
    """Spawn qcluster and gunicorn as supervised children; forward signals to both."""

    help = "Start qcluster and gunicorn under a common supervisor"

    def handle(self, *args: object, **options: object) -> None:
        """Launch child processes and hand off to the supervisor loop."""
        _supervise(
            [
                subprocess.Popen(  # nosec B603 — fixed args, no user input
                    [sys.executable, "manage.py", "qcluster"]
                ),
                subprocess.Popen(  # nosec B603 B607 — fixed venv path, no user input
                    ["gunicorn", "sloths_inventory.wsgi"]
                ),
            ]
        )
