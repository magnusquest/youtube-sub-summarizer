"""Database module for tracking processed video state.

This module provides a Database class that uses SQLite to store and manage
information about processed videos, enabling idempotent pipeline execution
and preventing duplicate summaries.
"""

import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

DATABASE_PATH = 'data/processed_videos.db'


class Database:
    """Manage video processing state using SQLite.
    
    This class provides methods to track which videos have been processed,
    retrieve statistics about processing, and maintain the database.
    
    Attributes:
        db_path: Path to the SQLite database file.
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize the Database.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to 
                     'data/processed_videos.db'. Use ':memory:' for 
                     in-memory database (useful for testing).
        """
        self.db_path = db_path
        self._is_memory = db_path == ':memory:'
        # For in-memory databases, keep a persistent connection to prevent
        # the database from being destroyed when all connections close
        self._persistent_conn = None
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist."""
        # Ensure data directory exists (skip for in-memory database)
        if not self._is_memory:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        
        # Create tables
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_videos (
                    video_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    channel_name TEXT,
                    title TEXT NOT NULL,
                    published_at TEXT,
                    processed_at TEXT NOT NULL,
                    status TEXT DEFAULT 'completed',
                    error_message TEXT
                )
            ''')
            
            # Create index for analytics
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processed_at 
                ON processed_videos(processed_at)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_channel_id 
                ON processed_videos(channel_id)
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections.
        
        For in-memory databases, returns the same persistent connection.
        For file-based databases, creates a new connection each time.
        
        Yields:
            sqlite3.Connection: Database connection with Row factory enabled.
        """
        if self._is_memory:
            # For in-memory databases, use a persistent connection
            if self._persistent_conn is None:
                self._persistent_conn = sqlite3.connect(':memory:')
                self._persistent_conn.row_factory = sqlite3.Row
            yield self._persistent_conn
            # Don't close the persistent connection
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Access columns by name
            try:
                yield conn
            finally:
                conn.close()
    
    def is_video_processed(self, video_id: str) -> bool:
        """Check if a video has already been processed.
        
        Args:
            video_id: YouTube video ID.
        
        Returns:
            True if video was processed, False otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT video_id FROM processed_videos WHERE video_id = ?',
                (video_id,)
            )
            result = cursor.fetchone()
            return result is not None
    
    def mark_video_processed(
        self, 
        video_data: dict, 
        status: str = 'completed', 
        error_message: Optional[str] = None
    ):
        """Mark a video as processed in the database.
        
        Args:
            video_data: Dict with video info. Required keys: 'video_id', 'title'.
                       Optional keys: 'channel_id', 'channel_name', 'published_at'.
            status: Processing status ('completed', 'failed', 'skipped').
            error_message: Optional error message if status is 'failed'.
        """
        processed_at = datetime.now(timezone.utc).isoformat()
        
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO processed_videos 
                (video_id, channel_id, channel_name, title, published_at, 
                 processed_at, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_data['video_id'],
                video_data.get('channel_id', ''),
                video_data.get('channel_name', ''),
                video_data['title'],
                video_data.get('published_at', ''),
                processed_at,
                status,
                error_message
            ))
            conn.commit()
            
            logger.info(f"Marked video {video_data['video_id']} as {status}")
    
    def get_processing_stats(self) -> dict:
        """Get statistics about processed videos.
        
        Returns:
            Dictionary containing:
                - total_videos: Total number of processed videos
                - status_breakdown: Dict mapping status to count
                - processed_today: Number of videos processed today
                - processed_this_week: Number of videos processed in last 7 days
        """
        with self._get_connection() as conn:
            # Total videos
            cursor = conn.execute('SELECT COUNT(*) as count FROM processed_videos')
            total = cursor.fetchone()['count']
            
            # Status breakdown
            cursor = conn.execute('''
                SELECT status, COUNT(*) as count 
                FROM processed_videos 
                GROUP BY status
            ''')
            status_breakdown = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Recent activity - use 'utc' modifier for consistent UTC comparison
            cursor = conn.execute('''
                SELECT COUNT(*) as count 
                FROM processed_videos 
                WHERE date(processed_at) = date('now', 'utc')
            ''')
            today = cursor.fetchone()['count']
            
            cursor = conn.execute('''
                SELECT COUNT(*) as count 
                FROM processed_videos 
                WHERE date(processed_at) >= date('now', '-7 days', 'utc')
            ''')
            this_week = cursor.fetchone()['count']
            
            return {
                'total_videos': total,
                'status_breakdown': status_breakdown,
                'processed_today': today,
                'processed_this_week': this_week
            }
    
    def get_failed_videos(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get list of recently failed videos.
        
        Args:
            limit: Maximum number of results.
        
        Returns:
            List of failed video records as dictionaries.
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT video_id, title, channel_name, error_message, processed_at
                FROM processed_videos
                WHERE status = 'failed'
                ORDER BY processed_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_videos_by_channel(self, channel_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get all processed videos from a specific channel.
        
        Args:
            channel_id: YouTube channel ID.
            limit: Maximum number of results.
        
        Returns:
            List of video records as dictionaries.
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM processed_videos
                WHERE channel_id = ?
                ORDER BY processed_at DESC
                LIMIT ?
            ''', (channel_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """Delete records older than specified days (for maintenance).
        
        Args:
            days: Number of days to keep.
        
        Returns:
            Number of deleted records.
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM processed_videos
                WHERE date(processed_at) < date('now', '-' || ? || ' days', 'utc')
            ''', (days,))
            conn.commit()
            
            deleted = cursor.rowcount
            logger.info(f"Cleaned up {deleted} records older than {days} days")
            return deleted
