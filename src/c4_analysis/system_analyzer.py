# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from src.c4.cognitive_router import CognitiveRouter
from src.c4_analysis.extended_engines import CognitiveStateClassifier
from src.c4_analysis.system_synthesizer import SYSTEMIC_INDICATORS


logger = logging.getLogger(__name__)

# Hidden systemic dimension triggers — words that IMPLY systemicity
IMPLICIT_SYSTEMIC = {
    "why": 0.4, "how": 0.3, "solve": 0.5, "optimize": 0.6,
    "balance": 0.7, "trade-off": 0.7, "system": 0.8, "network": 0.8,
    "ecosystem": 0.9, "cycle": 0.6, "loop": 0.7, "chain": 0.5,
    "interact": 0.6, "couple": 0.6, "depend": 0.7, "affect": 0.5,
    "regulate": 0.6, "feedback": 0.9, "emerge": 0.7, "holistic": 0.8,
    "complex": 0.5, "multi": 0.4, "inter": 0.3, "cross": 0.3,
}
EXPLICIT_SYSTEMIC = SYSTEMIC_INDICATORS  # "causes", "leads to", etc. → 0.8+


class SystemAnalyzer:
    """Universal query analyzer. Every query is systemic at some depth."""

    def __init__(self) -> None:
        self.router = CognitiveRouter()
        self.classifier = CognitiveStateClassifier()

    def analyze(self, query: str) -> dict[str, Any]:
        """Full analysis pipeline — parse, classify, decompose, rank, route.

        Returns:
            systemicity: 0.0 (pseudo-independent) to 1.0 (deeply systemic)
            entities: extracted key concepts
            dependency_graph: {entity: [depends_on_entities]}
            sub_problems: decomposed and ranked sub-problems with C4 routes
            critical_path: which sub-problems to solve FIRST
            explanation: human-readable analysis
        """
        q = query.lower()

        # 1. Extract entities
        entities = self._extract_entities(q)

        # 2. Detect dependencies
        dependencies = self._build_dependency_graph(q, entities)

        # 3. Classify systemicity
        systemicity = self._classify_systemicity(q, entities, dependencies)

        # 4. Decompose into sub-problems (with dependencies)
        sub_problems = self._decompose(q, entities, dependencies)

        # 5. Rank sub-problems (graph centrality — which to solve first)
        ranked = self._rank_by_centrality(sub_problems, dependencies)

        # 6. Route each sub-problem through C4
        routes = self._route_all(ranked)

        # 7. Find critical path (chain of most-dependent sub-problems)
        critical = self._critical_path(routes, dependencies)

        return {
            "query": query,
            "systemicity": round(systemicity, 2),
            "systemicity_label": self._label(systemicity),
            "entities": entities,
            "dependency_graph": {k: list(v) for k, v in dependencies.items()},
            "sub_problems": routes,
            "critical_path": critical,
            "c4_state": self.classifier.classify(query)["c4_state"],
            "analysis_depth": "deep" if systemicity > 0.6 else "moderate" if systemicity > 0.3 else "shallow",
            "explanation": self._generate_explanation(systemicity, routes, critical),
        }

    def _extract_entities(self, query: str) -> list[str]:
        """Extract key conceptual entities from query."""
        # Remove stopwords
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                     "to", "of", "in", "for", "on", "with", "at", "by", "from",
                     "and", "or", "but", "not", "this", "that", "it", "i", "we",
                     "can", "could", "would", "should", "will", "may", "might"}
        words = []
        for w in query.split():
            stripped = w.strip(".,;:!?()[]{}\"'")
            if stripped and stripped.lower() not in stopwords:
                words.append(stripped)

        # Merge adjacent words into phrases
        entities = []
        i = 0
        while i < len(words):
            # Try 2-word phrases
            if i + 1 < len(words):
                phrase = f"{words[i]} {words[i+1]}"
                if len(phrase) > 5 and phrase in query:
                    entities.append(phrase)
                    i += 2
                    continue
            entities.append(words[i])
            i += 1

        return entities[:15]

    def _build_dependency_graph(
        self, query: str, entities: list[str]
    ) -> dict[str, set[str]]:
        """Build dependency graph between entities.

        Dependency detected when:
        - Explicit causal: "X causes Y", "X leads to Y"
        - Implicit semantic: "X in Y", "X of Y", "X affects Y"
        - Order-based: first-mentioned entity often constrains later ones
        """
        deps: dict[str, set[str]] = defaultdict(set)
        n = len(entities)
        if n < 2:
            return deps

        # Explicit causal dependencies
        for i in range(n - 1):
            for j in range(i + 1, min(i + 3, n)):
                # Check if there's a causal connector between them
                if entities[i] in query and entities[j] in query:
                    e1_pos = query.find(entities[i])
                    e2_pos = query.find(entities[j])
                    if e1_pos < e2_pos:
                        between = query[e1_pos + len(entities[i]):e2_pos]
                        if any(ind in between for ind in EXPLICIT_SYSTEMIC):
                            deps[entities[j]].add(entities[i])

        # Implicit: order-based (earlier entities often constrain later)
        for i in range(n - 1):
            if not any(entities[i] in deps[k] for k in deps):
                deps[entities[i + 1]].add(entities[i])

        # LLM deep analysis for hidden dependencies
        deps = self._llm_deepen_deps(query, deps)

        return deps

    def _llm_deepen_deps(self, query: str, deps: dict[str, set[str]]) -> dict[str, set[str]]:
        """Use LLM to find hidden systemic dependencies not in surface text."""
        try:
            from src.plugins._llm_base import _llm_reason
            entities_str = ", ".join(list(deps.keys())[:8])
            sys = "You are a systems analyst. Find hidden dependencies between concepts. Output JSON: [[concept_a, depends_on_concept_b, why], ...]. Be brief."
            prompt = f"Query: {query[:400]}\nConcepts: {entities_str}\nWhat hidden systemic dependencies exist between these concepts? Output JSON array."
            result = _llm_reason(prompt, system=sys, max_tokens=200, temperature=0.2)
            if result:
                import json
                import re
                match = re.search(r"\[.*\]", result, re.DOTALL)
                if match:
                    for item in json.loads(match.group()):
                        if len(item) >= 2:
                            deps[str(item[0]).lower()].add(str(item[1]).lower())
                            deps[str(item[1]).lower()]  # ensure entity exists
        except Exception as e:
            logger.warning("LLM dependency deepening failed: %s", e)
        return deps

    def _classify_systemicity(
        self, query: str, entities: list[str], deps: dict[str, set[str]]
    ) -> float:
        """Classify how systemic the query is (0.0 to 1.0)."""
        score = 0.0

        # Explicit systemic indicators (strong)
        for ind in EXPLICIT_SYSTEMIC:
            if ind in query:
                score += 0.08
        score = min(score, 0.5)

        # Implicit systemic indicators (weaker)
        for word, weight in IMPLICIT_SYSTEMIC.items():
            if word in query.split():
                score += weight * 0.1
        score = min(score, 0.4 + score * 0.5)

        # Dependency graph complexity
        n_entities = len(entities)
        n_deps = sum(len(v) for v in deps.values())
        if n_entities > 0:
            edge_ratio = n_deps / max(1, n_entities)
            score += min(0.3, edge_ratio * 0.15)

        # Number of entities (more entities = more systemic)
        score += min(0.2, n_entities * 0.02)

        return min(1.0, score)

    def _decompose(
        self, query: str, entities: list[str], deps: dict[str, set[str]]
    ) -> list[dict[str, Any]]:
        """Decompose into sub-problems with explicit dependencies."""
        sub_problems = []
        n = len(entities)

        for i, entity in enumerate(entities):
            depends_on = list(deps.get(entity, set()))
            sub_problems.append({
                "entity": entity,
                "depends_on": depends_on,
                "dependency_count": len(depends_on),
                "position": i,
                "is_root": len(depends_on) == 0,
                "is_leaf": entity not in [d for deps_set in deps.values() for d in deps_set],
            })

        return sub_problems

    def _rank_by_centrality(
        self, sub_problems: list[dict[str, Any]], deps: dict[str, set[str]]
    ) -> list[dict[str, Any]]:
        """Rank sub-problems by graph centrality (most dependent first)."""
        # Count how many other entities depend on each entity
        depended_by: dict[str, int] = defaultdict(int)
        for _entity, depends in deps.items():
            for dep in depends:
                depended_by[dep] += 1

        for sp in sub_problems:
            sp["depended_by"] = depended_by.get(sp["entity"], 0)
            sp["centrality"] = sp["dependency_count"] + sp["depended_by"]

        # Sort: most central first (so foundational problems are solved before dependent ones)
        return sorted(sub_problems, key=lambda x: -x["centrality"])

    def _route_all(self, sub_problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Route each sub-problem through C4 + scientist matching."""
        for sp in sub_problems:
            route = self.router.route(sp["entity"])
            sp["scientist"] = route["scientist_pattern"]
            sp["c4_path"] = route["states"]
            sp["c4_steps"] = route["path_length"]
            sp["engines"] = route["engines_engaged"]
        return sub_problems

    def _critical_path(
        self, routes: list[dict[str, Any]], deps: dict[str, set[str]]
    ) -> list[str]:
        """Find critical path: chain of most-dependent sub-problems."""
        if not routes:
            return []

        # Start from most central (solved first)
        critical = [routes[0]["entity"]]

        # Follow dependency chain
        visited = {routes[0]["entity"]}
        for r in routes[1:]:
            entity = r["entity"]
            if entity not in visited:
                # Check if any dependency is already in critical path
                depends_on = r.get("depends_on", [])
                if any(d in critical for d in depends_on) or not depends_on:
                    critical.append(entity)
                    visited.add(entity)

        return critical

    def _label(self, systemicity: float) -> str:
        if systemicity >= 0.8:
            return "deeply systemic"
        if systemicity >= 0.6:
            return "strongly systemic"
        if systemicity >= 0.4:
            return "moderately systemic"
        if systemicity >= 0.2:
            return "weakly systemic"
        return "pseudo-atomic"

    def _generate_explanation(
        self, sys: float, routes: list[dict[str, Any]], critical: list[str]
    ) -> str:
        entities = len(routes)
        if entities <= 1:
            return f"Atomic query (systemicity={sys:.1f}). Single cognitive path."

        scientists = ", ".join(set(r["scientist"] for r in routes[:4]))
        return (
            f"Systemicity={sys:.1f}: {entities} interconnected entities detected. "
            f"Decomposed into {entities} sub-problems. "
            f"Critical path: {' → '.join(critical[:5])}. "
            f"Engaged scientists: {scientists}."
        )


__all__ = ["SystemAnalyzer"]
