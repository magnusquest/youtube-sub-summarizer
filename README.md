# YouTube Subscription Summarizer

An automated tool that monitors your YouTube subscriptions and sends email summaries with AI-generated narration for each new video.

## Overview

Instead of watching every video from your subscribed channels, receive concise AI summaries via email with audio narration. The system runs as a scheduled task (cron job) checking for new videos hourly.

## Features

- 📺 Automatic detection of new videos from YouTube subscriptions
- 📝 AI-powered text summaries using OpenAI GPT-4
- 🔊 Audio narration of summaries via OpenAI TTS
- 📧 Email delivery with summary text and audio attachment
- 🔄 Hourly automated checks via cron job
- 💾 State management to prevent duplicate processing

## Prerequisites

- **Python 3.9+**
- **API Keys:**
  - YouTube Data API v3 key ([Get one here](https://console.cloud.google.com/apis/credentials))
  - OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- **SMTP Server Access:**
  - Gmail (with App Password if 2FA enabled)
  - Or any other SMTP provider

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/magnusquest/youtube-sub-summarizer.git
cd youtube-sub-summarizer
```

### 2. Create and activate virtual environment

**Using uv (recommended):**

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Or using standard Python:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

**Using uv (recommended):**

```bash
uv pip install -r requirements.txt
```

**Or using pip:**

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```bash
YOUTUBE_API_KEY=your_actual_youtube_api_key
OPENAI_API_KEY=your_actual_openai_api_key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=your_email@gmail.com
OPENAI_TTS_VOICE=alloy
```

**Note:** For Gmail, you need to create an [App Password](https://support.google.com/accounts/answer/185833) if 2FA is enabled.

## Configuration

### YouTube OAuth 2.0 Setup (Required)

**IMPORTANT:** This application requires OAuth 2.0 authentication to access your YouTube subscriptions.

📖 **See [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed step-by-step instructions.**

**Quick summary:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to project root
6. On first run, authenticate in your browser

### OpenAI API Setup

1. Sign up at [OpenAI Platform](https://platform.openai.com/)
2. Add billing information
3. Create an API key
4. Copy the key to your `.env` file

### SMTP Configuration

**Gmail:**
- Set `SMTP_SERVER=smtp.gmail.com`
- Set `SMTP_PORT=587`
- Use your Gmail address for `SMTP_USERNAME`
- Generate and use an [App Password](https://support.google.com/accounts/answer/185833) for `SMTP_PASSWORD`

**Other providers:**
- Update `SMTP_SERVER` and `SMTP_PORT` accordingly
- Use appropriate credentials

## Usage

### Manual Execution

Run the pipeline manually:

```bash
# Full execution (fetches videos, summarizes, sends emails)
python -m src.main

# Dry run mode - process videos but don't send emails
python -m src.main --dry-run

# Check for videos from last 48 hours instead of default 24
python -m src.main --hours 48

# Enable verbose (DEBUG) logging
python -m src.main --verbose

# Combine options
python -m src.main --dry-run --hours 48 --verbose
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dry-run` | Process videos but don't send emails | False |
| `--hours N` | Check for videos from last N hours | 24 |
| `--verbose` | Enable DEBUG level logging | False |

### Using the Shell Wrapper Script

A convenience wrapper script is provided for cron jobs:

```bash
# Make executable (one-time)
chmod +x run_pipeline.sh

# Run the pipeline
./run_pipeline.sh

# Pass arguments to the pipeline
./run_pipeline.sh --dry-run
```

### Automated Execution (Cron Job)

Set up hourly execution:

```bash
crontab -e
```

Add one of these lines (adjust path to your installation):

```bash
# Using the wrapper script (recommended)
0 * * * * /path/to/youtube-sub-summarizer/run_pipeline.sh

# Or directly with Python
0 * * * * cd /path/to/youtube-sub-summarizer && source .venv/bin/activate && python -m src.main >> logs/cron.log 2>&1
```

**Alternative cron schedules:**

```bash
# Every 2 hours
0 */2 * * * /path/to/run_pipeline.sh

# Every 6 hours
0 */6 * * * /path/to/run_pipeline.sh

# Daily at 9 AM
0 9 * * * /path/to/run_pipeline.sh

# Twice daily (9 AM and 6 PM)
0 9,18 * * * /path/to/run_pipeline.sh
```

### Verify Cron Job

```bash
# Check if cron job is registered
crontab -l

# Monitor logs
tail -f logs/cron.log
tail -f logs/pipeline.log

# Test wrapper script manually
./run_pipeline.sh --dry-run
```

## Project Structure

```
youtube-sub-summarizer/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── youtube_client.py  # YouTube API integration
│   ├── transcript.py      # Transcript extraction
│   ├── summarizer.py      # AI summarization & TTS
│   ├── email_sender.py    # Email delivery
│   ├── database.py        # State management (SQLite)
│   └── main.py            # Main pipeline orchestration
├── tests/                 # Unit tests
├── data/
│   ├── audio/             # Generated audio files
│   └── processed_videos.db # SQLite database
├── logs/
│   ├── pipeline.log       # Pipeline execution logs (rotating)
│   └── cron.log           # Cron wrapper logs
├── docs/                  # Project documentation
├── run_pipeline.sh        # Cron wrapper script
├── .env                   # Environment variables (not in git)
├── .env.example           # Example environment file
├── .gitignore
├── requirements.txt
└── README.md
```

## Logging

The pipeline maintains two log files in the `logs/` directory:

- **pipeline.log**: Detailed execution logs with rotating file handler (10MB max, 5 backups)
- **cron.log**: Wrapper script output for cron job monitoring

Log format: `YYYY-MM-DD HH:MM:SS - module - LEVEL - message`

## Troubleshooting

### Configuration Errors

**Error: `Missing required environment variable: X`**
- Ensure all required variables are set in your `.env` file
- Check for typos in variable names
- Make sure `.env` file is in the project root directory

### YouTube API Issues

**Error: `API quota exceeded`**
- YouTube Data API has a quota of 10,000 units/day
- Hourly checks use ~50-100 units per run
- Check your quota usage in [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

### Email Delivery Issues

**Error: `SMTP authentication failed`**
- For Gmail: Ensure you're using an App Password, not your regular password
- Verify `SMTP_SERVER` and `SMTP_PORT` are correct
- Check if your email provider requires specific security settings

### OpenAI API Issues

**Error: `Rate limit exceeded`**
- You've hit OpenAI's rate limits
- Wait a few minutes and try again
- Consider upgrading your OpenAI plan for higher limits

### Cron Job Not Running

- Check cron service status: `systemctl status cron`
- Check cron logs: `grep CRON /var/log/syslog`
- Ensure absolute paths in crontab
- Verify script has execute permissions: `chmod +x run_pipeline.sh`
- Test wrapper script manually: `./run_pipeline.sh --dry-run`

### Pipeline Errors

- Check logs: `tail -f logs/pipeline.log`
- Run with verbose mode: `python -m src.main --dry-run --verbose`
- Verify API keys in `.env` file
- Check database permissions in `data/` directory

## Cost Estimation

**YouTube Data API:** Free (within 10,000 units/day quota)

**OpenAI:**
- GPT-4 Turbo: ~$0.01-0.03 per video summary (varies by transcript length)
- TTS: ~$0.015 per 1,000 characters (~$0.001-0.005 per summary)
- **Estimated monthly cost:** $5-20 depending on subscription count

**Example:** 50 videos/day × 30 days = 1,500 summaries/month ≈ $15-45/month

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines.

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Acknowledgments

- Built with [OpenAI API](https://platform.openai.com/)
- Uses [YouTube Data API v3](https://developers.google.com/youtube/v3)
- Transcript extraction via [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)
