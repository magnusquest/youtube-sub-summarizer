#!/usr/bin/env python3
"""Test script to process a single YouTube video.

This bypasses the subscription fetching and lets you test the core pipeline
with a single video ID.
"""

import argparse
import logging
import sys
from datetime import datetime, timezone

from src.config import validate_config
from src.database import Database
from src.email_sender import EmailSender
from src.summarizer import create_summary_with_audio
from src.transcript import get_transcript

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_video(video_id: str, dry_run: bool = False) -> bool:
    """Process a single YouTube video through the full pipeline.
    
    Args:
        video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')
        dry_run: If True, don't send email
    
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
        logger.info("To reprocess, delete data/processed_videos.db or use a different video")
        return False
    
    try:
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
        video_url = f"https://youtube.com/watch?v={video_id}"
        video_title = f"Test Video {video_id}"  # Will be in summary
        
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
                'channel_name': 'Test Channel',
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
            'channel_id': 'test',
            'channel_name': 'Test Channel'
        }, status='completed')
        logger.info("✓ Marked as processed in database")
        
        logger.info(f"\n=== SUCCESS! Video {video_id} processed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Test the pipeline with a single YouTube video'
    )
    parser.add_argument(
        'video_id',
        help='YouTube video ID (e.g., dQw4w9WgXcQ from https://youtube.com/watch?v=dQw4w9WgXcQ)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process but do not send email'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate configuration
        validate_config()
        
        # Process the video
        success = process_single_video(args.video_id, dry_run=args.dry_run)
        
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
