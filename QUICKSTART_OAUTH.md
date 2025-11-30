# Quick Start: OAuth Authentication

**Goal:** Get your YouTube Subscription Summarizer running in 10 minutes.

## Prerequisites
- ✅ Python 3.9+ installed
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ `.env` file configured with OpenAI & SMTP credentials

## Step 1: Get OAuth Credentials (5 minutes)

### Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Create project: "YouTube Summarizer"
3. Enable API: Search "YouTube Data API v3" → Enable

### Create OAuth Credentials
1. Go to: **APIs & Services** → **Credentials**
2. Click: **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Configure consent screen if prompted:
   - User type: **External**
   - Add your email as test user
   - Add scope: `../auth/youtube.readonly`
4. Application type: **Desktop app**
5. Click **CREATE** and **DOWNLOAD JSON**
6. Save as `credentials.json` in project root

## Step 2: First Run (2 minutes)

```bash
# Run the pipeline in dry-run mode
python -m src.main --dry-run --hours 1
```

**What happens:**
1. ✅ Browser opens automatically
2. ✅ Sign in to your Google account
3. ⚠️  Warning: "Google hasn't verified this app"
   - Click **Advanced**
   - Click **Go to YouTube Subscription Summarizer (unsafe)**
   - This is safe - you created the app!
4. ✅ Click **Allow** to grant permissions
5. ✅ Browser shows "Authentication flow completed"
6. ✅ Pipeline continues in terminal

## Step 3: Verify It Works

Check the logs:
```bash
tail -20 logs/pipeline.log
```

You should see:
```
INFO - Authenticating with YouTube OAuth...
INFO - OAuth authentication successful
INFO - Fetching subscriptions...
INFO - Found 42 subscribed channels
INFO - Checking for videos from last 1 hours...
```

## Done! 🎉

Your OAuth is now set up. The token is saved in `data/youtube_token.pickle` and will auto-refresh.

## What's Next?

### Test with a real run:
```bash
python -m src.main --hours 24
```

### Set up automation:
```bash
crontab -e
# Add: 0 * * * * /path/to/youtube-sub-summarizer/run_pipeline.sh
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "credentials.json not found" | Download OAuth credentials from Google Cloud Console |
| "This app isn't verified" | Click **Advanced** → **Go to [App] (unsafe)** |
| "Access blocked" | Add your email as test user in OAuth consent screen |
| Browser doesn't open | Run `python -m src.main --dry-run` and manually open the URL |

## Token Management

**Token location:** `data/youtube_token.pickle`

**Revoke access:** https://myaccount.google.com/permissions

**Re-authenticate:**
```bash
rm data/youtube_token.pickle
python -m src.main --dry-run
```

---

**Full documentation:** See [OAUTH_SETUP.md](OAUTH_SETUP.md)
