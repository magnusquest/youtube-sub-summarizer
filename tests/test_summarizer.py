"""Unit tests for AI summarization and audio narration module.

These tests use mocks to avoid making real OpenAI API calls during testing.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, mock_open


class TestSummarizeTranscript:
    """Tests for summarize_transcript function."""

    @patch('src.summarizer.get_openai_client')
    def test_summarize_transcript_success(self, mock_get_client):
        """Test successful transcript summarization."""
        from src.summarizer import summarize_transcript

        # Setup mock client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "This video discusses AI development. "
            "Key insights include the importance of data quality. "
            "The speaker recommends starting with small experiments."
        )
        mock_response.usage.total_tokens = 1500
        mock_response.usage.prompt_tokens = 1400
        mock_response.usage.completion_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response

        result = summarize_transcript(
            "Sample transcript about AI...",
            "AI Video",
            "https://youtube.com/watch?v=test123"
        )

        assert len(result) > 0
        assert "AI" in result
        mock_client.chat.completions.create.assert_called_once()

    @patch('src.summarizer.get_openai_client')
    def test_summarize_transcript_without_url(self, mock_get_client):
        """Test summarization without optional video URL."""
        from src.summarizer import summarize_transcript

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test summary."
        mock_response.usage.total_tokens = 500
        mock_response.usage.prompt_tokens = 450
        mock_response.usage.completion_tokens = 50
        mock_client.chat.completions.create.return_value = mock_response

        result = summarize_transcript(
            "Sample transcript",
            "Test Video"
        )

        assert result == "Test summary."

    @patch('src.summarizer.get_openai_client')
    def test_summarize_transcript_api_error(self, mock_get_client):
        """Test error handling when API call fails."""
        from src.summarizer import summarize_transcript

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            summarize_transcript("Test transcript", "Test Video")

    @patch('src.summarizer.get_openai_client')
    def test_summarize_transcript_uses_correct_model(self, mock_get_client):
        """Test that the correct GPT model is used."""
        from src.summarizer import summarize_transcript

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary"
        mock_response.usage.total_tokens = 100
        mock_response.usage.prompt_tokens = 90
        mock_response.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_response

        summarize_transcript("Test", "Title")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['model'] == "gpt-4-turbo-preview"
        assert call_args.kwargs['temperature'] == 0.7
        assert call_args.kwargs['max_tokens'] == 500


class TestGenerateAudioNarration:
    """Tests for generate_audio_narration function."""

    @patch('src.summarizer.get_openai_client')
    @patch('src.summarizer.os.makedirs')
    def test_generate_audio_narration_success(self, mock_makedirs, mock_get_client):
        """Test successful audio narration generation."""
        from src.summarizer import generate_audio_narration

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_client.audio.speech.create.return_value = mock_response

        result = generate_audio_narration(
            "This is a test summary.",
            "test123",
            "/tmp/test_audio"
        )

        assert result == "/tmp/test_audio/test123_summary.mp3"
        mock_makedirs.assert_called_once_with("/tmp/test_audio", exist_ok=True)
        mock_response.stream_to_file.assert_called_once_with(
            "/tmp/test_audio/test123_summary.mp3"
        )

    @patch('src.summarizer.get_openai_client')
    @patch('src.summarizer.os.makedirs')
    def test_generate_audio_narration_default_dir(self, mock_makedirs, mock_get_client):
        """Test audio generation with default output directory."""
        from src.summarizer import generate_audio_narration

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_client.audio.speech.create.return_value = mock_response

        result = generate_audio_narration("Test summary.", "vid456")

        assert result == "data/audio/vid456_summary.mp3"
        mock_makedirs.assert_called_once_with("data/audio", exist_ok=True)

    @patch('src.summarizer.get_openai_client')
    @patch('src.summarizer.os.makedirs')
    def test_generate_audio_narration_uses_configured_voice(
        self, mock_makedirs, mock_get_client
    ):
        """Test that configured TTS voice is used."""
        from src.summarizer import generate_audio_narration, OPENAI_TTS_VOICE

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_client.audio.speech.create.return_value = mock_response

        generate_audio_narration("Test", "vid789")

        call_args = mock_client.audio.speech.create.call_args
        assert call_args.kwargs['voice'] == OPENAI_TTS_VOICE
        assert call_args.kwargs['model'] == "tts-1"

    @patch('src.summarizer.get_openai_client')
    @patch('src.summarizer.os.makedirs')
    def test_generate_audio_narration_api_error(self, mock_makedirs, mock_get_client):
        """Test error handling when TTS API call fails."""
        from src.summarizer import generate_audio_narration

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.audio.speech.create.side_effect = Exception("TTS Error")

        with pytest.raises(Exception, match="TTS Error"):
            generate_audio_narration("Test summary", "vid123")


class TestCreateSummaryWithAudio:
    """Tests for create_summary_with_audio function."""

    @patch('src.summarizer.generate_audio_narration')
    @patch('src.summarizer.summarize_transcript')
    def test_create_summary_with_audio_success(
        self, mock_summarize, mock_audio
    ):
        """Test combined summary and audio generation."""
        from src.summarizer import create_summary_with_audio

        mock_summarize.return_value = "This is the summary."
        mock_audio.return_value = "/path/to/audio.mp3"

        result = create_summary_with_audio(
            "Full transcript text",
            "Video Title",
            "vid123",
            "https://youtube.com/watch?v=vid123"
        )

        assert result['summary'] == "This is the summary."
        assert result['audio_path'] == "/path/to/audio.mp3"
        mock_summarize.assert_called_once_with(
            "Full transcript text",
            "Video Title",
            "https://youtube.com/watch?v=vid123"
        )
        mock_audio.assert_called_once_with(
            "This is the summary.",
            "vid123",
            "data/audio"
        )

    @patch('src.summarizer.generate_audio_narration')
    @patch('src.summarizer.summarize_transcript')
    def test_create_summary_with_audio_custom_output_dir(
        self, mock_summarize, mock_audio
    ):
        """Test combined function with custom output directory."""
        from src.summarizer import create_summary_with_audio

        mock_summarize.return_value = "Summary"
        mock_audio.return_value = "/custom/path/audio.mp3"

        result = create_summary_with_audio(
            "Transcript",
            "Title",
            "vid456",
            output_dir="/custom/path"
        )

        mock_audio.assert_called_once_with("Summary", "vid456", "/custom/path")


class TestChunkTranscript:
    """Tests for chunk_transcript function."""

    def test_chunk_transcript_short_text(self):
        """Test that short transcripts are not chunked."""
        from src.summarizer import chunk_transcript

        short_text = "This is a short transcript."
        chunks = chunk_transcript(short_text)

        assert len(chunks) == 1
        assert chunks[0] == short_text

    def test_chunk_transcript_splits_long_text(self):
        """Test that long transcripts are split into chunks."""
        from src.summarizer import chunk_transcript

        # Create a long transcript (use small max_tokens for testing)
        long_text = ". ".join(["This is sentence number " + str(i) for i in range(100)])
        chunks = chunk_transcript(long_text, max_tokens=50)  # ~200 chars max

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_transcript_preserves_sentence_endings(self):
        """Test that chunks end with periods."""
        from src.summarizer import chunk_transcript

        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_transcript(text, max_tokens=10)  # Force chunking

        for chunk in chunks:
            assert chunk.endswith('.')

    def test_chunk_transcript_empty_text(self):
        """Test handling of empty transcript."""
        from src.summarizer import chunk_transcript

        chunks = chunk_transcript("")

        assert len(chunks) == 1
        assert chunks[0] == ""


class TestSummarizeLongTranscript:
    """Tests for summarize_long_transcript function."""

    @patch('src.summarizer.summarize_transcript')
    @patch('src.summarizer.chunk_transcript')
    def test_summarize_long_transcript_single_chunk(
        self, mock_chunk, mock_summarize
    ):
        """Test that single-chunk transcripts are summarized directly."""
        from src.summarizer import summarize_long_transcript

        mock_chunk.return_value = ["Short transcript"]
        mock_summarize.return_value = "This is the summary."

        result = summarize_long_transcript(
            "Short transcript",
            "Video Title",
            "https://youtube.com/..."
        )

        assert result == "This is the summary."
        mock_summarize.assert_called_once_with(
            "Short transcript",
            "Video Title",
            "https://youtube.com/..."
        )

    @patch('src.summarizer.summarize_transcript')
    @patch('src.summarizer.chunk_transcript')
    def test_summarize_long_transcript_multiple_chunks(
        self, mock_chunk, mock_summarize
    ):
        """Test multi-chunk summarization."""
        from src.summarizer import summarize_long_transcript

        mock_chunk.return_value = ["Chunk 1", "Chunk 2", "Chunk 3"]
        mock_summarize.side_effect = [
            "Summary of chunk 1.",
            "Summary of chunk 2.",
            "Summary of chunk 3.",
            "Final combined summary."
        ]

        result = summarize_long_transcript(
            "Long transcript...",
            "Video Title"
        )

        assert result == "Final combined summary."
        assert mock_summarize.call_count == 4

        # Verify chunk summaries were called with part numbers
        calls = mock_summarize.call_args_list
        assert "Part 1" in calls[0][0][1]
        assert "Part 2" in calls[1][0][1]
        assert "Part 3" in calls[2][0][1]


class TestCostTracking:
    """Tests for cost tracking and logging."""

    @patch('src.summarizer.logger')
    @patch('src.summarizer.get_openai_client')
    def test_summarize_logs_cost(self, mock_get_client, mock_logger):
        """Test that summarization logs cost estimate."""
        from src.summarizer import summarize_transcript

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary"
        mock_response.usage.total_tokens = 1000
        mock_response.usage.prompt_tokens = 900
        mock_response.usage.completion_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response

        summarize_transcript("Test", "Title")

        # Verify logger.info was called with cost information
        assert mock_logger.info.called
        log_call = mock_logger.info.call_args[0][0]
        assert "1000 tokens" in log_call
        assert "$" in log_call

    @patch('src.summarizer.logger')
    @patch('src.summarizer.os.makedirs')
    @patch('src.summarizer.get_openai_client')
    def test_audio_logs_cost(self, mock_get_client, mock_makedirs, mock_logger):
        """Test that audio generation logs cost estimate."""
        from src.summarizer import generate_audio_narration

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_client.audio.speech.create.return_value = mock_response

        generate_audio_narration("This is a test summary with some text.", "vid123")

        # Verify logger.info was called with character count
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("characters" in call for call in info_calls)
        assert any("$" in call for call in info_calls)
