"""
c4reqber: Verification Configuration

Feature flags and thresholds for auto-formalization, consensus, and alignment.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutoFormalizationConfig:
    """Configuration for automatic formal proof generation."""

    enabled: bool = True
    languages: list[str] = field(default_factory=lambda: ["lean4", "coq", "dafny"])
    min_score: float = 0.3
    min_confidence: float = 0.7
    max_cost_per_discovery: float = 5.0  # USD
    human_gate_threshold: float = 0.9
    semantic_alignment_check: bool = True
    min_agreement: int = 2

    @classmethod
    def from_env(cls) -> AutoFormalizationConfig:
        """Load config from environment variables."""
        return cls(
            enabled=_env_bool("C4_AUTO_FORMALIZATION_ENABLED", True),
            languages=_env_list("C4_AUTO_FORMALIZATION_LANGUAGES", ["lean4", "coq", "dafny"]),
            min_score=_env_float("C4_AUTO_FORMALIZATION_MIN_SCORE", 0.3),
            min_confidence=_env_float("C4_AUTO_FORMALIZATION_MIN_CONFIDENCE", 0.7),
            max_cost_per_discovery=_env_float("C4_AUTO_FORMALIZATION_MAX_COST", 5.0),
            human_gate_threshold=_env_float("C4_AUTO_FORMALIZATION_HUMAN_GATE", 0.9),
            semantic_alignment_check=_env_bool("C4_SEMANTIC_ALIGNMENT_ENABLED", True),
            min_agreement=_env_int("C4_AUTO_FORMALIZATION_MIN_AGREEMENT", 2),
        )


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name, "").lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_list(name: str, default: list[str]) -> list[str]:
    val = os.getenv(name, "")
    if not val:
        return default
    return [v.strip() for v in val.split(",") if v.strip()]


# Global singleton config instance
_AUTO_FORMALIZATION_CONFIG: AutoFormalizationConfig | None = None


def get_auto_formalization_config() -> AutoFormalizationConfig:
    """Get the global auto-formalization config."""
    global _AUTO_FORMALIZATION_CONFIG
    if _AUTO_FORMALIZATION_CONFIG is None:
        _AUTO_FORMALIZATION_CONFIG = AutoFormalizationConfig.from_env()
    return _AUTO_FORMALIZATION_CONFIG


def reset_auto_formalization_config() -> None:
    """Reset config (useful for testing)."""
    global _AUTO_FORMALIZATION_CONFIG
    _AUTO_FORMALIZATION_CONFIG = None
