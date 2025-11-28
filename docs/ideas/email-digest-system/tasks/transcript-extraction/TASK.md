# Task: Video Transcript Extraction

## Objective
Extract text transcripts/captions from YouTube videos using available subtitle tracks.

## Acceptance Criteria
- [ ] Given a video ID, retrieve available transcript/caption
- [ ] Handle multiple languages (prioritize English or user preference)
- [ ] Handle videos without captions gracefully (log warning, skip)
- [ ] Transcript text is clean and formatted (remove timestamps)
- [ ] Function returns full transcript as plain text string
- [ ] Unit tests verify transcript extraction

## Implementation Approach
1. Use `youtube-transcript-api` library (no API quota required)
2. Attempt to fetch transcript in preferred language order
3. If no transcript available, log and return None
4. Clean up formatting artifacts (excessive newlines, timestamps)
5. Return plain text suitable for AI summarization

## Dependencies
- Blocked by: Project Setup
- Blocks: AI Summarization
- Requires: `youtube-transcript-api` library

## Estimated Effort
1-2 hours

## Subtasks
1. [ ] Create `src/transcript.py` module
2. [ ] Implement `get_transcript(video_id, languages=['en'])` function
3. [ ] Add error handling for unavailable transcripts
4. [ ] Clean and format transcript text
5. [ ] Test with various video types (manual captions, auto-generated, none)
6. [ ] Add logging for transcript availability status

## Notes
- `youtube-transcript-api` does not use YouTube Data API quota
- Auto-generated captions may have lower quality than manual captions
- Some videos have no captions (live streams, old videos, creator choice)
- Future enhancement: fall back to audio transcription (Whisper) if no captions
