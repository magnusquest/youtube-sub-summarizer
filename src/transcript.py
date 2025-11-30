"""Transcript extraction module for YouTube videos.

This module provides functions to extract and clean transcripts/captions
from YouTube videos using the youtube-transcript-api library.

Note: This module does NOT use YouTube Data API quota - the youtube-transcript-api
library fetches transcripts independently and is free to call as many times as needed.
"""

import logging
import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

# Configure logging
logger = logging.getLogger(__name__)


def clean_transcript_text(text: str) -> str:
    """Clean up transcript text for AI summarization.

    Removes common artifacts from auto-generated captions such as
    [Music], [Applause], and other bracketed annotations.

    Args:
        text: Raw transcript text.

    Returns:
        Cleaned transcript text with artifacts removed.
    """
    # Remove all bracketed annotations like [Music], [Applause], etc.
    text = re.sub(r'\[.*?\]', '', text)

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Fix common spacing issues
    text = text.strip()

    return text


def get_transcript(video_id: str, languages: list[str] | None = None) -> str | None:
    """Retrieve transcript for a YouTube video.

    Attempts to find a transcript in the preferred languages first,
    then falls back to auto-generated English if no preferred language is found.

    Args:
        video_id: YouTube video ID.
        languages: List of preferred language codes (default: ['en']).

    Returns:
        Full transcript as plain text string, or None if unavailable.
    """
    if languages is None:
        languages = ['en']

    try:
        # Fetch transcript list
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Try to find transcript in preferred languages
        transcript = None
        for lang in languages:
            try:
                transcript = transcript_list.find_transcript([lang])
                logger.info(f"Found {lang} transcript for video {video_id}")
                break
            except NoTranscriptFound:
                continue

        # If no preferred language found, try auto-generated English
        if not transcript:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                logger.info(
                    f"Using auto-generated English transcript for video {video_id}"
                )
            except NoTranscriptFound:
                logger.warning(f"No transcript found for video {video_id}")
                return None

        # Fetch and format transcript
        transcript_data = transcript.fetch()
        full_text = ' '.join([entry.text for entry in transcript_data])

        # Clean up text
        cleaned_text = clean_transcript_text(full_text)

        return cleaned_text

    except TranscriptsDisabled:
        logger.warning(f"Transcripts disabled for video {video_id}")
        return None
    except VideoUnavailable:
        logger.error(f"Video {video_id} is unavailable")
        return None
    except Exception as e:
        logger.error(f"Error fetching transcript for {video_id}: {e}")
        return None


def get_available_languages(video_id: str) -> list[dict]:
    """Get list of available transcript languages for a video.

    Args:
        video_id: YouTube video ID.

    Returns:
        List of dictionaries containing language info with keys:
        - language: Human-readable language name
        - language_code: ISO language code
        - is_generated: Whether the transcript is auto-generated
        Returns empty list if no transcripts are available.
    """
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        languages = []

        for transcript in transcript_list:
            languages.append({
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated,
            })

        return languages
    except TranscriptsDisabled:
        logger.warning(f"Transcripts disabled for video {video_id}")
        return []
    except VideoUnavailable:
        logger.error(f"Video {video_id} is unavailable")
        return []
    except Exception as e:
        logger.error(f"Error getting languages for {video_id}: {e}")
        return []
