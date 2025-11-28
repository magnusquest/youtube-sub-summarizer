"""Configuration management for YouTube Subscription Summarizer.

Loads environment variables from .env file and validates required settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# YouTube API
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# OpenAI API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_TTS_VOICE = os.getenv('OPENAI_TTS_VOICE', 'alloy')

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

def validate_config():
    """Validate that all required environment variables are set.
    
    Raises:
        ValueError: If any required environment variable is missing.
    """
    required_vars = [
        'YOUTUBE_API_KEY',
        'OPENAI_API_KEY',
        'SMTP_SERVER',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'EMAIL_RECIPIENT'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
