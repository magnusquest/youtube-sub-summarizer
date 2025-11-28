# Task: State Management & Video Tracking

## Objective
Implement persistent storage to track which videos have been processed, preventing duplicate summaries and enabling idempotent pipeline execution.

## Acceptance Criteria
- [ ] SQLite database created to store processed video records
- [ ] Schema includes: video_id, channel_id, title, processed_at, status
- [ ] Function to check if video already processed
- [ ] Function to mark video as processed
- [ ] Database persists between script runs
- [ ] Migration/initialization script for first-time setup
- [ ] Unit tests verify database operations

## Implementation Approach
1. Use Python's built-in `sqlite3` library
2. Create database schema:
   ```sql
   CREATE TABLE processed_videos (
       video_id TEXT PRIMARY KEY,
       channel_id TEXT NOT NULL,
       title TEXT NOT NULL,
       published_at TEXT,
       processed_at TEXT NOT NULL,
       status TEXT DEFAULT 'completed',
       error_message TEXT
   );
   ```
3. Implement functions:
   - `is_video_processed(video_id) -> bool`
   - `mark_video_processed(video_data)`
   - `get_processing_stats() -> dict`
4. Handle database initialization on first run

## Dependencies
- Blocked by: Project Setup
- Blocks: Main Pipeline
- Requires: None (uses built-in sqlite3)

## Estimated Effort
1-2 hours

## Subtasks
1. [ ] Create `src/database.py` module
2. [ ] Implement `Database` class with connection management
3. [ ] Create database schema and initialization function
4. [ ] Implement `is_video_processed(video_id)` method
5. [ ] Implement `mark_video_processed(video_data, status='completed')` method
6. [ ] Add error logging (store failed video processing attempts)
7. [ ] Test database operations (insert, query, edge cases)

## Notes
- Database file location: `data/processed_videos.db`
- Use context managers for safe database connections
- Consider adding index on `processed_at` for future analytics
- Status values: 'completed', 'failed', 'skipped' (no transcript)
- Store error messages for debugging failed processing
