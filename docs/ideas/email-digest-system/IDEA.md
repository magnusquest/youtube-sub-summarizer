# Idea: Email Digest System with Audio Narration

## Concept
A scheduled automation system that monitors YouTube subscriptions via API polling, extracts video transcripts from captions, generates AI summaries and audio narrations using OpenAI, and delivers them via email. Runs as a cron job checking once per hour.

## Why This Approach
- **Aligns with simplicity** by using established APIs (YouTube Data API, OpenAI) rather than complex custom solutions
- **Fits within cost constraints** via hourly polling (reduces API calls) and caption-based processing (faster than audio transcription)
- **Enables efficient consumption** through both text summaries (quick scan) and audio narration (listen while commuting)
- **Self-hosted friendly** as a simple cron job with minimal dependencies

## Key Components

1. **Subscription Monitor**
   - Purpose: Fetch user's YouTube subscriptions and detect new videos
   - Tech: YouTube Data API v3, local database to track processed videos

2. **Transcript Extractor**
   - Purpose: Retrieve captions/subtitles from videos
   - Tech: YouTube Transcript API or caption download

3. **AI Summarizer & Narrator**
   - Purpose: Generate concise summary and audio narration
   - Tech: OpenAI GPT-4 (summarization) + TTS API (text-to-speech)

4. **Email Delivery**
   - Purpose: Send formatted email with summary text and audio attachment
   - Tech: SMTP (Gmail, SendGrid, or local mail server)

5. **State Management**
   - Purpose: Track which videos have been processed
   - Tech: SQLite database or JSON file

6. **Scheduler**
   - Purpose: Run the pipeline every hour
   - Tech: Cron job (Linux/macOS) or Task Scheduler (Windows)

## Architecture Flow

```
[Cron: Every hour]
    ↓
[1. Check YouTube API for new videos from subscriptions]
    ↓
[2. Filter out already-processed videos (check database)]
    ↓
[3. For each new video:]
    ↓
    [3a. Download transcript/captions]
    ↓
    [3b. Send to OpenAI GPT-4 for summarization]
    ↓
    [3c. Send summary to OpenAI TTS for audio narration]
    ↓
    [3d. Compose email with summary text + audio attachment]
    ↓
    [3e. Send email via SMTP]
    ↓
    [3f. Mark video as processed in database]
```

## Dependencies

**External APIs:**
- YouTube Data API v3 (requires API key, 10k quota/day)
- OpenAI API (GPT-4 + TTS, requires API key + billing)
- SMTP server credentials (Gmail, SendGrid, etc.)

**Technical Prerequisites:**
- Python 3.9+ (recommended for API libraries)
- Environment variables for API keys
- Cron or equivalent scheduler
- Network access for API calls

## Risk Assessment

**Primary Risks:**
1. **API Quota Exhaustion**: YouTube Data API has 10k units/day limit
   - Mitigation: Hourly checks use ~50-100 units per run (600-2400/day), well within limits

2. **OpenAI Cost Escalation**: Many new videos = high GPT-4 + TTS costs
   - Mitigation: Monitor spending, implement optional filtering (only summarize certain channels)

3. **Email Delivery Failures**: SMTP blocks, spam filters
   - Mitigation: Use authenticated SMTP, implement retry logic

4. **Caption Unavailability**: Some videos lack captions
   - Mitigation: Skip video with logged warning, or future fallback to Whisper transcription

5. **Cron Job Failures**: System downtime, crashes
   - Mitigation: Logging, error notifications, idempotent processing

## Technology Stack Recommendation

- **Language**: Python 3.9+
- **Libraries**:
  - `google-api-python-client` (YouTube Data API)
  - `youtube-transcript-api` (caption extraction)
  - `openai` (GPT-4 + TTS)
  - `smtplib` / `email` (built-in Python, or `sendgrid`)
  - `sqlite3` (built-in, for state tracking)
  - `python-dotenv` (environment variable management)

## Configuration Needs

**`.env` file:**
```
YOUTUBE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_RECIPIENT=your_email@gmail.com
```

## Next Steps
- [ ] Define detailed tasks for each component
- [ ] Estimate API costs for typical usage
- [ ] Create project structure and setup guide
- [ ] Implement core pipeline
- [ ] Test with sample channels
- [ ] Deploy with cron scheduler
