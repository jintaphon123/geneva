"""Unit tests for G6+/E+/G4+ web_api.py endpoints."""
import json

import pytest


def _dispatch_get(path, query=None):
    from src.geneva.web_runtime import SessionManager
    from src.geneva.web_api import _dispatch_get as dg

    mgr = SessionManager.__new__(SessionManager)
    return dg(mgr, path, query or {})


def _dispatch_post(path, payload=None):
    from src.geneva.web_runtime import SessionManager
    from src.geneva.web_api import _dispatch_post as dp

    mgr = SessionManager.__new__(SessionManager)
    return dp(mgr, path, payload or {})


def _dispatch_delete(path):
    from src.geneva.web_api import _dispatch_delete as dd

    return dd(path)


class TestPluginEndpoints:
    def test_list_plugins_returns_list(self):
        result = _dispatch_get("/api/plugins")
        assert "plugins" in result.body
        assert isinstance(result.body["plugins"], list)

    def test_get_plugin_deep_research(self):
        result = _dispatch_get("/api/plugins/deep_research")
        assert result.body.get("name") == "deep_research"

    def test_get_plugin_not_found(self):
        result = _dispatch_get("/api/plugins/nonexistent_xyz")
        assert result.status.value == 404

    def test_enable_missing_plugin_returns_404(self):
        result = _dispatch_post("/api/plugins/no_such_plugin/enable")
        assert result.status.value == 404

    def test_disable_missing_plugin_returns_404(self):
        result = _dispatch_post("/api/plugins/no_such_plugin/disable")
        assert result.status.value == 404


class TestConnectorEndpoints:
    def test_list_connectors_has_all_three(self):
        result = _dispatch_get("/api/connectors")
        assert "connectors" in result.body
        names = [c["connector"] for c in result.body["connectors"]]
        assert "google" in names
        assert "notion" in names
        assert "github" in names

    def test_configure_unknown_connector_404(self):
        result = _dispatch_post("/api/connectors/unknown/configure", {"token": "x"})
        assert result.status.value == 404

    def test_trust_server_requires_url(self):
        result = _dispatch_post("/api/connectors/google/trust", {})
        assert result.status.value == 400

    def test_trust_server_ok(self, tmp_path, monkeypatch):
        from src.services.mcp import trust_policy

        monkeypatch.setattr(trust_policy, "TRUST_PATH", tmp_path / "t.json")
        result = _dispatch_post("/api/connectors/mcp/trust", {"url": "https://test.com", "label": "Test"})
        assert result.body.get("ok") is True


class TestComputerUseEndpoint:
    def test_execute_missing_action_type_400(self):
        result = _dispatch_post("/api/computer-use/execute", {})
        assert result.status.value == 400

    def test_execute_navigate_no_adapter(self):
        result = _dispatch_post(
            "/api/computer-use/execute",
            {
                "action_type": "navigate",
                "target": "https://python.org",
            },
        )
        # No adapter -> still returns result dict (not 500)
        assert "status" in result.body or "error" in result.body

    def test_get_computer_use_log(self):
        result = _dispatch_get("/api/computer-use/log")
        assert "action_log" in result.body
