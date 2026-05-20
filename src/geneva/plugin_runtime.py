from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    description: str
    tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    evals: list[str] = field(default_factory=list)
    ui_panels: list[str] = field(default_factory=list)
    trust_policy: str = "workspace"
    enabled: bool = True
    source: str = "local"


BUILTIN_PLUGIN_MANIFESTS: tuple[PluginManifest, ...] = (
    PluginManifest(
        name="geneva.deep_research",
        version="0.1.0",
        description="Long-horizon research modes with source graph, evidence cards, citation map, trace, and quality score.",
        tools=["WebSearch", "WebFetch"],
        prompts=["deep-research-contract"],
        permissions=["network:web"],
        evals=["research_citation_smoke", "source_conflict_smoke", "mode_difference_smoke"],
        ui_panels=["research_trace", "citation_map", "source_graph"],
        trust_policy="geneva_builtin",
        source="builtin",
    ),
    PluginManifest(
        name="geneva.computer_use",
        version="0.1.0",
        description="Policy-first computer-use action runtime with sensitive-action confirmation and prompt-injection firewall.",
        tools=["ComputerUse"],
        permissions=["screen:observe", "browser:act", "desktop:act:user_confirmed"],
        evals=["sensitive_action_gate", "prompt_injection_firewall", "browser_action_log"],
        ui_panels=["computer_action_log", "screenshot_viewer"],
        trust_policy="geneva_builtin",
        source="builtin",
    ),
    PluginManifest(
        name="geneva.documents",
        version="0.1.0",
        description="Local-first document parse, generation, verification, and citation-trace runtime.",
        tools=["DocumentParse", "DocumentGenerate", "DocumentVerify"],
        permissions=["files:read", "files:write:user_confirmed"],
        evals=["document_parse_smoke", "document_generate_smoke", "citation_trace_smoke"],
        ui_panels=["document_artifact", "layout_preview", "citation_trace"],
        trust_policy="geneva_builtin",
        source="builtin",
    ),
)


import re as _re

_SAFE_PLUGIN_NAME_RE = _re.compile(r'^[A-Za-z0-9_\-]{1,64}$')


def _require_safe_plugin_name(name: str) -> None:
    """Raise ValueError if plugin name could be used for path traversal."""
    if not _SAFE_PLUGIN_NAME_RE.match(name):
        raise ValueError(
            f"Invalid plugin name {name!r}. "
            "Names must be 1-64 characters of [A-Za-z0-9_-]."
        )


class PluginRuntime:
    """Loads plugin manifests and exposes Geneva-owned first-class capabilities."""

    def __init__(self, plugin_dir: Path | None = None) -> None:
        self.plugin_dir = plugin_dir or (Path.home() / ".geneva" / "plugins")

    def list_manifests(self, *, include_builtin: bool = True) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []
        if include_builtin:
            manifests.extend(BUILTIN_PLUGIN_MANIFESTS)
        manifests.extend(self.load_local_manifests())
        return manifests

    def list_manifest_dicts(self, *, include_builtin: bool = True) -> list[dict[str, Any]]:
        return [asdict(manifest) for manifest in self.list_manifests(include_builtin=include_builtin)]

    def load_local_manifests(self) -> list[PluginManifest]:
        if not self.plugin_dir.exists():
            return []
        manifests: list[PluginManifest] = []
        for manifest_path in sorted(self.plugin_dir.glob("*/plugin.json")):
            try:
                manifest = self._manifest_from_json(manifest_path)
                manifests.append(manifest)
            except Exception:
                continue
        return manifests

    def install(self, manifest_path: Path | str) -> PluginManifest:
        """
        Install a plugin from a plugin.json manifest file or directory.
        Validates manifest fields. Copies to plugin_dir/{name}/plugin.json.
        Raises ValueError if manifest is invalid or plugin already installed.
        """
        path = Path(manifest_path)
        if path.is_dir():
            path = path / "plugin.json"
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"plugin manifest must be a JSON object: {path}")
        if not str(data.get("name") or "").strip():
            raise ValueError("Plugin manifest must have a name")
        if not str(data.get("version") or "").strip():
            raise ValueError("Plugin manifest must have a version")

        manifest = self._manifest_from_json(path)
        _require_safe_plugin_name(manifest.name)

        dest_dir = self.plugin_dir / manifest.name
        if dest_dir.exists():
            raise ValueError(
                f"Plugin '{manifest.name}' is already installed. Use update or uninstall first."
            )

        dest_dir.mkdir(parents=True, exist_ok=True)
        import shutil

        shutil.copy2(path, dest_dir / "plugin.json")
        return manifest

    def enable(self, plugin_name: str, *, approved_scopes: list[str] | None = None) -> bool:
        """
        Enable a plugin by name. Returns True on success.
        Checks that all declared permissions are either in approved_scopes or are "safe" scopes.
        Raises PermissionError if plugin requests unapproved sensitive scopes.
        """
        _require_safe_plugin_name(plugin_name)
        manifest_path = self.plugin_dir / plugin_name / "plugin.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Plugin '{plugin_name}' not found")

        manifest = self._manifest_from_json(manifest_path)

        SAFE_SCOPES = {"memory:read", "memory:write", "web:search", "web:fetch"}
        SENSITIVE_SCOPES = {
            "files:write",
            "browser:act",
            "screen:observe",
            "network:send",
            "desktop:act",
        }
        approved_scopes = approved_scopes or []

        for perm in manifest.permissions:
            if perm in SAFE_SCOPES:
                continue
            if perm in SENSITIVE_SCOPES and perm not in approved_scopes:
                raise PermissionError(
                    f"Plugin '{plugin_name}' requests sensitive scope '{perm}' "
                    f"which has not been approved. Pass approved_scopes=['{perm}'] to allow."
                )

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["enabled"] = True
        manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True

    def disable(self, plugin_name: str) -> bool:
        """Disable a plugin. Returns True on success."""
        _require_safe_plugin_name(plugin_name)
        manifest_path = self.plugin_dir / plugin_name / "plugin.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Plugin '{plugin_name}' not found")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["enabled"] = False
        manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True

    def uninstall(self, plugin_name: str) -> bool:
        """
        Remove a plugin directory entirely. Returns True on success.
        Cannot uninstall builtin plugins (raises ValueError).
        """
        _require_safe_plugin_name(plugin_name)
        builtin_names = {m.name for m in BUILTIN_PLUGIN_MANIFESTS}
        builtin_names.update(m.name.rsplit(".", 1)[-1] for m in BUILTIN_PLUGIN_MANIFESTS)
        if plugin_name in builtin_names:
            raise ValueError(f"Cannot uninstall builtin plugin '{plugin_name}'")

        plugin_dir = self.plugin_dir / plugin_name
        if not plugin_dir.exists():
            raise FileNotFoundError(f"Plugin '{plugin_name}' not installed")

        import shutil

        shutil.rmtree(plugin_dir)
        return True

    def save_revision(self, plugin_name: str) -> Path:
        """
        Save current plugin.json as a revision for rollback.
        Returns path to revision file.
        """
        _require_safe_plugin_name(plugin_name)
        manifest_path = self.plugin_dir / plugin_name / "plugin.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Plugin '{plugin_name}' not found")

        import shutil
        import time

        ts = int(time.time())
        revision_path = self.plugin_dir / plugin_name / f"plugin.json.{ts}.bak"
        shutil.copy2(manifest_path, revision_path)
        return revision_path

    def rollback(self, plugin_name: str) -> bool:
        """
        Restore the most recent revision backup. Returns True on success.
        Raises FileNotFoundError if no backup exists.
        """
        _require_safe_plugin_name(plugin_name)
        plugin_dir = self.plugin_dir / plugin_name
        backups = sorted(plugin_dir.glob("plugin.json.*.bak"), reverse=True)
        if not backups:
            raise FileNotFoundError(f"No revision backup found for plugin '{plugin_name}'")

        import shutil

        shutil.copy2(backups[0], plugin_dir / "plugin.json")
        backups[0].unlink()
        return True

    def _manifest_from_json(self, manifest_path: Path) -> PluginManifest:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"plugin manifest must be a JSON object: {manifest_path}")
        name = str(data.get("name") or "").strip()
        version = str(data.get("version") or "").strip()
        if not name or not version:
            raise ValueError(f"plugin manifest requires name and version: {manifest_path}")
        return PluginManifest(
            name=name,
            version=version,
            description=str(data.get("description") or ""),
            tools=self._string_list(data.get("tools")),
            skills=self._string_list(data.get("skills")),
            prompts=self._string_list(data.get("prompts")),
            mcp_servers=self._string_list(data.get("mcp_servers")),
            permissions=self._string_list(data.get("permissions")),
            evals=self._string_list(data.get("evals")),
            ui_panels=self._string_list(data.get("ui_panels")),
            trust_policy=str(data.get("trust_policy") or "workspace"),
            enabled=bool(data.get("enabled", True)),
            source=str(manifest_path),
        )

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]
