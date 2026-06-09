from __future__ import annotations


"""User Profile Manager — persistent storage for user settings."""

import json
import logging
from pathlib import Path
from typing import Any

from src.core.user_profile import UserProfile
from src.contracts.pipeline_config import PipelineConfig


logger = logging.getLogger(__name__)

# Default config directory
CONFIG_DIR = Path.home() / ".config" / "c4reqber"
PROFILE_FILE = CONFIG_DIR / "profile.json"


class UserProfileManager:
    """Manage user profile and pipeline config persistence."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or CONFIG_DIR
        self.profile_file = self.config_dir / "profile.json"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Create config directory if missing."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> UserProfile:
        """Load user profile from disk, or return default."""
        if not self.profile_file.exists():
            logger.info("No profile found at %s, using defaults", self.profile_file)
            return UserProfile()

        try:
            with open(self.profile_file, encoding="utf-8") as f:
                data = json.load(f)
            return self._deserialize(data)
        except Exception as e:
            logger.warning("Failed to load profile: %s, using defaults", e)
            return UserProfile()

    def save(self, profile: UserProfile) -> None:
        """Save user profile to disk."""
        data = self._serialize(profile)
        with open(self.profile_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Profile saved to %s", self.profile_file)

    def _serialize(self, profile: UserProfile) -> dict[str, Any]:
        """Convert profile + config to JSON-serializable dict."""
        data = profile.to_dict()
        # PipelineConfig is stored inside preferences
        if "pipeline_config" not in data["preferences"]:
            data["preferences"]["pipeline_config"] = PipelineConfig(name="default").to_dict()
        return data

    def _deserialize(self, data: dict[str, Any]) -> UserProfile:
        """Convert dict back to UserProfile with PipelineConfig."""
        profile = UserProfile.from_dict(data)
        # Ensure pipeline_config exists in preferences
        prefs = data.get("preferences", {})
        if "pipeline_config" not in prefs:
            prefs["pipeline_config"] = PipelineConfig(name="default").to_dict()
            profile.preferences = prefs
        return profile

    def get_config(self) -> PipelineConfig:
        """Get pipeline config from profile (or defaults)."""
        profile = self.load()
        cfg_dict = profile.preferences.get("pipeline_config", {})
        return PipelineConfig.from_dict(cfg_dict)

    def set_config(self, config: PipelineConfig) -> None:
        """Update pipeline config in profile and save."""
        profile = self.load()
        profile.preferences["pipeline_config"] = config.to_dict()
        self.save(profile)

    def update_config_field(self, key: str, value: Any) -> None:
        """Update a single config field and save."""
        profile = self.load()
        cfg = profile.preferences.get("pipeline_config", PipelineConfig(name="default").to_dict())
        cfg[key] = value
        profile.preferences["pipeline_config"] = cfg
        self.save(profile)

    def reset_config(self) -> None:
        """Reset pipeline config to defaults."""
        profile = self.load()
        profile.preferences["pipeline_config"] = PipelineConfig(name="default").to_dict()
        self.save(profile)

    @property
    def profile_path(self) -> str:
        return str(self.profile_file)
