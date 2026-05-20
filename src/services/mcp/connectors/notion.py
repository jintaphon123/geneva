"""
Notion connector - Page read/create/update, database query.
Uses Notion API v1 with Bearer token.
Credentials stored via mcp/credentials.py (key: 'notion', field: 'token').
"""
from __future__ import annotations

from typing import Any

from src.services.mcp.credentials import get_credential, save_credential

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionConnector:
    CONNECTOR_NAME = "notion"

    def __init__(self):
        self._token = get_credential(self.CONNECTOR_NAME, "token")

    def is_configured(self) -> bool:
        return bool(self._token)

    def configure(self, token: str) -> None:
        save_credential(self.CONNECTOR_NAME, "token", token)
        self._token = token

    def _headers(self) -> dict:
        if not self._token:
            raise RuntimeError(
                "Notion connector not configured. "
                "Call configure(token=...) with your Notion integration token."
            )
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def search(self, query: str, filter_type: str | None = None) -> list[dict]:
        """Search pages/databases. filter_type: 'page' or 'database' or None."""
        import httpx

        body: dict[str, Any] = {"query": query}
        if filter_type:
            body["filter"] = {"value": filter_type, "property": "object"}
        resp = httpx.post(f"{NOTION_API}/search", json=body, headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json().get("results", [])

    def get_page(self, page_id: str) -> dict:
        """Get a page by ID."""
        import httpx

        resp = httpx.get(f"{NOTION_API}/pages/{page_id}", headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def create_page(self, parent_id: str, title: str, content: str = "") -> dict:
        """Create a new page under parent_id with given title and optional content."""
        import httpx

        body = {
            "parent": {"page_id": parent_id},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": content}}]},
                }
            ]
            if content
            else [],
        }
        resp = httpx.post(f"{NOTION_API}/pages", json=body, headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def query_database(
        self,
        database_id: str,
        filter_obj: dict | None = None,
        max_results: int = 20,
    ) -> list[dict]:
        """Query a Notion database. Returns list of page dicts."""
        import httpx

        body: dict[str, Any] = {"page_size": max_results}
        if filter_obj:
            body["filter"] = filter_obj
        resp = httpx.post(
            f"{NOTION_API}/databases/{database_id}/query",
            json=body,
            headers=self._headers(),
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

    def get_connection_status(self) -> dict:
        return {
            "connector": "notion",
            "configured": self.is_configured(),
            "capabilities": ["pages:read", "pages:create", "database:query"],
        }
