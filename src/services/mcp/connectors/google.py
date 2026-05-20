"""
Google Workspace connector - Gmail, Calendar, Drive.
Uses Google API via httpx (no google-auth library required for basic REST).
Credentials stored via mcp/credentials.py (key: 'google', field: 'api_key').

API key approach: user generates API key in Google Cloud Console.
For OAuth flow: deferred to Layer 1.
"""
from __future__ import annotations

from src.services.mcp.credentials import get_credential, save_credential


class GoogleConnector:
    CONNECTOR_NAME = "google"

    def __init__(self):
        self._api_key = get_credential(self.CONNECTOR_NAME, "api_key")

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def configure(self, api_key: str) -> None:
        save_credential(self.CONNECTOR_NAME, "api_key", api_key)
        self._api_key = api_key

    def _require_config(self) -> None:
        if not self.is_configured():
            raise RuntimeError(
                "Google connector not configured. "
                "Call configure(api_key=...) or set via Settings."
            )

    def list_calendar_events(self, calendar_id: str = "primary", max_results: int = 10) -> list[dict]:
        """List upcoming calendar events. Returns list of event dicts."""
        self._require_config()
        import httpx

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        params = {
            "key": self._api_key,
            "maxResults": max_results,
            "orderBy": "startTime",
            "singleEvents": "true",
        }
        resp = httpx.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json().get("items", [])

    def search_gmail(self, query: str, max_results: int = 10) -> list[dict]:
        """Search Gmail messages. Returns list of message dicts."""
        self._require_config()
        raise RuntimeError(
            "Gmail search requires OAuth2 authorization (not API key). "
            "OAuth flow is deferred to Layer 1. "
            "Use the MCP Gmail connector (mcp__claude_ai_Gmail__search_threads) instead."
        )

    def search_drive(self, query: str, max_results: int = 10) -> list[dict]:
        """Search Google Drive files. Returns list of file dicts."""
        self._require_config()
        import httpx

        url = "https://www.googleapis.com/drive/v3/files"
        params = {
            "key": self._api_key,
            "q": query,
            "pageSize": max_results,
            "fields": "files(id,name,mimeType,modifiedTime,webViewLink)",
        }
        resp = httpx.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json().get("files", [])

    def get_connection_status(self) -> dict:
        return {
            "connector": "google",
            "configured": self.is_configured(),
            "capabilities": ["calendar:read", "drive:read"],
            "oauth_required_for": ["gmail:read", "gmail:send", "calendar:write"],
        }
