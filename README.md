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

### YouTube Data API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Copy the API key to your `.env` file

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

Run the pipeline manually to test:

```bash
python src/main.py
```

### Automated Execution (Cron Job)

Set up hourly execution:

```bash
crontab -e
```

Add this line (adjust path to your installation):

```
0 * * * * cd /path/to/youtube-sub-summarizer && source venv/bin/activate && python src/main.py >> logs/cron.log 2>&1
```

This runs every hour at minute 0.

## Project Structure

```
youtube-sub-summarizer/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── youtube_client.py  # YouTube API integration (TODO)
│   ├── transcript.py      # Transcript extraction (TODO)
│   ├── summarizer.py      # AI summarization & TTS (TODO)
│   ├── email_sender.py    # Email delivery (TODO)
│   ├── database.py        # State management (TODO)
│   └── main.py            # Main pipeline (TODO)
├── data/
│   ├── audio/             # Generated audio files
│   └── *.db               # SQLite database
├── logs/                  # Log files
├── docs/                  # Project documentation
├── .env                   # Environment variables (not in git)
├── .env.example           # Example environment file
├── .gitignore
├── requirements.txt
└── README.md
```

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
