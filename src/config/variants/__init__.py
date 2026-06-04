"""Multi-variant configuration system"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


VARIANTS = ["invent", "engineering", "business", "science"]

@dataclass
class VariantConfig:
    """VariantConfig."""
    name: str
    title: str
    subtitle: str
    default_patterns: list[str] = field(default_factory=list[Any])
    features: list[str] = field(default_factory=list[Any])
    theme_color: str = "#4ecdc4"

VARIANTS_CONFIG = {
    "invent": VariantConfig(
        name="invent",
        title="c4reqber Invent",
        subtitle="Universal Problem-Solving for Breakthrough Innovation",
        default_patterns=["monte_carlo", "agent_based", "circuit_simulation"],
        features=["triz", "c4", "abduction", "paradigm_detection"],
        theme_color="#6c5ce7",
    ),
    "engineering": VariantConfig(
        name="engineering",
        title="c4reqber Engineering",
        subtitle="Computational Simulation Platform for Engineers",
        default_patterns=["fem", "cfd", "pid_tuning", "kalman_filter"],
        features=["patterns", "c4", "triz", "simulation"],
        theme_color="#00b894",
    ),
    "business": VariantConfig(
        name="business",
        title="c4reqber Business",
        subtitle="Strategic Decision Intelligence for Business",
        default_patterns=["game_theory", "supply_chain", "queueing_networks"],
        features=["triz", "abduction", "dashboard", "plugins"],
        theme_color="#0984e3",
    ),
    "science": VariantConfig(
        name="science",
        title="c4reqber Science",
        subtitle="Accelerating Scientific Discovery with AI",
        default_patterns=["quantum", "molecular_dynamics", "dft"],
        features=["c4", "paradigm_detection", "abduction", "literature"],
        theme_color="#d63031",
    ),
}
