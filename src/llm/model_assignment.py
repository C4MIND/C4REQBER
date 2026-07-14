"""
Model Assignment — per-phase LLM model configuration with persistence.

Stores model assignments at ~/.c4reqber/models.json
Used by: blast config models (CLI), get_model_for_phase (routing)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Default config location — unified via central paths
from src.config.paths import CONFIG_DIR  # type: ignore[assignment]
from src.config.paths import MODELS_JSON as CONFIG_FILE


# Phase descriptions (shown in CLI)
PHASE_DESCRIPTIONS = {
    "A": "C4 Cognitive Framing — complexity + PCA analysis",
    "B": "Knowledge Search — paper dedup + graph analysis",
    "C": "Gap Analysis — abstract similarity + trend detection",
    "D": "Hypothesis Generation — paradigm-shifting ideas",
    "E": "Simulation — compute plugins only (no LLM)",
    "F": "Dissertation — academic writing quality",
    "G": "Quality Control — p-value + KS validation",
}

# Default assignments per cost tier
DEFAULT_ASSIGNMENTS = {
    "budget": {
        "A": "deepseek/deepseek-v4-flash",
        "B": "deepseek/deepseek-v4-flash",
        "C": "deepseek/deepseek-v3.2",
        "D": "deepseek/deepseek-v4-flash",
        "E": "",
        "F": "deepseek/deepseek-v4-flash",
        "G": "deepseek/deepseek-v4-flash",
    },
    "balanced": {
        "A": "anthropic/claude-sonnet-4.6",
        "B": "qwen/qwen-2.5-72b-instruct",
        "C": "qwen/qwen-2.5-72b-instruct",
        "D": "anthropic/claude-sonnet-4.6",
        "E": "",
        "F": "anthropic/claude-sonnet-4.6",
        "G": "openai/gpt-4o-mini",
    },
    "premium": {
        "A": "anthropic/claude-opus-4.6",
        "B": "qwen/qwen-2.5-72b-instruct",
        "C": "google/gemini-3.1-pro",
        "D": "anthropic/claude-opus-4.6",
        "E": "",
        "F": "anthropic/claude-opus-4.6",
        "G": "google/gemini-3-flash",
    },
    "local": {
        "A": "qwen3.6:35b-a3b",
        "B": "gemma4:26b",
        "C": "qwen3.6:35b-a3b",
        "D": "qwen3.6:35b-a3b",
        "E": "",
        "F": "qwen3.6:35b-a3b",
        "G": "gemma4:26b",
    },
    "ultra_budget": {
        "A": "deepseek/deepseek-v4-flash",
        "B": "nvidia/nemotron-3-nano-30b-a3b",
        "C": "deepseek/deepseek-v4-flash",
        "D": "deepseek/deepseek-v4-flash",
        "E": "",
        "F": "minimax/minimax-m2.5",
        "G": "nvidia/nemotron-3-nano-30b-a3b",
    },
}


@dataclass
class PhaseAssignment:
    """PhaseAssignment."""
    model: str = ""          # Full model ID or "provider/model" or "local:tag"
    temperature: float = 0.5
    max_tokens: int = 800
    provider: str = ""       # auto-detected from model ID

    def to_dict(self) -> dict[str, Any]:
        return {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens}


@dataclass
class ModelAssignment:
    """ModelAssignment."""
    cost_tier: str = "balanced"
    api_base_url: str = ""
    phases: dict[str, PhaseAssignment] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None = None) -> ModelAssignment:
        """Load assignment from config file. Falls back to defaults."""
        filepath = Path(path) if path else CONFIG_FILE
        if filepath.exists():
            try:
                data = json.loads(filepath.read_text())
                return cls.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass
        return cls.create_default("balanced")

    @classmethod
    def create_default(cls, cost_tier: str = "balanced") -> ModelAssignment:
        """Create default assignment for a cost tier."""
        defaults = DEFAULT_ASSIGNMENTS.get(cost_tier, DEFAULT_ASSIGNMENTS["balanced"])
        phases = {}
        for phase in "ABCDEFG":
            model = defaults.get(phase, "")
            provider = _detect_provider(model)
            temp = 0.7 if phase == "D" else 0.5 if phase == "F" else 0.3
            max_tok = 2000 if phase == "F" else 800 if phase == "D" else 500
            phases[phase] = PhaseAssignment(model=model, temperature=temp, max_tokens=max_tok, provider=provider)
        return cls(cost_tier=cost_tier, phases=phases)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelAssignment:
        """Load from dict."""
        phases = {}
        for phase, pd in data.get("phases", {}).items():
            model = pd.get("model", "")
            phases[phase] = PhaseAssignment(
                model=model,
                temperature=pd.get("temperature", 0.5),
                max_tokens=pd.get("max_tokens", 800),
                provider=_detect_provider(model),
            )
        return cls(cost_tier=data.get("cost_tier", "balanced"), api_base_url=data.get("api_base_url", ""), phases=phases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cost_tier": self.cost_tier,
            "api_base_url": self.api_base_url,
            "phases": {p: a.to_dict() for p, a in self.phases.items()},
        }

    def save(self, path: str | Path | None = None) -> None:
        """Save assignment to config file."""
        filepath = Path(path) if path else CONFIG_FILE
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(self.to_dict(), indent=2))

    def get_model(self, phase: str) -> str:
        """Get model ID for a phase. Falls back to balanced defaults."""
        # First: check env var override
        env_model = os.environ.get(f"PHASE_{phase}_MODEL", "")
        if env_model:
            return env_model
        # Second: check phase assignment
        if phase in self.phases and self.phases[phase].model:
            return self.phases[phase].model
        # Third: check cost tier defaults
        if phase in DEFAULT_ASSIGNMENTS.get(self.cost_tier, {}):
            return DEFAULT_ASSIGNMENTS[self.cost_tier][phase]
        return ""

    def get_temperature(self, phase: str) -> float:
        """Get temperature."""
        if phase in self.phases:
            return self.phases[phase].temperature
        return 0.5

    def get_max_tokens(self, phase: str) -> int:
        """Get max tokens."""
        if phase in self.phases:
            return self.phases[phase].max_tokens
        return 800

    def estimate_cost(self, prompt_tokens: int = 1000) -> dict[str, float]:
        """Estimate total pipeline cost based on assigned models."""
        from src.llm.model_catalog import CATALOG
        total = 0.0
        phases = {}
        for phase in "ABCDEFG":
            model = self.get_model(phase)
            if not model:
                phases[phase] = 0.0
                continue
            found = None
            # Try exact match first, then partial match on model ID suffix
            for _key, entry in CATALOG.items():
                if entry.id == model or entry.id.endswith(model) or model.endswith(entry.id.split("/")[-1]):
                    found = entry
                    break
            if not found:
                # Try matching by catalog key
                for _key, entry in CATALOG.items():
                    if _key == model or model.endswith(_key):
                        found = entry
                        break
            if found:
                max_tok = self.get_max_tokens(phase)
                cost = (prompt_tokens * found.cost_in + max_tok * found.cost_out) / 1_000_000
                phases[phase] = round(cost, 6)
                total += cost
            else:
                phases[phase] = 0.0  # local model = free
        phases["total"] = round(total, 6)
        return phases


def _detect_provider(model: str) -> str:
    """Detect provider from model ID prefix."""
    if not model:
        return ""
    if "/" in model and model.count("/") == 1:
        prefix = model.split("/")[0]
        # Known provider prefixes
        provider_map = {
            "anthropic": "openrouter",
            "openai": "openrouter",
            "google": "openrouter",
            "qwen": "openrouter",
            "meta": "openrouter",
            "nvidia": "nvidia",
            "nvidia-nim": "nvidia",
            "liquid": "liquid",
            "yandex": "yandex",
            "yandexgpt": "yandex",
            "deepseek": "deepseek",
            "xai": "xai",
            "mistral": "mistral",
            "moonshot": "moonshot",
        }
        for known_prefix, provider in provider_map.items():
            if prefix == known_prefix or model.lower().startswith(known_prefix + "/"):
                return provider
        return prefix
    if ":" in model:
        return "local"
    return ""


def load_assignment(cost_tier: str = "balanced") -> ModelAssignment:
    """Load or create model assignment."""
    assignment = ModelAssignment.load()
    if assignment.cost_tier != cost_tier:
        assignment.cost_tier = cost_tier
        defaults = DEFAULT_ASSIGNMENTS.get(cost_tier, DEFAULT_ASSIGNMENTS["balanced"])
        for phase in "ABCDEFG":
            if phase not in assignment.phases:
                continue
            if defaults.get(phase):
                assignment.phases[phase].model = defaults[phase]
                assignment.phases[phase].provider = _detect_provider(defaults[phase])
    return assignment


__all__ = ["ModelAssignment", "PhaseAssignment", "CONFIG_FILE", "CONFIG_DIR",
           "DEFAULT_ASSIGNMENTS", "PHASE_DESCRIPTIONS", "load_assignment"]
