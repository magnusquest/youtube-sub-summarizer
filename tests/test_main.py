"""Unit tests for main pipeline module.

These tests use mocks to avoid making real API calls during testing.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call
import logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before and after each test."""
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()
    original_level = root_logger.level

    yield

    # Restore original state
    root_logger.handlers.clear()
    for handler in original_handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(original_level)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_creates_handlers(self):
        """Test that logging is configured with console and file handlers."""
        from src.main import setup_logging

        # Clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup_logging(verbose=False)

        # Should have created handlers (console + file)
        assert len(root_logger.handlers) >= 1  # At least console handler

    def test_setup_logging_verbose_sets_debug_level(self):
        """Test that verbose mode sets DEBUG logging level."""
        from src.main import setup_logging

        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup_logging(verbose=True)

        assert root_logger.level == logging.DEBUG

    def test_setup_logging_default_sets_info_level(self):
        """Test that default mode sets INFO logging level."""
        from src.main import setup_logging

        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup_logging(verbose=False)

        assert root_logger.level == logging.INFO


class TestRunPipeline:
    """Tests for run_pipeline function."""

    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_no_subscriptions(
        self, mock_youtube_class, mock_email_class, mock_db_class
    ):
        """Test pipeline with no subscriptions."""
        from src.main import run_pipeline

        # Setup mocks
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = []
        mock_youtube_class.return_value = mock_youtube

        mock_db = MagicMock()
        mock_db.get_processing_stats.return_value = {
            'total_videos': 0,
            'processed_today': 0,
            'processed_this_week': 0
        }
        mock_db_class.return_value = mock_db

        stats = run_pipeline(dry_run=True)

        assert stats['total_videos_found'] == 0
        assert stats['new_videos'] == 0
        assert stats['processed'] == 0
        mock_youtube.get_subscriptions.assert_called_once()

    @patch('src.main.get_transcript')
    @patch('src.main.create_summary_with_audio')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_processes_new_video(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_create_summary, mock_get_transcript
    ):
        """Test pipeline successfully processes a new video."""
        from src.main import run_pipeline

        # Setup YouTube mock
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {
                'video_id': 'vid1',
                'title': 'Test Video',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1'
            }
        ]
        mock_youtube_class.return_value = mock_youtube

        # Setup Database mock
        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = False
        mock_db.get_processing_stats.return_value = {
            'total_videos': 1,
            'processed_today': 1,
            'processed_this_week': 1
        }
        mock_db_class.return_value = mock_db

        # Setup transcript mock
        mock_get_transcript.return_value = "This is a test transcript."

        # Setup summarizer mock
        mock_create_summary.return_value = {
            'summary': 'Test summary',
            'audio_path': '/tmp/audio.mp3'
        }

        stats = run_pipeline(dry_run=True)

        assert stats['total_videos_found'] == 1
        assert stats['new_videos'] == 1
        assert stats['processed'] == 1
        assert stats['failed'] == 0
        assert stats['skipped'] == 0

        mock_get_transcript.assert_called_once_with('vid1')
        mock_create_summary.assert_called_once()
        mock_db.mark_video_processed.assert_called()

    @patch('src.main.get_transcript')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_skips_video_without_transcript(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_get_transcript
    ):
        """Test pipeline skips video when transcript is not available."""
        from src.main import run_pipeline

        # Setup YouTube mock
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {
                'video_id': 'vid1',
                'title': 'Test Video',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1'
            }
        ]
        mock_youtube_class.return_value = mock_youtube

        # Setup Database mock
        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = False
        mock_db.get_processing_stats.return_value = {
            'total_videos': 1,
            'processed_today': 1,
            'processed_this_week': 1
        }
        mock_db_class.return_value = mock_db

        # No transcript available
        mock_get_transcript.return_value = None

        stats = run_pipeline(dry_run=True)

        assert stats['skipped'] == 1
        assert stats['processed'] == 0

        # Video should be marked as skipped
        mock_db.mark_video_processed.assert_called_once()
        call_args = mock_db.mark_video_processed.call_args
        assert call_args[1]['status'] == 'skipped'

    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_skips_already_processed_video(
        self, mock_youtube_class, mock_email_class, mock_db_class
    ):
        """Test pipeline skips videos that have already been processed."""
        from src.main import run_pipeline

        # Setup YouTube mock
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {
                'video_id': 'vid1',
                'title': 'Test Video',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1'
            }
        ]
        mock_youtube_class.return_value = mock_youtube

        # Setup Database mock - video already processed
        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = True
        mock_db.get_processing_stats.return_value = {
            'total_videos': 1,
            'processed_today': 0,
            'processed_this_week': 1
        }
        mock_db_class.return_value = mock_db

        stats = run_pipeline(dry_run=True)

        assert stats['total_videos_found'] == 1
        assert stats['new_videos'] == 0
        assert stats['processed'] == 0

    @patch('src.main.get_transcript')
    @patch('src.main.create_summary_with_audio')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_sends_email_when_not_dry_run(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_create_summary, mock_get_transcript
    ):
        """Test pipeline sends email when not in dry run mode."""
        from src.main import run_pipeline

        # Setup mocks
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {
                'video_id': 'vid1',
                'title': 'Test Video',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1'
            }
        ]
        mock_youtube_class.return_value = mock_youtube

        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = False
        mock_db.get_processing_stats.return_value = {
            'total_videos': 1,
            'processed_today': 1,
            'processed_this_week': 1
        }
        mock_db_class.return_value = mock_db

        mock_get_transcript.return_value = "Test transcript"
        mock_create_summary.return_value = {
            'summary': 'Test summary',
            'audio_path': '/tmp/audio.mp3'
        }

        run_pipeline(dry_run=False)

        mock_email.send_summary_email.assert_called_once()

    @patch('src.main.get_transcript')
    @patch('src.main.create_summary_with_audio')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_does_not_send_email_in_dry_run(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_create_summary, mock_get_transcript
    ):
        """Test pipeline does not send email in dry run mode."""
        from src.main import run_pipeline

        # Setup mocks
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {
                'video_id': 'vid1',
                'title': 'Test Video',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1'
            }
        ]
        mock_youtube_class.return_value = mock_youtube

        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = False
        mock_db.get_processing_stats.return_value = {
            'total_videos': 1,
            'processed_today': 1,
            'processed_this_week': 1
        }
        mock_db_class.return_value = mock_db

        mock_get_transcript.return_value = "Test transcript"
        mock_create_summary.return_value = {
            'summary': 'Test summary',
            'audio_path': '/tmp/audio.mp3'
        }

        run_pipeline(dry_run=True)

        mock_email.send_summary_email.assert_not_called()

    @patch('src.main.get_transcript')
    @patch('src.main.create_summary_with_audio')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_handles_processing_error(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_create_summary, mock_get_transcript
    ):
        """Test pipeline handles processing errors gracefully."""
        from src.main import run_pipeline

        # Setup mocks
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {
                'video_id': 'vid1',
                'title': 'Test Video',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1'
            }
        ]
        mock_youtube_class.return_value = mock_youtube

        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = False
        mock_db.get_processing_stats.return_value = {
            'total_videos': 1,
            'processed_today': 0,
            'processed_this_week': 1
        }
        mock_db_class.return_value = mock_db

        mock_get_transcript.return_value = "Test transcript"
        mock_create_summary.side_effect = Exception("API error")

        stats = run_pipeline(dry_run=True)

        assert stats['failed'] == 1
        assert stats['processed'] == 0

        # Video should be marked as failed
        mock_db.mark_video_processed.assert_called_once()
        call_args = mock_db.mark_video_processed.call_args
        assert call_args[1]['status'] == 'failed'
        assert 'API error' in call_args[1]['error_message']

    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_handles_channel_fetch_error(
        self, mock_youtube_class, mock_email_class, mock_db_class
    ):
        """Test pipeline continues when fetching from one channel fails."""
        from src.main import run_pipeline

        # Setup YouTube mock - first channel succeeds, second fails
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'},
            {'channel_id': 'ch2', 'channel_name': 'Channel 2'}
        ]
        mock_youtube.get_recent_videos.side_effect = [
            [],  # First channel returns no videos
            Exception("Network error")  # Second channel fails
        ]
        mock_youtube_class.return_value = mock_youtube

        mock_db = MagicMock()
        mock_db.get_processing_stats.return_value = {
            'total_videos': 0,
            'processed_today': 0,
            'processed_this_week': 0
        }
        mock_db_class.return_value = mock_db

        # Should not raise exception
        stats = run_pipeline(dry_run=True)

        # Pipeline should continue despite the error
        assert stats['total_videos_found'] == 0

    @patch('src.main.get_transcript')
    @patch('src.main.create_summary_with_audio')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_run_pipeline_uses_hours_parameter(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_create_summary, mock_get_transcript
    ):
        """Test pipeline passes hours parameter to get_recent_videos."""
        from src.main import run_pipeline

        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = []
        mock_youtube_class.return_value = mock_youtube

        mock_db = MagicMock()
        mock_db.get_processing_stats.return_value = {
            'total_videos': 0,
            'processed_today': 0,
            'processed_this_week': 0
        }
        mock_db_class.return_value = mock_db

        run_pipeline(dry_run=True, hours=48)

        mock_youtube.get_recent_videos.assert_called_once_with('ch1', hours=48)


class TestMain:
    """Tests for main CLI function."""

    @patch('src.main.validate_config')
    @patch('src.main.run_pipeline')
    @patch('src.main.setup_logging')
    def test_main_returns_zero_on_success(
        self, mock_setup_logging, mock_run_pipeline, mock_validate_config
    ):
        """Test main returns 0 on successful execution."""
        from src.main import main

        mock_run_pipeline.return_value = {'processed': 1}

        exit_code = main(['--dry-run'])

        assert exit_code == 0
        mock_validate_config.assert_called_once()
        mock_run_pipeline.assert_called_once_with(dry_run=True, hours=24)

    @patch('src.main.validate_config')
    @patch('src.main.run_pipeline')
    @patch('src.main.setup_logging')
    def test_main_returns_one_on_failure(
        self, mock_setup_logging, mock_run_pipeline, mock_validate_config
    ):
        """Test main returns 1 on failure."""
        from src.main import main

        mock_run_pipeline.side_effect = Exception("Pipeline error")

        exit_code = main(['--dry-run'])

        assert exit_code == 1

    @patch('src.main.validate_config')
    @patch('src.main.run_pipeline')
    @patch('src.main.setup_logging')
    def test_main_returns_one_on_config_error(
        self, mock_setup_logging, mock_run_pipeline, mock_validate_config
    ):
        """Test main returns 1 on configuration error."""
        from src.main import main

        mock_validate_config.side_effect = ValueError("Missing API key")

        exit_code = main(['--dry-run'])

        assert exit_code == 1
        mock_run_pipeline.assert_not_called()

    @patch('src.main.validate_config')
    @patch('src.main.run_pipeline')
    @patch('src.main.setup_logging')
    def test_main_parses_hours_argument(
        self, mock_setup_logging, mock_run_pipeline, mock_validate_config
    ):
        """Test main correctly parses --hours argument."""
        from src.main import main

        mock_run_pipeline.return_value = {'processed': 0}

        main(['--hours', '48'])

        mock_run_pipeline.assert_called_once_with(dry_run=False, hours=48)

    @patch('src.main.validate_config')
    @patch('src.main.run_pipeline')
    @patch('src.main.setup_logging')
    def test_main_parses_verbose_argument(
        self, mock_setup_logging, mock_run_pipeline, mock_validate_config
    ):
        """Test main correctly parses --verbose argument."""
        from src.main import main

        mock_run_pipeline.return_value = {'processed': 0}

        main(['--verbose'])

        mock_setup_logging.assert_called_once_with(verbose=True)

    @patch('src.main.validate_config')
    @patch('src.main.run_pipeline')
    @patch('src.main.setup_logging')
    def test_main_default_arguments(
        self, mock_setup_logging, mock_run_pipeline, mock_validate_config
    ):
        """Test main uses correct default arguments."""
        from src.main import main

        mock_run_pipeline.return_value = {'processed': 0}

        main([])

        mock_setup_logging.assert_called_once_with(verbose=False)
        mock_run_pipeline.assert_called_once_with(dry_run=False, hours=24)


class TestPipelineIntegration:
    """Integration tests for pipeline components."""

    @patch('src.main.get_transcript')
    @patch('src.main.create_summary_with_audio')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_pipeline_processes_multiple_videos(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_create_summary, mock_get_transcript
    ):
        """Test pipeline processes multiple videos correctly."""
        from src.main import run_pipeline

        # Setup YouTube mock with multiple videos
        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {'video_id': 'vid1', 'title': 'Video 1', 'channel_id': 'ch1',
             'channel_name': 'Channel 1'},
            {'video_id': 'vid2', 'title': 'Video 2', 'channel_id': 'ch1',
             'channel_name': 'Channel 1'},
            {'video_id': 'vid3', 'title': 'Video 3', 'channel_id': 'ch1',
             'channel_name': 'Channel 1'}
        ]
        mock_youtube_class.return_value = mock_youtube

        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = False
        mock_db.get_processing_stats.return_value = {
            'total_videos': 3,
            'processed_today': 3,
            'processed_this_week': 3
        }
        mock_db_class.return_value = mock_db

        mock_get_transcript.return_value = "Test transcript"
        mock_create_summary.return_value = {
            'summary': 'Test summary',
            'audio_path': '/tmp/audio.mp3'
        }

        stats = run_pipeline(dry_run=True)

        assert stats['total_videos_found'] == 3
        assert stats['new_videos'] == 3
        assert stats['processed'] == 3
        assert mock_get_transcript.call_count == 3
        assert mock_create_summary.call_count == 3

    @patch('src.main.get_transcript')
    @patch('src.main.create_summary_with_audio')
    @patch('src.main.Database')
    @patch('src.main.EmailSender')
    @patch('src.main.YouTubeClient')
    def test_pipeline_handles_mixed_success_and_failure(
        self, mock_youtube_class, mock_email_class, mock_db_class,
        mock_create_summary, mock_get_transcript
    ):
        """Test pipeline correctly handles mix of successes and failures."""
        from src.main import run_pipeline

        mock_youtube = MagicMock()
        mock_youtube.get_subscriptions.return_value = [
            {'channel_id': 'ch1', 'channel_name': 'Channel 1'}
        ]
        mock_youtube.get_recent_videos.return_value = [
            {'video_id': 'vid1', 'title': 'Video 1', 'channel_id': 'ch1',
             'channel_name': 'Channel 1'},
            {'video_id': 'vid2', 'title': 'Video 2', 'channel_id': 'ch1',
             'channel_name': 'Channel 1'},
            {'video_id': 'vid3', 'title': 'Video 3', 'channel_id': 'ch1',
             'channel_name': 'Channel 1'}
        ]
        mock_youtube_class.return_value = mock_youtube

        mock_db = MagicMock()
        mock_db.is_video_processed.return_value = False
        mock_db.get_processing_stats.return_value = {
            'total_videos': 3,
            'processed_today': 2,
            'processed_this_week': 3
        }
        mock_db_class.return_value = mock_db

        # First has transcript, second has none, third has error
        mock_get_transcript.side_effect = [
            "Test transcript",
            None,
            "Test transcript"
        ]
        mock_create_summary.side_effect = [
            {'summary': 'Test summary', 'audio_path': '/tmp/audio.mp3'},
            Exception("API error")
        ]

        stats = run_pipeline(dry_run=True)

        assert stats['processed'] == 1
        assert stats['skipped'] == 1
        assert stats['failed'] == 1
