#!/usr/bin/env python3
"""Test script to process a single YouTube video.

This bypasses the subscription fetching and lets you test the core pipeline
with a single video ID or URL.
"""

import argparse
import logging
import re
import sys
from datetime import datetime, timezone

from src.config import validate_config
from src.database import Database
from src.email_sender import EmailSender
from src.summarizer import create_summary_with_audio
from src.transcript import get_transcript
from src.youtube_client import YouTubeClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_video_id_from_url(url: str) -> str:
    """Extract video ID from various YouTube URL formats.

    Supports formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID

    Args:
        url: YouTube URL

    Returns:
        Extracted video ID

    Raises:
        ValueError: If video ID cannot be extracted from URL
    """
    # Try different URL patterns
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_video_metadata(video_id: str) -> dict:
    """Fetch video metadata from YouTube API.

    Args:
        video_id: YouTube video ID

    Returns:
        Dictionary with video_id, title, channel_id, channel_name

    Raises:
        Exception: If unable to fetch video metadata
    """
    try:
        client = YouTubeClient()

        # Use videos.list API to get video details
        response = client._api_call_with_retry(
            lambda: client.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
        )
        client.quota_tracker.log_usage(f'videos.list ({video_id})', 1)

        items = response.get('items', [])
        if not items:
            raise ValueError(f"No video found for ID: {video_id}")

        snippet = items[0]['snippet']
        return {
            'video_id': video_id,
            'title': snippet['title'],
            'channel_id': snippet['channelId'],
            'channel_name': snippet['channelTitle']
        }

    except Exception as e:
        logger.error(f"Error fetching video metadata: {e}")
        raise


def process_single_video(video_id: str, dry_run: bool = False, fetch_metadata: bool = True) -> bool:
    """Process a single YouTube video through the full pipeline.

    Args:
        video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')
        dry_run: If True, don't send email
        fetch_metadata: If True, fetch actual video metadata from YouTube API

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"=== Processing single video: {video_id} ===")
    
    # Initialize components
    db = Database()
    email_sender = EmailSender()

    # Check if already processed
    if db.is_video_processed(video_id):
        logger.warning(f"Video {video_id} has already been processed")
        logger.info("To reprocess, run: ./scripts/clear_processed_videos.sh")
        return False

    try:
        # 0. Fetch video metadata (if enabled)
        if fetch_metadata:
            logger.info("Step 0: Fetching video metadata from YouTube API...")
            video_metadata = get_video_metadata(video_id)
            video_title = video_metadata['title']
            channel_name = video_metadata['channel_name']
            channel_id = video_metadata['channel_id']
            logger.info(f"✓ Video: {video_title}")
            logger.info(f"✓ Channel: {channel_name}")
        else:
            # Use fallback metadata
            video_title = f"Test Video {video_id}"
            channel_name = "Test Channel"
            channel_id = "test"
            logger.info("Step 0: SKIPPED (using fallback metadata)")

        video_url = f"https://youtube.com/watch?v={video_id}"

        # 1. Extract transcript
        logger.info("Step 1: Extracting transcript...")
        transcript = get_transcript(video_id)
        
        if not transcript:
            logger.error("No transcript available for this video")
            logger.info("Try a different video that has captions/subtitles")
            return False
        
        logger.info(f"✓ Transcript extracted: {len(transcript)} characters")
        
        # 2. Generate summary and audio
        logger.info("Step 2: Generating AI summary and audio narration...")

        result = create_summary_with_audio(
            transcript=transcript,
            video_title=video_title,
            video_id=video_id,
            video_url=video_url
        )
        
        summary = result['summary']
        audio_path = result['audio_path']
        
        logger.info(f"✓ Summary generated ({len(summary)} chars)")
        logger.info(f"Summary: {summary}")
        logger.info(f"✓ Audio saved to: {audio_path}")
        
        # 3. Send email (or skip if dry-run)
        if not dry_run:
            logger.info("Step 3: Sending email...")
            video_data = {
                'video_id': video_id,
                'title': video_title,
                'channel_name': channel_name,
                'url': video_url
            }
            email_sender.send_summary_email(video_data, summary, audio_path)
            logger.info("✓ Email sent successfully")
        else:
            logger.info("Step 3: SKIPPED (dry-run mode)")

        # 4. Mark as processed
        db.mark_video_processed({
            'video_id': video_id,
            'title': video_title,
            'channel_id': channel_id,
            'channel_name': channel_name
        }, status='completed')
        logger.info("✓ Marked as processed in database")
        
        logger.info(f"\n=== SUCCESS! Video {video_id} processed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Test the pipeline with a single YouTube video',
        epilog='Examples:\n'
               '  %(prog)s --id dQw4w9WgXcQ\n'
               '  %(prog)s --url "https://youtube.com/watch?v=dQw4w9WgXcQ"\n'
               '  %(prog)s --url "https://youtu.be/dQw4w9WgXcQ" --dry-run\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Create mutually exclusive group for --id and --url
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--id',
        dest='video_id',
        help='YouTube video ID (e.g., dQw4w9WgXcQ)'
    )
    input_group.add_argument(
        '--url',
        dest='video_url',
        help='YouTube video URL (e.g., https://youtube.com/watch?v=dQw4w9WgXcQ)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process but do not send email'
    )
    parser.add_argument(
        '--no-fetch-metadata',
        action='store_true',
        help='Skip fetching video metadata from YouTube API (use fallback values)'
    )

    args = parser.parse_args()

    # Extract video ID from URL if provided
    if args.video_url:
        try:
            video_id = extract_video_id_from_url(args.video_url)
            logger.info(f"Extracted video ID: {video_id}")
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
    else:
        video_id = args.video_id
    
    try:
        # Validate configuration
        validate_config()

        # Process the video
        success = process_single_video(
            video_id,
            dry_run=args.dry_run,
            fetch_metadata=not args.no_fetch_metadata
        )

        sys.exit(0 if success else 1)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("\nMake sure your .env file has:")
        logger.info("- OPENAI_API_KEY (for summarization)")
        logger.info("- SMTP credentials (if not using --dry-run)")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
