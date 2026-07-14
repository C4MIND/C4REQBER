"""SkillRegistry — c4reqber module registration as agent tools."""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolCall:
    skill: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any] | None = None


@dataclass
class SkillDef:
    id: str
    name: str
    description: str
    tools: list[ToolDef] = field(default_factory=list)
    execute: Callable | None = None


class SkillRegistry:
    """Registry of all c4reqber skills the agent can use.

    Skills are registered by module path. Each skill exposes tools
    (callable functions) that the agent invokes via LLM tool calls.
    """

    def __init__(self) -> None:
        self.skills: dict[str, SkillDef] = {}
        self._register_all()

    def _register_all(self) -> None:
        """Register all c4reqber built-in skills."""
        # ── C4 Engine ──────────────────────────────────────────────────────
        self._register("c4.engine", "C4 Cognitive Engine", "27-state Z₃³ navigation, operators, pathfinding", [
            ToolDef("navigate", "Navigate to a C4 state", {"state": {"T": "int", "S": "int", "A": "int"}}),
            ToolDef("pathfind", "Find path between two C4 states"),
            ToolDef("describe_state", "Describe what a C4 state means"),
            ToolDef("all_states", "List all 27 C4 states"),
        ])

        # ── Pipeline ───────────────────────────────────────────────────────
        self._register("c4.pipeline", "Discovery & Problem Solving", "HILDiscoveryPipeline, UniversalSolvePipeline", [
            ToolDef("solve", "Solve a problem: PRD, plan, blueprint, code"),
            ToolDef("turbo", "Deep research: 28 knowledge sources, paradigm detection"),
            ToolDef("flash", "Quick LLM answer + optional web search"),
            ToolDef("turbofactory", "Parallel paradigm factory (5-100 pipelines)"),
        ])

        # ── TRIZ ───────────────────────────────────────────────────────────
        self._register("c4.triz", "TRIZ 40 Principles", "Contradiction matrix, principle extraction", [
            ToolDef("find_principles", "Find TRIZ principles for a contradiction"),
            ToolDef("analyze", "TRIZ analysis of a problem"),
            ToolDef("matrix", "Show contradiction matrix entries"),
        ])

        # ── Discovery ──────────────────────────────────────────────────────
        self._register("c4.discovery", "Gap Analysis & Discovery", "Knowledge gap mining, novelty detection", [
            ToolDef("analyze_gaps", "Find knowledge gaps in a field"),
            ToolDef("novelty_check", "Check novelty of an idea"),
            ToolDef("already_shifted", "Check if paradigm has shifted"),
        ])

        # ── Verification ───────────────────────────────────────────────────
        self._register("c4.verification", "Formal Verification", "Z3, Lean4, Coq, Dafny, Agda, TLA+, Alloy", [
            ToolDef("verify", "Verify a claim with specified backend"),
            ToolDef("list_backends", "List available verification backends"),
            ToolDef("generate_proof", "Generate proof outline"),
        ])

        # ── Knowledge ──────────────────────────────────────────────────────
        self._register("c4.knowledge", "28 Knowledge Sources", "arXiv, PubMed, Semantic Scholar, Google Scholar, Zenodo...", [
            ToolDef("search", "Search across multiple knowledge sources"),
            ToolDef("fetch_paper", "Fetch paper details by ID"),
            ToolDef("list_sources", "List all available knowledge sources"),
        ])

        # ── WASM ───────────────────────────────────────────────────────────
        self._register("c4.wasm", "WASM Plugin Runtime", "Fast in-browser/in-line computations", [
            ToolDef("load", "Load a WASM plugin"),
            ToolDef("execute", "Execute a WASM plugin function"),
            ToolDef("list", "List loaded WASM plugins"),
        ])

        # ── Memory ─────────────────────────────────────────────────────────
        self._register("c4.memory", "Zettelkasten Memory", "Structural memory, knowledge graph", [
            ToolDef("save", "Save a finding to memory"),
            ToolDef("recall", "Recall related findings"),
            ToolDef("graph", "Show memory knowledge graph"),
        ])

        # ── Export ─────────────────────────────────────────────────────────
        self._register("c4.export", "Document Generation", "Papers, reports, patents", [
            ToolDef("paper", "Generate a research paper"),
            ToolDef("report", "Generate a structured report"),
            ToolDef("patent", "Generate a patent draft"),
        ])

        # ── Security ───────────────────────────────────────────────────────
        self._register("c4.security", "Security & Safety", "Policy engine, prompt guard, audit", [
            ToolDef("scan", "Scan text for threats (injection, credentials)"),
            ToolDef("audit", "Show security audit log"),
            ToolDef("policy_check", "Check action against policy"),
        ])

        # ── Soul (meta-skill) ──────────────────────────────────────────────
        self._register("c4.soul", "Agent Persona", "Identity, core values, refusal rules, evolution", [
            ToolDef("show", "Show current soul / persona"),
            ToolDef("update", "Update soul configuration"),
            ToolDef("reset", "Reset to factory defaults"),
        ])

    def _register(
        self,
        skill_id: str,
        name: str,
        description: str,
        tools: list[ToolDef],
    ) -> None:
        self.skills[skill_id] = SkillDef(
            id=skill_id,
            name=name,
            description=description,
            tools=tools,
        )

    def describe(self) -> str:
        """Return a markdown description of all skills for the system prompt."""
        parts = []
        for sid, skill in self.skills.items():
            tools_str = "\n".join(
                f"  - `{sid}.{t.name}({self._format_params(t)})` — {t.description}"
                for t in skill.tools
            )
            parts.append(f"  **{skill.name}** (`{sid}`)\n{tools_str}")
        return "\n".join(parts)

    @staticmethod
    def _format_params(tool: ToolDef) -> str:
        if not tool.parameters:
            return "..."
        return ", ".join(tool.parameters.keys())

    def execute(self, call: ToolCall) -> Any:
        """Execute a tool call by routing to the appropriate module."""
        dispatch: dict[str, dict[str, Callable]] = {
            "c4.engine": {
                "all_states": lambda: _import_run("src.c4.engine", "C4Space", "list_states"),
                "describe_state": lambda: _import_run("src.c4.engine", "C4Space", "describe_state", **call.args),
                "navigate": lambda: _import_run("src.c4.engine", "C4Space", "navigate", **call.args),
                "pathfind": lambda: _import_run("src.c4.engine", "C4Space", "find_path", **call.args),
            },
            "c4.soul": {
                "show": lambda: _import_run("src.agents.soul", "Soul", "to_markdown"),
                "reset": lambda: (_import_run("src.agents.soul", "Soul", "reset") or "Soul reset"),
                "update": lambda: _import_run("src.agents.soul", "Soul", "add_evolution_entry", change=call.args.get("key", ""), author="agent"),
            },
            "c4.verification": {
                "verify": lambda: _import_run("src.verification.hoare_verifier", "HoareVerifier", "verify", code=call.args.get("code", "")),
                "list_backends": lambda: ["lean4", "coq", "dafny", "agda", "z3", "hoare"],
                "generate_proof": lambda: _import_run("src.verification.llm_prover", "LLMProver", "prove", hypothesis=call.args.get("hypothesis", ""), language=call.args.get("lang", "lean4")),
            },
            "c4.security": {
                "scan": lambda: _import_run("src.security.guardian", "Guardian", "full_scan", text=call.args.get("text", "")),
                "audit": lambda: _import_run("src.agents.policy", "PolicyEngine", "audit", read_all=lambda: "audit trail"),
                "policy_check": lambda: _import_run("src.agents.policy", "PolicyEngine", "evaluate", action_name=call.args.get("action", "unknown")),
            },
        }

        skill_dispatch = dispatch.get(call.skill, {})
        handler = skill_dispatch.get(call.tool)
        if handler:
            return handler()

        # Generic fallback: report available tools for the skill
        skill_def = self.skills.get(call.skill)
        if skill_def:
            available = [t.name for t in skill_def.tools]
            return f"Skill '{call.skill}' registered but '{call.tool}' not dispatched. Available: {available}"

        raise ValueError(f"Unknown tool: {call.skill}.{call.tool}")


def _import_run(module_path: str, class_name: str, method: str, **kwargs: Any) -> Any:
    """Import a module, instantiate a class, call a method."""
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    instance = cls()
    func = getattr(instance, method)
    return func(**kwargs) if kwargs else func()
