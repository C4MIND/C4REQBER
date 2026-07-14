"""
Complexity Adapter: Wraps C4 engines with progressive disclosure
Controls what users see based on their selected complexity level
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ComplexityLevel(Enum):
    """User-facing complexity levels"""

    LITE = "lite"
    ADVANCED = "advanced"
    EXPERT = "expert"


class DisclosureConfig(BaseModel):
    """
    Configuration that controls what features are visible at each complexity level

    Fields:
        show_c4_coordinates: Display C4 (T,S,A) coordinates in UI
        show_operators: Show operator names (Û_T, Û_S, Û_A)
        show_pipeline_steps: Show pipeline progression (8 steps)
        show_agent_details: Show MP agent reasoning
        show_troubleshooting: Show error details and debug info
        allow_custom_operators: Allow writing custom C4 operators
        allow_wasm_upload: Allow uploading WASM modules
    """

    model_config = {"frozen": True}  # Make config immutable

    show_c4_coordinates: bool = False
    show_operators: bool = False
    show_pipeline_steps: bool = False
    show_agent_details: bool = False
    show_troubleshooting: bool = False
    allow_custom_operators: bool = False
    allow_wasm_upload: bool = False


# Pre-configured disclosure settings for each level
LITE_CONFIG = DisclosureConfig(
    show_c4_coordinates=False,
    show_operators=False,
    show_pipeline_steps=False,
    show_agent_details=False,
    show_troubleshooting=False,
    allow_custom_operators=False,
    allow_wasm_upload=False,
)

ADVANCED_CONFIG = DisclosureConfig(
    show_c4_coordinates=True,  # Show as subtle tags
    show_operators=True,  # Show as descriptive step names
    show_pipeline_steps=True,  # Show as interactive flowchart
    show_agent_details=True,  # Show as toggleable agent cards
    show_troubleshooting=True,  # Show error details
    allow_custom_operators=False,
    allow_wasm_upload=False,
)

EXPERT_CONFIG = DisclosureConfig(
    show_c4_coordinates=True,  # Show raw coordinates
    show_operators=True,  # Show raw operator names
    show_pipeline_steps=True,  # Show editable pipeline
    show_agent_details=True,  # Show full agent reasoning
    show_troubleshooting=True,  # Show full stack traces
    allow_custom_operators=True,  # Enable custom operator editor
    allow_wasm_upload=True,  # Enable WASM module loader
)


# Mapping from level to config
_CONFIG_MAP = {
    ComplexityLevel.LITE: LITE_CONFIG,
    ComplexityLevel.ADVANCED: ADVANCED_CONFIG,
    ComplexityLevel.EXPERT: EXPERT_CONFIG,
}


def get_config(level: ComplexityLevel) -> DisclosureConfig:
    """
    Get the disclosure configuration for a given complexity level

    Args:
        level: The user's selected complexity level

    Returns:
        DisclosureConfig specifying what features to show

    Raises:
        ValueError: If invalid level provided
    """
    if not isinstance(level, ComplexityLevel):
        raise ValueError(f"Invalid complexity level: {level}")

    return _CONFIG_MAP[level]


def validate_level(level_str: str) -> ComplexityLevel:
    """
    Validate and convert string to ComplexityLevel enum

    Strips whitespace and normalizes case before validation

    Args:
        level_str: String representation (e.g., 'lite', 'advanced', 'expert')

    Returns:
        ComplexityLevel enum value

    Raises:
        ValueError: If string doesn't match any level after stripping
    """
    # Strip whitespace first
    level_str = level_str.strip()

    try:
        return ComplexityLevel(level_str.lower())
    except ValueError as err:
        raise ValueError(
            f"Invalid complexity level string: '{level_str}'. "
            f"Must be one of: {[level.value for level in ComplexityLevel]}"
        ) from err


class UserLevelStorage:
    """Handles persistence of user complexity level preference"""

    @staticmethod
    def get_default_level() -> ComplexityLevel:
        """New users start with Lite level"""
        return ComplexityLevel.LITE

    @staticmethod
    def get_for_existing_user() -> ComplexityLevel:
        """Existing users (pre-6.6) keep Advanced to preserve experience"""
        return ComplexityLevel.ADVANCED


# Cache TTL constants (in seconds)
CACHE_TTL_SHORT = 3600  # 1 hour
CACHE_TTL_LONG = 86400  # 24 hours


# Version tracking for migrations
CURRENT_CONFIG_VERSION = "1.0"
"""Bump this when DisclosureConfig schema changes"""
