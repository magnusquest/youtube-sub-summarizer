"""Unit tests for YouTube client module.

These tests use mocks to avoid consuming API quota during testing.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from googleapiclient.errors import HttpError


class TestQuotaTracker:
    """Tests for QuotaTracker class."""
    
    def test_log_usage_tracks_units(self):
        """Test that log_usage correctly tracks quota units."""
        from src.youtube_client import QuotaTracker
        
        tracker = QuotaTracker()
        tracker.log_usage('test_operation', 10)
        
        assert tracker.get_total_usage() == 10
        assert len(tracker.operations) == 1
        assert tracker.operations[0] == {'operation': 'test_operation', 'units': 10}
    
    def test_log_usage_accumulates(self):
        """Test that multiple operations accumulate correctly."""
        from src.youtube_client import QuotaTracker
        
        tracker = QuotaTracker()
        tracker.log_usage('op1', 5)
        tracker.log_usage('op2', 10)
        tracker.log_usage('op3', 3)
        
        assert tracker.get_total_usage() == 18
        assert len(tracker.operations) == 3
    
    def test_reset(self):
        """Test that reset clears all tracking data."""
        from src.youtube_client import QuotaTracker
        
        tracker = QuotaTracker()
        tracker.log_usage('op1', 10)
        tracker.reset()
        
        assert tracker.get_total_usage() == 0
        assert len(tracker.operations) == 0


class TestYouTubeClient:
    """Tests for YouTubeClient class."""
    
    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        from src.youtube_client import YouTubeClient
        
        client = YouTubeClient(api_key='test_api_key')
        assert client._api_key == 'test_api_key'
    
    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        from src.youtube_client import YouTubeClient
        
        with patch('src.youtube_client.YOUTUBE_API_KEY', None):
            with pytest.raises(ValueError, match="YouTube API key is required"):
                YouTubeClient(api_key=None)
    
    @patch('src.youtube_client.build')
    def test_youtube_property_lazy_init(self, mock_build):
        """Test that YouTube service is lazily initialized."""
        from src.youtube_client import YouTubeClient
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        client = YouTubeClient(api_key='test_key')
        
        # Service should not be built yet
        mock_build.assert_not_called()
        
        # Access the property
        service = client.youtube
        
        # Now it should be built
        mock_build.assert_called_once_with('youtube', 'v3', developerKey='test_key')
        assert service == mock_service
    
    @patch('src.youtube_client.build')
    def test_get_subscriptions_single_page(self, mock_build):
        """Test fetching subscriptions with single page of results."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        mock_youtube.subscriptions().list().execute.return_value = {
            'items': [
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC123'},
                        'title': 'Test Channel 1'
                    }
                },
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC456'},
                        'title': 'Test Channel 2'
                    }
                }
            ]
        }
        
        client = YouTubeClient(api_key='test_key')
        subscriptions = client.get_subscriptions()
        
        assert len(subscriptions) == 2
        assert subscriptions[0] == {'channel_id': 'UC123', 'channel_name': 'Test Channel 1'}
        assert subscriptions[1] == {'channel_id': 'UC456', 'channel_name': 'Test Channel 2'}
    
    @patch('src.youtube_client.build')
    def test_get_subscriptions_with_pagination(self, mock_build):
        """Test fetching subscriptions with multiple pages."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # First page
        first_response = {
            'items': [
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC123'},
                        'title': 'Channel 1'
                    }
                }
            ],
            'nextPageToken': 'token123'
        }
        
        # Second page (no next token)
        second_response = {
            'items': [
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC456'},
                        'title': 'Channel 2'
                    }
                }
            ]
        }
        
        mock_youtube.subscriptions().list().execute.side_effect = [
            first_response, second_response
        ]
        
        client = YouTubeClient(api_key='test_key')
        subscriptions = client.get_subscriptions()
        
        assert len(subscriptions) == 2
    
    @patch('src.youtube_client.build')
    def test_get_channel_uploads_playlist_id(self, mock_build):
        """Test fetching uploads playlist ID for a channel."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        mock_youtube.channels().list().execute.return_value = {
            'items': [
                {
                    'contentDetails': {
                        'relatedPlaylists': {
                            'uploads': 'UU123'
                        }
                    }
                }
            ]
        }
        
        client = YouTubeClient(api_key='test_key')
        playlist_id = client.get_channel_uploads_playlist_id('UC123')
        
        assert playlist_id == 'UU123'
    
    @patch('src.youtube_client.build')
    def test_get_channel_uploads_playlist_id_not_found(self, mock_build):
        """Test handling when channel is not found."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        mock_youtube.channels().list().execute.return_value = {'items': []}
        
        client = YouTubeClient(api_key='test_key')
        playlist_id = client.get_channel_uploads_playlist_id('UC_NONEXISTENT')
        
        assert playlist_id is None
    
    @patch('src.youtube_client.build')
    def test_get_recent_videos(self, mock_build):
        """Test fetching recent videos from a channel."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock channel response
        mock_youtube.channels().list().execute.return_value = {
            'items': [
                {
                    'contentDetails': {
                        'relatedPlaylists': {
                            'uploads': 'UU123'
                        }
                    }
                }
            ]
        }
        
        # Create a recent timestamp (1 hour ago)
        recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        # Create an old timestamp (48 hours ago)
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        
        mock_youtube.playlistItems().list().execute.return_value = {
            'items': [
                {
                    'snippet': {
                        'publishedAt': recent_time,
                        'title': 'Recent Video',
                        'channelTitle': 'Test Channel',
                        'description': 'A recent video',
                        'thumbnails': {
                            'default': {'url': 'http://example.com/thumb.jpg'}
                        }
                    },
                    'contentDetails': {
                        'videoId': 'vid123'
                    }
                },
                {
                    'snippet': {
                        'publishedAt': old_time,
                        'title': 'Old Video',
                        'channelTitle': 'Test Channel',
                        'description': 'An old video',
                        'thumbnails': {
                            'default': {'url': 'http://example.com/thumb2.jpg'}
                        }
                    },
                    'contentDetails': {
                        'videoId': 'vid456'
                    }
                }
            ]
        }
        
        client = YouTubeClient(api_key='test_key')
        videos = client.get_recent_videos('UC123', hours=24)
        
        # Should only return the recent video
        assert len(videos) == 1
        assert videos[0]['video_id'] == 'vid123'
        assert videos[0]['title'] == 'Recent Video'
    
    @patch('src.youtube_client.build')
    def test_get_recent_videos_channel_not_found(self, mock_build):
        """Test handling when channel is not found."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        mock_youtube.channels().list().execute.return_value = {'items': []}
        
        client = YouTubeClient(api_key='test_key')
        videos = client.get_recent_videos('UC_NONEXISTENT', hours=24)
        
        assert videos == []
    
    @patch('src.youtube_client.build')
    @patch('time.sleep')
    def test_api_call_with_retry_on_rate_limit(self, mock_sleep, mock_build):
        """Test retry logic on rate limit errors."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Create a mock HTTP error response
        mock_resp = MagicMock()
        mock_resp.status = 429
        
        # First two calls fail with rate limit, third succeeds
        mock_youtube.channels().list().execute.side_effect = [
            HttpError(mock_resp, b'Rate limit exceeded'),
            HttpError(mock_resp, b'Rate limit exceeded'),
            {
                'items': [
                    {
                        'contentDetails': {
                            'relatedPlaylists': {'uploads': 'UU123'}
                        }
                    }
                ]
            }
        ]
        
        client = YouTubeClient(api_key='test_key')
        playlist_id = client.get_channel_uploads_playlist_id('UC123')
        
        assert playlist_id == 'UU123'
        assert mock_sleep.call_count == 2
    
    @patch('src.youtube_client.build')
    def test_api_call_non_retryable_error(self, mock_build):
        """Test that non-retryable errors are raised immediately."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        mock_resp = MagicMock()
        mock_resp.status = 404  # Not found - non-retryable
        
        mock_youtube.channels().list().execute.side_effect = HttpError(
            mock_resp, b'Not found'
        )
        
        client = YouTubeClient(api_key='test_key')
        
        with pytest.raises(HttpError):
            client.get_channel_uploads_playlist_id('UC_NONEXISTENT')
    
    @patch('src.youtube_client.build')
    def test_quota_tracking(self, mock_build):
        """Test that quota usage is tracked correctly."""
        from src.youtube_client import YouTubeClient
        
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        mock_youtube.channels().list().execute.return_value = {
            'items': [
                {
                    'contentDetails': {
                        'relatedPlaylists': {'uploads': 'UU123'}
                    }
                }
            ]
        }
        
        recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mock_youtube.playlistItems().list().execute.return_value = {
            'items': [
                {
                    'snippet': {
                        'publishedAt': recent_time,
                        'title': 'Test Video',
                        'channelTitle': 'Test Channel',
                        'description': 'Test',
                        'thumbnails': {'default': {'url': 'http://example.com/t.jpg'}}
                    },
                    'contentDetails': {'videoId': 'vid123'}
                }
            ]
        }
        
        client = YouTubeClient(api_key='test_key')
        client.get_recent_videos('UC123', hours=24)
        
        # Should have 2 API calls: channels.list + playlistItems.list
        assert client.quota_tracker.get_total_usage() == 2
        assert len(client.quota_tracker.operations) == 2


class TestGetYouTubeClient:
    """Tests for get_youtube_client factory function."""
    
    def test_creates_client_with_api_key(self):
        """Test factory function creates client with provided API key."""
        from src.youtube_client import get_youtube_client, YouTubeClient
        
        client = get_youtube_client(api_key='test_key')
        
        assert isinstance(client, YouTubeClient)
        assert client._api_key == 'test_key'
