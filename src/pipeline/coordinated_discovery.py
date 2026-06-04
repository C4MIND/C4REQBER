# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Coordinated Multi-Pipeline Discovery — parallel pipelines that share and cross-validate.

Unlike SmartScheduler (rate-limit-aware queuing) or naive turbofactory (independent parallel runs),
this orchestrator makes pipelines COORDINATE: share findings, cross-validate hypotheses,
merge complementary results, and produce a consensus mega-dissertation.

Architecture:
    Coordinator
    ├─ Pipeline A (Einstein path, TRIZ #1: segmentation)
    │   Gap: "No model for HGT-driven eukaryotic evolution"
    ├─ Pipeline B (Darwin path, TRIZ #2: extraction)
    │   Gap: "HGT operates at different timescales than vertical evolution"
    ├─ Pipeline C (Curie path, TRIZ #10: preliminary action)
    │   Gap: "No model for HGT-driven eukaryotic evolution"  ← SAME as A → cross-validate!
    │
    ├─ Coordinator merges similar gaps → confidence boost
    ├─ Cross-validates hypotheses between pipelines
    ├─ Aggregates into unified mega-dissertation
    └─ Produces consensus report with agreement scores

Key difference from turbofactory: pipelines SHARE intermediate state, not just run independently.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class PipelineAgent:
    """PipelineAgent."""
    id: str
    scientist_path: str  # "Einstein", "Darwin", etc.
    triz_principle: str  # "Segmentation", "Extraction", etc.
    mode: str  # "turbo" | "solve"
    status: str = "pending"  # pending|running|done|failed
    gaps: list[dict] = field(default_factory=list)
    hypotheses: list[dict] = field(default_factory=list)
    verification: dict = field(default_factory=dict)
    dissertation: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def elapsed(self) -> float:
        """Elapsed."""
        if self.finished_at:
            return self.finished_at - self.started_at
        if self.started_at:
            return time.time() - self.started_at
        return 0.0


@dataclass
class CrossValidation:
    """Result of comparing two pipelines' findings."""
    pipeline_a: str
    pipeline_b: str
    gap_overlap: float  # Jaccard similarity of gaps
    hypothesis_agreement: float  # consensus score
    shared_evidence: list[str]  # evidence both found
    contradictory: bool  # pipelines disagree on key points


@dataclass
class CoordinatedResult:
    """CoordinatedResult."""
    topic: str
    agents: list[PipelineAgent]
    cross_validations: list[CrossValidation]
    consensus_gaps: list[dict]
    consensus_hypotheses: list[dict]
    agreement_score: float  # 0-1 overall agreement between pipelines
    mega_dissertation: str = ""
    started_at: float = field(default_factory=time.time)

    @property
    def total_elapsed(self) -> float:
        return time.time() - self.started_at

    @property
    def success_rate(self) -> float:
        """Success rate."""
        done = [a for a in self.agents if a.status == "done"]
        return len(done) / len(self.agents) if self.agents else 0.0


class CoordinatedDiscovery:
    """
    Parallel pipelines that share findings.

    Strategy:
        1. Select N different scientist paths + TRIZ principles (diversity)
        2. Launch all N pipelines concurrently (coordinated, not independent)
        3. After each pipeline completes Stage 5 (Gap Mining):
           → Coordinator merges similar gaps (cosine similarity > 0.7)
           → Cross-validates: 2+ pipelines finding same gap = high confidence
        4. After Stage 6 (Hypothesis):
           → Cross-validate hypotheses between pipelines
           → Detect contradictions → flag for human review
        5. After all complete:
           → Aggregate into consensus mega-dissertation
           → Include cross-validation report with agreement scores
    """

    SCIENTIST_PATHS = [
        "einstein", "darwin", "curie", "turing", "feynman",
        "newton", "bohr", "planck", "lovelace", "hawking",
    ]
    TRIZ_PRINCIPLES = [
        "segmentation", "extraction", "local_quality", "asymmetry",
        "merging", "universality", "nested_doll", "anti_weight",
        "preliminary_action", "feedback", "mediator", "self_service",
    ]

    def __init__(self, num_agents: int = 5, mode: str = "turbo") -> None:
        self.num_agents = min(num_agents, len(self.SCIENTIST_PATHS))
        self.mode = mode
        self._agents: list[PipelineAgent] = []
        self._cross_validations: list[CrossValidation] = []

    def plan(self, topic: str) -> list[PipelineAgent]:
        """Generate diverse pipeline assignments."""
        import random
        rng = random.Random(hash(topic) % 2**32)

        paths = rng.sample(self.SCIENTIST_PATHS, self.num_agents)
        trizs = rng.sample(self.TRIZ_PRINCIPLES, self.num_agents)

        self._agents = [
            PipelineAgent(
                id=f"agent_{i:02d}",
                scientist_path=paths[i],
                triz_principle=trizs[i],
                mode=self.mode,
            )
            for i in range(self.num_agents)
        ]
        logger.info("Coordinated plan: %d agents, paths=%s", self.num_agents, paths)
        return self._agents

    def cross_validate_gaps(self) -> list[CrossValidation]:
        """Cross-validate gaps between all agent pairs."""
        validations = []
        for i in range(len(self._agents)):
            for j in range(i + 1, len(self._agents)):
                a, b = self._agents[i], self._agents[j]
                if not a.gaps or not b.gaps:
                    continue
                cv = self._compare_agents(a, b)
                validations.append(cv)
                self._cross_validations.append(cv)
        return validations

    def _compare_agents(self, a: PipelineAgent, b: PipelineAgent) -> CrossValidation:
        """Compare two agents' findings."""
        # Jaccard on gap areas
        a_areas = {g.get("area", "")[:80] for g in a.gaps}
        b_areas = {g.get("area", "")[:80] for g in b.gaps}
        union = len(a_areas | b_areas)
        overlap = len(a_areas & b_areas) / union if union > 0 else 0.0

        # Hypothesis agreement: do they propose similar things?
        a_titles = {h.get("title", "")[:60] for h in a.hypotheses}
        b_titles = {h.get("title", "")[:60] for h in b.hypotheses}
        hyp_union = len(a_titles | b_titles)
        hyp_overlap = len(a_titles & b_titles) / hyp_union if hyp_union > 0 else 0.0

        # Check for contradictions
        contradictory = False
        a_verdicts = {h.get("conclusion", "") for h in a.hypotheses}
        b_verdicts = {h.get("conclusion", "") for h in b.hypotheses}
        if a_verdicts and b_verdicts and not (a_verdicts & b_verdicts):
            contradictory = True

        shared = [g for g in a_areas & b_areas]

        return CrossValidation(
            pipeline_a=a.id,
            pipeline_b=b.id,
            gap_overlap=round(overlap, 3),
            hypothesis_agreement=round(hyp_overlap, 3),
            shared_evidence=shared,
            contradictory=contradictory,
        )

    def merge_consensus(self) -> CoordinatedResult:
        """Merge all agents' findings into consensus."""
        # Collect all gaps, deduplicate by area similarity
        all_gaps: list[dict[str, Any]] = []
        seen = set()
        for agent in self._agents:
            for g in agent.gaps:
                area_hash = hashlib.sha256(g.get("area", "")[:100].encode()).hexdigest()
                if area_hash not in seen:
                    seen.add(area_hash)
                    g["found_by"] = [agent.id]
                    g["confidence"] = 1.0  # First found
                else:
                    # Boost confidence for independently found gaps
                    for existing in all_gaps:
                        if hashlib.sha256(existing.get("area", "")[:100].encode()).hexdigest() == area_hash:
                            existing["found_by"].append(agent.id)
                            existing["confidence"] = min(1.0, existing["confidence"] + 0.3)
                            break
                all_gaps.append(g)

        # Sort by confidence (gaps found by multiple agents first)
        all_gaps.sort(key=lambda g: g.get("confidence", 0), reverse=True)

        # Overall agreement score
        if self._cross_validations:
            avg_gap_overlap = sum(cv.gap_overlap for cv in self._cross_validations) / len(self._cross_validations)
            avg_hyp_agreement = sum(cv.hypothesis_agreement for cv in self._cross_validations) / len(self._cross_validations)
            agreement_score = round(0.5 * avg_gap_overlap + 0.5 * avg_hyp_agreement, 3)
        else:
            agreement_score = 0.0

        all_hypotheses = []
        for agent in self._agents:
            for h in agent.hypotheses:
                h["agent_id"] = agent.id
                all_hypotheses.append(h)

        return CoordinatedResult(
            topic=f"coordinated_discovery_{int(time.time())}",
            agents=self._agents,
            cross_validations=self._cross_validations,
            consensus_gaps=all_gaps,
            consensus_hypotheses=all_hypotheses,
            agreement_score=agreement_score,
        )

    def cross_validation_report(self) -> str:
        """Cross validation report."""
        result = self.merge_consensus()
        lines = [
            "\n## Cross-Validation Report",
            "",
            f"**Agents:** {len(self._agents)} | **Agreement Score:** {result.agreement_score:.2f}",
            f"**Success Rate:** {result.success_rate:.0%} | **Elapsed:** {result.total_elapsed:.0f}s",
            "",
            "### Agent Assignments",
        ]
        for agent in self._agents:
            lines.append(f"- [{agent.id}] {agent.scientist_path.title()} path + TRIZ: {agent.triz_principle} → {agent.status} ({agent.elapsed:.0f}s)")

        lines += ["", "### Cross-Validations"]
        for cv in self._cross_validations:
            con = " ⚠️ CONTRADICTORY" if cv.contradictory else ""
            lines.append(
                f"- {cv.pipeline_a} ↔ {cv.pipeline_b}: "
                f"gaps={cv.gap_overlap:.2f} hyps={cv.hypothesis_agreement:.2f}{con}"
            )

        lines += ["", "### Consensus Gaps (by confidence)"]
        for g in result.consensus_gaps[:5]:
            found_by = ", ".join(g.get("found_by", ["?"]))
            lines.append(f"- [{g.get('confidence', 0):.0%}] {g.get('area', '?')[:80]} (by: {found_by})")

        return "\n".join(lines)
