"""
C4REQBER: 153 Metaprograms Library - Core data structures
Metaprogram (MP) filters that shape agent perception and reasoning.

Each MP is a perceptual dimension. Agents operate with MP profiles
(combinations of MPs) to eliminate blind spots through rotation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING


class MPDimension(Enum):
    """Major MP dimension categories."""

    THINKING = "thinking"  # How information is processed
    FEELING = "feeling"  # Emotional/motivational patterns
    DOING = "doing"  # Action orientation
    RELATING = "relating"  # Interpersonal patterns
    PERCEIVING = "perceiving"  # Sensory/perceptual patterns
    IDENTITY = "identity"  # Self-concept patterns
    TIME = "time"  # Temporal orientation
    CHUNKING = "chunking"  # Information granularity
    DIRECTION = "direction"  # Goal orientation
    REASON = "reason"  # Decision-making basis


if TYPE_CHECKING:
    from src.metamodels.mp.library import MPLibrary

@dataclass
class Metaprogram:
    """Single metaprogram dimension with two poles."""

    id: str
    name: str
    name_ru: str
    dimension: MPDimension
    pole_a: str
    pole_b: str
    description: str
    agent_prompt_suffix: str = ""  # How to instruct an agent with this MP

    def profile_prompt(self, leaning: str = "balanced") -> str:
        """Generate prompt modifier for this MP."""
        if leaning == "a":
            return f"Prioritize {self.pole_a} over {self.pole_b}. {self.agent_prompt_suffix}"
        elif leaning == "b":
            return f"Prioritize {self.pole_b} over {self.pole_a}. {self.agent_prompt_suffix}"
        return f"Balance {self.pole_a} and {self.pole_b}. {self.agent_prompt_suffix}"


if TYPE_CHECKING:
    from src.metamodels.mp.library import MPLibrary

@dataclass
class MPProfile:
    """A complete MP profile: one setting per dimension."""

    name: str
    name_ru: str
    settings: dict[str, str]  # MP id → "a", "b", or "balanced"
    description: str = ""

    def to_prompt(self, mplib: MPLibrary) -> str:
        """Convert profile to full agent prompt modifier."""
        parts = [f"# Agent Profile: {self.name}\n{self.description}\n"]
        for mp_id, leaning in self.settings.items():
            mp = mplib.get(mp_id)
            if mp:
                parts.append(
                    f"- {mp.name}: {mp.pole_a if leaning == 'a' else mp.pole_b if leaning == 'b' else 'balanced'}"
                )
        return "\n".join(parts)
