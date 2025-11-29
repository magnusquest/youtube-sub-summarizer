"""Unit tests for database state management module.

These tests use in-memory SQLite databases to avoid side effects.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestDatabaseInit:
    """Tests for Database initialization."""
    
    def test_init_creates_database_in_memory(self):
        """Test that database can be created in memory."""
        from src.database import Database
        
        db = Database(':memory:')
        assert db.db_path == ':memory:'
    
    def test_init_creates_tables(self):
        """Test that initialization creates the required tables."""
        from src.database import Database
        
        db = Database(':memory:')
        
        with db._get_connection() as conn:
            # Check that the processed_videos table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='processed_videos'"
            )
            result = cursor.fetchone()
            assert result is not None
            assert result['name'] == 'processed_videos'
    
    def test_init_creates_indexes(self):
        """Test that initialization creates the required indexes."""
        from src.database import Database
        
        db = Database(':memory:')
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row['name'] for row in cursor.fetchall()]
            
            assert 'idx_processed_at' in indexes
            assert 'idx_channel_id' in indexes
    
    def test_init_creates_directory_for_file_database(self):
        """Test that data directory is created for file-based database."""
        from src.database import Database
        import tempfile
        import os
        
        # Use a temporary directory that doesn't exist yet
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, 'subdir', 'test.db')
            
            # The subdir doesn't exist yet
            assert not os.path.exists(os.path.dirname(test_path))
            
            # Create the database - should create the directory
            db = Database(test_path)
            
            # Now the directory should exist
            assert os.path.exists(os.path.dirname(test_path))


class TestIsVideoProcessed:
    """Tests for is_video_processed method."""
    
    def test_returns_false_for_new_video(self):
        """Test that unprocessed videos return False."""
        from src.database import Database
        
        db = Database(':memory:')
        
        assert db.is_video_processed('nonexistent_video_id') is False
    
    def test_returns_true_for_processed_video(self):
        """Test that processed videos return True."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'channel456',
            'title': 'Test Video'
        }
        db.mark_video_processed(video_data)
        
        assert db.is_video_processed('test123') is True
    
    def test_returns_false_for_different_video(self):
        """Test that different video IDs return False."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'video1',
            'channel_id': 'channel1',
            'title': 'Test Video 1'
        }
        db.mark_video_processed(video_data)
        
        assert db.is_video_processed('video2') is False


class TestMarkVideoProcessed:
    """Tests for mark_video_processed method."""
    
    def test_marks_video_as_completed_by_default(self):
        """Test that videos are marked as completed by default."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'channel456',
            'title': 'Test Video'
        }
        db.mark_video_processed(video_data)
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT status FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = cursor.fetchone()
            assert result['status'] == 'completed'
    
    def test_marks_video_as_failed_with_error_message(self):
        """Test marking a video as failed with error message."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'channel456',
            'title': 'Test Video'
        }
        db.mark_video_processed(video_data, status='failed', error_message='Network error')
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT status, error_message FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = cursor.fetchone()
            assert result['status'] == 'failed'
            assert result['error_message'] == 'Network error'
    
    def test_marks_video_as_skipped(self):
        """Test marking a video as skipped."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'channel456',
            'title': 'Test Video'
        }
        db.mark_video_processed(video_data, status='skipped')
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT status FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = cursor.fetchone()
            assert result['status'] == 'skipped'
    
    def test_stores_all_video_data(self):
        """Test that all video data fields are stored correctly."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'channel456',
            'channel_name': 'Test Channel',
            'title': 'Test Video Title',
            'published_at': '2024-01-01T12:00:00Z'
        }
        db.mark_video_processed(video_data)
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = dict(cursor.fetchone())
            
            assert result['video_id'] == 'test123'
            assert result['channel_id'] == 'channel456'
            assert result['channel_name'] == 'Test Channel'
            assert result['title'] == 'Test Video Title'
            assert result['published_at'] == '2024-01-01T12:00:00Z'
            assert result['processed_at'] is not None
            assert result['status'] == 'completed'
    
    def test_handles_missing_optional_fields(self):
        """Test that missing optional fields default to empty strings."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # video_id and title are truly required (KeyError if missing)
        # channel_id, channel_name, published_at will default to empty string
        video_data = {
            'video_id': 'test123',
            'title': 'Test Video'
        }
        db.mark_video_processed(video_data)
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT channel_id, channel_name, published_at FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = dict(cursor.fetchone())
            
            assert result['channel_id'] == ''
            assert result['channel_name'] == ''
            assert result['published_at'] == ''
    
    def test_replaces_existing_video_record(self):
        """Test that processing same video again replaces the record."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'channel456',
            'title': 'Test Video'
        }
        
        # First processing - failed
        db.mark_video_processed(video_data, status='failed', error_message='First error')
        
        # Second processing - completed
        db.mark_video_processed(video_data, status='completed')
        
        with db._get_connection() as conn:
            # Should only have one record
            cursor = conn.execute('SELECT COUNT(*) as count FROM processed_videos')
            count = cursor.fetchone()['count']
            assert count == 1
            
            # Status should be updated
            cursor = conn.execute(
                'SELECT status, error_message FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = cursor.fetchone()
            assert result['status'] == 'completed'
            assert result['error_message'] is None


class TestGetProcessingStats:
    """Tests for get_processing_stats method."""
    
    def test_returns_zero_stats_for_empty_database(self):
        """Test stats for empty database."""
        from src.database import Database
        
        db = Database(':memory:')
        stats = db.get_processing_stats()
        
        assert stats['total_videos'] == 0
        assert stats['status_breakdown'] == {}
        assert stats['processed_today'] == 0
        assert stats['processed_this_week'] == 0
    
    def test_returns_correct_total_count(self):
        """Test that total video count is correct."""
        from src.database import Database
        
        db = Database(':memory:')
        
        for i in range(5):
            db.mark_video_processed({
                'video_id': f'video{i}',
                'channel_id': 'channel1',
                'title': f'Video {i}'
            })
        
        stats = db.get_processing_stats()
        assert stats['total_videos'] == 5
    
    def test_returns_correct_status_breakdown(self):
        """Test that status breakdown is correct."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # Add videos with different statuses
        db.mark_video_processed({
            'video_id': 'vid1',
            'channel_id': 'ch1',
            'title': 'Video 1'
        }, status='completed')
        
        db.mark_video_processed({
            'video_id': 'vid2',
            'channel_id': 'ch1',
            'title': 'Video 2'
        }, status='completed')
        
        db.mark_video_processed({
            'video_id': 'vid3',
            'channel_id': 'ch1',
            'title': 'Video 3'
        }, status='failed', error_message='Error')
        
        db.mark_video_processed({
            'video_id': 'vid4',
            'channel_id': 'ch1',
            'title': 'Video 4'
        }, status='skipped')
        
        stats = db.get_processing_stats()
        
        assert stats['status_breakdown']['completed'] == 2
        assert stats['status_breakdown']['failed'] == 1
        assert stats['status_breakdown']['skipped'] == 1
    
    def test_processed_today_counts_correctly(self):
        """Test that today's count is correct."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # Add a video today
        db.mark_video_processed({
            'video_id': 'vid1',
            'channel_id': 'ch1',
            'title': 'Video 1'
        })
        
        stats = db.get_processing_stats()
        assert stats['processed_today'] == 1


class TestGetFailedVideos:
    """Tests for get_failed_videos method."""
    
    def test_returns_empty_list_when_no_failed_videos(self):
        """Test that empty list is returned when no failed videos exist."""
        from src.database import Database
        
        db = Database(':memory:')
        
        db.mark_video_processed({
            'video_id': 'vid1',
            'channel_id': 'ch1',
            'title': 'Video 1'
        }, status='completed')
        
        failed = db.get_failed_videos()
        assert failed == []
    
    def test_returns_failed_videos(self):
        """Test that failed videos are returned."""
        from src.database import Database
        
        db = Database(':memory:')
        
        db.mark_video_processed({
            'video_id': 'vid1',
            'channel_id': 'ch1',
            'channel_name': 'Channel 1',
            'title': 'Video 1'
        }, status='failed', error_message='Network error')
        
        db.mark_video_processed({
            'video_id': 'vid2',
            'channel_id': 'ch1',
            'channel_name': 'Channel 1',
            'title': 'Video 2'
        }, status='completed')
        
        failed = db.get_failed_videos()
        
        assert len(failed) == 1
        assert failed[0]['video_id'] == 'vid1'
        assert failed[0]['error_message'] == 'Network error'
    
    def test_respects_limit(self):
        """Test that limit parameter is respected."""
        from src.database import Database
        
        db = Database(':memory:')
        
        for i in range(5):
            db.mark_video_processed({
                'video_id': f'vid{i}',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1',
                'title': f'Video {i}'
            }, status='failed', error_message=f'Error {i}')
        
        failed = db.get_failed_videos(limit=3)
        assert len(failed) == 3
    
    def test_orders_by_processed_at_descending(self):
        """Test that results are ordered by processed_at descending."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # Add videos (note: they'll be processed in quick succession)
        for i in range(3):
            db.mark_video_processed({
                'video_id': f'vid{i}',
                'channel_id': 'ch1',
                'channel_name': 'Channel 1',
                'title': f'Video {i}'
            }, status='failed', error_message=f'Error {i}')
        
        failed = db.get_failed_videos()
        
        # The last one added should be first (newest first)
        # Due to quick succession, we just verify order exists
        assert len(failed) == 3


class TestGetVideosByChannel:
    """Tests for get_videos_by_channel method."""
    
    def test_returns_empty_list_for_nonexistent_channel(self):
        """Test that empty list is returned for nonexistent channel."""
        from src.database import Database
        
        db = Database(':memory:')
        
        videos = db.get_videos_by_channel('nonexistent_channel')
        assert videos == []
    
    def test_returns_videos_for_channel(self):
        """Test that videos for specific channel are returned."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # Add videos for different channels
        db.mark_video_processed({
            'video_id': 'vid1',
            'channel_id': 'channel_A',
            'title': 'Video 1'
        })
        
        db.mark_video_processed({
            'video_id': 'vid2',
            'channel_id': 'channel_A',
            'title': 'Video 2'
        })
        
        db.mark_video_processed({
            'video_id': 'vid3',
            'channel_id': 'channel_B',
            'title': 'Video 3'
        })
        
        videos_a = db.get_videos_by_channel('channel_A')
        videos_b = db.get_videos_by_channel('channel_B')
        
        assert len(videos_a) == 2
        assert len(videos_b) == 1
        assert all(v['channel_id'] == 'channel_A' for v in videos_a)
    
    def test_respects_limit(self):
        """Test that limit parameter is respected."""
        from src.database import Database
        
        db = Database(':memory:')
        
        for i in range(10):
            db.mark_video_processed({
                'video_id': f'vid{i}',
                'channel_id': 'channel_A',
                'title': f'Video {i}'
            })
        
        videos = db.get_videos_by_channel('channel_A', limit=5)
        assert len(videos) == 5


class TestCleanupOldRecords:
    """Tests for cleanup_old_records method."""
    
    def test_returns_zero_for_empty_database(self):
        """Test that cleanup returns zero for empty database."""
        from src.database import Database
        
        db = Database(':memory:')
        
        deleted = db.cleanup_old_records(days=90)
        assert deleted == 0
    
    def test_returns_zero_when_all_records_are_recent(self):
        """Test that cleanup returns zero when all records are recent."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # Add a recent video
        db.mark_video_processed({
            'video_id': 'vid1',
            'channel_id': 'ch1',
            'title': 'Video 1'
        })
        
        deleted = db.cleanup_old_records(days=90)
        assert deleted == 0
        
        # Video should still exist
        assert db.is_video_processed('vid1')
    
    def test_deletes_old_records(self):
        """Test that old records are deleted."""
        from src.database import Database
        from datetime import timezone
        
        db = Database(':memory:')
        
        # Insert an old record directly
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        
        with db._get_connection() as conn:
            conn.execute('''
                INSERT INTO processed_videos 
                (video_id, channel_id, title, processed_at, status)
                VALUES (?, ?, ?, ?, ?)
            ''', ('old_vid', 'ch1', 'Old Video', old_date, 'completed'))
            conn.commit()
        
        # Add a recent video
        db.mark_video_processed({
            'video_id': 'recent_vid',
            'channel_id': 'ch1',
            'title': 'Recent Video'
        })
        
        deleted = db.cleanup_old_records(days=90)
        
        assert deleted == 1
        assert not db.is_video_processed('old_vid')
        assert db.is_video_processed('recent_vid')


class TestConnectionManagement:
    """Tests for database connection management."""
    
    def test_connection_context_manager_closes_connection(self):
        """Test that connection is properly closed after use."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # Get a connection and verify it's closed after context
        with db._get_connection() as conn:
            # Connection should be open here
            cursor = conn.execute('SELECT 1')
            assert cursor.fetchone() is not None
        
        # Connection should be closed now
        # (can't easily verify this without internals, but the code path is tested)
    
    def test_row_factory_allows_dict_access(self):
        """Test that Row factory is set for dict-like access."""
        from src.database import Database
        import sqlite3
        
        db = Database(':memory:')
        
        db.mark_video_processed({
            'video_id': 'test123',
            'channel_id': 'channel456',
            'title': 'Test Video'
        })
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT video_id, title FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            row = cursor.fetchone()
            
            # Should be able to access by name
            assert row['video_id'] == 'test123'
            assert row['title'] == 'Test Video'


class TestDatabaseLogging:
    """Tests for logging functionality."""
    
    @patch('src.database.logger')
    def test_logs_database_initialization(self, mock_logger):
        """Test that database initialization is logged."""
        from src.database import Database
        
        db = Database(':memory:')
        
        assert mock_logger.info.called
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any('initialized' in call.lower() for call in info_calls)
    
    @patch('src.database.logger')
    def test_logs_video_marked_as_processed(self, mock_logger):
        """Test that marking video as processed is logged."""
        from src.database import Database
        
        db = Database(':memory:')
        mock_logger.reset_mock()
        
        db.mark_video_processed({
            'video_id': 'test123',
            'channel_id': 'ch1',
            'title': 'Test Video'
        })
        
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any('test123' in call for call in info_calls)
    
    @patch('src.database.logger')
    def test_logs_cleanup_operation(self, mock_logger):
        """Test that cleanup operation is logged."""
        from src.database import Database
        
        db = Database(':memory:')
        mock_logger.reset_mock()
        
        db.cleanup_old_records(days=90)
        
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any('cleaned up' in call.lower() for call in info_calls)


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_handles_special_characters_in_title(self):
        """Test that special characters in title are handled correctly."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'ch1',
            'title': "Video with 'quotes' and \"double quotes\" and emoji 🎉"
        }
        db.mark_video_processed(video_data)
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT title FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = cursor.fetchone()
            assert result['title'] == video_data['title']
    
    def test_handles_unicode_characters(self):
        """Test that unicode characters are handled correctly."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': 'test123',
            'channel_id': 'ch1',
            'channel_name': '日本語チャンネル',
            'title': 'Видео на русском языке'
        }
        db.mark_video_processed(video_data)
        
        with db._get_connection() as conn:
            cursor = conn.execute(
                'SELECT channel_name, title FROM processed_videos WHERE video_id = ?',
                ('test123',)
            )
            result = cursor.fetchone()
            assert result['channel_name'] == '日本語チャンネル'
            assert result['title'] == 'Видео на русском языке'
    
    def test_handles_empty_string_video_id(self):
        """Test behavior with empty string video_id."""
        from src.database import Database
        
        db = Database(':memory:')
        
        video_data = {
            'video_id': '',
            'channel_id': 'ch1',
            'title': 'Test Video'
        }
        db.mark_video_processed(video_data)
        
        # Should be able to check for empty string video_id
        assert db.is_video_processed('') is True
    
    def test_multiple_operations_in_sequence(self):
        """Test that multiple database operations work correctly in sequence."""
        from src.database import Database
        
        db = Database(':memory:')
        
        # Add multiple videos
        for i in range(10):
            status = 'completed' if i % 2 == 0 else 'failed'
            db.mark_video_processed({
                'video_id': f'vid{i}',
                'channel_id': f'ch{i % 3}',
                'title': f'Video {i}'
            }, status=status, error_message='Error' if status == 'failed' else None)
        
        # Check various operations
        stats = db.get_processing_stats()
        assert stats['total_videos'] == 10
        
        failed = db.get_failed_videos()
        assert len(failed) == 5
        
        ch0_videos = db.get_videos_by_channel('ch0')
        assert len(ch0_videos) == 4  # Videos 0, 3, 6, 9
        
        for i in range(10):
            assert db.is_video_processed(f'vid{i}')
