"""YouTube Data API client for fetching subscriptions and recent videos.

This module provides a YouTubeClient class that wraps the YouTube Data API v3
to fetch user subscriptions and recent videos from channels.

Quota Usage Notes:
- Fetching subscriptions: 1 unit per page (50 subscriptions/page)
- Fetching channel details: 1 unit per call
- Fetching playlist items: 1 unit per page
- Using search API: 100 units per call (avoided in favor of playlist approach)

Daily quota limit: 10,000 units
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import YOUTUBE_API_KEY

# Configure logging
logger = logging.getLogger(__name__)


class QuotaTracker:
    """Tracks YouTube API quota usage."""
    
    def __init__(self):
        self.total_units = 0
        self.operations = []
    
    def log_usage(self, operation: str, units: int):
        """Log quota usage for an API operation.
        
        Args:
            operation: Description of the API operation.
            units: Number of quota units consumed.
        """
        self.total_units += units
        self.operations.append({'operation': operation, 'units': units})
        logger.info(f"YouTube API: {operation} used {units} quota units (total: {self.total_units})")
    
    def get_total_usage(self) -> int:
        """Return total quota units used."""
        return self.total_units
    
    def reset(self):
        """Reset the quota tracker."""
        self.total_units = 0
        self.operations = []


class YouTubeClient:
    """Client for interacting with YouTube Data API v3.
    
    This client provides methods to fetch user subscriptions and recent videos
    from channels, with built-in retry logic and quota tracking.
    
    Attributes:
        quota_tracker: QuotaTracker instance for monitoring API usage.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the YouTube client.
        
        Args:
            api_key: YouTube Data API key. If not provided, uses YOUTUBE_API_KEY
                    from environment configuration.
        
        Raises:
            ValueError: If no API key is provided or configured.
        """
        self._api_key = api_key or YOUTUBE_API_KEY
        if not self._api_key:
            raise ValueError("YouTube API key is required")
        
        self._youtube = None
        self.quota_tracker = QuotaTracker()
    
    @property
    def youtube(self):
        """Lazily initialize and return the YouTube API service object."""
        if self._youtube is None:
            self._youtube = build('youtube', 'v3', developerKey=self._api_key)
        return self._youtube
    
    def _api_call_with_retry(self, func, max_retries: int = 3):
        """Execute an API call with retry logic for transient failures.
        
        Args:
            func: Callable that executes the API call.
            max_retries: Maximum number of retry attempts.
        
        Returns:
            The API response.
        
        Raises:
            HttpError: If the API call fails after all retries.
            Exception: If max retries are exceeded.
        """
        import time
        
        for attempt in range(max_retries):
            try:
                return func()
            except HttpError as e:
                if e.resp.status in [403, 429, 500, 503]:
                    # Quota exceeded, rate limit, or server error - retry with backoff
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"API error (status {e.resp.status}), "
                        f"retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    # Non-retryable error
                    logger.error(f"YouTube API error: {e}")
                    raise
        
        raise Exception(f"Max retries ({max_retries}) exceeded for API call")
    
    def get_subscriptions(self) -> list[dict]:
        """Retrieve all channels the authenticated user is subscribed to.
        
        Note: This method requires OAuth 2.0 authentication with the
        'youtube.readonly' scope, as it uses 'mine=True'. When using
        only an API key, this will fail.
        
        Returns:
            List of dictionaries containing channel_id and channel_name
            for each subscription.
        
        Raises:
            HttpError: If the API call fails.
        """
        subscriptions = []
        page_token = None
        page_count = 0
        
        while True:
            def make_request():
                return self.youtube.subscriptions().list(
                    part='snippet',
                    mine=True,
                    maxResults=50,
                    pageToken=page_token
                ).execute()
            
            response = self._api_call_with_retry(make_request)
            page_count += 1
            self.quota_tracker.log_usage(f'subscriptions.list (page {page_count})', 1)
            
            for item in response.get('items', []):
                subscriptions.append({
                    'channel_id': item['snippet']['resourceId']['channelId'],
                    'channel_name': item['snippet']['title']
                })
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        
        logger.info(f"Retrieved {len(subscriptions)} subscriptions")
        return subscriptions
    
    def get_channel_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """Get the uploads playlist ID for a channel.
        
        Args:
            channel_id: The YouTube channel ID.
        
        Returns:
            The uploads playlist ID, or None if not found.
        
        Raises:
            HttpError: If the API call fails.
        """
        def make_request():
            return self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
        
        response = self._api_call_with_retry(make_request)
        self.quota_tracker.log_usage(f'channels.list ({channel_id})', 1)
        
        items = response.get('items', [])
        if not items:
            logger.warning(f"No channel found for ID: {channel_id}")
            return None
        
        return items[0]['contentDetails']['relatedPlaylists']['uploads']
    
    def get_recent_videos(self, channel_id: str, hours: int = 24) -> list[dict]:
        """Fetch recent videos from a channel's uploads playlist.
        
        This method uses the uploads playlist approach instead of the search API
        to conserve quota (1 unit vs 100 units per call).
        
        Args:
            channel_id: The YouTube channel ID.
            hours: Number of hours to look back for recent videos (default: 24).
        
        Returns:
            List of dictionaries containing video details for videos
            published within the specified time window.
        
        Raises:
            HttpError: If the API call fails.
        """
        # Get the uploads playlist ID
        uploads_playlist_id = self.get_channel_uploads_playlist_id(channel_id)
        if not uploads_playlist_id:
            return []
        
        # Calculate the cutoff time
        published_after = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        videos = []
        page_token = None
        page_count = 0
        
        while True:
            def make_request():
                return self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=page_token
                ).execute()
            
            response = self._api_call_with_retry(make_request)
            page_count += 1
            self.quota_tracker.log_usage(
                f'playlistItems.list ({channel_id}, page {page_count})', 1
            )
            
            items = response.get('items', [])
            if not items:
                break
            
            # Check if we've gone past the time window
            all_older = True
            
            for item in items:
                published_at_str = item['snippet']['publishedAt']
                # Parse ISO 8601 date format
                published_at = datetime.fromisoformat(
                    published_at_str.replace('Z', '+00:00')
                )
                
                if published_at >= published_after:
                    all_older = False
                    videos.append({
                        'video_id': item['contentDetails']['videoId'],
                        'title': item['snippet']['title'],
                        'channel_id': channel_id,
                        'channel_name': item['snippet'].get('channelTitle', ''),
                        'published_at': published_at_str,
                        'description': item['snippet'].get('description', ''),
                        'thumbnail_url': item['snippet'].get('thumbnails', {}).get(
                            'default', {}
                        ).get('url', '')
                    })
            
            # Stop pagination if all items are older than our window
            # or if there's no next page
            page_token = response.get('nextPageToken')
            if all_older or not page_token:
                break
        
        logger.info(
            f"Found {len(videos)} videos from channel {channel_id} "
            f"in the last {hours} hours"
        )
        return videos
    
    def get_video_duration(self, video_id: str) -> Optional[int]:
        """Get the duration of a video in seconds.

        Args:
            video_id: The YouTube video ID.

        Returns:
            Duration in seconds, or None if not found.

        Raises:
            HttpError: If the API call fails.
        """
        def make_request():
            return self.youtube.videos().list(
                part='contentDetails',
                id=video_id
            ).execute()

        response = self._api_call_with_retry(make_request)
        self.quota_tracker.log_usage(f'videos.list ({video_id})', 1)

        items = response.get('items', [])
        if not items:
            logger.warning(f"No video found for ID: {video_id}")
            return None

        # Parse ISO 8601 duration format (e.g., "PT1H23M45S")
        duration_str = items[0]['contentDetails']['duration']
        return self._parse_duration(duration_str)

    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration format to seconds.

        Args:
            duration_str: ISO 8601 duration string (e.g., "PT1H23M45S").

        Returns:
            Duration in seconds.
        """
        import re

        # Pattern to extract hours, minutes, and seconds
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)

        if not match:
            logger.warning(f"Failed to parse duration: {duration_str}")
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def get_recent_videos_from_subscriptions(
        self, hours: int = 24, max_channels: Optional[int] = None
    ) -> list[dict]:
        """Fetch recent videos from all subscribed channels.

        Args:
            hours: Number of hours to look back for recent videos (default: 24).
            max_channels: Maximum number of channels to check (for quota management).

        Returns:
            List of all recent videos from subscribed channels.

        Raises:
            HttpError: If any API call fails.
        """
        subscriptions = self.get_subscriptions()

        if max_channels:
            subscriptions = subscriptions[:max_channels]

        all_videos = []
        for subscription in subscriptions:
            try:
                videos = self.get_recent_videos(subscription['channel_id'], hours)
                all_videos.extend(videos)
            except HttpError as e:
                logger.error(
                    f"Error fetching videos from {subscription['channel_name']}: {e}"
                )
                continue

        # Sort by published date, newest first
        all_videos.sort(key=lambda x: x['published_at'], reverse=True)

        logger.info(
            f"Retrieved {len(all_videos)} total recent videos "
            f"from {len(subscriptions)} channels"
        )
        return all_videos


def get_youtube_client(api_key: Optional[str] = None) -> YouTubeClient:
    """Factory function to create a YouTubeClient instance.
    
    Args:
        api_key: Optional YouTube API key. If not provided, uses environment config.
    
    Returns:
        Configured YouTubeClient instance.
    """
    return YouTubeClient(api_key=api_key)
