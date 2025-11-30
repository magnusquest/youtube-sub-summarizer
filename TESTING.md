# Testing with a Single YouTube Video

This guide shows you how to test the pipeline with a single YouTube video, bypassing the OAuth subscription fetching issue.

## Quick Start

### Step 1: Find a YouTube Video ID

Pick any YouTube video with captions/subtitles. The video ID is the part after `v=` in the URL.

**Examples:**
- URL: `https://youtube.com/watch?v=dQw4w9WgXcQ`
- Video ID: `dQw4w9WgXcQ`

**Tips for finding good test videos:**
- Use videos with auto-generated captions (most videos have them)
- Educational or tech videos usually have good transcripts
- Shorter videos (5-15 min) will process faster and cost less

### Step 2: Run the Test Script

**With dry-run (recommended for first test):**
```bash
python test_single_video.py VIDEO_ID --dry-run
```

**Example:**
```bash
# This will process the video but NOT send an email
python test_single_video.py dQw4w9WgXcQ --dry-run
```

**Without dry-run (sends actual email):**
```bash
# This will process AND send an email
python test_single_video.py dQw4w9WgXcQ
```

## What the Script Does

The test script processes a single video through the complete pipeline:

1. ✅ **Extract transcript** from YouTube (via youtube-transcript-api)
2. ✅ **Generate AI summary** (via OpenAI GPT-4)
3. ✅ **Create audio narration** (via OpenAI TTS)
4. ✅ **Send email** with summary + audio (via SMTP) - unless `--dry-run`
5. ✅ **Save to database** (marks video as processed)

## Expected Output

```
2025-11-29 23:15:00,000 - __main__ - INFO - === Processing single video: dQw4w9WgXcQ ===
2025-11-29 23:15:00,001 - __main__ - INFO - Step 1: Extracting transcript...
2025-11-29 23:15:00,500 - __main__ - INFO - ✓ Transcript extracted: 1234 characters
2025-11-29 23:15:00,501 - __main__ - INFO - Step 2: Generating AI summary and audio narration...
2025-11-29 23:15:05,000 - src.summarizer - INFO - Summarization: 250 tokens, ~$0.0025
2025-11-29 23:15:06,000 - src.summarizer - INFO - TTS: 150 characters, ~$0.000002
2025-11-29 23:15:06,001 - __main__ - INFO - ✓ Summary generated (150 chars)
2025-11-29 23:15:06,002 - __main__ - INFO - Summary: This video discusses...
2025-11-29 23:15:06,003 - __main__ - INFO - ✓ Audio saved to: data/audio/dQw4w9WgXcQ_summary.mp3
2025-11-29 23:15:06,004 - __main__ - INFO - Step 3: SKIPPED (dry-run mode)
2025-11-29 23:15:06,005 - __main__ - INFO - ✓ Marked as processed in database
2025-11-29 23:15:06,006 - __main__ - INFO - 
=== SUCCESS! Video dQw4w9WgXcQ processed successfully ===
```

## Required Environment Variables

**For dry-run mode (no email):**
```bash
OPENAI_API_KEY=sk-...  # Required for summarization
```

**For full test (with email):**
```bash
OPENAI_API_KEY=sk-...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your_app_password
EMAIL_RECIPIENT=your@email.com
```

## Troubleshooting

### "No transcript available for this video"
**Cause:** The video doesn't have captions/subtitles.  
**Solution:** Try a different video. Most popular videos have auto-generated captions.

### "Video has already been processed"
**Cause:** The video ID is already in the database.  
**Solution:** Either:
- Use a different video ID
- Delete `data/processed_videos.db` to reset the database
- Edit the database to remove that specific video

### "Configuration error: Missing required environment variable"
**Cause:** Your `.env` file is missing required API keys.  
**Solution:** Make sure your `.env` file has `OPENAI_API_KEY` at minimum.

### "SMTP authentication failed"
**Cause:** Email credentials are incorrect or Gmail App Password not set up.  
**Solution:** 
- Use `--dry-run` to test without email
- Or set up a Gmail App Password: https://support.google.com/accounts/answer/185833

## Finding Good Test Videos

### Recommended Test Videos (with good transcripts):

1. **TED Talks** - Always have high-quality captions
2. **Tech tutorials** - Usually have auto-generated captions
3. **Educational channels** - Good quality transcripts

### How to Check if a Video Has Captions:

1. Go to the YouTube video
2. Click the "CC" (closed captions) button
3. If it shows subtitles, the video has a transcript

## Cost Estimation

Testing a single 10-minute video costs approximately:
- **GPT-4 Summarization:** ~$0.01-0.03
- **TTS Audio:** ~$0.001-0.005
- **Total:** ~$0.02-0.04 per video

## Next Steps After Testing

Once you've successfully tested with a single video:

1. ✅ **Verify email delivery** - check your inbox for the summary email
2. ✅ **Check audio file** - `data/audio/VIDEO_ID_summary.mp3`
3. ✅ **Review database** - use SQLite viewer to check `data/processed_videos.db`
4. ✅ **Review logs** - check `logs/pipeline.log`

Then you can:
- Implement OAuth 2.0 for full subscription support
- Or manually specify channel IDs to monitor
- Or use the RSS feed approach

