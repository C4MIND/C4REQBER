"""Topic-aware pattern selection for Phase E simulation."""

from __future__ import annotations

from typing import Any


# Heavy GCM / ocean models — only when topic explicitly asks for physics/climate.
_HEAVY_PHYSICS_PATTERNS: frozenset[str] = frozenset(
    {
        "ocean_circulation",
        "climate_gcm",
        "cloud_microphysics",
        "mantle_convection",
        "sea_ice",
        "land_surface",
    }
)

_BIO_REMEDIATION_KEYWORDS: frozenset[str] = frozenset(
    {
        "plastic",
        "microbe",
        "microbial",
        "enzyme",
        "biodegrad",
        "bacteria",
        "consortium",
        "remediation",
        "bioremedi",
        "pet",
        "polymer",
        "ferment",
        "metabolic",
        "synthetic biology",
        "genome",
        "protein",
        "epigenetic",
    }
)

_OCEAN_PHYSICS_KEYWORDS: frozenset[str] = frozenset(
    {
        "circulation",
        "gyre",
        "thermohaline",
        "gcm",
        "coriolis",
        "salinity",
        "current",
        "eddy",
        "upwelling",
        "meridional",
    }
)

_DOMAIN_PATTERNS: dict[str, list[str]] = {
    "plastic": ["reaction_diffusion", "biogeochemistry", "gene_regulatory", "population_genetics"],
    "microbe": ["gene_regulatory", "population_genetics", "lotka_volterra", "biogeochemistry"],
    "enzyme": ["gene_regulatory", "reaction_diffusion", "pharmacokinetics"],
    "biodegrad": ["reaction_diffusion", "biogeochemistry", "gene_regulatory"],
    "ocean": ["biogeochemistry", "reaction_diffusion"],
    "climate": ["climate_gcm", "cloud_microphysics", "land_surface"],
    "quantum": ["quantum", "ising", "qft_lattice", "open_quantum"],
    "photosynthesis": ["reaction_diffusion", "gene_regulatory"],
    "concrete": ["continuum_mechanics", "composite_mechanics", "fem"],
    "fusion": ["plasma_pic", "qft_lattice"],
    "neuro": ["neural_mass", "neural_network", "synaptic_plasticity"],
    "epigenetic": ["gene_regulatory", "population_genetics"],
    "robot": ["inverse_kinematics", "optimization"],
    "traffic": ["traffic_flow", "agent_based"],
    "economic": ["dsge", "agent_based", "game_theory"],
}


def select_pattern_for_topic(
    topic: str,
    available: list[str],
    metadata_getter: Any,
) -> tuple[str, dict[str, Any]]:
    """Return (pattern_id, params) best matching *topic* from *available*."""
    if not available:
        return "monte_carlo", {"fast_mode": True}

    topic_lower = topic.lower()
    topic_words = set(topic_lower.split())

    has_bio = any(kw in topic_lower for kw in _BIO_REMEDIATION_KEYWORDS)
    wants_ocean_physics = any(kw in topic_lower for kw in _OCEAN_PHYSICS_KEYWORDS)

    scores: list[tuple[str, int]] = []

    for pid in available:
        meta = metadata_getter(pid) or {}
        name = (meta.get("name") or "").lower()
        desc = (meta.get("description") or "").lower()
        keywords = [k.lower() for k in meta.get("keywords", [])]

        score = 0
        for word in topic_words:
            if len(word) <= 3:
                continue
            if word in name:
                score += 3
            if word in desc:
                score += 2
            if any(word in kw for kw in keywords):
                score += 2

        for domain_key, pattern_ids in _DOMAIN_PATTERNS.items():
            if domain_key in topic_lower and pid in pattern_ids:
                score += 10

        # Bio remediation topics: prefer biochemistry, not ocean GCM.
        if has_bio and pid in _HEAVY_PHYSICS_PATTERNS:
            if wants_ocean_physics:
                score += 2
            else:
                score -= 25

        # Generic "ocean" word alone must not pick ocean_circulation for plastic topics.
        if pid == "ocean_circulation" and has_bio and not wants_ocean_physics:
            score -= 30

        if score > 0:
            scores.append((pid, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    if scores:
        best_pid, best_score = scores[0]
        return best_pid, {"fast_mode": True}

    return "monte_carlo", {"fast_mode": True}
