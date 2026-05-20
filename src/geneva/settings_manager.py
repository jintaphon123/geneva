from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

GENEVA_DIR = Path.home() / ".geneva"
DEFAULT_PROVIDER = "openrouter"
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"


@dataclass
class GenevaConfig:
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    google_api_key: str = ""
    gemini_cli_path: str = "gemini"
    codex_cli_path: str = "codex"
    default_provider: str = DEFAULT_PROVIDER
    default_model: str = DEFAULT_MODEL
    research_model: str = DEFAULT_MODEL
    fast_model: str = DEFAULT_MODEL
    default_mode: str = "medium"
    geneva_dir: str = str(GENEVA_DIR)
    workspace_dir: str = str(Path.home() / "Documents" / "Geneva")
    dark_mode: bool = False


def _config_path() -> Path:
    path = GENEVA_DIR / "settings.json"
    GENEVA_DIR.mkdir(parents=True, exist_ok=True)
    return path


def load_settings() -> GenevaConfig:
    path = _config_path()
    if not path.exists():
        return GenevaConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _normalize_config(
            GenevaConfig(
                **{
                    key: value
                    for key, value in data.items()
                    if key in GenevaConfig.__dataclass_fields__
                }
            )
        )
    except Exception:
        return GenevaConfig()


def _normalize_config(config: GenevaConfig) -> GenevaConfig:
    """Keep older multi-provider settings usable in the single-key OpenRouter flow."""
    if not config.openrouter_api_key and config.anthropic_api_key:
        config.openrouter_api_key = config.anthropic_api_key
        config.anthropic_api_key = ""
    config.default_provider = DEFAULT_PROVIDER
    config.default_model = DEFAULT_MODEL
    config.research_model = DEFAULT_MODEL
    config.fast_model = DEFAULT_MODEL
    return config


def save_settings(config: GenevaConfig) -> None:
    path = _config_path()
    payload = json.dumps(asdict(_normalize_config(config)), indent=2, ensure_ascii=False)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(path)


def get_redacted(config: GenevaConfig) -> dict[str, object]:
    """Return config dict with API keys redacted for API response."""
    data = asdict(config)
    for key in ("anthropic_api_key", "openrouter_api_key", "google_api_key"):
        value = data.get(key, "")
        if isinstance(value, str):
            data[key] = f"sk-***...{value[-4:]}" if len(value) > 8 else ("set" if value else "")
    return data


def check_cli(binary: str) -> bool:
    return shutil.which(binary) is not None
