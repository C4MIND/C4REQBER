"""
C4REQBER: Pipeline Configuration System
Plugin registry and templates for custom metamodels.

The concrete config dataclasses (PipelineConfig, PipelineStepConfig,
PipelineStepType) now live in src/contracts/pipeline_config.py — the foundational
types layer — so lower-level packages can use them without depending on this
high-level `pipeline` package. They are re-exported here for backward compatibility.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.contracts.pipeline_config import (
    PipelineConfig,
    PipelineStepConfig,
    PipelineStepType,
)


__all__ = [
    "PipelineConfig",
    "PipelineStepConfig",
    "PipelineStepType",
    "MetamodelPlugin",
    "PluginRegistry",
    "PipelineTemplateLibrary",
]


# ═══════════════════════════════════════════════════════════════════
# PLUGIN REGISTRY
# ═══════════════════════════════════════════════════════════════════


@dataclass
class MetamodelPlugin:
    """A third-party metamodel plugin."""

    id: str
    name: str
    description: str
    version: str
    author: str
    entrypoint: str  # Python module path
    config_schema: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    installed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "installed": self.installed,
        }


class PluginRegistry:
    """Registry for third-party metamodel plugins."""

    def __init__(self, plugins_dir: Path | None = None) -> None:
        self.plugins_dir = plugins_dir or Path("plugins")
        self._plugins: dict[str, MetamodelPlugin] = {}
        self._handlers: dict[str, Callable] = {}  # type: ignore[type-arg]
        self._load_builtin_plugins()

    def _load_builtin_plugins(self) -> None:
        """Register built-in plugins."""
        builtins = [
            MetamodelPlugin(
                id="swot",
                name="SWOT Analysis",
                description="Strengths, Weaknesses, Opportunities, Threats analysis",
                version="1.0",
                author="C4Reqber",
                entrypoint="src.plugins.swot",
                tags=["business", "strategy"],
                installed=True,
            ),
            MetamodelPlugin(
                id="five_whys",
                name="5 Whys",
                description="Root cause analysis through iterative questioning",
                version="1.0",
                author="C4Reqber",
                entrypoint="src.plugins.five_whys",
                tags=["analysis", "root_cause"],
                installed=True,
            ),
            MetamodelPlugin(
                id="morphological",
                name="Morphological Analysis",
                description="Systematic exploration of all possible solutions",
                version="1.0",
                author="C4Reqber",
                entrypoint="src.plugins.morphological",
                tags=["creativity", "systematic"],
                installed=True,
            ),
            MetamodelPlugin(
                id="lateral_thinking",
                name="Lateral Thinking",
                description="De Bono's lateral thinking techniques",
                version="1.0",
                author="C4Reqber",
                entrypoint="src.plugins.lateral_thinking",
                tags=["creativity", "divergent"],
                installed=True,
            ),
        ]
        for p in builtins:
            self._plugins[p.id] = p

    def register(self, plugin: MetamodelPlugin) -> None:
        """Register a new plugin."""
        self._plugins[plugin.id] = plugin

    def get(self, plugin_id: str) -> MetamodelPlugin | None:
        """Get plugin by ID."""
        return self._plugins.get(plugin_id)

    def list_all(self) -> list[MetamodelPlugin]:
        """List all registered plugins."""
        return list(self._plugins.values())

    def list_by_tag(self, tag: str) -> list[MetamodelPlugin]:
        """List plugins by tag."""
        return [p for p in self._plugins.values() if tag in p.tags]

    def list_installed(self) -> list[MetamodelPlugin]:
        """List installed plugins."""
        return [p for p in self._plugins.values() if p.installed]

    def install(self, plugin_id: str) -> bool:
        """Mark plugin as installed."""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].installed = True
            return True
        return False

    def uninstall(self, plugin_id: str) -> bool:
        """Mark plugin as uninstalled."""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].installed = False
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize registry."""
        return {
            "plugins": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "version": p.version,
                    "author": p.author,
                    "tags": p.tags,
                    "installed": p.installed,
                }
                for p in self._plugins.values()
            ],
            "total": len(self._plugins),
        }


# ═══════════════════════════════════════════════════════════════════
# PIPELINE TEMPLATES
# ═══════════════════════════════════════════════════════════════════


class PipelineTemplateLibrary:
    """Library of pre-built pipeline templates."""

    TEMPLATES: dict[str, PipelineConfig] = {
        "default": PipelineConfig(
            name="Default Pipeline",
            description="Standard 8-step universal problem-solving pipeline",
            steps=[
                PipelineStepConfig(step_type="impact", enabled=True),
                PipelineStepConfig(step_type="prior_art", enabled=True),
                PipelineStepConfig(step_type="c4_fingerprint", enabled=True),
                PipelineStepConfig(step_type="mp_rotation", enabled=True),
                PipelineStepConfig(step_type="qzrf_select", enabled=True),
                PipelineStepConfig(step_type="isomorphism", enabled=True),
                PipelineStepConfig(step_type="synthesis", enabled=True),
                PipelineStepConfig(step_type="validation", enabled=True),
            ],
        ),
        "research": PipelineConfig(
            name="Research Pipeline",
            description="Heavy emphasis on prior art and isomorphism search",
            steps=[
                PipelineStepConfig(step_type="impact", enabled=True),
                PipelineStepConfig(
                    step_type="prior_art",
                    enabled=True,
                    config={"sources": ["arxiv", "semantic_scholar", "pubmed"]},
                ),
                PipelineStepConfig(step_type="c4_fingerprint", enabled=True),
                PipelineStepConfig(step_type="isomorphism", enabled=True),
                PipelineStepConfig(step_type="synthesis", enabled=True),
                PipelineStepConfig(step_type="validation", enabled=True),
            ],
            metamodels={
                "impact": True,
                "compass": False,
                "tote": False,
                "qzrf": False,
                "matrix_dream": False,
                "mp_rotation": False,
            },
        ),
        "creative": PipelineConfig(
            name="Creative Pipeline",
            description="Emphasis on divergent thinking and pattern matching",
            steps=[
                PipelineStepConfig(step_type="impact", enabled=True),
                PipelineStepConfig(step_type="c4_fingerprint", enabled=True),
                PipelineStepConfig(
                    step_type="mp_rotation", enabled=True, config={"n_profiles": 5}
                ),
                PipelineStepConfig(step_type="qzrf_select", enabled=True),
                PipelineStepConfig(
                    step_type="synthesis", enabled=True, config={"temperature": 0.9}
                ),
            ],
            metamodels={
                "impact": True,
                "compass": False,
                "tote": False,
                "qzrf": True,
                "matrix_dream": True,
                "mp_rotation": True,
            },
        ),
        "rapid": PipelineConfig(
            name="Rapid Pipeline",
            description="Fast problem-solving with minimal steps",
            steps=[
                PipelineStepConfig(step_type="c4_fingerprint", enabled=True),
                PipelineStepConfig(step_type="mp_rotation", enabled=True),
                PipelineStepConfig(step_type="synthesis", enabled=True),
            ],
            provider_routing={"default": "local_only"},
        ),
        "deep_analysis": PipelineConfig(
            name="Deep Analysis",
            description="Thorough analysis with all metamodels and validation",
            steps=[
                PipelineStepConfig(step_type="impact", enabled=True),
                PipelineStepConfig(step_type="prior_art", enabled=True),
                PipelineStepConfig(step_type="c4_fingerprint", enabled=True),
                PipelineStepConfig(step_type="mp_rotation", enabled=True),
                PipelineStepConfig(step_type="qzrf_select", enabled=True),
                PipelineStepConfig(step_type="isomorphism", enabled=True),
                PipelineStepConfig(step_type="synthesis", enabled=True),
                PipelineStepConfig(
                    step_type="validation", enabled=True, config={"iterations": 3}
                ),
            ],
            provider_routing={"synthesis": "quality", "validation": "quality"},
        ),
    }

    @classmethod
    def get(cls, name: str) -> PipelineConfig | None:
        """Get template by name."""
        return cls.TEMPLATES.get(name)

    @classmethod
    def list_all(cls) -> list[dict[str, str]]:
        """List all templates."""
        return [
            {"id": k, "name": v.name, "description": v.description}
            for k, v in cls.TEMPLATES.items()
        ]

    @classmethod
    def instantiate(cls, name: str, overrides: dict | None = None) -> PipelineConfig:  # type: ignore[type-arg]
        """Create a new config from template with optional overrides."""
        template = cls.TEMPLATES.get(name, cls.TEMPLATES["default"])
        config = PipelineConfig.from_dict(template.to_dict())
        if overrides:
            for key, value in overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        config.name = f"{config.name} (Custom)"
        config.created_at = time.time()
        return config
