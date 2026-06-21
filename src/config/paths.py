"""Central configuration paths for c4reqber.

Single source of truth for user config dir (~/.c4reqber preferred).

Used by: wizard, launchers, model assignment, profile, agent, TUI wrappers, etc.
This reduces duplication and makes desktop/CLI first-run consistent.
"""
from __future__ import annotations

import os
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
