"""Uploads output/short.mp4 to YouTube using a stored refresh token."""
import json
import os
import pathlib

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

OUT = pathlib.Path(__file__).parent / "output"
meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))

def env(name):
    return os.environ.get(name, "").strip().strip('"').strip("'")


CID, CSEC, RTOK = env("YT_CLIENT_ID"), env("YT_CLIENT_SECRET"), env("YT_REFRESH_TOKEN")
# Safe checks (no secret values are printed):
print("Check client_id: starts with", CID[:8], "| ends with .apps.googleusercontent.com:",
      CID.endswith(".apps.googleusercontent.com"), "| length", len(CID))
print("Check client_secret: starts with GOCSPX-:", CSEC.startswith("GOCSPX-"), "| length", len(CSEC))
print("Check refresh token: starts with 1//:", RTOK.startswith("1//"), "| length", len(RTOK))

creds = Credentials(
    None,
    refresh_token=RTOK,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CID,
    client_secret=CSEC,
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
# AI label: on by default (honest: the narration is AI-generated). Set repo variable AI_LABEL=false to turn it off.
if os.environ.get("AI_LABEL", "true").strip().lower() != "false":
    body["status"]["containsSyntheticMedia"] = True

req = youtube.videos().insert(
    part="snippet,status",
    body=body,
    media_body=MediaFileUpload(str(OUT / "short.mp4"), chunksize=-1, resumable=True),
)
resp = None
while resp is None:
    _, resp = req.next_chunk()
print("Uploaded:", "https://youtube.com/shorts/" + resp["id"], "| privacy:", body["status"]["privacyStatus"])
