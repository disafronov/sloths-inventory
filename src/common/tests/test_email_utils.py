"""Tests for common.email_utils."""

import smtplib
from unittest.mock import call, patch

from django.test import override_settings

from common.email_utils import _send_with_retry, send_email_async, send_transfer_email

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


class TestSendWithRetry:
    @override_settings(**_RETRY_0)
    def test_success_on_first_attempt(self):
        with patch("common.email_utils.send_mail") as mock_send:
            _send_with_retry("subj", "body", ["a@example.com"], None)
        mock_send.assert_called_once_with(
            subject="subj",
            message="body",
            from_email=None,
            recipient_list=["a@example.com"],
            html_message=None,
        )

    @override_settings(**_RETRY_0)
    def test_passes_html_message(self):
        with patch("common.email_utils.send_mail") as mock_send:
            _send_with_retry("subj", "body", ["a@example.com"], "<p>html</p>")
        mock_send.assert_called_once_with(
            subject="subj",
            message="body",
            from_email=None,
            recipient_list=["a@example.com"],
            html_message="<p>html</p>",
        )

    @override_settings(**_RETRY_2)
    def test_retries_on_recoverable_error_then_succeeds(self):
        with (
            patch("common.email_utils.send_mail") as mock_send,
            patch("common.email_utils.time.sleep") as mock_sleep,
        ):
            mock_send.side_effect = [smtplib.SMTPConnectError(421, "retry"), None]
            _send_with_retry("subj", "body", ["a@example.com"], None)
        assert mock_send.call_count == 2
        mock_sleep.assert_called_once_with(0.0)

    @override_settings(**_RETRY_2)
    def test_all_retries_exhausted_on_recoverable_error(self):
        with (
            patch("common.email_utils.send_mail") as mock_send,
            patch("common.email_utils.time.sleep"),
        ):
            mock_send.side_effect = smtplib.SMTPServerDisconnected("gone")
            _send_with_retry("subj", "body", ["a@example.com"], None)
        assert mock_send.call_count == 3  # 1 initial + 2 retries

    @override_settings(
        EMAIL_RETRY_MAX_RETRIES=2,
        EMAIL_RETRY_BASE_DELAY_SECONDS=10.0,
        EMAIL_RETRY_BACKOFF_FACTOR=3.0,
    )
    def test_backoff_delay_increases_between_retries(self):
        with (
            patch("common.email_utils.send_mail") as mock_send,
            patch("common.email_utils.time.sleep") as mock_sleep,
        ):
            mock_send.side_effect = smtplib.SMTPConnectError(421, "retry")
            _send_with_retry("subj", "body", ["a@example.com"], None)
        mock_sleep.assert_has_calls([call(10.0), call(30.0)])

    @override_settings(**_RETRY_2)
    def test_no_retry_on_non_recoverable_error(self):
        with patch("common.email_utils.send_mail") as mock_send:
            mock_send.side_effect = smtplib.SMTPAuthenticationError(535, "auth")
            _send_with_retry("subj", "body", ["a@example.com"], None)
        assert mock_send.call_count == 1


class TestSendEmailAsync:
    def test_empty_string_recipient_skips_send(self):
        with patch("common.email_utils._send_with_retry") as mock_retry:
            send_email_async("subj", "body", "")
        mock_retry.assert_not_called()

    def test_list_of_empty_strings_skips_send(self):
        with patch("common.email_utils._send_with_retry") as mock_retry:
            send_email_async("subj", "body", ["", ""])
        mock_retry.assert_not_called()

    @override_settings(EMAIL_SEND_ASYNC=True)
    def test_spawns_daemon_thread_when_async_enabled(self):
        with patch("common.email_utils.threading.Thread") as mock_thread_cls:
            instance = mock_thread_cls.return_value
            send_email_async("subj", "body", "a@example.com", "<p>html</p>")
        mock_thread_cls.assert_called_once_with(
            target=_send_with_retry,
            args=("subj", "body", ["a@example.com"], "<p>html</p>"),
            daemon=True,
        )
        instance.start.assert_called_once()

    @override_settings(EMAIL_SEND_ASYNC=False, **_RETRY_0)
    def test_calls_retry_directly_when_async_disabled(self):
        with patch("common.email_utils._send_with_retry") as mock_retry:
            send_email_async("subj", "body", "a@example.com", "<p>html</p>")
        mock_retry.assert_called_once_with(
            "subj", "body", ["a@example.com"], "<p>html</p>"
        )


class TestSendTransferEmail:
    def test_renders_templates_and_delegates(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.send_email_async") as mock_async,
        ):
            send_transfer_email("subj.txt", "body.txt", {}, "a@example.com")
        mock_async.assert_called_once_with(
            "rendered", "rendered", "a@example.com", None
        )

    def test_html_template_rendered_and_passed(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.send_email_async") as mock_async,
        ):
            send_transfer_email(
                "subj.txt",
                "body.txt",
                {},
                "a@example.com",
                html_template="body.html",
            )
        mock_async.assert_called_once_with(
            "rendered", "rendered", "a@example.com", "rendered"
        )
