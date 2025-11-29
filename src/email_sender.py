"""Email Delivery System module.

This module provides functionality to send formatted emails with video summary
text and audio narration attachment via SMTP.

Supports multiple SMTP providers including Gmail, SendGrid, Outlook, and custom SMTP servers.
Includes retry logic with exponential backoff for handling transient failures.

Example SMTP Configuration:
- Gmail: smtp.gmail.com:587 (requires App Password)
- SendGrid: smtp.sendgrid.net:587
- Outlook: smtp-mail.outlook.com:587
"""

import logging
import os
import smtplib
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

from src.config import (
    EMAIL_RECIPIENT,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
    SMTP_USERNAME,
)

logger = logging.getLogger(__name__)


class EmailSender:
    """Handle email delivery with retry logic."""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        recipient: Optional[str] = None,
    ):
        """Initialize EmailSender with SMTP configuration.

        Args:
            smtp_server: SMTP server hostname. Defaults to config value.
            smtp_port: SMTP server port. Defaults to config value.
            username: SMTP authentication username. Defaults to config value.
            password: SMTP authentication password. Defaults to config value.
            recipient: Email recipient address. Defaults to config value.
        """
        self.smtp_server = smtp_server or SMTP_SERVER
        self.smtp_port = smtp_port or SMTP_PORT
        self.username = username or SMTP_USERNAME
        self.password = password or SMTP_PASSWORD
        self.recipient = recipient or EMAIL_RECIPIENT

    def send_summary_email(
        self,
        video_data: dict,
        summary: str,
        audio_path: str,
        max_retries: int = 3,
    ) -> bool:
        """Send video summary email with audio attachment.

        Implements retry logic with exponential backoff for transient failures.

        Args:
            video_data: Dict with video info (title, channel_name, video_id, url, thumbnail).
            summary: Text summary of the video.
            audio_path: Path to MP3 audio file.
            max_retries: Maximum retry attempts (default: 3).

        Returns:
            bool: True if email sent successfully.

        Raises:
            Exception: If email sending fails after all retry attempts.
        """
        for attempt in range(max_retries):
            try:
                # Create message
                msg = self._create_message(video_data, summary, audio_path)

                # Send email
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)

                logger.info(f"Email sent successfully for video: {video_data['title']}")
                return True

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to send email after {max_retries} attempts")
                    raise

        return False

    def _create_message(
        self,
        video_data: dict,
        summary: str,
        audio_path: str,
    ) -> MIMEMultipart:
        """Create formatted email message with HTML, plain text, and audio attachment.

        Args:
            video_data: Dict with video info (title, channel_name, video_id, url, thumbnail).
            summary: Text summary of the video.
            audio_path: Path to MP3 audio file.

        Returns:
            MIMEMultipart: Constructed email message ready for sending.
        """
        msg = MIMEMultipart("mixed")

        # Email metadata
        channel_name = video_data.get("channel_name", "Unknown Channel")
        video_title = video_data["title"]

        # Truncate title if too long for subject line
        truncated_title = (
            video_title[:50] + "..." if len(video_title) > 50 else video_title
        )
        msg["Subject"] = f"[{channel_name}] {truncated_title}"
        msg["From"] = formataddr(("YouTube Digest", self.username))
        msg["To"] = self.recipient

        # Create alternative part for HTML and plain text
        alt_part = MIMEMultipart("alternative")

        # Create plain text body
        plain_body = self._create_plain_text_body(video_data, summary)
        plain_part = MIMEText(plain_body, "plain")
        alt_part.attach(plain_part)

        # Create HTML body
        html_body = self._create_html_body(video_data, summary)
        html_part = MIMEText(html_body, "html")
        alt_part.attach(html_part)

        msg.attach(alt_part)

        # Attach audio file
        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            audio_part = MIMEApplication(audio_data, _subtype="mpeg")
            audio_part.add_header(
                "Content-Disposition",
                "attachment",
                filename=f"{video_data['video_id']}_summary.mp3",
            )
            msg.attach(audio_part)
            logger.info(f"Attached audio file: {audio_path}")
        else:
            logger.warning(f"Audio file not found: {audio_path}")

        return msg

    def _create_html_body(self, video_data: dict, summary: str) -> str:
        """Create HTML email body with responsive styling.

        Args:
            video_data: Dict with video info (title, channel_name, video_id, url, thumbnail).
            summary: Text summary of the video.

        Returns:
            str: HTML formatted email body.
        """
        channel_name = video_data.get("channel_name", "Unknown Channel")
        video_title = video_data["title"]
        video_id = video_data["video_id"]
        video_url = video_data.get("url", f"https://youtube.com/watch?v={video_id}")
        thumbnail_url = video_data.get(
            "thumbnail", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        )

        # Escape HTML special characters in user-provided content
        import html

        channel_name = html.escape(channel_name)
        video_title = html.escape(video_title)
        summary = html.escape(summary)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #FF0000;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 0 0 8px 8px;
        }}
        .video-thumbnail {{
            width: 100%;
            max-width: 560px;
            height: auto;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .channel {{
            color: #606060;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .title {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .summary {{
            background-color: white;
            padding: 15px;
            border-left: 4px solid #FF0000;
            margin: 20px 0;
        }}
        .watch-button {{
            display: inline-block;
            background-color: #FF0000;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 15px;
        }}
        .audio-note {{
            background-color: #e8f4f8;
            padding: 10px;
            border-radius: 4px;
            margin-top: 15px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>&#128250; YouTube Video Summary</h1>
    </div>
    <div class="content">
        <div class="channel">&#128226; {channel_name}</div>
        <div class="title">{video_title}</div>

        <a href="{video_url}" target="_blank">
            <img src="{thumbnail_url}" alt="Video thumbnail" class="video-thumbnail">
        </a>

        <div class="summary">
            <strong>Summary:</strong><br>
            {summary}
        </div>

        <a href="{video_url}" class="watch-button" target="_blank">&#9654; Watch on YouTube</a>

        <div class="audio-note">
            &#128266; <strong>Audio narration attached</strong> - Listen to this summary on the go!
        </div>
    </div>
</body>
</html>"""
        return html_content

    def _create_plain_text_body(self, video_data: dict, summary: str) -> str:
        """Create plain text email body for clients that don't support HTML.

        Args:
            video_data: Dict with video info (title, channel_name, video_id, url, thumbnail).
            summary: Text summary of the video.

        Returns:
            str: Plain text formatted email body.
        """
        channel_name = video_data.get("channel_name", "Unknown Channel")
        video_title = video_data["title"]
        video_id = video_data["video_id"]
        video_url = video_data.get("url", f"https://youtube.com/watch?v={video_id}")

        text = f"""YouTube Video Summary

Channel: {channel_name}
Title: {video_title}

Summary:
{summary}

Watch: {video_url}

(Audio narration is attached to this email)"""
        return text
