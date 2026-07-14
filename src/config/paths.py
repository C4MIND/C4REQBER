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

_KILO_ENV_LOADED = False

# OpenCode Zen free models (per ~/.kilo/.env — 6 accounts × 7 models)
OPENCODE_ZEN_FREE_MODELS: tuple[str, ...] = (
    "deepseek-v4-flash-free",
    "qwen3.6-plus-free",
    "big-pickle",
    "nemotron-3-ultra-free",
    "mimo-v2.5-free",
    "north-mini-code-free",
    "minimax-m3-free",
)


def load_verifiers_env() -> None:
    """Load verifier tool paths (Java, TLA_TOOLS_JAR, CVC5) from ~/.c4reqber/verifiers.env."""
    env_file = CONFIG_DIR / "verifiers.env"
    if not env_file.is_file():
        return
    for line in env_file.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.startswith("export "):
            continue
        key_val = stripped.removeprefix("export ").split("=", 1)
        if len(key_val) != 2:
            continue
        key, raw_val = key_val[0].strip(), key_val[1].strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = raw_val


def load_kilo_env(*, override: bool = False) -> None:
    """Load API keys from ~/.kilo (canonical vault). Idempotent."""
    load_verifiers_env()
    global _KILO_ENV_LOADED
    if _KILO_ENV_LOADED and not override:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    kilo_root = Path(os.environ.get("KILO_HOME", Path.home() / ".kilo"))
    for path in (
        kilo_root / ".env",
        kilo_root / "secrets" / "api_keys_working.env",
    ):
        if path.is_file():
            load_dotenv(path, override=override)
    _KILO_ENV_LOADED = True


def opencode_api_keys() -> list[str]:
    """Collect OpenCode Zen keys (OPENCODE_API_KEY + OPENCODE_API_KEY_1..N)."""
    load_kilo_env()
    keys: list[str] = []
    primary = os.environ.get("OPENCODE_API_KEY", "")
    if primary:
        keys.append(primary)
    for i in range(1, 13):
        k = os.environ.get(f"OPENCODE_API_KEY_{i}", "")
        if k and k not in keys:
            keys.append(k)
    return keys


def load_config_toml() -> dict[str, dict[str, str]]:
    """Load the user config.toml into nested dicts (or empty)."""
    if not CONFIG_TOML.is_file():
        return {}
    try:
        import toml  # type: ignore[import-untyped]

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
    """Return the important API keys from config.toml + env (env always wins).

    This is the preferred single source for keys instead of scattered os.getenv.
    """
    sections = load_config_toml()
    core = sections.get("core", {})
    llm = sections.get("llm", {})
    keys_sec = sections.get("keys", {})

    def pick(name: str, env_name: str, fallback: str = "") -> str:
        val = keys_sec.get(name) or llm.get(name) or core.get(name) or fallback
        return os.environ.get(env_name, val)

    return {
        "openrouter_api_key": pick("openrouter_api_key", "OPENROUTER_API_KEY"),
        "deepseek_api_key": pick("deepseek_api_key", "DEEPSEEK_API_KEY"),
        "brave_api_key": pick("brave_api_key", "BRAVE_API_KEY"),
        "tavily_api_key": pick("tavily_api_key", "TAVILY_API_KEY"),
        "exa_api_key": pick("exa_api_key", "EXA_API_KEY"),
        "xai_api_key": pick("xai_api_key", "XAI_API_KEY"),
        "lean4_path": pick("lean4_path", "LEAN4_PATH"),
        "api_url": pick("api_url", "C4_API_URL", "http://127.0.0.1:8000"),
        "language": core.get("language", "en"),
        "demo_mode": core.get("demo_mode", "false"),
    }


def get_key(name: str) -> str:
    """Convenience accessor for a single key.

    Supports common aliases:
      openrouter, deepseek, brave, tavily, exa, xai, lean4
    Falls back to direct env if unknown.
    """
    keys = get_user_keys()
    alias_map = {
        "openrouter": "openrouter_api_key",
        "openrouter_api_key": "openrouter_api_key",
        "deepseek": "deepseek_api_key",
        "deepseek_api_key": "deepseek_api_key",
        "brave": "brave_api_key",
        "brave_api_key": "brave_api_key",
        "tavily": "tavily_api_key",
        "tavily_api_key": "tavily_api_key",
        "exa": "exa_api_key",
        "exa_api_key": "exa_api_key",
        "xai": "xai_api_key",
        "xai_api_key": "xai_api_key",
        "lean4": "lean4_path",
        "lean4_path": "lean4_path",
    }
    key_name = alias_map.get(name.lower(), name)
    if key_name in keys:
        return keys[key_name]
    # Unknown key -> direct env fallback (for rare keys)
    env_name = name.upper() if not name.endswith("_API_KEY") else name
    return os.environ.get(env_name, "")


def get_search_keys() -> dict[str, str]:
    """Return the web/search related keys (most important for knowledge)."""
    k = get_user_keys()
    return {
        "brave_api_key": k.get("brave_api_key", ""),
        "tavily_api_key": k.get("tavily_api_key", ""),
        "exa_api_key": k.get("exa_api_key", ""),
    }


def apply_config_to_env() -> None:
    """Export known config values into os.environ (only if not already set).

    Called early by desktop launcher and CLI entrypoints.
    """
    load_kilo_env()
    try:
        from src.config.secrets_store import load_secrets_env

        load_secrets_env(override=False)
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("secrets.env load failed: %s", exc)
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
    """Lightweight view of user ~/.c4reqber settings (config + models tier etc).

    Use get_key() / get_user_keys() / get_search_keys() for full access.
    """

    config_dir: Path = CONFIG_DIR
    api_url: str = "http://127.0.0.1:8000"
    language: str = "en"
    demo_mode: bool = False
    openrouter_api_key: str = ""
    deepseek_api_key: str = ""
    brave_api_key: str = ""
    tavily_api_key: str = ""
    exa_api_key: str = ""
    xai_api_key: str = ""
    lean4_path: str = ""

    @classmethod
    def load(cls) -> UserSettings:
        sections = load_config_toml()
        core = sections.get("core", {})
        keys = get_user_keys()
        return cls(
            api_url=core.get("api_url", "http://127.0.0.1:8000"),
            language=core.get("language", "en"),
            demo_mode=core.get("demo_mode", "false").lower() in ("true", "1"),
            openrouter_api_key=keys.get("openrouter_api_key", ""),
            deepseek_api_key=keys.get("deepseek_api_key", ""),
            brave_api_key=keys.get("brave_api_key", ""),
            tavily_api_key=keys.get("tavily_api_key", ""),
            exa_api_key=keys.get("exa_api_key", ""),
            xai_api_key=keys.get("xai_api_key", ""),
            lean4_path=keys.get("lean4_path", ""),
        )

    def apply(self) -> None:
        """Apply this settings instance to env."""
        apply_config_to_env()
