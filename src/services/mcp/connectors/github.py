"""
GitHub connector - repo read, commits, PRs, issues.
Uses GitHub REST API v3 with Personal Access Token.
Credentials stored via mcp/credentials.py (key: 'github', field: 'token').
"""
from __future__ import annotations

from src.services.mcp.credentials import get_credential, save_credential

GITHUB_API = "https://api.github.com"


class GitHubConnector:
    CONNECTOR_NAME = "github"

    def __init__(self):
        self._token = get_credential(self.CONNECTOR_NAME, "token")

    def is_configured(self) -> bool:
        return bool(self._token)

    def configure(self, token: str) -> None:
        save_credential(self.CONNECTOR_NAME, "token", token)
        self._token = token

    def _headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _require_config(self) -> None:
        if not self.is_configured():
            raise RuntimeError(
                "GitHub connector not configured. "
                "Call configure(token=...) with a GitHub Personal Access Token."
            )

    def list_repos(self, owner: str | None = None, per_page: int = 20) -> list[dict]:
        """List repos for authenticated user or a specific owner."""
        import httpx

        self._require_config()
        url = f"{GITHUB_API}/user/repos" if not owner else f"{GITHUB_API}/users/{owner}/repos"
        resp = httpx.get(url, headers=self._headers(), params={"per_page": per_page}, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def list_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 20) -> list[dict]:
        """List issues in a repo."""
        import httpx

        self._require_config()
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
        resp = httpx.get(
            url,
            headers=self._headers(),
            params={"state": state, "per_page": per_page},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()

    def list_pull_requests(self, owner: str, repo: str, state: str = "open", per_page: int = 20) -> list[dict]:
        """List pull requests in a repo."""
        import httpx

        self._require_config()
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
        resp = httpx.get(
            url,
            headers=self._headers(),
            params={"state": state, "per_page": per_page},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()

    def get_repo(self, owner: str, repo: str) -> dict:
        """Get repository metadata."""
        import httpx

        url = f"{GITHUB_API}/repos/{owner}/{repo}"
        resp = httpx.get(url, headers=self._headers(), timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def list_commits(self, owner: str, repo: str, per_page: int = 20) -> list[dict]:
        """List recent commits."""
        import httpx

        self._require_config()
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
        resp = httpx.get(url, headers=self._headers(), params={"per_page": per_page}, timeout=10.0)
        resp.raise_for_status()
        return resp.json()

    def get_connection_status(self) -> dict:
        return {
            "connector": "github",
            "configured": self.is_configured(),
            "capabilities": ["repos:read", "issues:read", "prs:read", "commits:read"],
        }
