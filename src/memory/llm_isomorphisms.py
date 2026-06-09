from __future__ import annotations


"""C4-Native Structural Isomorphism Engine.

Discovers cross-domain isomorphisms by mapping problems into C4 cognitive state
space (Z₃³) and finding distant domains that share structural operator paths.

Pipeline:
  1. C4 fingerprint the problem → start state
  2. First-principles decomposition → constraints, invariants, abstractions
  3. C4 routing to "distant" states → target states with maximal Hamming distance
  4. LLM fills domain-specific mappings between start ↔ target structures
  5. Confidence scored by C4 path length + structural overlap
"""

import asyncio
import json
import logging
import os
from typing import Any

import httpx

from src.c4.engine import C4Space, C4State
from src.c4.routing import FRARouter, QualityPreset


logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "deepseek/deepseek-chat"
_FALLBACK_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o-mini",
]


# ── C4-Native Isomorphism Prompts ──────────────────────────────────────

_FIRST_PRINCIPLES_PROMPT = """You are a first-principles decomposer.

Task: Decompose the following problem into its fundamental structural elements.

Output JSON:
{{
  "abstraction_level": "concrete|abstract|meta",
  "physical_constraints": ["list of hard constraints"],
  "invariants": ["what must be preserved"],
  "variables": ["what can change"],
  "flows": ["energy/information/material flows"],
  "bottlenecks": ["limiting factors"],
  "c4_situation": "chaos|stagnation|conflict|entropy|overload|isolation|rigidity"
}}

Problem: {problem}
TRIZ context: {triz_str}
"""

_ISOMORPHISM_C4_PROMPT = """You are a cross-domain structural isomorphism engine.

C4 Cognitive Context:
- Source problem maps to C4 state: {source_state}
- Target isomorphism domain maps to C4 state: {target_state}
- C4 operator path between them: {operator_path}
- Hamming distance (structural distance): {hamming}

First-Principles Structure of Source Problem:
{first_principles_json}

Task: Find {n} deep structural isomorphisms between the source problem and the
target domain state. The isomorphism must respect the C4 operator path — each
mapping should explain how the target domain realizes a similar structural
transformation.

Rules:
1. Map specific structural elements (NOT vague metaphors).
2. The isomorphism must be actionable — explain HOW to transfer the insight.
3. Confidence reflects structural fidelity to the C4 path.
4. Include a "c4_operator_link" field naming which operator in the path enables
   this specific mapping.

Output strictly as JSON list:
[
  {{
    "source_domain": "original problem domain",
    "target_domain": "isomorphism domain",
    "source_structure": "specific structural element",
    "target_structure": "corresponding element in target",
    "mapping": "concise explanation of correspondence",
    "confidence": 0.0-1.0,
    "action_hint": "how to apply back to original problem",
    "c4_operator_link": "tau+|lambda-|kappa+ etc"
  }}
]
"""


# ── Public API ─────────────────────────────────────────────────────────

async def discover_isomorphisms(
    problem: str,
    triz: list[str],
    seed_count: int = 3,
    model: str | None = None,
    use_c4: bool = True,
    use_first_principles: bool = True,
) -> list[dict[str, Any]]:
    """Discover cross-domain isomorphisms via C4 + first principles + LLM.

    Args:
        problem: Problem statement.
        triz: TRIZ parameters/principles.
        seed_count: Number of isomorphisms to generate.
        model: Override OpenRouter model.
        use_c4: Whether to route through C4 state space (default True).
        use_first_principles: Whether to decompose via first principles (default True).

    Returns:
        Validated isomorphism list, sorted by confidence descending.
    """
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    if not or_key:
        logger.warning("discover_isomorphisms: OPENROUTER_API_KEY not set")
        return []

    triz_str = ", ".join(triz[:5]) if triz else "none"
    router = FRARouter()

    # ── Phase 1: C4 Fingerprint ──────────────────────────────────────
    source_state = router.classify_c4_state(problem)
    logger.info("C4 fingerprint: %s for problem: %.40s...", source_state, problem)

    # ── Phase 2: First Principles Decomposition ─────────────────────
    first_principles: dict[str, Any] = {}
    if use_first_principles:
        fp_raw = await _llm_call(
            or_key,
            _DEFAULT_MODEL,
            _FIRST_PRINCIPLES_PROMPT.format(problem=problem, triz_str=triz_str),
        )
        first_principles = _safe_json_parse(fp_raw) or {}
        logger.debug("First principles: %s", first_principles.get("abstraction_level", "unknown"))

    # ── Phase 3: C4 Routing to Distant States ───────────────────────
    target_states: list[C4State] = []
    if use_c4:
        space = C4Space()
        # Find states with maximal Hamming distance (most structurally distant)
        all_states = space.states
        distances = [
            (s, space.hamming_distance(source_state, s))
            for s in all_states
            if s != source_state
        ]
        distances.sort(key=lambda x: x[1], reverse=True)
        # Take top-N distant states as isomorphism targets
        target_states = [s for s, _ in distances[:seed_count]]
    else:
        # Fallback: no C4 routing, LLM picks domains freely
        target_states = [C4State(T=0, S=0, A=0)]  # Dummy

    # ── Phase 4: LLM Isomorphism per Target State ────────────────────
    all_isomorphisms: list[dict[str, Any]] = []
    for target_state in target_states:
        if use_c4:
            route = router.find_route(source_state, target_state, preset=QualityPreset.SYNTHESIS)
            op_path = " → ".join(route.operators) if route.operators else "direct"
            hamming = route.hamming_distance
        else:
            op_path = "N/A"
            hamming = 0

        prompt = _ISOMORPHISM_C4_PROMPT.format(
            source_state=str(source_state),
            target_state=str(target_state),
            operator_path=op_path,
            hamming=hamming,
            first_principles_json=json.dumps(first_principles, indent=2, ensure_ascii=False),
            n=max(1, seed_count // len(target_states)),
        )

        models_to_try = ([model] if model else []) + [_DEFAULT_MODEL] + _FALLBACK_MODELS
        for attempt_model in models_to_try:
            if not attempt_model:
                continue
            try:
                raw = await _llm_call(or_key, attempt_model, prompt)
                parsed = _parse_isomorphisms(raw, problem, seed_count)
                # Enrich with C4 metadata
                for iso in parsed:
                    iso["c4_source_state"] = str(source_state)
                    iso["c4_target_state"] = str(target_state)
                    iso["c4_hamming_distance"] = hamming
                    iso["c4_operator_path"] = op_path
                    iso["first_principles"] = first_principles.get("abstraction_level", "unknown")
                all_isomorphisms.extend(parsed)
                break
            except Exception as exc:
                logger.warning("Model %s failed for target %s: %s", attempt_model, target_state, exc)
                await asyncio.sleep(0.3)

    # ── Phase 5: Deduplicate & Rank ──────────────────────────────────
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for iso in all_isomorphisms:
        key = f"{iso.get('source_structure','')}→{iso.get('target_structure','')}"
        if key not in seen:
            seen.add(key)
            unique.append(iso)

    unique.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
    return unique[:seed_count]


# ── Internals ──────────────────────────────────────────────────────────

async def _llm_call(api_key: str, model: str, prompt: str) -> str:
    """Single OpenRouter call with JSON-object response format."""
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://c4reqber.io",
                "X-Title": "c4reqber-isomorphism-engine",
            },
            json={
                "model": model,
                "max_tokens": 1500,
                "temperature": 0.75,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a precise structural reasoning engine. Output valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _safe_json_parse(raw: str) -> dict[str, Any] | None:
    """Parse JSON, stripping markdown fences if needed."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _parse_isomorphisms(raw: str, problem: str, expected_count: int) -> list[dict[str, Any]]:
    """Parse LLM output into structured, validated isomorphisms."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON array
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                return []
        else:
            return []

    items: list[Any] = []
    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        for key in ("isomorphisms", "analogies", "results", "items"):
            if key in parsed and isinstance(parsed[key], list):
                items = parsed[key]
                break
        if not items:
            items = [parsed]

    validated: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        iso = {
            "source_domain": item.get("source_domain", "unknown"),
            "target_domain": item.get("target_domain", "unknown"),
            "source_structure": item.get("source_structure", ""),
            "target_structure": item.get("target_structure", ""),
            "mapping": item.get("mapping", ""),
            "confidence": _clamp(float(item.get("confidence", 0.5)), 0.0, 1.0),
            "action_hint": item.get("action_hint", ""),
            "c4_operator_link": item.get("c4_operator_link", ""),
            "problem": problem,
        }
        validated.append(iso)

    validated.sort(key=lambda x: x["confidence"], reverse=True)
    return validated[:expected_count]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
