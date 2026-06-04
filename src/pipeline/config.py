"""
C4REQBER: Pipeline Configuration System
Export/import and plugin registry for custom metamodels.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PipelineStepType(Enum):
    """Built-in pipeline step types."""

    IMPACT = "impact"
    PRIOR_ART = "prior_art"
    C4_FINGERPRINT = "c4_fingerprint"
    MP_ROTATION = "mp_rotation"
    QZRF_SELECT = "qzrf_select"
    ISOMORPHISM = "isomorphism"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    CUSTOM = "custom"


@dataclass
class PipelineStepConfig:
    """Configuration for a single pipeline step."""

    step_type: str
    enabled: bool = True
    provider_preset: str | None = None  # LLM provider routing
    config: dict[str, Any] = field(default_factory=dict)
    # For custom steps
    plugin_id: str | None = None
    plugin_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    name: str = "default"
    description: str = ""
    version: str = "1.0"
    domain: str = "general"
    mode: str = "autopilot"
    steps: list[PipelineStepConfig] = field(default_factory=list)
    provider_routing: dict[str, str] = field(default_factory=dict)
    metamodels: dict[str, bool] = field(
        default_factory=lambda: {
            "impact": True,
            "compass": True,
            "tote": True,
            "qzrf": True,
            "matrix_dream": True,
            "mp_rotation": True,
        }
    )
    c4_pipeline: dict[str, Any] = field(
        default_factory=lambda: {
            "initial_state": [1, 1, 1],
            "target_state": [2, 2, 2],
            "observer_positions": ["IMMERSED", "OBSERVING", "META"],
        }
    )
    integrations: dict[str, bool] = field(
        default_factory=lambda: {
            "arxiv": True,
            "semantic_scholar": True,
            "wikipedia": True,
            "obsidian_export": True,
        }
    )
    created_at: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)

    # Quality gate thresholds
    min_sources: int = 3
    min_source_databases: int = 1
    min_sources_with_url: int = 2
    min_gaps: int = 1
    min_gap_evidence_length: int = 20
    min_hypotheses: int = 1
    require_numerical_constraints: bool = False
    hypothesis_ambition: str = "novel"
    require_simulation_success: bool = False
    simulation_timeout_seconds: float = 60.0
    require_verification: bool = False
    min_dissertation_words: int = 600
    verification_backend: str = "hybrid"
    enable_functors: bool = True
    max_sources: int = 50
    fallback_to_web_search: bool = True
    include_epistemic_notice: bool = True
    min_quality_score: int = 60
    api_keys: dict[str, str] = field(default_factory=dict)
    llm_temperature: float = 0.8
    auto_retry_failed_steps: bool = True
    enable_quality_score: bool = True
    max_llm_tokens_per_section: int = 800

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        result = asdict(self)
        # Convert steps
        result["steps"] = [asdict(s) for s in self.steps]
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        """Load from dict — all fields deserialized."""
        steps = [PipelineStepConfig(**s) for s in data.get("steps", [])]
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            domain=data.get("domain", "general"),
            mode=data.get("mode", "autopilot"),
            steps=steps,
            provider_routing=data.get("provider_routing", {}),
            metamodels=data.get("metamodels", {}),
            c4_pipeline=data.get("c4_pipeline", {}),
            integrations=data.get("integrations", {}),
            created_at=data.get("created_at", time.time()),
            tags=data.get("tags", []),
            min_sources=data.get("min_sources", 3),
            min_source_databases=data.get("min_source_databases", 1),
            min_sources_with_url=data.get("min_sources_with_url", 2),
            min_gaps=data.get("min_gaps", 1),
            min_gap_evidence_length=data.get("min_gap_evidence_length", 20),
            min_hypotheses=data.get("min_hypotheses", 1),
            require_numerical_constraints=data.get("require_numerical_constraints", False),
            hypothesis_ambition=data.get("hypothesis_ambition", "novel"),
            require_simulation_success=data.get("require_simulation_success", False),
            simulation_timeout_seconds=data.get("simulation_timeout_seconds", 60.0),
            require_verification=data.get("require_verification", False),
            min_dissertation_words=data.get("min_dissertation_words", 600),
            verification_backend=data.get("verification_backend", "hybrid"),
            enable_functors=data.get("enable_functors", True),
            max_sources=data.get("max_sources", 50),
            fallback_to_web_search=data.get("fallback_to_web_search", True),
            include_epistemic_notice=data.get("include_epistemic_notice", True),
            min_quality_score=data.get("min_quality_score", 60),
            api_keys=data.get("api_keys", {}),
            llm_temperature=data.get("llm_temperature", 0.8),
            auto_retry_failed_steps=data.get("auto_retry_failed_steps", True),
            enable_quality_score=data.get("enable_quality_score", True),
            max_llm_tokens_per_section=data.get("max_llm_tokens_per_section", 800),
        )

    @classmethod
    def from_json(cls, json_str: str) -> PipelineConfig:
        """Load from JSON string."""
        return cls.from_dict(json.loads(json_str))


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
