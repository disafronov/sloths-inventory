"""Tests for common.email_utils."""

import smtplib
from unittest.mock import call, patch

from django.test import override_settings

from common.email_utils import _send_with_retry, send_transfer_email

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


class TestSendTransferEmail:
    def test_empty_string_recipient_does_not_spawn_thread(self):
        with patch("common.email_utils.threading.Thread") as mock_thread:
            send_transfer_email("subj.txt", "body.txt", {}, "")
        mock_thread.assert_not_called()

    def test_list_of_empty_strings_does_not_spawn_thread(self):
        with patch("common.email_utils.threading.Thread") as mock_thread:
            send_transfer_email("subj.txt", "body.txt", {}, ["", ""])
        mock_thread.assert_not_called()

    def test_spawns_daemon_thread_with_rendered_content(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.threading.Thread") as mock_thread_cls,
        ):
            instance = mock_thread_cls.return_value
            send_transfer_email("subj.txt", "body.txt", {}, "a@example.com")
        mock_thread_cls.assert_called_once_with(
            target=_send_with_retry,
            args=("rendered", "rendered", ["a@example.com"], None),
            daemon=True,
        )
        instance.start.assert_called_once()

    def test_html_template_rendered_and_passed_to_thread(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.threading.Thread") as mock_thread_cls,
        ):
            instance = mock_thread_cls.return_value
            send_transfer_email(
                "subj.txt",
                "body.txt",
                {},
                "a@example.com",
                html_template="body.html",
            )
        args = mock_thread_cls.call_args.kwargs["args"]
        assert args[3] == "rendered"
        instance.start.assert_called_once()
