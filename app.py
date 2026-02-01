import base64
import json
import os
import pickle
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.pickle")
CLIENT_SECRETS_PATH = os.getenv("GOOGLE_CLIENT_SECRETS_PATH", "credentials.json")

app = Flask(__name__)


def _parse_google_credentials(value: str) -> Dict[str, Any]:
    raw_value = value.strip()
    if not raw_value:
        raise ValueError("GOOGLE_CREDENTIALS is empty after trimming.")

    try:
        decoded = base64.b64decode(raw_value).decode("utf-8")
        return json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return json.loads(raw_value)


def _credentials_from_env() -> Optional[Credentials]:
    creds_value = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_value:
        return None

    creds_data = _parse_google_credentials(creds_value)
    required_fields = ["refresh_token", "client_id", "client_secret"]
    missing_fields = [field for field in required_fields if not creds_data.get(field)]
    if missing_fields:
        raise ValueError(
            "GOOGLE_CREDENTIALS is missing required fields: "
            f"{', '.join(missing_fields)}."
        )

    token_uri = creds_data.get("token_uri", "https://oauth2.googleapis.com/token")
    creds = Credentials(
        token=creds_data.get("token"),
        refresh_token=creds_data.get("refresh_token"),
        token_uri=token_uri,
        client_id=creds_data.get("client_id"),
        client_secret=creds_data.get("client_secret"),
        scopes=SCOPES,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def _credentials_from_local_token() -> Optional[Credentials]:
    if not os.path.exists(TOKEN_PATH):
        return None

    with open(TOKEN_PATH, "rb") as token_file:
        creds = pickle.load(token_file)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as token_file:
            pickle.dump(creds, token_file)

    return creds


def _credentials_from_local_flow() -> Optional[Credentials]:
    if not os.path.exists(CLIENT_SECRETS_PATH):
        return None

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, "wb") as token_file:
        pickle.dump(creds, token_file)

    return creds


def get_calendar_service():
    try:
        creds = _credentials_from_env()
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Calendar not connected. GOOGLE_CREDENTIALS is set but invalid. "
            "Regenerate it locally with generate_cloud_credentials.py or fix the env var."
        ) from exc

    if not creds:
        creds = _credentials_from_local_token()

    if not creds and not os.getenv("GOOGLE_CREDENTIALS"):
        creds = _credentials_from_local_flow()

    if not creds:
        raise RuntimeError(
            "Calendar not connected. Check that GOOGLE_CREDENTIALS is set correctly "
            "in environment variables, or run locally to authenticate."
        )

    return build("calendar", "v3", credentials=creds)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calendar/status")
def calendar_status():
    try:
        service = get_calendar_service()
        calendar = service.calendarList().list(maxResults=1).execute()
        return jsonify({"connected": True, "calendar": calendar.get("items", [])})
    except Exception as exc:  # pragma: no cover - surfaced in API response
        return jsonify({"connected": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
