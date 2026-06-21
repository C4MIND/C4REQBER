"""c4-cdi-turbo: Configuration module.

Contains all configuration classes and utilities.
"""

from src.config.db_config import DatabaseConfig, get_database_config, reset_database_config
from src.config.paths import (
    CONFIG_DIR,
    CONFIG_TOML,
    MODELS_JSON,
    PROFILE_JSON,
    ensure_config_dir,
    get_config_path,
    get_user_keys,
    apply_config_to_env,
    load_config_toml,
    UserSettings,
)

__all__ = [
    "DatabaseConfig",
    "get_database_config",
    "reset_database_config",
    "CONFIG_DIR",
    "CONFIG_TOML",
    "MODELS_JSON",
    "PROFILE_JSON",
    "ensure_config_dir",
    "get_config_path",
    "get_user_keys",
    "apply_config_to_env",
    "load_config_toml",
    "UserSettings",
]
