"""
C4REQBER: Multi-Agent System — Specialized Agents
"""
from __future__ import annotations

from typing import Any

from src.agents.multi.core import AgentOutput, AgentRole, BaseAgent


class AnalystAgent(BaseAgent):
    """Analyst Agent: Breaks down problems and identifies patterns."""

    def __init__(self) -> None:
        super().__init__(AgentRole.ANALYST, "Analyst")

    async def process(self, context: dict[str, Any]) -> AgentOutput:
        """Analyze problem and produce structured analysis."""
        problem = context.get("problem", "")
        decomposition = self._decompose_problem(problem)
        domain = self._identify_domain(problem)
        constraints = self._identify_constraints(problem)
        analogies = self._find_analogous_domains(problem, domain)

        analysis = {
            "problem": problem,
            "decomposition": decomposition,
            "primary_domain": domain,
            "constraints": constraints,
            "analogous_domains": analogies,
            "key_concepts": self._extract_concepts(problem),
            "complexity_score": self._assess_complexity(problem),
        }

        return AgentOutput(
            agent_role=self.role.value,
            agent_name=self.name,
            output_type="analysis",
            content=analysis,
            confidence=0.75,
            reasoning=f"Analyzed problem across {len(analogies)} potential domains",
        )

    def _decompose_problem(self, problem: str) -> list[dict[str, str]]:
        """Break problem into sub-problems."""
        parts = []
        if "increase" in problem.lower() or "improve" in problem.lower():
            parts.append({"type": "optimization", "description": "Maximization objective"})
        if "without" in problem.lower() or "while" in problem.lower():
            parts.append({"type": "constraint", "description": "Trade-off management"})
        if "and" in problem.lower():
            parts.append({"type": "multi_objective", "description": "Multiple requirements"})
        return parts if parts else [{"type": "general", "description": "Single objective"}]

    def _identify_domain(self, problem: str) -> str:
        """Identify primary scientific domain."""
        keywords = {
            "battery": "energy", "energy": "energy",
            "software": "computer_science", "algorithm": "computer_science",
            "protein": "biology", "cell": "biology",
            "drug": "medicine", "disease": "medicine",
            "material": "materials", "chemical": "chemistry",
        }
        problem_lower = problem.lower()
        for keyword, domain in keywords.items():
            if keyword in problem_lower:
                return domain
        return "general"

    def _identify_constraints(self, problem: str) -> list[str]:
        """Extract constraints from problem."""
        constraints = []
        if "without" in problem.lower():
            constraints.append("Must maintain existing properties")
        if "cheap" in problem.lower() or "cost" in problem.lower():
            constraints.append("Cost constraint")
        if "fast" in problem.lower() or "quick" in problem.lower():
            constraints.append("Time constraint")
        return constraints

    def _find_analogous_domains(self, problem: str, primary_domain: str) -> list[str]:
        """Find domains with similar problems."""
        analogies = {
            "energy": ["biology", "chemistry", "materials"],
            "computer_science": ["mathematics", "cognitive_science", "biology"],
            "biology": ["chemistry", "computer_science", "medicine"],
            "medicine": ["biology", "chemistry"],
            "materials": ["physics", "chemistry", "engineering"],
        }
        return analogies.get(primary_domain, ["general"])

    def _extract_concepts(self, problem: str) -> list[str]:
        """Extract key concepts from problem."""
        words = problem.lower().split()
        stopwords = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "without", "with"}
        concepts = [w for w in words if w not in stopwords and len(w) > 3]
        return list(set(concepts))[:10]

    def _assess_complexity(self, problem: str) -> float:
        """Assess problem complexity (0-1)."""
        score = 0.5
        if "without" in problem.lower():
            score += 0.1
        if "and" in problem.lower():
            score += 0.1
        if len(problem.split()) > 10:
            score += 0.1
        return min(score, 1.0)


class ScientistAgent(BaseAgent):
    """Scientist Agent: Generates hypotheses using C4+TRIZ+Analogy."""

    def __init__(self) -> None:
        super().__init__(AgentRole.SCIENTIST, "Scientist")

    async def process(self, context: dict[str, Any]) -> AgentOutput:
        """Generate hypotheses based on analysis."""
        analysis = context.get("analysis", {})
        problem = analysis.get("problem", "")
        analyst_memory = self.get_relevant_memory("analysis")
        if analyst_memory:
            analysis = analyst_memory[-1].content

        hypotheses = []
        hypotheses.extend(await self._generate_c4_hypotheses(problem, analysis))
        hypotheses.extend(await self._generate_triz_hypotheses(problem, analysis))
        hypotheses.extend(await self._generate_analogy_hypotheses(problem, analysis))

        return AgentOutput(
            agent_role=self.role.value,
            agent_name=self.name,
            output_type="hypotheses",
            content=hypotheses,
            confidence=0.7,
            reasoning=f"Generated {len(hypotheses)} hypotheses using C4, TRIZ, and analogy",
        )

    async def _generate_c4_hypotheses(self, problem: str, analysis: dict[str, Any]) -> list[dict]:  # type: ignore[type-arg]
        """Generate hypotheses using C4 operators."""
        paths = [
            ["tau+", "sigma", "delta", "lambda+"],
            ["sigma", "iota", "rho+", "lambda+"],
            ["delta", "gamma", "iota", "lambda+"],
        ]
        hypotheses = []
        for i, path in enumerate(paths[:2]):
            h = {
                "id": f"c4_{i + 1}",
                "type": "c4",
                "hypothesis": f"Apply C4 transformation: {' → '.join(path)}",
                "c4_path": path,
                "confidence": 0.65 + (i * 0.05),
                "description": self._describe_c4_path(path),
            }
            hypotheses.append(h)
        return hypotheses

    def _describe_c4_path(self, path: list[str]) -> str:
        """Generate human-readable description of C4 path."""
        descriptions = {
            "tau+": "shift to future perspective",
            "sigma": "abstract to higher level",
            "delta": "transform across time",
            "lambda+": "synthesize at meta level",
            "iota": "integrate across domains",
            "rho+": "expand agency to system",
            "gamma": "bridge past and future",
        }
        parts = [descriptions.get(p, p) for p in path]
        return " → ".join(parts)

    async def _generate_triz_hypotheses(self, problem: str, analysis: dict[str, Any]) -> list[dict]:  # type: ignore[type-arg]
        """Generate hypotheses using TRIZ principles."""
        principles = [
            {"num": 1, "name": "Segmentation"},
            {"num": 15, "name": "Dynamics"},
            {"num": 35, "name": "Parameter Changes"},
        ]
        hypotheses = []
        for _i, p in enumerate(principles[:2]):
            h = {
                "id": f"triz_{p['num']}",
                "type": "triz",
                "hypothesis": f"Apply TRIZ Principle {p['num']}: {p['name']}",
                "triz_principle": p["num"],
                "confidence": 0.6,
                "description": f"Use {p['name'].lower()} to solve the problem",  # type: ignore[attr-defined]
            }
            hypotheses.append(h)
        return hypotheses

    async def _generate_analogy_hypotheses(self, problem: str, analysis: dict[str, Any]) -> list[dict]:  # type: ignore[type-arg]
        """Generate hypotheses using cross-domain analogies."""
        domains = analysis.get("analogous_domains", ["general"])
        hypotheses = []
        for i, domain in enumerate(domains[:2]):
            h = {
                "id": f"analogy_{i + 1}",
                "type": "analogy",
                "hypothesis": f"Apply {domain} solution pattern",
                "source_domain": domain,
                "confidence": 0.55,
                "description": f"Adapt solution from {domain} domain",
            }
            hypotheses.append(h)
        return hypotheses


class CriticAgent(BaseAgent):
    """Critic Agent: Evaluates and challenges hypotheses."""

    def __init__(self) -> None:
        super().__init__(AgentRole.CRITIC, "Critic")

    async def process(self, context: dict[str, Any]) -> AgentOutput:
        """Critique hypotheses from Scientist."""
        scientist_messages = self.get_relevant_memory("hypotheses")
        if not scientist_messages:
            return AgentOutput(
                agent_role=self.role.value,
                agent_name=self.name,
                output_type="critique",
                content={"error": "No hypotheses to critique"},
                confidence=0.0,
                reasoning="No hypotheses received",
            )

        all_hypotheses = []
        for msg in scientist_messages:
            all_hypotheses.extend(msg.content)

        critiques = []
        for h in all_hypotheses:
            critique = self._critique_hypothesis(h)
            critiques.append({"hypothesis_id": h["id"], "hypothesis": h["hypothesis"], **critique})

        return AgentOutput(
            agent_role=self.role.value,
            agent_name=self.name,
            output_type="critique",
            content=critiques,
            confidence=0.8,
            reasoning=f"Critiqued {len(critiques)} hypotheses",
        )

    def _critique_hypothesis(self, hypothesis: dict[str, Any]) -> dict[str, Any]:
        """Critique a single hypothesis."""
        weaknesses = []
        assumptions = []
        h_type = hypothesis.get("type", "")

        if h_type == "c4":
            weaknesses.append("Requires validation of C4 state transitions")
            assumptions.append("Problem is transformable via C4 operators")
        if h_type == "triz":
            weaknesses.append("May not account for domain-specific constraints")
            assumptions.append("TRIZ principles apply to this domain")
        if h_type == "analogy":
            weaknesses.append("Analogical transfer may not preserve causal structure")
            assumptions.append("Source and target domains are sufficiently similar")

        weaknesses.append("Needs empirical validation")
        falsifiability_score = self._assess_falsifiability(hypothesis)
        feasibility_score = self._assess_feasibility(hypothesis)
        novelty_score = self._assess_novelty(hypothesis)

        return {
            "weaknesses": weaknesses,
            "assumptions": assumptions,
            "falsifiability_score": falsifiability_score,
            "feasibility_score": feasibility_score,
            "novelty_score": novelty_score,
            "overall_score": (falsifiability_score + feasibility_score + novelty_score) / 3,
            "verdict": self._generate_verdict(falsifiability_score, feasibility_score),
        }

    def _assess_falsifiability(self, hypothesis: dict[str, Any]) -> float:
        """Assess how falsifiable the hypothesis is (0-1)."""
        score = 0.5
        h_text = hypothesis.get("hypothesis", "")
        if len(h_text) > 50:
            score += 0.2
        if "measure" in h_text.lower() or "test" in h_text.lower():
            score += 0.2
        return min(score, 1.0)

    def _assess_feasibility(self, hypothesis: dict[str, Any]) -> float:
        """Assess feasibility (0-1)."""
        return 0.6

    def _assess_novelty(self, hypothesis: dict[str, Any]) -> float:
        """Assess novelty (0-1)."""
        if hypothesis.get("type") == "analogy":
            return 0.75
        return 0.6

    def _generate_verdict(self, falsifiability: float, feasibility: float) -> str:
        """Generate overall verdict."""
        if falsifiability > 0.6 and feasibility > 0.5:
            return "PROMISING"
        elif falsifiability > 0.4:
            return "NEEDS REFINEMENT"
        return "HIGH RISK"


class SynthesizerAgent(BaseAgent):
    """Synthesizer Agent: Combines outputs into coherent recommendations."""

    def __init__(self) -> None:
        super().__init__(AgentRole.SYNTHESIZER, "Synthesizer")

    async def process(self, context: dict[str, Any]) -> AgentOutput:
        """Synthesize all agent outputs into final result."""
        hypotheses_msgs = self.get_relevant_memory("hypotheses")
        critique_msgs = self.get_relevant_memory("critique")

        all_hypotheses = []
        all_critiques = []
        for msg in hypotheses_msgs:
            all_hypotheses.extend(msg.content)
        for msg in critique_msgs:
            all_critiques.extend(msg.content)

        scored_hypotheses = self._score_hypotheses(all_hypotheses, all_critiques)
        synthesis = {
            "top_hypotheses": scored_hypotheses[:3],
            "all_hypotheses": scored_hypotheses,
            "research_plan": self._generate_research_plan(scored_hypotheses[:3]),
            "risk_assessment": self._assess_risks(scored_hypotheses, all_critiques),
            "recommended_next_steps": self._generate_next_steps(scored_hypotheses[0] if scored_hypotheses else None),
        }

        return AgentOutput(
            agent_role=self.role.value,
            agent_name=self.name,
            output_type="synthesis",
            content=synthesis,
            confidence=0.75,
            reasoning=f"Synthesized {len(scored_hypotheses)} hypotheses with critiques",
        )

    def _score_hypotheses(self, hypotheses: list[dict], critiques: list[dict]) -> list[dict]:  # type: ignore[type-arg]
        """Score hypotheses based on critiques."""
        scored = []
        for h in hypotheses:
            critique = next((c for c in critiques if c["hypothesis_id"] == h["id"]), None)
            base_score = h.get("confidence", 0.5)
            if critique:
                crit_score = critique.get("overall_score", 0.5)
                h["final_score"] = (base_score + crit_score) / 2
                h["critique"] = critique
            else:
                h["final_score"] = base_score
            scored.append(h)
        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored

    def _generate_research_plan(self, top_hypotheses: list[dict]) -> list[dict]:  # type: ignore[type-arg]
        """Generate research plan for top hypotheses."""
        plan = []
        for i, h in enumerate(top_hypotheses, 1):
            step = {
                "phase": i,
                "hypothesis_id": h["id"],
                "action": f"Validate: {h['hypothesis'][:50]}...",
                "estimated_duration": "2-4 weeks",
                "key_metrics": ["Success rate", "Cost efficiency", "Robustness"],
            }
            plan.append(step)
        return plan

    def _assess_risks(self, hypotheses: list[dict], critiques: list[dict]) -> dict[str, Any]:  # type: ignore[type-arg]
        """Assess overall risks."""
        risk_factors = []
        for c in critiques:
            if c.get("verdict") == "HIGH RISK":
                risk_factors.append(f"Hypothesis {c['hypothesis_id']} has high risk")
        return {
            "risk_level": "MEDIUM" if len(risk_factors) < 3 else "HIGH",
            "risk_factors": risk_factors,
            "mitigation_strategies": [
                "Start with small-scale validation",
                "Use parallel validation of multiple hypotheses",
                "Monitor for early warning signs",
            ],
        }

    def _generate_next_steps(self, top_hypothesis: dict | None) -> list[str]:  # type: ignore[type-arg]
        """Generate recommended next steps."""
        if not top_hypothesis:
            return ["Refine problem statement"]
        return [
            f"1. Design experiment for: {top_hypothesis['hypothesis'][:60]}...",
            "2. Define success metrics and falsifiability criteria",
            "3. Estimate resource requirements",
            "4. Create validation timeline",
        ]
