"""Tests for common.email_backends."""

import smtplib
from unittest.mock import MagicMock, call, patch

from django.core.mail import EmailMessage
from django.test import override_settings

from common.email_backends import AsyncEmailBackend, _deliver_messages

_RETRY_0 = dict(
    EMAIL_RETRY_MAX_RETRIES=0,
    EMAIL_RETRY_BASE_DELAY_SECONDS=0.0,
    EMAIL_RETRY_BACKOFF_FACTOR=2.0,
)
_RETRY_2 = dict(
    EMAIL_RETRY_MAX_RETRIES=2,
    EMAIL_RETRY_BASE_DELAY_SECONDS=0.0,
    EMAIL_RETRY_BACKOFF_FACTOR=2.0,
)


class TestDeliverMessages:
    @override_settings(**_RETRY_0)
    def test_success_returns_count(self):
        messages = [MagicMock()]
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)
        mock_smtp.send_messages.return_value = 1
        with patch("common.email_backends.SmtpBackend", return_value=mock_smtp):
            assert _deliver_messages(messages) == 1
        mock_smtp.send_messages.assert_called_once_with(messages)

    @override_settings(**_RETRY_2)
    def test_retries_on_recoverable_error_then_succeeds(self):
        messages = [MagicMock()]
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)
        mock_smtp.send_messages.side_effect = [
            smtplib.SMTPConnectError(421, "retry"),
            1,
        ]
        with patch("common.email_backends.SmtpBackend", return_value=mock_smtp):
            assert _deliver_messages(messages) == 1
        assert mock_smtp.send_messages.call_count == 2

    @override_settings(**_RETRY_2)
    def test_all_retries_exhausted_returns_zero(self):
        messages = [MagicMock()]
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)
        mock_smtp.send_messages.side_effect = smtplib.SMTPServerDisconnected("gone")
        with patch("common.email_backends.SmtpBackend", return_value=mock_smtp):
            assert _deliver_messages(messages) == 0
        assert mock_smtp.send_messages.call_count == 3  # 1 + 2 retries

    @override_settings(**_RETRY_2)
    def test_no_retry_on_non_recoverable_error(self):
        messages = [MagicMock()]
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)
        mock_smtp.send_messages.side_effect = smtplib.SMTPAuthenticationError(
            535, "auth"
        )
        with patch("common.email_backends.SmtpBackend", return_value=mock_smtp):
            assert _deliver_messages(messages) == 0
        mock_smtp.send_messages.assert_called_once()

    @override_settings(
        EMAIL_RETRY_MAX_RETRIES=2,
        EMAIL_RETRY_BASE_DELAY_SECONDS=10.0,
        EMAIL_RETRY_BACKOFF_FACTOR=3.0,
    )
    def test_backoff_delay_increases_between_retries(self):
        messages = [MagicMock()]
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp.__exit__ = MagicMock(return_value=False)
        mock_smtp.send_messages.side_effect = smtplib.SMTPConnectError(421, "retry")
        with (
            patch("common.email_backends.SmtpBackend", return_value=mock_smtp),
            patch("common.email_backends.time.sleep") as mock_sleep,
        ):
            _deliver_messages(messages)
        mock_sleep.assert_has_calls([call(10.0), call(30.0)])


class TestAsyncEmailBackend:
    def test_empty_list_returns_zero(self):
        assert AsyncEmailBackend().send_messages([]) == 0

    @override_settings(EMAIL_SEND_ASYNC=True)
    def test_enqueues_when_async_enabled(self):
        messages = [EmailMessage(subject="s", body="b", to=["a@example.com"])]
        with patch("common.email_backends.async_task") as mock_task:
            result = AsyncEmailBackend().send_messages(messages)
        mock_task.assert_called_once_with(
            "common.email_backends._deliver_messages", messages
        )
        assert result == 1

    @override_settings(EMAIL_SEND_ASYNC=False)
    def test_delivers_synchronously_when_async_disabled(self):
        messages = [EmailMessage(subject="s", body="b", to=["a@example.com"])]
        with patch("common.email_backends._deliver_messages") as mock_deliver:
            mock_deliver.return_value = 1
            result = AsyncEmailBackend().send_messages(messages)
        mock_deliver.assert_called_once_with(messages)
        assert result == 1
