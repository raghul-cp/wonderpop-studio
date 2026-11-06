"""
Run this ONCE, locally (never in GitHub Actions — it needs a browser).

It opens a browser window for you to sign in to the Google account that
owns your YouTube channel, then prints a long-lived refresh token.
Paste that token into the YOUTUBE_REFRESH_TOKEN GitHub Secret (see
SETUP.md) and the GitHub Action can upload videos forever without you
signing in again (until you manually revoke access).

Prerequisites (see SETUP.md for the full walkthrough):
  1. A Google Cloud project with the "YouTube Data API v3" enabled.
  2. An OAuth 2.0 Client ID of type "Desktop app", downloaded as
     client_secret.json and placed in this project's root folder
     (this file is gitignored — never commit it).

Usage:
    python -m src.get_youtube_token
"""

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

ROOT_DIR = Path(__file__).resolve().parent.parent
CLIENT_SECRET_FILE = ROOT_DIR / "client_secret.json"


def main():
    if not CLIENT_SECRET_FILE.exists():
        print(f"ERROR: {CLIENT_SECRET_FILE} not found.")
        print("Download your OAuth client (type: Desktop app) from Google Cloud Console")
        print("and save it as client_secret.json in the project root. See SETUP.md.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    credentials = flow.run_local_server(port=0)

    print("\n--- SUCCESS ---")
    print("Add these as GitHub Secrets (Settings -> Secrets and variables -> Actions):\n")
    print(f"YOUTUBE_CLIENT_ID={credentials.client_id}")
    print(f"YOUTUBE_CLIENT_SECRET={credentials.client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}")
    print("\nKeep these secret — anyone with the refresh token can upload to your channel.")

    # Also save locally for convenience when testing uploads on your own machine.
    token_path = ROOT_DIR / "data" / ".youtube_token.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps({
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "refresh_token": credentials.refresh_token,
    }, indent=2), encoding="utf-8")
    print(f"\nAlso saved locally to {token_path} (gitignored) for local testing.")


if __name__ == "__main__":
    main()
