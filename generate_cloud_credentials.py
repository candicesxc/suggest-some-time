#!/usr/bin/env python3
"""
Generate base64-encoded credentials for cloud deployment.

Run this script locally AFTER you have authenticated with Google Calendar
(i.e., after token.pickle exists). It will output a base64 string that you
can use as the GOOGLE_CREDENTIALS environment variable on Render.

Usage:
    python generate_cloud_credentials.py

Then copy the output and paste it as the GOOGLE_CREDENTIALS environment
variable in your Render dashboard.
"""

import pickle
import json
import base64
import os

def main():
    if not os.path.exists('token.pickle'):
        print("Error: token.pickle not found!")
        print("Please run 'python app.py' locally first to authenticate with Google Calendar.")
        return

    if not os.path.exists('credentials.json'):
        print("Error: credentials.json not found!")
        print("Please download your OAuth credentials from Google Cloud Console.")
        return

    # Load the token
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)

    # Load the client credentials
    with open('credentials.json', 'r') as f:
        client_creds = json.load(f)

    # Extract client info (handle both 'installed' and 'web' types)
    client_info = client_creds.get('installed') or client_creds.get('web', {})

    # Build the credentials object for cloud
    cloud_creds = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': client_info.get('client_id'),
        'client_secret': client_info.get('client_secret'),
    }

    # Encode as base64
    creds_json = json.dumps(cloud_creds)
    creds_base64 = base64.b64encode(creds_json.encode()).decode()

    print("\n" + "="*60)
    print("GOOGLE_CREDENTIALS for Render:")
    print("="*60)
    print(creds_base64)
    print("="*60)
    print("\nCopy the above string and paste it as the GOOGLE_CREDENTIALS")
    print("environment variable in your Render dashboard.")
    print("\nNote: Keep this secret! It contains your Google Calendar access.")

if __name__ == '__main__':
    main()
