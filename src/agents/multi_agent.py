"""
TURBO-CDI: Multi-Agent System
AI Co-Scientist style multi-agent scientific discovery
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()


class AgentRole(Enum):
    """Specialized agent roles."""

    ANALYST = "analyst"  # Analyzes problems, finds patterns
    SCIENTIST = "scientist"  # Generates hypotheses
    CRITIC = "critic"  # Evaluates and challenges
    SYNTHESIZER = "synthesizer"  # Combines outputs
    VALIDATOR = "validator"  # Checks falsifiability


@dataclass
class AgentMessage:
    """Message between agents."""

    from_agent: str
    to_agent: str
    message_type: str  # "hypothesis", "critique", "analysis", "synthesis"
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentOutput:
    """Output from an agent."""

    agent_role: str
    agent_name: str
    output_type: str
    content: Any
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, role: AgentRole, name: str):
        self.role = role
        self.name = name
        self.memory: List[AgentMessage] = []
        self.confidence_threshold = 0.6

    def receive_message(self, message: AgentMessage):
        """Receive message from another agent."""
        self.memory.append(message)

    async def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Process input and produce output. Override in subclasses."""
        raise NotImplementedError

    def get_relevant_memory(
        self, message_type: Optional[str] = None
    ) -> List[AgentMessage]:
        """Get relevant messages from memory."""
        if message_type:
            return [m for m in self.memory if m.message_type == message_type]
        return self.memory


class AnalystAgent(BaseAgent):
    """
    Analyst Agent: Breaks down problems and identifies patterns.

    Responsibilities:
    - Problem decomposition
    - Pattern recognition
    - Domain analysis
    - Constraint identification
    """

    def __init__(self):
        super().__init__(AgentRole.ANALYST, "Analyst")

    async def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Analyze problem and produce structured analysis."""
        problem = context.get("problem", "")

        # Decompose problem
        decomposition = self._decompose_problem(problem)

        # Identify domain
        domain = self._identify_domain(problem)

        # Find constraints
        constraints = self._identify_constraints(problem)

        # Identify analogous domains
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

    def _decompose_problem(self, problem: str) -> List[Dict[str, str]]:
        """Break problem into sub-problems."""
        # Simple heuristic decomposition
        parts = []

        # Look for common patterns
        if "increase" in problem.lower() or "improve" in problem.lower():
            parts.append(
                {"type": "optimization", "description": "Maximization objective"}
            )

        if "without" in problem.lower() or "while" in problem.lower():
            parts.append({"type": "constraint", "description": "Trade-off management"})

        if "and" in problem.lower():
            parts.append(
                {"type": "multi_objective", "description": "Multiple requirements"}
            )

        return (
            parts if parts else [{"type": "general", "description": "Single objective"}]
        )

    def _identify_domain(self, problem: str) -> str:
        """Identify primary scientific domain."""
        keywords = {
            "battery": "energy",
            "energy": "energy",
            "software": "computer_science",
            "algorithm": "computer_science",
            "protein": "biology",
            "cell": "biology",
            "drug": "medicine",
            "disease": "medicine",
            "material": "materials",
            "chemical": "chemistry",
        }

        problem_lower = problem.lower()
        for keyword, domain in keywords.items():
            if keyword in problem_lower:
                return domain

        return "general"

    def _identify_constraints(self, problem: str) -> List[str]:
        """Extract constraints from problem."""
        constraints = []

        # Look for constraint indicators
        if "without" in problem.lower():
            constraints.append("Must maintain existing properties")

        if "cheap" in problem.lower() or "cost" in problem.lower():
            constraints.append("Cost constraint")

        if "fast" in problem.lower() or "quick" in problem.lower():
            constraints.append("Time constraint")

        return constraints

    def _find_analogous_domains(self, problem: str, primary_domain: str) -> List[str]:
        """Find domains with similar problems."""
        analogies = {
            "energy": ["biology", "chemistry", "materials"],
            "computer_science": ["mathematics", "cognitive_science", "biology"],
            "biology": ["chemistry", "computer_science", "medicine"],
            "medicine": ["biology", "chemistry"],
            "materials": ["physics", "chemistry", "engineering"],
        }

        return analogies.get(primary_domain, ["general"])

    def _extract_concepts(self, problem: str) -> List[str]:
        """Extract key concepts from problem."""
        # Simple extraction - in production use NLP
        words = problem.lower().split()
        # Filter out common words
        stopwords = {
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "and",
            "or",
            "without",
            "with",
        }
        concepts = [w for w in words if w not in stopwords and len(w) > 3]
        return list(set(concepts))[:10]

    def _assess_complexity(self, problem: str) -> float:
        """Assess problem complexity (0-1)."""
        score = 0.5  # Base

        # More constraints = higher complexity
        if "without" in problem.lower():
            score += 0.1
        if "and" in problem.lower():
            score += 0.1

        # Length heuristic
        if len(problem.split()) > 10:
            score += 0.1

        return min(score, 1.0)


class ScientistAgent(BaseAgent):
    """
    Scientist Agent: Generates hypotheses using C4+TRIZ+Analogy.

    Responsibilities:
    - Generate multiple hypotheses
    - Apply C4 cognitive geometry
    - Use TRIZ principles
    - Cross-domain analogy
    """

    def __init__(self):
        super().__init__(AgentRole.SCIENTIST, "Scientist")

    async def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Generate hypotheses based on analysis."""
        analysis = context.get("analysis", {})
        problem = analysis.get("problem", "")

        hypotheses = []

        # Get analysis from Analyst if available
        analyst_memory = self.get_relevant_memory("analysis")
        if analyst_memory:
            analysis = analyst_memory[-1].content

        # Generate via C4
        c4_hypotheses = await self._generate_c4_hypotheses(problem, analysis)
        hypotheses.extend(c4_hypotheses)

        # Generate via TRIZ
        triz_hypotheses = await self._generate_triz_hypotheses(problem, analysis)
        hypotheses.extend(triz_hypotheses)

        # Generate via Analogy
        analogy_hypotheses = await self._generate_analogy_hypotheses(problem, analysis)
        hypotheses.extend(analogy_hypotheses)

        return AgentOutput(
            agent_role=self.role.value,
            agent_name=self.name,
            output_type="hypotheses",
            content=hypotheses,
            confidence=0.7,
            reasoning=f"Generated {len(hypotheses)} hypotheses using C4, TRIZ, and analogy",
        )

    async def _generate_c4_hypotheses(self, problem: str, analysis: Dict) -> List[Dict]:
        """Generate hypotheses using C4 operators."""
        from src.core.c4_state import C4Space

        space = C4Space()

        # Common C4 paths for innovation
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

    def _describe_c4_path(self, path: List[str]) -> str:
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

    async def _generate_triz_hypotheses(
        self, problem: str, analysis: Dict
    ) -> List[Dict]:
        """Generate hypotheses using TRIZ principles."""
        # Common TRIZ principles for innovation
        principles = [
            {"num": 1, "name": "Segmentation"},
            {"num": 15, "name": "Dynamics"},
            {"num": 35, "name": "Parameter Changes"},
        ]

        hypotheses = []
        for i, p in enumerate(principles[:2]):
            h = {
                "id": f"triz_{p['num']}",
                "type": "triz",
                "hypothesis": f"Apply TRIZ Principle {p['num']}: {p['name']}",
                "triz_principle": p["num"],
                "confidence": 0.6,
                "description": f"Use {p['name'].lower()} to solve the problem",
            }
            hypotheses.append(h)

        return hypotheses

    async def _generate_analogy_hypotheses(
        self, problem: str, analysis: Dict
    ) -> List[Dict]:
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
    """
    Critic Agent: Evaluates and challenges hypotheses.

    Responsibilities:
    - Identify weaknesses
    - Check assumptions
    - Evaluate falsifiability
    - Assess feasibility
    """

    def __init__(self):
        super().__init__(AgentRole.CRITIC, "Critic")

    async def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Critique hypotheses from Scientist."""
        # Get hypotheses from memory
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
            critiques.append(
                {"hypothesis_id": h["id"], "hypothesis": h["hypothesis"], **critique}
            )

        return AgentOutput(
            agent_role=self.role.value,
            agent_name=self.name,
            output_type="critique",
            content=critiques,
            confidence=0.8,
            reasoning=f"Critiqued {len(critiques)} hypotheses",
        )

    def _critique_hypothesis(self, hypothesis: Dict) -> Dict:
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

        # General critique
        weaknesses.append("Needs empirical validation")

        # Score
        falsifiability_score = self._assess_falsifiability(hypothesis)
        feasibility_score = self._assess_feasibility(hypothesis)
        novelty_score = self._assess_novelty(hypothesis)

        return {
            "weaknesses": weaknesses,
            "assumptions": assumptions,
            "falsifiability_score": falsifiability_score,
            "feasibility_score": feasibility_score,
            "novelty_score": novelty_score,
            "overall_score": (falsifiability_score + feasibility_score + novelty_score)
            / 3,
            "verdict": self._generate_verdict(falsifiability_score, feasibility_score),
        }

    def _assess_falsifiability(self, hypothesis: Dict) -> float:
        """Assess how falsifiable the hypothesis is (0-1)."""
        # More specific = more falsifiable
        score = 0.5

        h_text = hypothesis.get("hypothesis", "")
        if len(h_text) > 50:  # More detailed = more falsifiable
            score += 0.2

        if "measure" in h_text.lower() or "test" in h_text.lower():
            score += 0.2

        return min(score, 1.0)

    def _assess_feasibility(self, hypothesis: Dict) -> float:
        """Assess feasibility (0-1)."""
        # For now, moderate feasibility
        return 0.6

    def _assess_novelty(self, hypothesis: Dict) -> float:
        """Assess novelty (0-1)."""
        # Cross-domain analogies are more novel
        if hypothesis.get("type") == "analogy":
            return 0.75
        return 0.6

    def _generate_verdict(self, falsifiability: float, feasibility: float) -> str:
        """Generate overall verdict."""
        if falsifiability > 0.6 and feasibility > 0.5:
            return "PROMISING"
        elif falsifiability > 0.4:
            return "NEEDS REFINEMENT"
        else:
            return "HIGH RISK"


class SynthesizerAgent(BaseAgent):
    """
    Synthesizer Agent: Combines outputs into coherent recommendations.

    Responsibilities:
    - Merge multiple hypotheses
    - Resolve conflicts
    - Create final recommendations
    - Generate research plan
    """

    def __init__(self):
        super().__init__(AgentRole.SYNTHESIZER, "Synthesizer")

    async def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Synthesize all agent outputs into final result."""
        # Gather all outputs from memory
        hypotheses_msgs = self.get_relevant_memory("hypotheses")
        critique_msgs = self.get_relevant_memory("critique")
        analysis_msgs = self.get_relevant_memory("analysis")

        all_hypotheses = []
        all_critiques = []

        for msg in hypotheses_msgs:
            all_hypotheses.extend(msg.content)

        for msg in critique_msgs:
            all_critiques.extend(msg.content)

        # Score and rank hypotheses
        scored_hypotheses = self._score_hypotheses(all_hypotheses, all_critiques)

        # Generate synthesis
        synthesis = {
            "top_hypotheses": scored_hypotheses[:3],
            "all_hypotheses": scored_hypotheses,
            "research_plan": self._generate_research_plan(scored_hypotheses[:3]),
            "risk_assessment": self._assess_risks(scored_hypotheses, all_critiques),
            "recommended_next_steps": self._generate_next_steps(
                scored_hypotheses[0] if scored_hypotheses else None
            ),
        }

        return AgentOutput(
            agent_role=self.role.value,
            agent_name=self.name,
            output_type="synthesis",
            content=synthesis,
            confidence=0.75,
            reasoning=f"Synthesized {len(scored_hypotheses)} hypotheses with critiques",
        )

    def _score_hypotheses(
        self, hypotheses: List[Dict], critiques: List[Dict]
    ) -> List[Dict]:
        """Score hypotheses based on critiques."""
        scored = []

        for h in hypotheses:
            # Find corresponding critique
            critique = next(
                (c for c in critiques if c["hypothesis_id"] == h["id"]), None
            )

            base_score = h.get("confidence", 0.5)

            if critique:
                # Adjust based on critique
                crit_score = critique.get("overall_score", 0.5)
                final_score = (base_score + crit_score) / 2

                h["critique"] = critique
                h["final_score"] = final_score
            else:
                h["final_score"] = base_score

            scored.append(h)

        # Sort by final score
        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored

    def _generate_research_plan(self, top_hypotheses: List[Dict]) -> List[Dict]:
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

    def _assess_risks(self, hypotheses: List[Dict], critiques: List[Dict]) -> Dict:
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

    def _generate_next_steps(self, top_hypothesis: Optional[Dict]) -> List[str]:
        """Generate recommended next steps."""
        if not top_hypothesis:
            return ["Refine problem statement"]

        return [
            f"1. Design experiment for: {top_hypothesis['hypothesis'][:60]}...",
            "2. Define success metrics and falsifiability criteria",
            "3. Estimate resource requirements",
            "4. Create validation timeline",
        ]


class MultiAgentSystem:
    """
    Multi-Agent Scientific Discovery System.

    Coordinates multiple specialized agents to:
    1. Analyze problems
    2. Generate diverse hypotheses
    3. Critique and evaluate
    4. Synthesize recommendations

    Inspired by AI Co-Scientist (Google DeepMind, 2025).
    """

    def __init__(self):
        self.agents: Dict[AgentRole, BaseAgent] = {
            AgentRole.ANALYST: AnalystAgent(),
            AgentRole.SCIENTIST: ScientistAgent(),
            AgentRole.CRITIC: CriticAgent(),
            AgentRole.SYNTHESIZER: SynthesizerAgent(),
        }
        self.message_bus: List[AgentMessage] = []

    async def discover(self, problem: str) -> Dict[str, Any]:
        """
        Run multi-agent discovery process.

        Args:
            problem: Research problem to solve

        Returns:
            Complete synthesis with recommendations
        """
        console.print(
            Panel.fit(
                f"[bold blue]🤖 Multi-Agent Discovery System[/bold blue]\n\n"
                f"Problem: {problem}\n"
                f"Agents: Analyst → Scientist → Critic → Synthesizer",
                title="Starting Discovery",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Phase 1: Analysis
            task1 = progress.add_task("[cyan]Analyst analyzing problem...", total=None)
            analysis = await self.agents[AgentRole.ANALYST].process(
                {"problem": problem}
            )
            self._broadcast(analysis, AgentRole.ANALYST)
            progress.update(task1, completed=True)

            # Phase 2: Hypothesis Generation
            task2 = progress.add_task(
                "[cyan]Scientist generating hypotheses...", total=None
            )
            hypotheses = await self.agents[AgentRole.SCIENTIST].process(
                {"analysis": analysis.content}
            )
            self._broadcast(hypotheses, AgentRole.SCIENTIST)
            progress.update(task2, completed=True)

            # Phase 3: Critique
            task3 = progress.add_task(
                "[cyan]Critic evaluating hypotheses...", total=None
            )
            critique = await self.agents[AgentRole.CRITIC].process({})
            self._broadcast(critique, AgentRole.CRITIC)
            progress.update(task3, completed=True)

            # Phase 4: Synthesis
            task4 = progress.add_task(
                "[cyan]Synthesizer creating recommendations...", total=None
            )
            synthesis = await self.agents[AgentRole.SYNTHESIZER].process({})
            progress.update(task4, completed=True)

        return {
            "problem": problem,
            "analysis": analysis.content,
            "hypotheses": hypotheses.content,
            "critique": critique.content,
            "synthesis": synthesis.content,
            "agent_count": len(self.agents),
        }

    def _broadcast(self, output: AgentOutput, from_role: AgentRole):
        """Broadcast output to all other agents."""
        message = AgentMessage(
            from_agent=output.agent_name,
            to_agent="all",
            message_type=output.output_type,
            content=output.content,
        )

        for role, agent in self.agents.items():
            if role != from_role:
                agent.receive_message(message)

        self.message_bus.append(message)

    def render_conversation_tree(self) -> str:
        """Render conversation tree for visualization."""
        tree = Tree("[bold]Multi-Agent Conversation[/bold]")

        for msg in self.message_bus:
            branch = tree.add(f"[cyan]{msg.from_agent}[/cyan] → {msg.message_type}")
            if isinstance(msg.content, list):
                branch.add(f"[{len(msg.content)} items]")
            elif isinstance(msg.content, dict):
                branch.add(f"[{len(msg.content)} keys]")

        return str(tree)


# Singleton
_system: Optional[MultiAgentSystem] = None


def get_multi_agent_system() -> MultiAgentSystem:
    """Get singleton multi-agent system."""
    global _system
    if _system is None:
        _system = MultiAgentSystem()
    return _system
