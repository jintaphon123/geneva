"""Unit tests for Phase E+ — SkillEvalRunner + PluginRuntime CRUD."""

import json

import pytest

from src.geneva.plugin_runtime import PluginRuntime
from src.skills.eval_runner import SkillEvalCase, SkillEvalRunner


class TestSkillEvalRunner:
    def setup_method(self):
        self.runner = SkillEvalRunner(threshold=0.7)

    def test_keyword_scorer_all_present(self):
        scorer = SkillEvalRunner.keyword_scorer(["python", "code"])
        assert scorer("Here is some python code") == 1.0

    def test_keyword_scorer_partial(self):
        scorer = SkillEvalRunner.keyword_scorer(["python", "code", "example"])
        score = scorer("python example")
        assert abs(score - 2 / 3) < 0.01

    def test_min_length_scorer(self):
        scorer = SkillEvalRunner.min_length_scorer(100)
        assert scorer("x" * 100) == 1.0
        assert scorer("x" * 50) == 0.0

    def test_report_passes_above_threshold(self):
        cases = [
            SkillEvalCase("c1", "prompt", SkillEvalRunner.keyword_scorer(["hello"])),
        ]
        report = self.runner.run("test_skill", cases, ["hello world"])
        assert report.passed
        assert report.overall_score == 1.0

    def test_report_fails_below_threshold(self):
        cases = [
            SkillEvalCase("c1", "prompt", SkillEvalRunner.keyword_scorer(["hello"])),
        ]
        report = self.runner.run("test_skill", cases, ["goodbye world"])
        assert not report.passed
        assert report.overall_score == 0.0

    def test_mismatched_lengths_raise(self):
        cases = [SkillEvalCase("c1", "p", SkillEvalRunner.keyword_scorer([]))]
        with pytest.raises(ValueError):
            self.runner.run("s", cases, ["out1", "out2"])


class TestPluginRuntimeCRUD:
    def setup_method(self, tmp_path_factory):
        pass  # uses pytest tmp_path fixture below

    def test_install_valid_manifest(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        # Create a valid manifest
        manifest_dir = tmp_path / "my_plugin"
        manifest_dir.mkdir()
        (manifest_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "my_plugin",
                    "version": "1.0.0",
                    "description": "Test plugin",
                    "permissions": ["web:search"],
                    "enabled": True,
                }
            )
        )
        manifest = rt.install(manifest_dir / "plugin.json")
        assert manifest.name == "my_plugin"
        assert (tmp_path / "plugins" / "my_plugin" / "plugin.json").exists()

    def test_install_duplicate_raises(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        manifest_dir = tmp_path / "dup_plugin"
        manifest_dir.mkdir()
        (manifest_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "dup_plugin",
                    "version": "1.0",
                    "description": "x",
                    "permissions": [],
                    "enabled": True,
                }
            )
        )
        rt.install(manifest_dir / "plugin.json")
        with pytest.raises(ValueError, match="already installed"):
            rt.install(manifest_dir / "plugin.json")

    def test_enable_safe_scope_no_approval_needed(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        plugin_dir = tmp_path / "plugins" / "safe_plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "safe_plugin",
                    "version": "1.0",
                    "description": "x",
                    "permissions": ["web:search"],
                    "enabled": False,
                }
            )
        )
        assert rt.enable("safe_plugin") is True

    def test_enable_sensitive_scope_requires_approval(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        plugin_dir = tmp_path / "plugins" / "risky_plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "risky_plugin",
                    "version": "1.0",
                    "description": "x",
                    "permissions": ["files:write"],
                    "enabled": False,
                }
            )
        )
        with pytest.raises(PermissionError):
            rt.enable("risky_plugin")
        # With approval it works
        assert rt.enable("risky_plugin", approved_scopes=["files:write"]) is True

    def test_disable_plugin(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        plugin_dir = tmp_path / "plugins" / "tog_plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "tog_plugin",
                    "version": "1.0",
                    "description": "x",
                    "permissions": [],
                    "enabled": True,
                }
            )
        )
        assert rt.disable("tog_plugin") is True
        data = json.loads((plugin_dir / "plugin.json").read_text())
        assert data["enabled"] is False

    def test_rollback_restores_previous_version(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        plugin_dir = tmp_path / "plugins" / "rb_plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "rb_plugin",
                    "version": "1.0",
                    "description": "original",
                    "permissions": [],
                    "enabled": True,
                }
            )
        )
        rt.save_revision("rb_plugin")
        # Modify
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "rb_plugin",
                    "version": "2.0",
                    "description": "modified",
                    "permissions": [],
                    "enabled": True,
                }
            )
        )
        rt.rollback("rb_plugin")
        data = json.loads((plugin_dir / "plugin.json").read_text())
        assert data["version"] == "1.0"

    def test_uninstall_removes_directory(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        plugin_dir = tmp_path / "plugins" / "del_plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "del_plugin",
                    "version": "1.0",
                    "description": "x",
                    "permissions": [],
                    "enabled": True,
                }
            )
        )
        rt.uninstall("del_plugin")
        assert not plugin_dir.exists()

    def test_cannot_uninstall_builtin(self, tmp_path):
        rt = PluginRuntime(plugin_dir=tmp_path / "plugins")
        with pytest.raises(ValueError, match="builtin"):
            rt.uninstall("deep_research")
