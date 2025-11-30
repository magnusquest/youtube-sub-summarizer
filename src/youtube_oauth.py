"""YouTube API client with OAuth 2.0 authentication.

This module provides OAuth-based authentication for accessing YouTube user data,
replacing the API key approach which doesn't work for the subscriptions endpoint.
"""

import logging
import os
import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes required for YouTube API
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# Token storage path
TOKEN_FILE = 'data/youtube_token.pickle'
CREDENTIALS_FILE = 'credentials.json'


class YouTubeOAuthClient:
    """YouTube client using OAuth 2.0 authentication.
    
    This client handles the OAuth flow for accessing user subscriptions
    and other authenticated YouTube Data API endpoints.
    """
    
    def __init__(self, credentials_file: str = CREDENTIALS_FILE, token_file: str = TOKEN_FILE):
        """Initialize OAuth client.
        
        Args:
            credentials_file: Path to OAuth 2.0 client credentials JSON file.
            token_file: Path to store/load the OAuth token pickle file.
        
        Raises:
            FileNotFoundError: If credentials file doesn't exist.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self._youtube = None
        self._credentials = None
        
        # Ensure data directory exists
        Path(token_file).parent.mkdir(parents=True, exist_ok=True)
    
    def authenticate(self) -> Credentials:
        """Authenticate with YouTube OAuth 2.0.
        
        This method:
        1. Checks for existing valid token
        2. Refreshes expired token if possible
        3. Runs OAuth flow if no valid token exists
        
        Returns:
            Google OAuth credentials object.
        
        Raises:
            FileNotFoundError: If credentials.json doesn't exist.
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            logger.info(f"Loading existing OAuth token from {self.token_file}")
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials are invalid or don't exist, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired OAuth token")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}. Starting new OAuth flow.")
                    creds = None
            
            if not creds:
                # Run OAuth flow
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"OAuth credentials file not found: {self.credentials_file}\n"
                        "Please download credentials.json from Google Cloud Console.\n"
                        "See OAUTH_SETUP.md for instructions."
                    )
                
                logger.info("Starting OAuth 2.0 authentication flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, 
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("OAuth authentication successful")
            
            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
                logger.info(f"Saved OAuth token to {self.token_file}")
        
        self._credentials = creds
        return creds
    
    @property
    def youtube(self):
        """Get YouTube API service object.
        
        Returns:
            YouTube API service resource.
        """
        if self._youtube is None:
            if self._credentials is None:
                self.authenticate()
            self._youtube = build('youtube', 'v3', credentials=self._credentials)
        return self._youtube
    
    def get_subscriptions(self) -> list[dict]:
        """Fetch all channels the authenticated user is subscribed to.

        Returns:
            List of subscription dictionaries with channel_id and channel_name.
        """
        subscriptions = []
        page_token = None
        page_count = 0

        while True:
            request = self.youtube.subscriptions().list(
                part='snippet',
                mine=True,
                maxResults=50,
                pageToken=page_token
            )
            response = request.execute()
            page_count += 1
            logger.info(f'Fetched subscriptions page {page_count}')

            for item in response.get('items', []):
                subscriptions.append({
                    'channel_id': item['snippet']['resourceId']['channelId'],
                    'channel_name': item['snippet']['title']
                })

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        logger.info(f"Retrieved {len(subscriptions)} subscriptions")
        return subscriptions


def get_authenticated_client() -> YouTubeOAuthClient:
    """Factory function to create and authenticate a YouTube OAuth client.
    
    Returns:
        Authenticated YouTubeOAuthClient instance.
    """
    client = YouTubeOAuthClient()
    client.authenticate()
    return client
