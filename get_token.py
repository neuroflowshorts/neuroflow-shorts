"""Run ONCE on your own computer to get the YouTube refresh token.
Needs client_secret.json (downloaded from Google Cloud) in the same folder.
pip install google-auth-oauthlib
"""
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json", ["https://www.googleapis.com/auth/youtube.upload"]
)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("\n=== Save these 3 values as GitHub Secrets ===")
print("YT_CLIENT_ID     =", creds.client_id)
print("YT_CLIENT_SECRET =", creds.client_secret)
print("YT_REFRESH_TOKEN =", creds.refresh_token)
