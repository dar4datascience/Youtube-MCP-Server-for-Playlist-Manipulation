#!/usr/bin/env python3
"""
One-time OAuth2 setup script to obtain a refresh token for YouTube API access.
Run this once, authorize in browser, then copy the refresh token to your .env file.
"""
import os
import sys
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Load environment variables from .env file
load_dotenv()

# OAuth2 scopes needed for playlist manipulation
SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.readonly'
]


def main():
    client_id = os.getenv('YOUTUBE_CLIENT_ID')
    client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("ERROR: YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET must be set in .env file")
        print("\nTo get these credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable the YouTube Data API v3")
        print("4. Go to Credentials → Create Credentials → OAuth client ID")
        print("5. Choose 'Desktop app' as the application type")
        print("6. Download the credentials and extract client_id and client_secret")
        sys.exit(1)

    # Create client config dict
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080"]
        }
    }

    print("Starting OAuth2 flow...")
    print("A browser window will open. Please authorize access to your YouTube account.")
    print()

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=8080)

    print("\n" + "=" * 60)
    print("SUCCESS! OAuth2 authorization completed.")
    print("=" * 60)
    print()
    print("Add the following to your .env file:")
    print()
    print(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}")
    print()
    print("IMPORTANT: Keep this token secure. Do not commit it to version control.")

    # Also write to a temporary file for convenience
    token_file = '.refresh_token'
    with open(token_file, 'w') as f:
        f.write(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}\n")

    print(f"\nToken also saved to: {token_file}")

    # Test the credentials
    print("\nTesting credentials by fetching your channel info...")
    from googleapiclient.discovery import build

    youtube = build('youtube', 'v3', credentials=credentials)
    try:
        response = youtube.channels().list(part='snippet', mine=True).execute()
        if response.get('items'):
            channel = response['items'][0]
            print(f"✓ Connected to channel: {channel['snippet']['title']}")
        else:
            print("⚠ Could not fetch channel info, but credentials appear valid")
    except Exception as e:
        print(f"✗ Error testing credentials: {e}")


if __name__ == '__main__':
    main()
