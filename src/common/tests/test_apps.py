"""Tests for common.apps management commands."""

import signal
import sys
from unittest.mock import MagicMock, patch

import pytest


def test_gunicorn_command_execs_gunicorn():
    """manage.py gunicorn replaces the process with gunicorn."""
    import os

    with patch.object(os, "execvp") as mock_exec:
        from common.management.commands.gunicorn import Command

        Command().handle()

    mock_exec.assert_called_once_with("gunicorn", ["gunicorn", "sloths_inventory.wsgi"])


def test_start_command_spawns_correct_processes():
    """manage.py start launches qcluster and gunicorn with expected args."""
    mock_qcluster = MagicMock()
    mock_gunicorn = MagicMock()
    mock_qcluster.poll.return_value = 0
    mock_gunicorn.poll.return_value = None

    popen_calls: list[list[str]] = []

    def capture_popen(args: list[str]) -> MagicMock:
        popen_calls.append(args)
        return [mock_qcluster, mock_gunicorn][len(popen_calls) - 1]

    with (
        patch("subprocess.Popen", side_effect=capture_popen),
        patch("signal.signal"),
        patch("time.sleep"),
        patch("common.management.commands.start._stop"),
        pytest.raises(SystemExit),
    ):
        from common.management.commands.start import Command

        Command().handle()

    assert popen_calls[0] == [sys.executable, "manage.py", "qcluster"]
    assert popen_calls[1] == ["gunicorn", "sloths_inventory.wsgi"]


def test_start_command_stops_survivor_and_exits_with_rc():
    """When one child crashes, _stop() is called for survivors and rc is propagated."""
    mock_qcluster = MagicMock()
    mock_gunicorn = MagicMock()
    mock_qcluster.poll.return_value = None
    mock_gunicorn.poll.return_value = 2

    with (
        patch("subprocess.Popen", side_effect=[mock_qcluster, mock_gunicorn]),
        patch("signal.signal"),
        patch("time.sleep"),
        patch("common.management.commands.start._stop") as mock_stop,
        pytest.raises(SystemExit) as exc_info,
    ):
        from common.management.commands.start import Command

        Command().handle()

    mock_stop.assert_called_once_with([mock_qcluster])
    assert exc_info.value.code == 2


def test_start_command_sleeps_when_both_running():
    """While both children are alive, the supervisor sleeps between polls."""
    mock_qcluster = MagicMock()
    mock_gunicorn = MagicMock()
    mock_qcluster.poll.side_effect = [None, 0]
    mock_gunicorn.poll.side_effect = [None]

    with (
        patch("subprocess.Popen", side_effect=[mock_qcluster, mock_gunicorn]),
        patch("signal.signal"),
        patch("time.sleep") as mock_sleep,
        patch("common.management.commands.start._stop"),
        pytest.raises(SystemExit),
    ):
        from common.management.commands.start import Command

        Command().handle()

    mock_sleep.assert_called_once_with(0.5)


def test_start_command_sigterm_stops_all_and_exits_zero():
    """SIGTERM (planned stop): _stop() called for all children, exit code 0."""
    mock_qcluster = MagicMock()
    mock_gunicorn = MagicMock()
    mock_qcluster.poll.return_value = None
    mock_gunicorn.poll.return_value = None

    registered: dict[int, object] = {}

    def capture_signal(signum: int, handler: object) -> None:
        registered[signum] = handler

    def fire_sigterm(_: object) -> None:
        handler = registered.get(signal.SIGTERM)
        if callable(handler):
            handler(signal.SIGTERM, None)  # type: ignore[operator]

    with (
        patch("subprocess.Popen", side_effect=[mock_qcluster, mock_gunicorn]),
        patch("signal.signal", side_effect=capture_signal),
        patch("time.sleep", side_effect=fire_sigterm),
        patch("common.management.commands.start._stop") as mock_stop,
        pytest.raises(SystemExit) as exc_info,
    ):
        from common.management.commands.start import Command

        Command().handle()

    mock_stop.assert_called_once_with([mock_qcluster, mock_gunicorn])
    assert exc_info.value.code == 0


def test_start_command_sigint_stops_all_and_reraises():
    """SIGINT: _stop() for all children; re-raise SIGINT with default handler."""
    mock_qcluster = MagicMock()
    mock_gunicorn = MagicMock()
    mock_qcluster.poll.return_value = None
    mock_gunicorn.poll.return_value = None

    registered: dict[int, object] = {}

    def capture_signal(signum: int, handler: object) -> None:
        registered[signum] = handler

    def fire_sigint(_: object) -> None:
        handler = registered.get(signal.SIGINT)
        if callable(handler):
            handler(signal.SIGINT, None)  # type: ignore[operator]

    with (
        patch("subprocess.Popen", side_effect=[mock_qcluster, mock_gunicorn]),
        patch("signal.signal", side_effect=capture_signal),
        patch("time.sleep", side_effect=fire_sigint),
        patch("common.management.commands.start._stop") as mock_stop,
        # raise_signal(SIGINT) with SIG_DFL kills the process; model that as SystemExit.
        patch("signal.raise_signal", side_effect=SystemExit(130)) as mock_raise,
        pytest.raises(SystemExit),
    ):
        from common.management.commands.start import Command

        Command().handle()

    mock_stop.assert_called_once_with([mock_qcluster, mock_gunicorn])
    mock_raise.assert_called_once_with(signal.SIGINT)


def test_stop_terminates_then_kills_on_timeout():
    """_stop() sends SIGTERM and falls back to SIGKILL if process does not exit."""
    from common.management.commands.start import _stop

    alive = MagicMock()
    alive.wait.side_effect = __import__("subprocess").TimeoutExpired(
        cmd="x", timeout=10
    )

    died = MagicMock()

    _stop([alive, died])

    assert alive.terminate.call_count == 1
    assert alive.kill.call_count == 1
    assert died.terminate.call_count == 1
    assert died.kill.call_count == 0  # exited in time — no SIGKILL needed
