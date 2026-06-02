"""Tests for common.email_utils."""

from unittest.mock import patch

from common.email_utils import send_transfer_email


class TestSendTransferEmail:
    def test_renders_templates_and_sends(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.send_mail") as mock_send,
        ):
            send_transfer_email("subj.txt", "body.txt", {}, "a@example.com")
        mock_send.assert_called_once_with(
            subject="rendered",
            message="rendered",
            from_email=None,
            recipient_list=["a@example.com"],
            html_message=None,
        )

    def test_html_template_rendered_and_passed(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.send_mail") as mock_send,
        ):
            send_transfer_email(
                "subj.txt", "body.txt", {}, "a@example.com", html_template="body.html"
            )
        mock_send.assert_called_once_with(
            subject="rendered",
            message="rendered",
            from_email=None,
            recipient_list=["a@example.com"],
            html_message="rendered",
        )

    def test_empty_string_recipient_skips_send(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.send_mail") as mock_send,
        ):
            send_transfer_email("subj.txt", "body.txt", {}, "")
        mock_send.assert_not_called()

    def test_list_of_empty_strings_skips_send(self):
        with (
            patch("common.email_utils.render_to_string", return_value="rendered"),
            patch("common.email_utils.send_mail") as mock_send,
        ):
            send_transfer_email("subj.txt", "body.txt", {}, ["", ""])
        mock_send.assert_not_called()
