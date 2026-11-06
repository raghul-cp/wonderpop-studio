"""
Step 9-10 of the pipeline: upload the assembled video to YouTube via the
YouTube Data API v3, with support for scheduled (private-until-publishAt)
uploads. Vertical (9:16, <=3min) video + "Shorts" in the title/description
is auto-classified as a YouTube Short by YouTube itself — no special
upload flag is required.

Auth: refresh-token based (see src/get_youtube_token.py — run that once,
locally, then store the three values it prints as GitHub Secrets).
This module never performs an interactive login; it only ever uses an
existing refresh token, so it works unattended inside GitHub Actions.
"""

import os
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]


def _get_credentials() -> Credentials:
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    missing = [n for n, v in [("YOUTUBE_CLIENT_ID", client_id),
                               ("YOUTUBE_CLIENT_SECRET", client_secret),
                               ("YOUTUBE_REFRESH_TOKEN", refresh_token)] if not v]
    if missing:
        raise RuntimeError(
            f"Missing YouTube credentials: {', '.join(missing)}. "
            "Run `python -m src.get_youtube_token` locally once, then set these "
            "as GitHub Secrets (see SETUP.md)."
        )

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


def upload_video(video_path: str, title: str, description: str, tags: list,
                  cfg: dict, category_id: str = None) -> dict:
    """
    Uploads video_path to YouTube. Returns {"video_id": str, "url": str}.
    Respects cfg["upload"]["privacy_status"] and, if scheduling, computes
    publishAt from cfg["upload"]["schedule_ahead_hours"].
    """
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    privacy_status = cfg["upload"]["privacy_status"]
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id or cfg["channel"]["default_category_id"],
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": cfg["channel"]["made_for_kids"],
            # See SETUP.md before setting this true: it discloses *realistic*
            # altered/synthetic media per YouTube policy, not stylized animation.
            "containsSyntheticMedia": cfg["upload"].get("contains_synthetic_media", False),
        },
    }

    if privacy_status == "private" and cfg["upload"].get("schedule_ahead_hours"):
        publish_at = datetime.now(timezone.utc) + timedelta(hours=cfg["upload"]["schedule_ahead_hours"])
        body["status"]["publishAt"] = publish_at.isoformat().replace("+00:00", "Z")

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")

    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[youtube_uploader] Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    url = f"https://youtube.com/shorts/{video_id}"
    print(f"[youtube_uploader] Uploaded: {url}")
    return {"video_id": video_id, "url": url}


if __name__ == "__main__":
    print("This module is meant to be called from src/main.py. "
          "To test auth only, run `python -m src.get_youtube_token` first.")
