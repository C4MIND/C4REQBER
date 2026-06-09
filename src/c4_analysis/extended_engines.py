# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
import math
import time
from collections import defaultdict
from typing import Any


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Cognitive State Classifier — HF model + keyword fallback
# ═══════════════════════════════════════════════════════════════════════════════

class CognitiveStateClassifier:
    """Classify problem text into C4 Z₃³ state (Time × Scale × Agency).

    Tries HF C4 classifier model. Falls back to keyword-based classification.
    """

    def __init__(self) -> None:
        self._hf_loaded = False
        self._hf_model: Any = None
        self._hf_tokenizer: Any = None

    def classify(self, problem_text: str) -> dict[str, Any]:
        """Classify problem into C4 state coordinates."""
        # Try HF model
        hf_result = self._try_hf_classify(problem_text)
        if hf_result:
            return hf_result
        return self._keyword_classify(problem_text)

    def _try_hf_classify(self, problem_text: str) -> dict[str, Any] | None:
        """Load and run a HuggingFace C4 classifier (3-output regression model).

        Expects a model that outputs exactly 3 logits/coordinates for T, S, A axes.
        Falls back to keyword classification if the model is unavailable or returns
        unexpected dimensions.
        """
        if not self._hf_loaded:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                self._hf_tokenizer = AutoTokenizer.from_pretrained("HangJang/C4-Cognitive-Classifier-v1")
                self._hf_model = AutoModelForSequenceClassification.from_pretrained("HangJang/C4-Cognitive-Classifier-v1")
                self._hf_loaded = True
            except Exception:
                self._hf_loaded = True
                return None
        if self._hf_model is None or self._hf_tokenizer is None:
            return None
        try:
            import torch
            inputs = self._hf_tokenizer(problem_text[:512], return_tensors="pt", truncation=True)
            with torch.no_grad():
                outputs = self._hf_model(**inputs)
            logits = outputs.logits[0]
            if logits.shape[0] == 3:
                t_val = int(round(float(logits[0].item()))) % 3
                s_val = int(round(float(logits[1].item()))) % 3
                a_val = int(round(float(logits[2].item()))) % 3
                return self._build_result(t_val, s_val, a_val, problem_text, "hf_model")
            else:
                logger.warning(
                    "HF model returned %d-dim output; expected 3-dim C4 classifier. "
                    "Falling back to keyword classification.",
                    logits.shape[0],
                )
                return None
        except Exception:
            return None

    def _keyword_classify(self, problem_text: str) -> dict[str, Any]:
        t = problem_text.lower()

        time_val = 1  # PRESENT
        if any(kw in t for kw in ("future", "predict", "will", "forecast", "next", "project")):
            time_val = 2
        elif any(kw in t for kw in ("past", "historical", "previous", "was", "had", "occurred")):
            time_val = 0

        scale_val = 0  # CONCRETE
        if any(kw in t for kw in ("meta", "theory of", "philosophy of", "methodology", "epistemology")):
            scale_val = 2
        elif any(kw in t for kw in ("abstract", "principle", "general", "universal", "mathematical", "formalism")):
            scale_val = 1

        agency_val = 0  # SELF
        if any(kw in t for kw in ("system", "ecosystem", "network", "collective", "emergent")):
            agency_val = 2
        elif any(kw in t for kw in ("other", "competitor", "external", "social", "collaborative", "multi-agent")):
            agency_val = 1

        return self._build_result(time_val, scale_val, agency_val, problem_text, "keyword")

    def _build_result(self, t: int, s: int, a: int, text: str, source: str) -> dict[str, Any]:
        time_names = ["PAST", "PRESENT", "FUTURE"]
        scale_names = ["CONCRETE", "ABSTRACT", "META"]
        agency_names = ["SELF", "OTHER", "SYSTEM"]
        t, s, a = max(0, min(2, t)), max(0, min(2, s)), max(0, min(2, a))
        return {
            "c4_state": f"{scale_names[s]}/{time_names[t]}/{agency_names[a]}",
            "time": time_names[t], "scale": scale_names[s], "agency": agency_names[a],
            "time_val": t, "scale_val": s, "agency_val": a,
            "source": source, "problem": text[:200],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Creative Divergence Engine — WILD hypotheses
# ═══════════════════════════════════════════════════════════════════════════════

class CreativeDivergenceEngine:
    """Generate deliberately wild, paradigm-shifting hypotheses.

    NOT refinement — DIVERGENCE. Uses lateral thinking operators
    to break out of local minima in hypothesis space.
    """

    DIVERGENCE_OPERATORS = [
        ("invert", "What if the OPPOSITE is true?"),
        ("scale_extreme", "What if we scale this by 10^20 or 10^-20?"),
        ("cross_domain", "What if this principle applies in a completely different domain?"),
        ("remove_axiom", "What if we remove a fundamental assumption?"),
        ("reverse_causality", "What if the effect CAUSES the cause?"),
        ("unify", "What if two seemingly unrelated phenomena are the SAME thing?"),
        ("dimension_shift", "What if we add or remove a dimension?"),
        ("discrete_continuous", "What if we switch between discrete and continuous?"),
    ]

    def diverge(self, hypothesis: str, count: int = 4) -> list[dict[str, str]]:
        """Generate divergent hypotheses from an existing one."""
        results = []
        for op_name, prompt in self.DIVERGENCE_OPERATORS[:count]:
            divergence = self._apply_operator(hypothesis, op_name, prompt)
            results.append({
                "operator": op_name,
                "prompt": prompt,
                "divergent_hypothesis": divergence,
            })
        return results

    def _apply_operator(self, hypothesis: str, op: str, prompt: str) -> str:
        try:
            from src.plugins._llm_base import _llm_reason
            sys = f"You are a creative divergence engine. Apply the '{op}' operator to generate wild, paradigm-shifting alternatives. Be bold."
            full_prompt = f"{prompt}\n\nHYPOTHESIS: {hypothesis[:500]}\n\nGenerate ONE bold divergent alternative (1-2 sentences)."
            result = _llm_reason(full_prompt, system=sys, max_tokens=200, temperature=0.9)
            if result:
                return result.strip()
        except (ImportError, ModuleNotFoundError, OSError) as e:
            logger.warning("LLM divergence engine unavailable: %s", e)
        return self._heuristic_diverge(hypothesis, op)

    def _heuristic_diverge(self, hypothesis: str, op: str) -> str:
        heuristics = {
            "invert": f"What if the opposite holds? Instead of '{hypothesis[:80]}...', the reverse: ",
            "scale_extreme": f"At cosmic or quantum scale: '{hypothesis[:80]}...' becomes: ",
            "cross_domain": f"Applied to biology instead: '{hypothesis[:80]}...' suggests: ",
            "remove_axiom": f"Without assuming causality: '{hypothesis[:80]}...' could be: ",
        }
        return heuristics.get(op, f"[{op}] {hypothesis[:100]}...")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Uncertainty Quantifier
# ═══════════════════════════════════════════════════════════════════════════════

class UncertaintyQuantifier:
    """Formal epistemic uncertainty for each pipeline step.

    Bayesian posterior: P(hypothesis | evidence) using conjugate priors.
    """

    def quantify(self, evidence: int = 0, total: int = 0, prior: float = 0.5) -> dict[str, Any]:
        """Bayesian update: Beta(α,β) posterior.

        evidence = supporting observations, total = total observations.
        """
        alpha_prior = prior * 2
        beta_prior = (1 - prior) * 2

        if total > 0:
            alpha = alpha_prior + evidence
            beta = beta_prior + (total - evidence)
        else:
            alpha, beta = alpha_prior, beta_prior

        mean = alpha / (alpha + beta)
        variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
        ci_lower = mean - 1.96 * math.sqrt(variance)
        ci_upper = mean + 1.96 * math.sqrt(variance)

        return {
            "posterior_mean": round(mean, 4),
            "posterior_variance": round(variance, 6),
            "ci_95": [round(max(0, ci_lower), 4), round(min(1, ci_upper), 4)],
            "effective_sample_size": alpha + beta,
            "evidence_strength": "strong" if alpha + beta > 10 else "moderate" if alpha + beta > 4 else "weak",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Temporal Projector
# ═══════════════════════════════════════════════════════════════════════════════

class TemporalProjector:
    """Project C4 state forward/backward in time axis.

    "If we're at state X now, what states are reachable in K steps?"
    Uses Theorem 11 bound: at most 6 steps between any states.
    """

    def project(self, current_state: str, steps: int = 2, direction: str = "forward") -> list[str]:
        """Project from current C4 state K steps forward/backward."""
        parts = current_state.split("/")
        if len(parts) != 3:
            return [current_state]

        scale_names = ["CONCRETE", "ABSTRACT", "META"]
        time_names = ["PAST", "PRESENT", "FUTURE"]
        agency_names = ["SELF", "OTHER", "SYSTEM"]

        scale_idx = scale_names.index(parts[0]) if parts[0] in scale_names else 0
        time_idx = time_names.index(parts[1]) if parts[1] in time_names else 1
        agency_idx = agency_names.index(parts[2]) if parts[2] in agency_names else 0

        delta = steps if direction == "forward" else -steps
        projected_time = (time_idx + delta) % 3

        reachable = []
        for s in range(3):
            for a in range(3):
                state = f"{scale_names[s]}/{time_names[projected_time]}/{agency_names[a]}"
                distance = abs(s - scale_idx) + abs(a - agency_idx)
                if distance <= steps:
                    reachable.append(f"{state} [{distance}h]")
        return reachable

    def predict_next_state(self, current_state: str, scientist_path: list[dict[str, Any]]) -> str | None:
        """Given current state and path, predict next state."""
        parts = current_state.split("/")
        if len(parts) != 3:
            return None
        for s in scientist_path:
            if s.get("c4_state", "") == current_state:
                idx = scientist_path.index(s) + 1
                if idx < len(scientist_path):
                    return scientist_path[idx].get("c4_state", "")
                return "TERMINAL"
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Meta-Learning Loop
# ═══════════════════════════════════════════════════════════════════════════════

class MetaLearningLoop:
    """Learn from discovery history to improve routing.

    Tracks: which paths succeeded, which engines produced value,
    path length vs quality correlation.
    """

    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []
        self.engine_effectiveness: dict[str, list[float]] = defaultdict(list)

    def record(self, path_key: str, engines: list[str], quality: float, steps: int) -> None:
        """Record."""
        self.history.append({
            "path": path_key, "engines": engines, "quality": quality, "steps": steps,
            "timestamp": time.time(),
        })
        for eng in engines:
            self.engine_effectiveness[eng].append(quality)

    def recommend(self) -> dict[str, Any]:
        """Recommend best path and engines based on history."""
        if not self.history:
            return {"recommendation": "insufficient_history", "best_path": "darwin"}

        # Best path by average quality
        path_scores: dict[str, list[float]] = defaultdict(list)
        for entry in self.history:
            path_scores[entry["path"]].append(entry["quality"])

        best_path = max(path_scores, key=lambda p: sum(path_scores[p]) / len(path_scores[p]))

        # Best engines by effectiveness
        engine_scores = {
            eng: sum(scores) / len(scores)
            for eng, scores in self.engine_effectiveness.items()
            if scores
        }
        best_engines = sorted(engine_scores, key=lambda e: engine_scores[e], reverse=True)[:5]

        return {
            "recommendation": f"Use {best_path} path with {best_engines[:3]} engines",
            "best_path": best_path,
            "best_path_avg_quality": round(sum(path_scores[best_path]) / len(path_scores[best_path]), 2),
            "best_engines": best_engines,
            "total_discoveries": len(self.history),
            "learning_ready": len(self.history) >= 3,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Explainability Tracer
# ═══════════════════════════════════════════════════════════════════════════════

class ExplainabilityTracer:
    """Trace and explain WHY the CognitiveRouter chose a specific path.

    Generates human-readable explanations of the cognitive decision process.
    """

    def trace(self, router_result: dict[str, Any]) -> str:
        """Generate explanation of router decision."""
        fp = router_result.get("fingerprint", {})
        path = router_result.get("states", [])

        parts = []
        parts.append(f"1/ PROBLEM FINGERPRINT: C4 state {fp.get('c4_state', 'unknown')}")
        parts.append(f"   Time={fp.get('time')}, Scale={fp.get('scale')}, Agency={fp.get('agency')}")
        parts.append(f"2/ MATCHED PATTERN: {router_result.get('scientist_pattern', 'unknown')}")
        parts.append(f"   Historical example: {router_result.get('discovery_example', 'N/A')[:80]}")
        parts.append(f"3/ PATH ({len(path)} steps, Theorem 11 bound: ≤6):")

        for i, state in enumerate(path):
            step_num = f"A{i}" if i == 0 else f"B{i}" if i == 1 else f"C{i}" if i == 2 else f"D{i}" if i == 3 else f"E{i}" if i == 4 else f"F{i}"
            parts.append(f"   {step_num}/ {state['c4_state']} → {state['engine']}: {state['description'][:60]}")

        parts.append(f"4/ EXPLANATION: {router_result.get('explanation', 'N/A')}")
        return "\n".join(parts)

    def explain_alternatives(self, router_result: dict[str, Any], alternatives: list[dict[str, Any]]) -> str:
        """Explain why alternatives were NOT chosen."""
        chosen = router_result.get("scientist_pattern", "")
        lines = [f"Chosen: {chosen} ({router_result.get('path_length', 0)} steps)"]
        lines.append("Alternatives considered (not chosen):")
        for alt in alternatives[:5]:
            lines.append(f"  - {alt['scientist']} ({alt['era']}): {alt['discovery'][:60]}... ({alt['path_length']} steps)")
            lines.append(f"    Method: {alt['method'][:80]}...")
        return "\n".join(lines)

    def path_as_ascii(
        self, states: list[dict[str, Any]], scientist: str = "", era: str = ""
    ) -> str:
        """Render C4 path as ASCII art for terminal/TUI display."""
        if not states:
            return f"[{scientist} ({era})] No path"

        header = f"[{scientist} ({era})] {len(states)} steps"
        path_viz = header + "\n"
        for i, s in enumerate(states):
            connector = "└─" if i == len(states) - 1 else "├─"
            path_viz += f"  {connector} {s['c4_state']:<28s} → {s['engine']}\n"
        return path_viz


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Cognitive Load Balancer
# ═══════════════════════════════════════════════════════════════════════════════

class CognitiveLoadBalancer:
    """Distribute cognitive work across engines. Prevent overload.

    Tracks engine usage and suggests load distribution.
    """

    def __init__(self, max_engines_per_phase: int = 3) -> None:
        self.max_per_phase = max_engines_per_phase
        self.usage: defaultdict[str, int] = defaultdict(int)

    def should_engage(self, engine: str, phase: str, current_engines: int) -> bool:
        """Decide if engine should be engaged in this phase."""
        if current_engines >= self.max_per_phase:
            return False
        if self.usage[engine] > 10:
            return False  # Prevent overuse
        return True

    def record_engagement(self, engine: str) -> None:
        self.usage[engine] += 1

    def balance(self, phases: dict[str, list[str]]) -> dict[str, list[str]]:
        """Rebalance engines across phases to prevent overload."""
        balanced: dict[str, list[str]] = {}
        for phase, engines in phases.items():
            if len(engines) <= self.max_per_phase:
                balanced[phase] = engines
            else:
                balanced[phase] = engines[:self.max_per_phase]
        return balanced

    def stats(self) -> dict[str, Any]:
        return {
            "engine_usage": dict(self.usage),
            "total_engagements": sum(self.usage.values()),
            "most_used": max(self.usage, key=lambda k: self.usage[k]) if self.usage else "none",
        }


__all__ = [
    "CognitiveStateClassifier", "CreativeDivergenceEngine",
    "UncertaintyQuantifier", "TemporalProjector",
    "MetaLearningLoop", "ExplainabilityTracer", "CognitiveLoadBalancer",
]
