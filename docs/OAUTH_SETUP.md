# YouTube OAuth 2.0 Setup Guide

The YouTube Subscription Summarizer requires OAuth 2.0 authentication to access your YouTube subscriptions. This guide will walk you through setting up OAuth credentials.

## Why OAuth 2.0?

YouTube's API requires OAuth 2.0 (not just an API key) for accessing user-specific data like subscriptions. This is a security measure to ensure only authorized applications can access your personal YouTube data.

## Step-by-Step Setup

### 1. Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 2. Create or Select a Project

- Click **Select a Project** at the top
- Click **NEW PROJECT**
- **Project name:** `YouTube Summarizer` (or any name you prefer)
- Click **CREATE**

### 3. Enable YouTube Data API v3

- In the left sidebar, go to **APIs & Services** → **Library**
- Search for **YouTube Data API v3**
- Click on it and click **ENABLE**

### 4. Configure OAuth Consent Screen

- Go to **APIs & Services** → **OAuth consent screen**
- Select **External** user type
- Click **CREATE**

**Fill in the required fields:**
- **App name:** `YouTube Subscription Summarizer`
- **User support email:** Your email address
- **Developer contact information:** Your email address
- Click **SAVE AND CONTINUE**

**Scopes page:**
- Click **ADD OR REMOVE SCOPES**
- Find and check: `../auth/youtube.readonly`
- Click **UPDATE**
- Click **SAVE AND CONTINUE**

**Test users page:**
- Click **+ ADD USERS**
- Add your Gmail address
- Click **ADD**
- Click **SAVE AND CONTINUE**

Click **BACK TO DASHBOARD**

### 5. Create OAuth 2.0 Credentials

- Go to **APIs & Services** → **Credentials**
- Click **+ CREATE CREDENTIALS** at the top
- Select **OAuth client ID**
- **Application type:** Select **Desktop app**
- **Name:** `YouTube Summarizer Desktop Client`
- Click **CREATE**

### 6. Download Credentials

- A dialog will appear with your Client ID and Client Secret
- Click **DOWNLOAD JSON**
- **IMPORTANT:** Save this file as `credentials.json` in your project root directory

```bash
# Your project structure should look like:
youtube-sub-summarizer/
├── credentials.json  ← The file you just downloaded
├── src/
├── data/
└── ...
```

### 7. Secure Your Credentials

Add `credentials.json` to `.gitignore` (it should already be there):

```bash
# Check that credentials.json is in .gitignore
grep credentials.json .gitignore
```

**IMPORTANT:** Never commit `credentials.json` to version control!

## First-Time Authentication

### Run the Pipeline

The first time you run the pipeline, it will:

1. **Open your browser** automatically
2. Ask you to **sign in** to your Google account
3. Show a **consent screen** asking for permission to access YouTube
4. Ask you to **allow** the application

```bash
python -m src.main --dry-run
```

### What to Expect

1. **Browser opens** with Google sign-in page
2. Sign in with your Google/YouTube account
3. **Warning screen** may appear saying "Google hasn't verified this app"
   - Click **Advanced**
   - Click **Go to YouTube Subscription Summarizer (unsafe)**
   - This is normal for personal projects not published publicly
4. **Permission screen** asks to:
   - View your YouTube account
   - See a list of your subscriptions
   - Click **Allow**
5. **Success!** Browser shows "The authentication flow has completed"
6. Return to your terminal - the pipeline will continue running

### Token Storage

After successful authentication, a token file is created:
- Location: `data/youtube_token.pickle`
- Contains: Your OAuth access and refresh tokens
- **Important:** This file should never be shared or committed to git

The token is valid for a long time and will auto-refresh, so you only need to authenticate once.

## Troubleshooting

### "credentials.json not found"

**Problem:** The OAuth credentials file is missing.

**Solution:**
1. Download `credentials.json` from Google Cloud Console
2. Place it in the project root directory (same level as `src/`)
3. Ensure it's named exactly `credentials.json`

### "This app isn't verified"

**Problem:** Google shows a warning that the app isn't verified.

**Solution:** This is normal for personal projects! 
1. Click **Advanced**
2. Click **Go to [App Name] (unsafe)**
3. This is safe because you created the app yourself

### "Access blocked: This app's request is invalid"

**Problem:** OAuth consent screen not configured properly.

**Solution:**
1. Go to Google Cloud Console → OAuth consent screen
2. Make sure you added your email as a **test user**
3. Ensure the `youtube.readonly` scope is added

### "The request uses the 'mine' parameter but is not properly authorized"

**Problem:** Still using API key instead of OAuth.

**Solution:** Make sure you're running the latest version of `main.py` that uses `YouTubeOAuthClient`.

### Token Expired

**Problem:** Token file exists but authentication fails.

**Solution:**
1. Delete `data/youtube_token.pickle`
2. Run the pipeline again - it will re-authenticate

```bash
rm data/youtube_token.pickle
python -m src.main --dry-run
```

## Security Best Practices

### ✅ DO:
- Keep `credentials.json` private (don't share or commit)
- Keep `data/youtube_token.pickle` private
- Use a strong Google account password
- Enable 2FA on your Google account

### ❌ DON'T:
- Share your `credentials.json` file
- Commit `credentials.json` or token files to git
- Give credentials to untrusted applications
- Use this on a shared/public computer

## Verifying Your Setup

Check that everything is in place:

```bash
# Check credentials file exists
ls -l credentials.json

# Check it's in .gitignore
grep -E "(credentials\.json|youtube_token\.pickle)" .gitignore

# Test authentication (dry-run)
python -m src.main --dry-run --hours 1
```

If authentication succeeds, you'll see:
```
INFO - Authenticating with YouTube OAuth...
INFO - Loading existing OAuth token from data/youtube_token.pickle
INFO - Fetching subscriptions...
INFO - Found XX subscribed channels
```

## Optional: Publishing Your App (Advanced)

If you want to avoid the "unverified app" warning:

1. Go to Google Cloud Console → OAuth consent screen
2. Click **PUBLISH APP**
3. Submit for verification (requires answering questions)
4. Wait for Google's review (can take days/weeks)

**Note:** This is NOT required for personal use! The app works fine without publishing.

## FAQ

**Q: Do I need to pay for Google Cloud?**  
A: No! The YouTube Data API is free within the quota limits (10,000 units/day).

**Q: Is my data safe?**  
A: Yes! OAuth tokens only grant access to YOUR YouTube subscriptions, and only this application can use them.

**Q: Can I revoke access later?**  
A: Yes! Go to https://myaccount.google.com/permissions and remove "YouTube Subscription Summarizer".

**Q: How long does the token last?**  
A: The refresh token lasts indefinitely and auto-refreshes access tokens as needed.

**Q: Can I use this on multiple computers?**  
A: Yes, but you'll need to authenticate on each computer. You can't copy the token file between computers.

## Next Steps

After completing OAuth setup:
1. ✅ Test with dry-run: `python -m src.main --dry-run`
2. ✅ Configure `.env` with OpenAI and SMTP credentials
3. ✅ Test end-to-end: `python -m src.main --dry-run --hours 24`
4. ✅ Set up cron job for automation

---

**Need help?** Check the logs in `logs/pipeline.log` for detailed error messages.
