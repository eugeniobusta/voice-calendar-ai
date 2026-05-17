"""
setup_google_auth.py — Run this ONCE on your Mac to get Google Calendar credentials.

WHAT THIS DOES:
  1. Opens a browser window for you to log into Google
  2. Asks for Calendar access permission (you click Allow)
  3. Prints your client ID, client secret, and refresh token

  You then copy those three values into your .env file.
  After that, delete this file and credentials.json — they're no longer needed.
  The refresh token stored in .env is what the app uses forever.

BEFORE RUNNING:
  1. Complete the Google Cloud Console setup (see README)
  2. Download your OAuth credentials as 'credentials.json'
  3. Place credentials.json in this same folder
  4. Run: python setup_google_auth.py

ONLY NEEDS TO RUN ONCE:
  Refresh tokens don't expire unless you revoke them in Google account settings.
  You never need to re-authenticate.
"""
import json
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing package. Run: pip install google-auth-oauthlib")
    exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",  # read + write calendar events
]


def main():
    creds_file = Path("credentials.json")

    if not creds_file.exists():
        print("\n  ERROR: credentials.json not found.\n")
        print("  Steps to get it:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. Create a new project (name it anything, e.g. 'voice-calendar')")
        print("  3. Go to 'APIs & Services' → 'Library'")
        print("  4. Search for 'Google Calendar API' → Enable it")
        print("  5. Go to 'APIs & Services' → 'Credentials'")
        print("  6. Click 'Create Credentials' → 'OAuth 2.0 Client ID'")
        print("  7. If prompted, configure the consent screen first:")
        print("       User Type: External → App name: Voice Calendar → Save")
        print("  8. Application type: Desktop app → Name: voice-calendar → Create")
        print("  9. Click the download icon (⬇) → rename file to credentials.json")
        print(" 10. Move credentials.json into this project folder")
        print("\n  Then run this script again.\n")
        return

    print("\n  Opening browser for Google login...")
    print("  (If the browser doesn't open, copy the URL shown in the terminal)\n")

    # This opens a browser, handles the OAuth dance, and returns credentials
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
    creds = flow.run_local_server(port=0)

    # Read the client ID and secret from the credentials file
    with open(creds_file) as f:
        data = json.load(f)
    client = data.get("installed") or data.get("web", {})

    print("\n" + "=" * 65)
    print("  SUCCESS! Copy these three lines into your .env file:")
    print("=" * 65)
    print(f"GOOGLE_CLIENT_ID={client.get('client_id', '')}")
    print(f"GOOGLE_CLIENT_SECRET={client.get('client_secret', '')}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 65)
    print()
    print("  IMPORTANT: After copying these to .env, delete credentials.json")
    print("  It's a sensitive file and shouldn't stay in your project folder.\n")


if __name__ == "__main__":
    main()
