"""
Concrete pipeline configuration dataclasses — foundational types layer.

Moved here from src/pipeline/config.py so that lower-level packages (e.g. core)
can depend on the config WITHOUT depending on the high-level `pipeline` package.
No imports from src.* — this module is a dependency-graph leaf.

Note: src/contracts/pipeline_types.py holds the structural `PipelineConfig`
Protocol; this module holds the concrete dataclass that satisfies it.
src/pipeline/config.py re-exports these for backward compatibility.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
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
