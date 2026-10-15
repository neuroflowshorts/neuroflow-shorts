"""Uploads output/short.mp4 to YouTube using a stored refresh token."""
import json
import os
import pathlib

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

OUT = pathlib.Path(__file__).parent / "output"
meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))

creds = Credentials(
    None,
    refresh_token=os.environ["YT_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["YT_CLIENT_ID"],
    client_secret=os.environ["YT_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)
youtube = build("youtube", "v3", credentials=creds)

body = {
    "snippet": {
        "title": meta["title"],
        "description": meta["description"],
        "tags": meta["tags"],
        "categoryId": "27",  # Education
    },
    "status": {
        "privacyStatus": os.environ.get("PRIVACY", "private") or "private",
        "selfDeclaredMadeForKids": False,
    },
}
req = youtube.videos().insert(
    part="snippet,status",
    body=body,
    media_body=MediaFileUpload(str(OUT / "short.mp4"), chunksize=-1, resumable=True),
)
resp = None
while resp is None:
    _, resp = req.next_chunk()
print("Uploaded:", "https://youtube.com/shorts/" + resp["id"], "| privacy:", body["status"]["privacyStatus"])
