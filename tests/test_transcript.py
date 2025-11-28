"""Unit tests for transcript extraction module.

These tests use mocks to avoid making real API calls during testing.
"""

import pytest
from unittest.mock import MagicMock, patch

from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


class TestCleanTranscriptText:
    """Tests for clean_transcript_text function."""

    def test_removes_music_annotation(self):
        """Test that [Music] annotations are removed."""
        from src.transcript import clean_transcript_text

        raw = "Hello [Music] world"
        cleaned = clean_transcript_text(raw)
        assert cleaned == "Hello world"

    def test_removes_applause_annotation(self):
        """Test that [Applause] annotations are removed."""
        from src.transcript import clean_transcript_text

        raw = "Thank you [Applause] everyone"
        cleaned = clean_transcript_text(raw)
        assert cleaned == "Thank you everyone"

    def test_removes_multiple_annotations(self):
        """Test that multiple annotations are removed."""
        from src.transcript import clean_transcript_text

        raw = "Hello [Music] world [Applause] test [Laughter]"
        cleaned = clean_transcript_text(raw)
        assert cleaned == "Hello world test"

    def test_removes_excessive_whitespace(self):
        """Test that excessive whitespace is normalized."""
        from src.transcript import clean_transcript_text

        raw = "Hello   world    this   is   a   test"
        cleaned = clean_transcript_text(raw)
        assert cleaned == "Hello world this is a test"

    def test_strips_leading_trailing_whitespace(self):
        """Test that leading and trailing whitespace is stripped."""
        from src.transcript import clean_transcript_text

        raw = "   Hello world   "
        cleaned = clean_transcript_text(raw)
        assert cleaned == "Hello world"

    def test_handles_empty_string(self):
        """Test that empty string returns empty string."""
        from src.transcript import clean_transcript_text

        raw = ""
        cleaned = clean_transcript_text(raw)
        assert cleaned == ""

    def test_combined_cleaning(self):
        """Test combined cleaning of annotations and whitespace."""
        from src.transcript import clean_transcript_text

        raw = "   Hello   [Music]  world  [Applause]   "
        cleaned = clean_transcript_text(raw)
        assert cleaned == "Hello world"


class TestGetTranscript:
    """Tests for get_transcript function."""

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_success_preferred_language(self, mock_api):
        """Test successful transcript retrieval with preferred language."""
        from src.transcript import get_transcript

        # Setup mocks
        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [
            {'text': 'Hello'},
            {'text': 'world'},
        ]

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_api.list_transcripts.return_value = mock_transcript_list

        result = get_transcript('test_video_id', languages=['en'])

        assert result == "Hello world"
        mock_api.list_transcripts.assert_called_once_with('test_video_id')
        mock_transcript_list.find_transcript.assert_called_once_with(['en'])

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_fallback_to_generated(self, mock_api):
        """Test fallback to auto-generated transcript when preferred not found."""
        from src.transcript import get_transcript

        # Setup mocks
        mock_generated_transcript = MagicMock()
        mock_generated_transcript.fetch.return_value = [
            {'text': 'Auto'},
            {'text': 'generated'},
        ]

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.side_effect = NoTranscriptFound(
            'test_video_id', ['en'], None
        )
        mock_transcript_list.find_generated_transcript.return_value = (
            mock_generated_transcript
        )
        mock_api.list_transcripts.return_value = mock_transcript_list

        result = get_transcript('test_video_id', languages=['en'])

        assert result == "Auto generated"
        mock_transcript_list.find_generated_transcript.assert_called_once_with(['en'])

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_no_transcript_found(self, mock_api):
        """Test returns None when no transcript is available."""
        from src.transcript import get_transcript

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.side_effect = NoTranscriptFound(
            'test_video_id', ['en'], None
        )
        mock_transcript_list.find_generated_transcript.side_effect = NoTranscriptFound(
            'test_video_id', ['en'], None
        )
        mock_api.list_transcripts.return_value = mock_transcript_list

        result = get_transcript('test_video_id')

        assert result is None

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_transcripts_disabled(self, mock_api):
        """Test returns None when transcripts are disabled."""
        from src.transcript import get_transcript

        mock_api.list_transcripts.side_effect = TranscriptsDisabled('test_video_id')

        result = get_transcript('test_video_id')

        assert result is None

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_video_unavailable(self, mock_api):
        """Test returns None when video is unavailable."""
        from src.transcript import get_transcript

        mock_api.list_transcripts.side_effect = VideoUnavailable('test_video_id')

        result = get_transcript('test_video_id')

        assert result is None

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_generic_exception(self, mock_api):
        """Test returns None on generic exception."""
        from src.transcript import get_transcript

        mock_api.list_transcripts.side_effect = Exception('Network error')

        result = get_transcript('test_video_id')

        assert result is None

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_cleans_text(self, mock_api):
        """Test that transcript text is cleaned before returning."""
        from src.transcript import get_transcript

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [
            {'text': '[Music]'},
            {'text': 'Hello'},
            {'text': '[Applause]'},
            {'text': 'world'},
        ]

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_api.list_transcripts.return_value = mock_transcript_list

        result = get_transcript('test_video_id')

        assert result == "Hello world"

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_default_languages(self, mock_api):
        """Test that default languages is ['en'] when not specified."""
        from src.transcript import get_transcript

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [{'text': 'Test'}]

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_api.list_transcripts.return_value = mock_transcript_list

        get_transcript('test_video_id')

        mock_transcript_list.find_transcript.assert_called_once_with(['en'])

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_transcript_multiple_languages(self, mock_api):
        """Test trying multiple preferred languages."""
        from src.transcript import get_transcript

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [{'text': 'Spanish text'}]

        mock_transcript_list = MagicMock()
        # First language 'en' not found, second language 'es' found
        mock_transcript_list.find_transcript.side_effect = [
            NoTranscriptFound('test_video_id', ['en'], None),
            mock_transcript,
        ]
        mock_api.list_transcripts.return_value = mock_transcript_list

        result = get_transcript('test_video_id', languages=['en', 'es'])

        assert result == "Spanish text"
        assert mock_transcript_list.find_transcript.call_count == 2


class TestGetAvailableLanguages:
    """Tests for get_available_languages function."""

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_available_languages_success(self, mock_api):
        """Test successful retrieval of available languages."""
        from src.transcript import get_available_languages

        mock_transcript_1 = MagicMock()
        mock_transcript_1.language = 'English'
        mock_transcript_1.language_code = 'en'
        mock_transcript_1.is_generated = False

        mock_transcript_2 = MagicMock()
        mock_transcript_2.language = 'Spanish'
        mock_transcript_2.language_code = 'es'
        mock_transcript_2.is_generated = True

        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__ = lambda self: iter(
            [mock_transcript_1, mock_transcript_2]
        )
        mock_api.list_transcripts.return_value = mock_transcript_list

        result = get_available_languages('test_video_id')

        assert len(result) == 2
        assert result[0] == {
            'language': 'English',
            'language_code': 'en',
            'is_generated': False,
        }
        assert result[1] == {
            'language': 'Spanish',
            'language_code': 'es',
            'is_generated': True,
        }

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_available_languages_transcripts_disabled(self, mock_api):
        """Test returns empty list when transcripts are disabled."""
        from src.transcript import get_available_languages

        mock_api.list_transcripts.side_effect = TranscriptsDisabled('test_video_id')

        result = get_available_languages('test_video_id')

        assert result == []

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_available_languages_video_unavailable(self, mock_api):
        """Test returns empty list when video is unavailable."""
        from src.transcript import get_available_languages

        mock_api.list_transcripts.side_effect = VideoUnavailable('test_video_id')

        result = get_available_languages('test_video_id')

        assert result == []

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_available_languages_generic_exception(self, mock_api):
        """Test returns empty list on generic exception."""
        from src.transcript import get_available_languages

        mock_api.list_transcripts.side_effect = Exception('Network error')

        result = get_available_languages('test_video_id')

        assert result == []

    @patch('src.transcript.YouTubeTranscriptApi')
    def test_get_available_languages_empty(self, mock_api):
        """Test returns empty list when no languages available."""
        from src.transcript import get_available_languages

        mock_transcript_list = MagicMock()
        mock_transcript_list.__iter__ = lambda self: iter([])
        mock_api.list_transcripts.return_value = mock_transcript_list

        result = get_available_languages('test_video_id')

        assert result == []
