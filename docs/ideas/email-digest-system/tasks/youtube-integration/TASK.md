# Task: YouTube Data API Integration

## Objective
Implement functionality to authenticate with YouTube Data API v3 and fetch user's subscriptions and recent uploads from each subscribed channel.

## Acceptance Criteria
- [ ] YouTube API client successfully authenticates with API key
- [ ] Function retrieves all channels user is subscribed to
- [ ] Function fetches recent videos (last 24 hours) from a given channel
- [ ] API quota usage is logged and monitored
- [ ] Error handling for API failures (rate limits, network errors)
- [ ] Unit tests verify API integration works

## Implementation Approach
1. Use `google-api-python-client` to create YouTube service object
2. Implement `get_subscriptions()` to fetch all subscribed channel IDs
3. Implement `get_recent_videos(channel_id, hours=24)` to get new uploads
4. Handle pagination if user has many subscriptions
5. Add retry logic for transient failures
6. Log quota consumption estimates

## Dependencies
- Blocked by: Project Setup
- Blocks: State Management, Main Pipeline
- Requires: YouTube Data API key

## Estimated Effort
2-3 hours

## Subtasks
1. [ ] Create `src/youtube_client.py` module
2. [ ] Implement `YouTubeClient` class with API authentication
3. [ ] Implement `get_subscriptions()` method
4. [ ] Implement `get_recent_videos(channel_id, hours=24)` method
5. [ ] Add error handling and logging
6. [ ] Test with real YouTube account
7. [ ] Document quota usage (subscriptions: 1 unit/page, search: 100 units)

## Notes
- YouTube Data API quota: 10,000 units/day
- Fetching subscriptions: ~1-5 units depending on subscription count
- Fetching recent videos: Use `search` endpoint (100 units) or `playlistItems` for channel uploads playlist (1 unit)
- Consider using channel's "uploads" playlist for efficiency
