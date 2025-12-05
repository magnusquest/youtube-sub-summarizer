#!/usr/bin/env python3
"""YouTube Subscription Summarizer - Main Pipeline.

Fetches new videos from YouTube subscriptions, generates AI summaries with audio
narration, and sends email notifications.

This module orchestrates the entire pipeline: fetch → extract → summarize → email.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.config import validate_config
from src.database import Database
from src.email_sender import EmailSender
from src.summarizer import create_summary_with_audio
from src.transcript import get_transcript
from src.youtube_client import YouTubeClient
from src.youtube_oauth import YouTubeOAuthClient

# Ensure logs directory exists
LOGS_DIR = 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with both file and console handlers.

    Args:
        verbose: If True, set logging level to DEBUG. Otherwise INFO.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates when called multiple times
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # Rotating file handler - 10MB max, keep 5 backups
    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, 'pipeline.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)


def run_pipeline(dry_run: bool = False, hours: int = 24, max_duration_minutes: int = 30) -> dict:
    """Main pipeline: fetch videos → process → email.

    Args:
        dry_run: If True, process but don't send emails.
        hours: Check for videos from last N hours.
        max_duration_minutes: Maximum video duration in minutes (default: 30).
                             Videos longer than this will be skipped.

    Returns:
        Dictionary containing pipeline statistics:
            - total_videos_found: Total videos discovered
            - new_videos: Videos not previously processed
            - processed: Successfully processed count
            - failed: Failed processing count
            - skipped: Skipped (no transcript) count
            - skipped_too_long: Skipped (video too long) count
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"=== Pipeline started at {start_time.isoformat()} ===")
    logger.info(f"Dry run mode: {dry_run}")
    logger.info(f"Looking for videos from last {hours} hours")
    logger.info(f"Max video duration: {max_duration_minutes} minutes")

    # Initialize components
    youtube_oauth = YouTubeOAuthClient()
    youtube_api = YouTubeClient()  # For non-authenticated calls (get_recent_videos)
    email_sender = EmailSender()
    db = Database()

    stats = {
        'total_videos_found': 0,
        'new_videos': 0,
        'processed': 0,
        'failed': 0,
        'skipped': 0,
        'skipped_too_long': 0
    }

    try:
        # Authenticate with OAuth
        logger.info("Authenticating with YouTube OAuth...")
        youtube_oauth.authenticate()

        # 1. Get user's subscriptions
        logger.info("Fetching subscriptions...")
        subscriptions = youtube_oauth.get_subscriptions()
        logger.info(f"Found {len(subscriptions)} subscribed channels")

        # 2. Get recent videos from each channel
        logger.info(f"Checking for videos from last {hours} hours...")
        all_videos = []

        for subscription in subscriptions:
            channel_id = subscription['channel_id']
            channel_name = subscription['channel_name']

            try:
                videos = youtube_api.get_recent_videos(channel_id, hours=hours)
                if videos:
                    logger.info(
                        f"Found {len(videos)} new video(s) from {channel_name}"
                    )
                    all_videos.extend(videos)
                stats['total_videos_found'] += len(videos)
            except Exception as e:
                logger.error(f"Error fetching videos from {channel_name}: {e}")

        logger.info(f"Total videos found: {len(all_videos)}")

        # 3. Filter out already-processed videos
        new_videos = [
            v for v in all_videos if not db.is_video_processed(v['video_id'])
        ]
        stats['new_videos'] = len(new_videos)
        logger.info(f"New videos to process: {len(new_videos)}")

        # 4. Process each new video
        for i, video in enumerate(new_videos, 1):
            logger.info(f"\n--- Processing video {i}/{len(new_videos)} ---")
            logger.info(f"Title: {video['title']}")
            logger.info(f"Channel: {video.get('channel_name', 'Unknown')}")
            logger.info(f"Video ID: {video['video_id']}")

            try:
                # a. Check video duration
                logger.info("Checking video duration...")
                duration_seconds = youtube_api.get_video_duration(video['video_id'])

                if duration_seconds is None:
                    logger.warning("Could not fetch video duration, skipping video")
                    db.mark_video_processed(
                        video,
                        status='skipped',
                        error_message='Could not fetch video duration'
                    )
                    stats['skipped'] += 1
                    continue

                duration_minutes = duration_seconds / 60
                logger.info(f"Video duration: {duration_minutes:.1f} minutes ({duration_seconds} seconds)")

                # Check minimum duration (1 minute)
                if duration_minutes < 1:
                    logger.warning(
                        f"Video is too short ({duration_minutes:.1f} min < 1 min), skipping"
                    )
                    db.mark_video_processed(
                        video,
                        status='skipped',
                        error_message=f'Video too short ({duration_minutes:.1f} minutes)'
                    )
                    stats['skipped'] += 1
                    continue

                # Check maximum duration
                if duration_minutes > max_duration_minutes:
                    logger.warning(
                        f"Video is too long ({duration_minutes:.1f} min > {max_duration_minutes} min), skipping"
                    )
                    db.mark_video_processed(
                        video,
                        status='skipped',
                        error_message=f'Video too long ({duration_minutes:.1f} minutes)'
                    )
                    stats['skipped_too_long'] += 1
                    continue

                # b. Extract transcript
                logger.info("Extracting transcript...")
                transcript = get_transcript(video['video_id'])

                if not transcript:
                    logger.warning("No transcript available, skipping video")
                    db.mark_video_processed(
                        video,
                        status='skipped',
                        error_message='No transcript available'
                    )
                    stats['skipped'] += 1
                    continue

                logger.info(f"Transcript length: {len(transcript)} characters")

                # c. Generate summary and audio
                logger.info("Generating summary and audio narration...")
                video_url = f"https://youtube.com/watch?v={video['video_id']}"
                result = create_summary_with_audio(
                    transcript=transcript,
                    video_title=video['title'],
                    video_id=video['video_id'],
                    video_url=video_url
                )

                summary = result['summary']
                audio_path = result['audio_path']
                logger.info(f"Summary: {summary[:100]}...")
                logger.info(f"Audio saved to: {audio_path}")

                # d. Send email
                if not dry_run:
                    logger.info("Sending email...")
                    video_data = {
                        **video,
                        'url': video_url
                    }
                    email_sender.send_summary_email(video_data, summary, audio_path)
                    logger.info("Email sent successfully")
                else:
                    logger.info("DRY RUN: Email not sent")

                # e. Mark as processed
                db.mark_video_processed(video, status='completed')
                stats['processed'] += 1
                logger.info(
                    f"✓ Video processed successfully ({i}/{len(new_videos)})"
                )

            except Exception as e:
                logger.error(
                    f"✗ Error processing video {video['video_id']}: {e}",
                    exc_info=True
                )
                db.mark_video_processed(
                    video,
                    status='failed',
                    error_message=str(e)
                )
                stats['failed'] += 1

        # 5. Log summary
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.info("\n=== Pipeline Summary ===")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Total videos found: {stats['total_videos_found']}")
        logger.info(f"New videos: {stats['new_videos']}")
        logger.info(f"Successfully processed: {stats['processed']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Skipped (no transcript): {stats['skipped']}")
        logger.info(f"Skipped (too long): {stats['skipped_too_long']}")

        # Get overall database stats
        db_stats = db.get_processing_stats()
        logger.info(f"\nTotal videos in database: {db_stats['total_videos']}")
        logger.info(f"Processed today: {db_stats['processed_today']}")
        logger.info(f"Processed this week: {db_stats['processed_this_week']}")

        logger.info(f"=== Pipeline completed at {end_time.isoformat()} ===\n")

        return stats

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise


def main(args: Optional[list[str]] = None) -> int:
    """CLI entry point.

    Args:
        args: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    parser = argparse.ArgumentParser(
        description='YouTube Subscription Summarizer - '
                    'Fetch new videos, generate summaries, and send email notifications.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process videos but do not send emails'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Check for videos from last N hours (default: 24)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=30,
        help='Maximum video duration in minutes (default: 30). Videos longer than this will be skipped.'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )

    parsed_args = parser.parse_args(args)

    # Setup logging
    setup_logging(verbose=parsed_args.verbose)

    try:
        # Validate configuration before running
        validate_config()
        run_pipeline(
            dry_run=parsed_args.dry_run,
            hours=parsed_args.hours,
            max_duration_minutes=parsed_args.limit
        )
        return 0
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
