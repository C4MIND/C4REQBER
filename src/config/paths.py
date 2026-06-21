"""Central configuration paths for c4reqber.

Single source of truth for user config dir (~/.c4reqber preferred).

Used by: wizard, launchers, model assignment, profile, agent, TUI wrappers, etc.
This reduces duplication and makes desktop/CLI first-run consistent.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Primary unified location for all user data (config.toml, models.json, state, keys, etc.)
# Override with env C4REQBER_CONFIG=/custom/path for tests or containers.
CONFIG_DIR: Path = Path(os.environ.get("C4REQBER_CONFIG", Path.home() / ".c4reqber"))

# Common files
CONFIG_TOML = CONFIG_DIR / "config.toml"
MODELS_JSON = CONFIG_DIR / "models.json"
PROFILE_JSON = CONFIG_DIR / "profile.json"
STATE_JSON = CONFIG_DIR / "tui-v9-state.json"


def ensure_config_dir() -> Path:
    """Ensure the config dir exists and return it."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def get_config_path() -> Path:
    """Return the main config.toml path (does not create)."""
    return CONFIG_TOML


def resolve_config_dir() -> Path:
    """Return CONFIG_DIR after ensuring it (convenience for callers)."""
    return ensure_config_dir()


# --- Key loading (start of centralization to fight getenv sprawl) ---

def load_config_toml() -> dict[str, dict[str, str]]:
    """Load the user config.toml into nested dicts (or empty)."""
    if not CONFIG_TOML.is_file():
        return {}
    try:
        import toml

        raw = toml.load(CONFIG_TOML)
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, str]] = {}
        for section, values in raw.items():
            if isinstance(values, dict):
                out[str(section)] = {str(k): str(v) for k, v in values.items()}
        return out
    except Exception:
        return {}


def get_user_keys() -> dict[str, str]:
    """Return the important API keys from config.toml + env (env wins for override).

    This is the start of a single place to read keys instead of 100+ os.getenv.
    Keys: openrouter, deepseek, brave, tavily, exa, xai, lean4_path, etc.
    """
    sections = load_config_toml()
    core = sections.get("core", {})
    llm = sections.get("llm", {})
    keys = sections.get("keys", {})

    def pick(name: str, env_name: str, section_val: str | None = None) -> str:
        if section_val is None:
            # try common sections
            section_val = keys.get(name) or llm.get(name) or core.get(name) or ""
        return os.environ.get(env_name, section_val or "")

    return {
        "openrouter_api_key": pick("openrouter_api_key", "OPENROUTER_API_KEY", llm.get("openrouter_api_key")),
        "deepseek_api_key": pick("deepseek_api_key", "DEEPSEEK_API_KEY"),
        "brave_api_key": pick("brave_api_key", "BRAVE_API_KEY"),
        "tavily_api_key": pick("tavily_api_key", "TAVILY_API_KEY"),
        "exa_api_key": pick("exa_api_key", "EXA_API_KEY"),
        "xai_api_key": pick("xai_api_key", "XAI_API_KEY"),
        "lean4_path": pick("lean4_path", "LEAN4_PATH"),
        "api_url": pick("api_url", "C4_API_URL", core.get("api_url")),
        "language": core.get("language", "en"),
        "demo_mode": core.get("demo_mode", "false"),
    }


def apply_config_to_env() -> None:
    """Export known config values into os.environ (only if not already set).

    Called early by desktop launcher and CLI entrypoints.
    """
    mapping = get_user_keys()
    extra = {}
    sections = load_config_toml()
    core = sections.get("core", {})
    if core.get("demo_mode") in ("true", "1", "True"):
        extra["C4_DEMO_AUTH"] = "1"
    if core.get("language"):
        extra.setdefault("C4_LANG", core["language"])
    for key, val in {**mapping, **extra}.items():
        if key in ("language", "demo_mode"):
            continue  # handled above or via specific
        env_key = {
            "api_url": "C4_API_URL",
        }.get(key, key.upper())
        if val and not os.getenv(env_key):
            os.environ[env_key] = str(val)


# --- Minimal Settings object (start toward P3 "one Settings(BaseSettings)" from audit) ---

@dataclass
class UserSettings:
    """Lightweight view of user ~/.c4reqber settings (config + models tier etc)."""
    config_dir: Path = CONFIG_DIR
    api_url: str = "http://127.0.0.1:8000"
    language: str = "en"
    demo_mode: bool = False
    openrouter_api_key: str = ""
    deepseek_api_key: str = ""
    # ... add more as needed; keys loaded via get_user_keys

    @classmethod
    def load(cls) -> "UserSettings":
        sections = load_config_toml()
        core = sections.get("core", {})
        keys = get_user_keys()
        return cls(
            api_url=core.get("api_url", "http://127.0.0.1:8000"),
            language=core.get("language", "en"),
            demo_mode=core.get("demo_mode", "false").lower() in ("true", "1"),
            openrouter_api_key=keys.get("openrouter_api_key", ""),
            deepseek_api_key=keys.get("deepseek_api_key", ""),
        )

    def apply(self) -> None:
        """Apply this settings instance to env."""
        apply_config_to_env()
