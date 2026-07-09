"""Tests for topic-aware pattern routing."""

from __future__ import annotations

from src.patterns.topic_router import select_pattern_for_topic


def test_ocean_plastic_prefers_bio_not_circulation() -> None:
    available = [
        "ocean_circulation",
        "gene_regulatory",
        "biogeochemistry",
        "reaction_diffusion",
        "monte_carlo",
    ]
    pid, params = select_pattern_for_topic(
        "ocean plastic remediation via enzyme-engineered microbes",
        available,
        lambda p: {"name": p.replace("_", " "), "description": "", "keywords": []},
    )
    assert pid != "ocean_circulation"
    assert pid in {"gene_regulatory", "biogeochemistry", "reaction_diffusion"}
    assert params.get("fast_mode") is True


def test_ocean_circulation_when_physics_topic() -> None:
    available = ["ocean_circulation", "gene_regulatory", "monte_carlo"]
    pid, _ = select_pattern_for_topic(
        "thermohaline ocean circulation gyre dynamics",
        available,
        lambda p: {"name": p.replace("_", " "), "description": "", "keywords": []},
    )
    assert pid == "ocean_circulation"
