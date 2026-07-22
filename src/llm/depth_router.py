# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
# mypy: ignore-errors
from __future__ import annotations

import logging
from typing import ClassVar


logger = logging.getLogger(__name__)


class DepthBasedRouter:
    """DepthBasedRouter."""

    DEPTH_MODEL_MAP: ClassVar[dict[int, dict[str, str]]] = {
        0: {  # Fast-complete + local MLX
            "local": "mlx-community/Qwen2.5-Coder-7B-4bit",  # $0 — Apple GPU
            "cheap": "mlx-community/Qwen2.5-Coder-7B-4bit",
            "balanced": "openai/gpt-4o-mini",
            "premium": "google/gemini-2.0-flash-001",  # fast + cheap premium
        },
        1: {
            "cheap": "openai/gpt-4o-mini",  # $0.15/MTok — discovery/search
            "balanced": "qwen/qwen-2.5-7b-instruct",  # free? / very cheap
            "premium": "deepseek/deepseek-chat",  # $0.14/MTok — (DeepSeek V3 cheap tier)
        },
        2: {
            "cheap": "qwen/qwen-2.5-7b-instruct",
            "balanced": "deepseek/deepseek-chat",  # cheap + strong reasoning
            "premium": "anthropic/claude-sonnet-4.6",  # high-quality reasoning (Sonnet 4.6)
        },
        3: {
            "cheap": "deepseek/deepseek-chat",
            "balanced": "deepseek/deepseek-chat",  # powerful verification (cheap tier)
            "premium": "anthropic/claude-sonnet-4.6",  # final quality (Sonnet 4.6)
        },
    }

    COST_PER_1K: ClassVar[dict[str, float]] = {
        "openai/gpt-4o-mini": 0.00015,
        "qwen/qwen-2.5-7b-instruct": 0.00007,
        "google/gemini-2.0-flash-001": 0.00015,
        "deepseek/deepseek-chat": 0.00014,
        "anthropic/claude-sonnet-4.6": 0.003,
    }

    STAGE_TO_DEPTH: ClassVar[dict[int, int]] = {
        1: 1,
        2: 1,
        3: 1,
        4: 1,
        5: 2,
        6: 2,
        7: 2,
        8: 2,
        9: 3,
        10: 3,
        11: 3,
        12: 3,
    }

    # Pipeline phase A–G → depth tier (fallback when models.json has no entry)
    PHASE_TO_DEPTH: ClassVar[dict[str, int]] = {
        "A": 1,
        "B": 1,
        "C": 1,
        "D": 2,
        "E": 0,
        "F": 3,
        "G": 3,
    }

    @classmethod
    def route_for_pipeline_phase(cls, phase: str, budget: str = "balanced") -> str:
        """Prefer ModelAssignment (models.json); fall back to depth map."""
        phase_key = (phase or "").strip().upper()
        if phase_key == "E":
            return ""
        try:
            from src.llm.model_assignment import get_model_for_phase

            assigned = get_model_for_phase(phase_key)
            if assigned:
                return assigned
        except Exception as exc:
            logger.debug("ModelAssignment lookup failed for phase %s: %s", phase_key, exc)
        depth = cls.PHASE_TO_DEPTH.get(phase_key, 2)
        return cls.route(depth, budget)

    @classmethod
    def route(cls, depth: int, budget: str = "balanced") -> str:
        """Route."""
        if budget not in ("cheap", "balanced", "premium"):
            budget = "balanced"
        return cls.DEPTH_MODEL_MAP.get(depth, cls.DEPTH_MODEL_MAP[2]).get(
            budget, cls.DEPTH_MODEL_MAP[2]["balanced"]
        )

    @classmethod
    def route_for_stage(cls, stage: int, budget: str = "balanced") -> str:
        """Route numeric pipeline stage — honors models.json when mappable to A–G."""
        stage_to_phase = {
            1: "A",
            2: "A",
            3: "B",
            4: "B",
            5: "C",
            6: "C",
            7: "D",
            8: "D",
            9: "F",
            10: "F",
            11: "G",
            12: "G",
        }
        phase = stage_to_phase.get(stage, "")
        if phase:
            assigned = cls.route_for_pipeline_phase(phase, budget)
            if assigned:
                return assigned
        depth = cls.STAGE_TO_DEPTH.get(stage, 2)
        return cls.route(depth, budget)

    @classmethod
    def estimate_cost(
        cls, pipeline_stages: list[int], budget: str = "balanced", tokens_per_stage: int = 4000
    ) -> float:
        """Estimate cost."""
        total = 0.0
        for stage in pipeline_stages:
            model = cls.route_for_stage(stage, budget)
            cost_per_1k = cls.COST_PER_1K.get(model, 0.001)
            total += cost_per_1k * (tokens_per_stage / 1000)
        return round(total, 4)

    @classmethod
    def cost_badge(cls, cost: float) -> str:
        """Cost badge."""
        if cost < 0.10:
            return f"[green]${cost:.4f}[/]"
        elif cost < 0.50:
            return f"[yellow]${cost:.4f}[/]"
        return f"[red]${cost:.4f}[/]"
