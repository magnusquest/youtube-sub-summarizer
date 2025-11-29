"""Unit tests for Email Delivery System module.

These tests use mocks to avoid making real SMTP connections during testing.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, mock_open


class TestEmailSenderInit:
    """Tests for EmailSender initialization."""

    def test_init_with_explicit_params(self):
        """Test initialization with explicit parameters."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=465,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        assert sender.smtp_server == "smtp.test.com"
        assert sender.smtp_port == 465
        assert sender.username == "test@test.com"
        assert sender.password == "testpass"
        assert sender.recipient == "recipient@test.com"

    @patch("src.email_sender.SMTP_SERVER", "smtp.default.com")
    @patch("src.email_sender.SMTP_PORT", 587)
    @patch("src.email_sender.SMTP_USERNAME", "default@test.com")
    @patch("src.email_sender.SMTP_PASSWORD", "defaultpass")
    @patch("src.email_sender.EMAIL_RECIPIENT", "default_recipient@test.com")
    def test_init_with_defaults_from_config(self):
        """Test initialization with default values from config."""
        from src.email_sender import EmailSender

        sender = EmailSender()

        assert sender.smtp_server == "smtp.default.com"
        assert sender.smtp_port == 587
        assert sender.username == "default@test.com"
        assert sender.password == "defaultpass"
        assert sender.recipient == "default_recipient@test.com"


class TestSendSummaryEmail:
    """Tests for send_summary_email method."""

    @patch("src.email_sender.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "dQw4w9WgXcQ",
            "title": "Test Video Title",
            "channel_name": "Test Channel",
            "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        }
        summary = "This is a test summary of the video content."

        with patch("os.path.exists", return_value=False):
            result = sender.send_summary_email(video_data, summary, "/tmp/audio.mp3")

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "testpass")
        mock_server.send_message.assert_called_once()

    @patch("src.email_sender.smtplib.SMTP")
    @patch("src.email_sender.time.sleep")
    def test_send_email_retry_on_failure(self, mock_sleep, mock_smtp):
        """Test retry logic on transient failures."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Fail first two attempts, succeed on third
        mock_server.send_message.side_effect = [
            Exception("Connection error"),
            Exception("Timeout"),
            None,  # Success
        ]

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        with patch("os.path.exists", return_value=False):
            result = sender.send_summary_email(video_data, "Summary", "/tmp/audio.mp3")

        assert result is True
        assert mock_server.send_message.call_count == 3
        assert mock_sleep.call_count == 2
        # Check exponential backoff: 2^0=1, 2^1=2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch("src.email_sender.smtplib.SMTP")
    @patch("src.email_sender.time.sleep")
    def test_send_email_raises_after_max_retries(self, mock_sleep, mock_smtp):
        """Test that exception is raised after max retries."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = Exception("Persistent error")

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        with patch("os.path.exists", return_value=False):
            with pytest.raises(Exception, match="Persistent error"):
                sender.send_summary_email(
                    video_data, "Summary", "/tmp/audio.mp3", max_retries=3
                )

        assert mock_server.send_message.call_count == 3

    @patch("src.email_sender.smtplib.SMTP")
    def test_send_email_with_audio_attachment(self, mock_smtp):
        """Test email sending with audio file attachment."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        # Mock file operations
        mock_audio_data = b"fake audio data"
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_audio_data)):
                result = sender.send_summary_email(
                    video_data, "Summary", "/tmp/audio.mp3"
                )

        assert result is True
        mock_server.send_message.assert_called_once()


class TestCreateMessage:
    """Tests for _create_message method."""

    def test_create_message_basic(self):
        """Test basic message creation."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video Title",
            "channel_name": "Test Channel",
            "url": "https://youtube.com/watch?v=test123",
        }

        with patch("os.path.exists", return_value=False):
            msg = sender._create_message(video_data, "Test summary", "/tmp/audio.mp3")

        assert msg["Subject"] == "[Test Channel] Test Video Title"
        assert msg["To"] == "recipient@test.com"
        assert "YouTube Digest" in msg["From"]

    def test_create_message_truncates_long_title(self):
        """Test that long video titles are truncated in subject."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "A" * 100,  # Very long title
            "channel_name": "Test Channel",
        }

        with patch("os.path.exists", return_value=False):
            msg = sender._create_message(video_data, "Test summary", "/tmp/audio.mp3")

        # Title should be truncated to 50 chars + "..."
        assert "[Test Channel] " + "A" * 50 + "..." in msg["Subject"]
        assert len(msg["Subject"]) < 100

    def test_create_message_with_default_channel_name(self):
        """Test message creation with missing channel name."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            # No channel_name
        }

        with patch("os.path.exists", return_value=False):
            msg = sender._create_message(video_data, "Test summary", "/tmp/audio.mp3")

        assert "[Unknown Channel]" in msg["Subject"]

    def test_create_message_with_audio_attachment(self):
        """Test message creation includes audio attachment."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        mock_audio_data = b"fake audio data"
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_audio_data)):
                msg = sender._create_message(
                    video_data, "Test summary", "/tmp/audio.mp3"
                )

        # Check that message is multipart
        assert msg.is_multipart()

        # Check for audio attachment (message structure: mixed -> [alternative, audio])
        payloads = msg.get_payload()
        has_audio = False
        for part in payloads:
            content_type = part.get_content_type()
            # MIMEApplication with _subtype='mpeg' creates application/mpeg content type
            if content_type == "application/mpeg":
                has_audio = True
                # Check filename
                content_disp = part.get("Content-Disposition")
                assert "test123_summary.mp3" in content_disp
            elif content_type == "multipart/alternative":
                # Check that alternative part has HTML and plain text
                alt_payloads = part.get_payload()
                content_types = [p.get_content_type() for p in alt_payloads]
                assert "text/plain" in content_types
                assert "text/html" in content_types
        assert has_audio


class TestCreateHtmlBody:
    """Tests for _create_html_body method."""

    def test_html_body_contains_video_info(self):
        """Test that HTML body contains video information."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video Title",
            "channel_name": "Test Channel Name",
            "url": "https://youtube.com/watch?v=test123",
            "thumbnail": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
        }

        html = sender._create_html_body(video_data, "This is the test summary.")

        assert "Test Channel Name" in html
        assert "Test Video Title" in html
        assert "This is the test summary." in html
        assert "https://youtube.com/watch?v=test123" in html
        assert "https://img.youtube.com/vi/test123/maxresdefault.jpg" in html

    def test_html_body_uses_default_url(self):
        """Test HTML body uses default URL when not provided."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
            # No url or thumbnail
        }

        html = sender._create_html_body(video_data, "Summary")

        assert "https://youtube.com/watch?v=test123" in html
        assert "https://img.youtube.com/vi/test123/maxresdefault.jpg" in html

    def test_html_body_escapes_special_characters(self):
        """Test that HTML body escapes special characters."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "<script>alert('XSS')</script>",
            "channel_name": "Test & Channel",
        }

        html = sender._create_html_body(video_data, "Summary with <html> tags")

        # Should escape HTML special characters
        assert "&lt;script&gt;" in html
        assert "&amp;" in html
        assert "<script>" not in html


class TestCreatePlainTextBody:
    """Tests for _create_plain_text_body method."""

    def test_plain_text_body_contains_video_info(self):
        """Test that plain text body contains video information."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video Title",
            "channel_name": "Test Channel Name",
            "url": "https://youtube.com/watch?v=test123",
        }

        text = sender._create_plain_text_body(video_data, "This is the test summary.")

        assert "Test Channel Name" in text
        assert "Test Video Title" in text
        assert "This is the test summary." in text
        assert "https://youtube.com/watch?v=test123" in text
        assert "Audio narration is attached" in text

    def test_plain_text_body_uses_default_url(self):
        """Test plain text body uses default URL when not provided."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
            # No url
        }

        text = sender._create_plain_text_body(video_data, "Summary")

        assert "https://youtube.com/watch?v=test123" in text

    def test_plain_text_body_default_channel_name(self):
        """Test plain text body uses default channel name when not provided."""
        from src.email_sender import EmailSender

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            # No channel_name
        }

        text = sender._create_plain_text_body(video_data, "Summary")

        assert "Unknown Channel" in text


class TestEmailLogging:
    """Tests for logging functionality."""

    @patch("src.email_sender.smtplib.SMTP")
    @patch("src.email_sender.logger")
    def test_logs_success(self, mock_logger, mock_smtp):
        """Test that successful email sending is logged."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        with patch("os.path.exists", return_value=False):
            sender.send_summary_email(video_data, "Summary", "/tmp/audio.mp3")

        assert mock_logger.info.called
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Email sent successfully" in call for call in info_calls)

    @patch("src.email_sender.smtplib.SMTP")
    @patch("src.email_sender.logger")
    def test_logs_audio_attachment(self, mock_logger, mock_smtp):
        """Test that audio attachment is logged."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        mock_audio_data = b"fake audio data"
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_audio_data)):
                sender.send_summary_email(video_data, "Summary", "/tmp/audio.mp3")

        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Attached audio file" in call for call in info_calls)

    @patch("src.email_sender.smtplib.SMTP")
    @patch("src.email_sender.logger")
    def test_logs_missing_audio_warning(self, mock_logger, mock_smtp):
        """Test that missing audio file triggers a warning."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        with patch("os.path.exists", return_value=False):
            sender.send_summary_email(video_data, "Summary", "/tmp/nonexistent.mp3")

        assert mock_logger.warning.called
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Audio file not found" in call for call in warning_calls)

    @patch("src.email_sender.smtplib.SMTP")
    @patch("src.email_sender.time.sleep")
    @patch("src.email_sender.logger")
    def test_logs_retry_attempts(self, mock_logger, mock_sleep, mock_smtp):
        """Test that retry attempts are logged."""
        from src.email_sender import EmailSender

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = [
            Exception("Connection error"),
            None,  # Success
        ]

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="testpass",
            recipient="recipient@test.com",
        )

        video_data = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        with patch("os.path.exists", return_value=False):
            sender.send_summary_email(video_data, "Summary", "/tmp/audio.mp3")

        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("Attempt 1" in call for call in error_calls)

        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Retrying" in call for call in info_calls)
