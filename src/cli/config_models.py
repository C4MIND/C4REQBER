"""JSON exports for TUI models/council overlay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config.paths import MODELS_JSON
from src.llm.council import COUNCIL_MODELS
from src.llm.model_assignment import PHASE_DESCRIPTIONS, ModelAssignment
from src.llm.model_catalog import CATALOG, estimate_pipeline_cost, list_models


def _load_models_json() -> dict[str, Any]:
    if MODELS_JSON.is_file():
        try:
            return json.loads(MODELS_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def export_config_json() -> dict[str, Any]:
    """Phase assignments + council tiers for TUI."""
    assignment = ModelAssignment.load()
    raw = _load_models_json()
    council = raw.get("council") or COUNCIL_MODELS
    phases: list[dict[str, Any]] = []
    for phase in "ABCDEFG":
        model = assignment.get_model(phase)
        phases.append(
            {
                "phase": phase,
                "description": PHASE_DESCRIPTIONS.get(phase, ""),
                "model": model,
                "temperature": assignment.get_temperature(phase),
                "max_tokens": assignment.get_max_tokens(phase),
            }
        )
    cost = assignment.estimate_cost(1000)
    return {
        "cost_tier": assignment.cost_tier,
        "config_path": str(MODELS_JSON),
        "phases": phases,
        "council": council,
        "estimated_cost_usd": cost.get("total", 0.0),
    }


def export_models_json(tier: str = "") -> dict[str, Any]:
    """Model catalog for TUI browse."""
    models = list_models(tier) if tier else list_models()
    cost = estimate_pipeline_cost(1000)
    return {
        "tier_filter": tier or "all",
        "count": len(models),
        "models": models,
        "catalog_size": len(CATALOG),
        "estimated_pipeline_cost_usd": cost.get("total", 0.0),
    }


def print_json(payload: dict[str, Any]) -> None:
    import sys

    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
