"""Unit tests for G4P.1-G4P.2 (credentials + trust policy). No live API calls."""
import pytest


class TestCredentials:
    def test_save_and_get(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        credentials.save_credential("github", "token", "ghp_testtoken")
        assert credentials.get_credential("github", "token") == "ghp_testtoken"

    def test_get_missing_returns_none(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        assert credentials.get_credential("nonexistent", "token") is None

    def test_delete_single_key(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        credentials.save_credential("notion", "token", "secret_notion")
        credentials.delete_credential("notion", "token")
        assert credentials.get_credential("notion", "token") is None

    def test_credentials_are_not_plaintext(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        creds_path = tmp_path / "creds.json"
        monkeypatch.setattr(credentials, "CREDS_PATH", creds_path)
        credentials.save_credential("test", "key", "my_secret_value")
        raw_text = creds_path.read_text()
        assert "my_secret_value" not in raw_text

    def test_list_connectors(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        credentials.save_credential("google", "api_key", "key1")
        credentials.save_credential("github", "token", "tok1")
        connectors = credentials.list_connectors()
        assert "google" in connectors
        assert "github" in connectors


class TestTrustPolicy:
    def test_approve_and_is_trusted(self, tmp_path, monkeypatch):
        from src.services.mcp import trust_policy
        monkeypatch.setattr(trust_policy, "TRUST_PATH", tmp_path / "trusted.json")
        trust_policy.approve("https://my-mcp-server.com", "My Server")
        assert trust_policy.is_trusted("https://my-mcp-server.com")

    def test_untrusted_server_denied(self, tmp_path, monkeypatch):
        from src.services.mcp import trust_policy
        monkeypatch.setattr(trust_policy, "TRUST_PATH", tmp_path / "trusted.json")
        assert not trust_policy.is_trusted("https://evil-server.com")

    def test_require_trust_raises_for_unknown(self, tmp_path, monkeypatch):
        from src.services.mcp import trust_policy
        monkeypatch.setattr(trust_policy, "TRUST_PATH", tmp_path / "trusted.json")
        with pytest.raises(PermissionError):
            trust_policy.require_trust("https://unknown.com")

    def test_revoke_removes_trust(self, tmp_path, monkeypatch):
        from src.services.mcp import trust_policy
        monkeypatch.setattr(trust_policy, "TRUST_PATH", tmp_path / "trusted.json")
        trust_policy.approve("https://server.com")
        trust_policy.revoke("https://server.com")
        assert not trust_policy.is_trusted("https://server.com")


class TestConnectorStatus:
    def test_google_unconfigured(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        from src.services.mcp.connectors.google import GoogleConnector
        conn = GoogleConnector()
        status = conn.get_connection_status()
        assert status["configured"] is False

    def test_notion_unconfigured(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        from src.services.mcp.connectors.notion import NotionConnector
        conn = NotionConnector()
        assert not conn.is_configured()

    def test_github_unconfigured(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        from src.services.mcp.connectors.github import GitHubConnector
        conn = GitHubConnector()
        assert not conn.is_configured()

    def test_configure_saves_credential(self, tmp_path, monkeypatch):
        from src.services.mcp import credentials
        monkeypatch.setattr(credentials, "CREDS_PATH", tmp_path / "creds.json")
        from src.services.mcp.connectors.github import GitHubConnector
        conn = GitHubConnector()
        conn.configure("ghp_mytoken")
        assert conn.is_configured()
        assert credentials.get_credential("github", "token") == "ghp_mytoken"
