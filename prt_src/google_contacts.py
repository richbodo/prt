"""Utilities to sync Google contacts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import data_dir

SCOPES = ["https://www.googleapis.com/auth/contacts.readonly"]


def _secrets_file() -> Path:
    """Return path to ``client_secret.json`` in the repo ``secrets`` folder."""
    secrets_dir = Path(__file__).resolve().parents[1] / "secrets"
    path = secrets_dir / "client_secret.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return path


def _credentials() -> Credentials:
    """Load stored credentials or run OAuth flow."""
    token_path = data_dir() / "token.json"
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secrets_file = _secrets_file()
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return creds


def fetch_contacts(config: Dict[str, str]) -> List[Tuple[str, str]]:
    """Fetch contacts from Google People API."""
    creds = _credentials()
    try:
        service = build("people", "v1", credentials=creds)
        result = (
            service.people()
            .connections()
            .list(
                resourceName="people/me",
                pageSize=10,
                personFields="names,emailAddresses",
            )
            .execute()
        )
    except HttpError as err:
        raise RuntimeError(f"Google API error: {err}") from err

    contacts: List[Tuple[str, str]] = []
    for person in result.get("connections", []):
        name = ""
        email = ""
        if person.get("names"):
            name = person["names"][0].get("displayName", "")
        if person.get("emailAddresses"):
            email = person["emailAddresses"][0].get("value", "")
        contacts.append((name, email))
    return contacts
