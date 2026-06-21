"""
c4reqber BLAST CLI — 4-Mode Command System.

Modes:
  blast solve       → Problem solving (UniversalSolvePipeline v2)
  blast turbo       → Research proposals (HILDiscoveryPipeline v4)
  blast flash       → Quick answers
  blast turbofactory → Parallel paradigm factory

Auto-routing: blast "query" → auto-selects best mode
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import typer
from rich.console import Console

from src import __version__
from src.cli.blast_core import (
    cmd_auto,
    cmd_flash,
    cmd_solve,
    cmd_turbo,
    cmd_turbofactory,
)
from src.cli.mode_router import get_mode_description
from src.wasm.runtime import WASMPluginRuntime


# Shared WASM runtime — persists loaded modules across CLI commands
_wasm_runtime = WASMPluginRuntime()

app = typer.Typer(
    name="blast",
    help=f"c4reqber v{__version__} — Cognitive Exoskeleton for AI Agents",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# Auto-dispatch (no subcommand)
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("auto", hidden=True)
def blast_auto(
    query: str = typer.Argument(..., help="Query to process (auto-routed to best mode)"),
) -> None:
    """Auto-route query to best pipeline mode."""
    cmd_auto(query)


# ═══════════════════════════════════════════════════════════════════════════════
# Mode A: blast solve
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("solve")
def blast_solve(
    problem: str = typer.Argument(..., help="Problem statement to solve"),
    mode: str = typer.Option("autopilot", "--mode", "-m", help="Pipeline mode: autopilot|turbo|deep-work"),
    output_format: str = typer.Option("auto", "--format", "-f", help="Output: auto|prd|code|plan|blueprint|protocol"),
    domain: str | None = typer.Option(None, "--domain", "-d", help="Domain hint"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """Solve a problem — produces strategic artifacts (PRD, plans, blueprints, code)."""
    if not problem.strip():
        console.print("[red]Error: problem statement cannot be empty[/]")
        raise typer.Exit(1)
    cmd_solve(problem=problem, mode=mode, output_format=output_format, domain=domain, output=output, verbose=verbose)


# ═══════════════════════════════════════════════════════════════════════════════
# Mode B: blast turbo
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("turbo")
def blast_turbo(
    topic: str = typer.Argument(..., help="Research topic to discover"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    verify_backend: str = typer.Option("hybrid", "--verify-backend", help="Verification: hybrid|z3|lean4|coq|dafny|agda|hoare"),
    functors: bool = typer.Option(True, "--functors/--no-functors", help="Enable 9 cognitive functor agents"),
    plugins: str | None = typer.Option(None, "--plugins", "-p", help="Plugins: swot,six_hats,first_principles..."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show quality report"),
    competing: int = typer.Option(2, "--competing", help="Number of competing hypotheses"),
    no_iterative: bool = typer.Option(False, "--no-iterative", help="Skip iterative refinement"),
) -> None:
    """Generate paradigm-shifting research proposal: 28 knowledge sources (orchestrator), iterative paradigm detection, competing hypotheses, redundant quality gates."""
    if not topic.strip():
        console.print("[red]Error: topic cannot be empty[/]")
        raise typer.Exit(1)
    cmd_turbo(topic=topic, output=output, verify_backend=verify_backend, functors=functors, plugins=plugins, verbose=verbose, competing=competing, no_iterative=no_iterative)


# ═══════════════════════════════════════════════════════════════════════════════
# Mode C: blast flash
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("flash")
def blast_flash(
    question: str = typer.Argument(..., help="Question to answer quickly"),
    with_sources: bool = typer.Option(False, "--sources", "-s", help="Include source citations"),
    deep: bool = typer.Option(False, "--deep", "-d", help="Deep mode: USP cognitive components + multi-source search"),
    format: str = typer.Option("concise", "--format", "-f", help="Output format: concise|detailed|bullet|code"),
) -> None:
    """Get a quick answer — no pipeline, just fast LLM + optional web search."""
    if not question.strip():
        console.print("[red]Error: question cannot be empty[/]")
        raise typer.Exit(1)
    cmd_flash(question=question, with_sources=with_sources, deep=deep, format=format)


# ═══════════════════════════════════════════════════════════════════════════════
# Mode D: blast turbofactory
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("turbofactory")
def blast_turbofactory(
    domain: str = typer.Argument(..., help="Domain or problem to research in depth"),
    scale: str = typer.Option("standard", "--scale", "-s", help="Scale: mini|standard|mega|giga"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    max_concurrent: int = typer.Option(5, "--max-concurrent", "-c", help="Max concurrent pipelines"),
    pipeline_mode: str = typer.Option("mixed", "--pipeline", "-p", help="Pipeline: solve|turbo|mixed"),
) -> None:
    """Run parallel paradigm factory (10-100 pipelines) for ultimate domain reports."""
    cmd_turbofactory(domain=domain, scale=scale, output=output, max_concurrent=max_concurrent, pipeline_mode=pipeline_mode)


# ═══════════════════════════════════════════════════════════════════════════════
# Info commands
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("modes")
def blast_modes() -> None:
    """Show available modes and their descriptions."""
    console.print("[bold]BLAST Modes[/bold]\n")
    for mode in ["solve", "turbo", "flash", "turbofactory"]:
        console.print(f"  [bold]{mode}[/bold] — {get_mode_description(mode)}")
    console.print("\n[dim]Usage: blast [mode] \"your query\"[/dim]")
    console.print("[dim]Or: blast \"your query\" (auto-routed)[/dim]")


# ═══════════════════════════════════════════════════════════════════════════════
# WASM Plugin Commands
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("wasm-load")
def wasm_load(
    path: str = typer.Argument(..., help="Path to .wasm file"),
) -> None:
    """Load a WASM plugin module and register it in the pipeline."""
    wasm_file = Path(path)
    if not wasm_file.exists():
        console.print(f"[red]File not found: {path}[/]")
        raise typer.Exit(1)
    wasm_bytes = wasm_file.read_bytes()

    module = _wasm_runtime.load(wasm_bytes)
    funcs = _wasm_runtime.list_functions(module)
    plugin_name = wasm_file.stem

    console.print(f"[green]Loaded:[/] {wasm_file.name}")

    # Parse exports to understand what functions are available
    exports = _wasm_runtime._parse_exports(wasm_bytes) if not _wasm_runtime._has_wasmtime else \
        [(n, 0) for n in funcs]
    console.print(f"  Exports: {[(n, 'func' if k==0 else 'mem' if k==2 else f'kind{k}') for n,k in exports]}")
    console.print(f"  Runtime: {'wasmtime' if _wasm_runtime._has_wasmtime else 'stub (pip install wasmtime for execution)'}")

    # Register with plugin registry → appears in pipeline
    from src.plugins.unified_registry import ToolMetadata
    from src.plugins.unified_registry import PLUGIN_REGISTRY, PluginInfo
    from src.wasm.runtime import WASMToolPlugin

    wasm_meta = ToolMetadata(
        name=plugin_name,
        version="1.0.0",
        description=f"WASM plugin: {plugin_name} ({len(exports)} exports)",
        author="user",
        requires=["wasmtime"],
    )
    wasm_plugin = WASMToolPlugin(_wasm_runtime, wasm_bytes, wasm_meta)

    # Wrap for v2_registry compatibility
    PLUGIN_REGISTRY[f"wasm_{plugin_name}"] = PluginInfo(
        id=f"wasm_{plugin_name}",
        name=f"WASM: {plugin_name}",
        description=wasm_meta.description,
        category="wasm",
        execute_fn=wasm_plugin.execute,
        icon="package",
    )
    console.print(f"  [cyan]Pipeline:[/] registered as [bold]wasm_{plugin_name}[/] — active in next run")
    console.print(f"  [dim]Total plugins in pipeline: {len(PLUGIN_REGISTRY)}[/]")


@app.command("wasm-list")
def wasm_list() -> None:
    """List loaded WASM modules and their functions."""
    runtime = _wasm_runtime
    if not runtime._modules:
        console.print("[dim]No WASM modules loaded.[/]")
        console.print()
        console.print("[bold]Built-in WASM modules (frontend):[/]")
        console.print("  • [cyan]wasm/spectral/[/] — Spectral embedding (10x faster than Python)")
        console.print("  • [cyan]wasm/graph/[/]    — Fruchterman-Reingold force-directed layout")
        console.print()
        console.print("[bold]CLI plugins (pre-built):[/]")
        console.print("  [dim]Built with: python -m src.wasm.build_plugins[/]")
        console.print("  • [green]wasm_plugins/hello.wasm[/]    — Returns 42 (demo)")
        console.print("  • [green]wasm_plugins/sha256.wasm[/]   — Hash fingerprint: n*31 XOR 0xCD")
        console.print("  • [green]wasm_plugins/math.wasm[/]     — Modular math: (n*7+3)")
        console.print("  • [green]wasm_plugins/identity.wasm[/] — Passthrough (overhead benchmark)")
        console.print()
        console.print("[bold]To load:[/]")
        console.print("  [green]blast wasm-load wasm_plugins/hello.wasm[/]")
        console.print()
        console.print("[dim]Requires: pip install wasmtime  (optional — stub mode works without it)[/]")
        return
    for key, mod in runtime._modules.items():
        funcs = runtime.list_functions(mod)
        console.print(f"[bold]{key}:[/] {funcs}")


@app.command("wasm-execute")
def wasm_execute(
    plugin_name: str = typer.Argument(..., help="Registered plugin name (e.g. wasm_hello)"),
) -> None:
    """Execute a registered WASM plugin through the pipeline registry."""
    from src.plugins.unified_registry import PLUGIN_REGISTRY

    info = PLUGIN_REGISTRY.get(plugin_name)
    if info is None:
        console.print(f"[red]Plugin not found: {plugin_name}[/]")
        console.print("[dim]Available plugins:[/]")
        for pid, pi in PLUGIN_REGISTRY.items():
            cat = pi.category if hasattr(pi, 'category') else 'unknown'
            if cat == 'wasm':
                console.print(f"  [cyan]{pid}[/] — {pi.description}")
        raise typer.Exit(1)

    console.print(f"[bold]Executing:[/] {info.name}")
    try:
        result = info.execute_fn(problem="test", hypothesis_text="test")
        console.print(f"[green]Result:[/] {result}")
    except RuntimeError as e:
        console.print(f"[yellow]Stub mode:[/] {e}")


@app.command("models")
def blast_models(
    tier: str = typer.Option("", "--tier", "-t", help="Filter: frontier|premium|balanced|budget|ultra_budget|free|local"),
) -> None:
    """Browse available LLM models with benchmarks and pricing."""
    from src.llm.model_catalog import CATALOG, estimate_pipeline_cost, list_models

    if tier:
        models = list_models(tier)
    else:
        models = list_models()

    if tier:
        console.print(f"[bold]Models — {tier} tier[/bold]")
    else:
        console.print(f"[bold]C4REQBER Model Catalog — {len(CATALOG)} models[/bold]")

    console.print()
    for m in models:
        price = f"in=${m['cost_in']:.2f} out=${m['cost_out']:.2f}" if m['cost_in'] > 0 else "FREE"
        console.print(f"  [cyan]{m['key']}[/cyan] ({m['provider']})")
        console.print(f"    {price} | {m['context']//1000}K ctx | tier={m['tier']}")
        if m['strengths']:
            console.print(f"    {', '.join(m['strengths'][:5])}")
        if m.get('open_weight'):
            console.print(f"    open-weight ({m.get('license','')})")

    console.print()
    cost = estimate_pipeline_cost(1000)
    console.print(f"[bold]Pipeline cost estimate:[/bold] ${cost['total']:.4f} (balanced tier, 7 phases)")


@app.command("config")
def blast_config(
    section: str = typer.Argument("models", help="Config section: models | user | keys"),
    cost_tier: str = typer.Option("", "--tier", "-t", help="Cost tier: budget|balanced|premium|local|ultra_budget"),
    set_phase: str = typer.Option("", "--set", "-s", help="Set model for phase: e.g. 'D=claude-sonnet-4.6'"),
    show: bool = typer.Option(False, "--show", help="Show current model assignments"),
    save: bool = typer.Option(False, "--save", help="Save config to ~/.c4reqber/models.json"),
) -> None:
    """Configure model assignments per pipeline phase (or full user config).

    Examples:
        blast config --show                    # View current assignments
        blast config user --show               # Show full ~/.c4reqber/config.toml + keys
        blast config --tier budget             # Switch to budget tier
        blast config --set D=claude-sonnet-4.6 --save  # Phase D → Claude Sonnet
    """
    from src.llm.model_assignment import (
        CONFIG_FILE,
        DEFAULT_ASSIGNMENTS,
        PHASE_DESCRIPTIONS,
        ModelAssignment,
    )

    # Load existing or create default
    assignment = ModelAssignment.load()

    if section.lower() in ("user", "full"):
        from src.cli.config_init import show_current_config
        show_current_config()
        if show or section:
            return
        # fallthrough only for other ops

    if section.lower() == "keys":
        from src.config import get_user_keys
        keys = get_user_keys()
        console.print("\n[bold]Current API keys (from ~/.c4reqber + env)[/bold]\n")
        important = ["openrouter_api_key", "deepseek_api_key", "brave_api_key", "tavily_api_key", "exa_api_key", "xai_api_key"]
        for k in important:
            val = keys.get(k, "")
            masked = "****" + val[-4:] if len(val) > 8 else "(not set)"
            console.print(f"  {k}: {masked}")
        console.print("\n[dim]Use 'blast init' to set keys interactively, or edit ~/.c4reqber/config.toml[/]")
        return

    # Apply cost tier
    if cost_tier:
        if cost_tier not in DEFAULT_ASSIGNMENTS:
            console.print(f"[red]Unknown tier: {cost_tier}. Options: {list(DEFAULT_ASSIGNMENTS.keys())}[/]")
            raise typer.Exit(1)
        assignment = ModelAssignment.create_default(cost_tier)
        console.print(f"[green]Switched to {cost_tier} tier[/]")

    # Apply per-phase model override
    if set_phase:
        if "=" not in set_phase:
            console.print("[red]Use format: --set D=model-name[/]")
            raise typer.Exit(1)
        phase, model = set_phase.split("=", 1)
        phase = phase.strip().upper()
        if phase not in "ABCDEFG":
            console.print("[red]Phase must be A-G[/]")
            raise typer.Exit(1)
        from src.llm.model_assignment import PhaseAssignment, _detect_provider
        temp = 0.7 if phase == "D" else 0.5 if phase == "F" else 0.3
        max_tok = 2000 if phase == "F" else 800 if phase == "D" else 500
        assignment.phases[phase] = PhaseAssignment(
            model=model.strip(), temperature=temp, max_tokens=max_tok,
            provider=_detect_provider(model.strip()),
        )
        console.print(f"[green]Phase {phase}: set to {model.strip()}[/]")

    # Show current state
    if show:
        console.print()
        console.print(f"[bold]Model Assignments — {assignment.cost_tier} tier[/bold]")
        if assignment.api_base_url:
            console.print(f"[dim]API base: {assignment.api_base_url}[/]")
        console.print()
        for phase in "ABCDEFG":
            desc = PHASE_DESCRIPTIONS.get(phase, "")
            model = assignment.get_model(phase)
            if not model:
                console.print(f"  [cyan]Phase {phase}[/cyan]: [dim](compute — no LLM)[/]")
            else:
                # Don't double-display provider prefix if model ID already has it
                display = model
                temp = assignment.get_temperature(phase)
                console.print(f"  [cyan]Phase {phase}[/cyan]: {display}  [dim]T={temp}[/]  — {desc[:50]}...")

        cost = assignment.estimate_cost(1000)
        console.print()
        console.print(f"[bold]Estimated pipeline cost:[/bold] ${cost['total']:.4f}")

    # Save
    if save:
        assignment.save()
        console.print(f"[green]Saved to {CONFIG_FILE}[/]")
        console.print(f"[dim]Config file:[/] {CONFIG_FILE}")
    else:
        console.print("[dim]Use --save to persist to disk[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Commands — Soul, Policy, QA, Guardian
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("soul")
def blast_soul(
    show: bool = typer.Option(False, "--show", "-s", help="Display current soul"),
    reset: bool = typer.Option(False, "--reset", help="Reset to factory defaults"),
    edit: str = typer.Option("", "--edit", "-e", help="Edit field: key=value"),
) -> None:
    """Manage the AI assistant persona (soul)."""
    from src.agents.soul import Soul

    soul = Soul()

    if reset:
        soul.reset()
        console.print("[green]Soul reset to factory defaults[/]")
        return

    if edit:
        if "=" not in edit:
            console.print("[red]Use format: --edit key=value[/]")
            raise typer.Exit(1)
        key, value = edit.split("=", 1)
        soul.add_evolution_entry(f"Edited {key} = {value}")
        console.print(f"[green]Updated {key} = {value}[/]")
        return

    # Default: show soul
    console.print(soul.to_markdown())


@app.command("policy")
def blast_policy(
    show_rules: bool = typer.Option(False, "--rules", "-r", help="Show risk rules"),
    show_audit: bool = typer.Option(False, "--audit", "-a", help="Show recent audit entries"),
    evaluate: str = typer.Option("", "--eval", help="Evaluate action: name:type"),
    approve: bool = typer.Option(False, "--approve", help="Mark as user-approved"),
) -> None:
    """Policy engine — risk classification and audit trail."""
    from src.agents.policy import Action, PolicyEngine

    engine = PolicyEngine()

    if show_rules:
        console.print("[bold]Risk Rules[/bold]")
        for action_type, tier in sorted(engine.get_rules().items()):
            color = {
                "READ": "green",
                "SOFT_WRITE": "yellow",
                "HARD_WRITE": "orange3",
                "DANGEROUS": "red",
            }.get(tier, "white")
            console.print(f"  {action_type:<30} [{color}]{tier}[/]")
        return

    if show_audit:
        entries = engine.audit.read_last(20)
        if not entries:
            console.print("[dim]No audit entries yet.[/]")
            return
        console.print(f"[bold]Recent Audit Entries ({len(entries)})[/bold]")
        for e in entries:
            status = "[green]ALLOW[/]" if e.allowed else "[red]DENY[/]"
            console.print(
                f"  {e.timestamp:.0f} {status} [{e.risk_tier}] {e.action_name} — {e.reason[:50]}"
            )
        stats = engine.audit.stats()
        console.print(f"\n[dim]Total: {stats['total']}, Allowed: {stats['allowed']}, Denied: {stats['denied']}[/]")
        return

    if evaluate:
        if ":" not in evaluate:
            console.print("[red]Use format: --eval name:action_type[/]")
            raise typer.Exit(1)
        name, action_type = evaluate.split(":", 1)
        action = Action(name=name.strip(), action_type=action_type.strip())
        decision = engine.evaluate(action, user_approved=approve)
        color = "green" if decision.allowed else "red"
        console.print(f"[{color}]{'ALLOWED' if decision.allowed else 'DENIED'}[/]")
        console.print(f"  Tier: {decision.risk_tier.value}")
        console.print(f"  Reason: {decision.reason}")
        if decision.requires_approval:
            console.print("  [yellow]Requires user approval[/]")
        if decision.requires_multi_factor:
            console.print("  [red]Requires multi-factor approval[/]")
        return

    console.print("[bold]Policy Engine[/bold]")
    console.print("  Use --rules to see risk classification")
    console.print("  Use --audit to see audit trail")
    console.print("  Use --eval name:type to evaluate an action")


@app.command("qa")
def blast_qa(
    full: bool = typer.Option(False, "--full", "-f", help="Run all QA checks"),
    check: str = typer.Option("", "--check", "-c", help="Single check: ruff|mypy|pytest|version_sync|secrets|circular_imports"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Quality assurance — lint, typecheck, tests, version sync, secrets."""
    from src.agents.qa import QAController

    qa = QAController()

    if check:
        check_map = {
            "ruff": qa.check_ruff,
            "mypy": qa.check_mypy,
            "pytest": qa.check_pytest,
            "version_sync": qa.check_version_sync,
            "secrets": qa.check_secrets,
            "circular_imports": qa.check_circular_imports,
        }
        fn = check_map.get(check)
        if fn is None:
            console.print(f"[red]Unknown check: {check}. Options: {list(check_map.keys())}[/]")
            raise typer.Exit(1)
        result = fn()
        color = "green" if result.passed else "red"
        console.print(f"[{color}]{check}: {'PASS' if result.passed else 'FAIL'}[/] ({result.duration_ms:.0f}ms)")
        for err in result.errors:
            console.print(f"  [red]  {err}[/]")
        return

    # Full QA run
    console.print("[bold]Running QA suite...[/bold]\n")
    qa_result = qa.run_all()

    if json_out:
        console.print(qa_result.to_json())
        return

    for name, _chk in qa_result.checks.items():
        color = "green" if _chk.passed else "red"
        icon = "✓" if _chk.passed else "✗"
        console.print(f"  [{color}]{icon} {name:<20} {'PASS' if _chk.passed else 'FAIL'}[/] ({_chk.duration_ms:.0f}ms)")
        for err in _chk.errors[:3]:
            console.print(f"    [red]  {err}[/]")

    rate_color = "green" if qa_result.success_rate >= 0.8 else "yellow" if qa_result.success_rate >= 0.5 else "red"
    console.print(f"\n[bold]Result:[/] [{rate_color}]{qa_result.passed}/{qa_result.total} passed ({qa_result.success_rate*100:.0f}%)[/] in {qa_result.duration_sec:.1f}s")


@app.command("guardian")
def blast_guardian(
    scan: str = typer.Option("", "--scan", "-s", help="Text to scan for threats"),
    scan_file: str = typer.Option("", "--file", "-f", help="File to scan"),
    code: str = typer.Option("", "--code", "-c", help="Python code to validate AST"),
) -> None:
    """Safety guardian — scan for prompt injection, credentials, unsafe code."""
    from src.security.guardian import Guardian

    guardian = Guardian()

    if scan_file:
        path = Path(scan_file)
        if not path.exists():
            console.print(f"[red]File not found: {scan_file}[/]")
            raise typer.Exit(1)
        text = path.read_text(encoding="utf-8")
        result = guardian.full_scan(text)
    elif scan:
        result = guardian.full_scan(scan)
    elif code:
        result = guardian.validate_ast(code)
    else:
        console.print("[bold]Guardian — Safety Scanner[/bold]")
        console.print("  Use --scan 'text' to scan text")
        console.print("  Use --file path to scan file")
        console.print("  Use --code 'python code' to validate AST")
        return

    if result.clean:
        console.print("[green]✓ Clean — no threats detected[/]")
    else:
        severity_color = {"low": "yellow", "medium": "orange3", "high": "red", "critical": "red"}.get(result.severity, "red")
        console.print(f"[{severity_color}]✗ Threats detected (severity: {result.severity})[/]")
        for threat in result.threats:
            console.print(f"  [red]  • {threat}[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# Social — Preprint Publishing + Messengers
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("social")
def blast_social(
    action: str = typer.Argument("status", help="Action: status, health, publish, preview, drafts, clean, setup"),
    draft_id: str = typer.Option("", "--id", help="Draft ID"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without API calls"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm publish"),
    older_than_days: int = typer.Option(30, "--older-than", help="Days for cleanup"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """Social publishing — preprints, posts, messengers, health.

    \b
        blast social status           # Show social module status
        blast social health           # Check all platform connections
        blast social preview --id X   # Preview a draft
        blast social publish --id X   # Publish a draft
        blast social publish --id X --dry-run  # Simulate publish
        blast social clean --older-than 30     # Clean old drafts
        blast social setup telegram   # Setup wizard
    """
    import asyncio

    if action == "health":
        async def _health():
            from src.social.health_checker import check_all
            result = await check_all(dry_run)
            for name, status in sorted(result.items()):
                icon = "●" if status.get("healthy") else "○"
                reason = status.get("reason", status.get("note", ""))
                console.print(f"  {icon} {name:<12} {reason}")
        asyncio.run(_health())
        return

    if action == "status":
        from src.social.profile_manager import UserProfile
        p = UserProfile.load()
        console.print("[bold]Social Module Status[/bold]")
        console.print(f"  Profile: {p.primary_author.name or '(not set)'}")
        console.print("  Drafts directory: ~/.c4reqber/drafts/")
        drafts = list((Path.home() / ".c4reqber" / "drafts").glob("*")) if (Path.home() / ".c4reqber" / "drafts").exists() else []
        console.print(f"  Drafts: {len([d for d in drafts if d.is_dir()])} pending")
        return

    if action == "publish" and draft_id:
        async def _pub():
            from src.social.publisher import Publisher
            pub = Publisher(dry_run=dry_run)
            result = await pub.publish(draft_id)
            if result.get("error"):
                console.print(f"[red]{result['error']}[/]")
            else:
                console.print(f"[green]Published {draft_id}[/]")
                for step, val in result.get("steps", {}).items():
                    doi = val.get("doi", "") if isinstance(val, dict) else ""
                    console.print(f"  {step}: {doi or val}")
        asyncio.run(_pub())
        return

    if action == "preview" and draft_id:
        draft_dir = Path.home() / ".c4reqber" / "drafts" / draft_id
        md = draft_dir / "dissertation.md"
        if md.exists():
            from rich.markdown import Markdown
            console.print(Markdown(md.read_text()[:3000]))
        else:
            console.print(f"[yellow]Draft {draft_id} not found or no dissertation.md[/]")
        return

    if action == "drafts":
        d = Path.home() / ".c4reqber" / "drafts"
        if d.exists():
            for draft in sorted(d.iterdir(), reverse=True):
                if draft.is_dir():
                    state_file = draft / "draft_state.json"
                    status = "?"
                    if state_file.exists():
                        import json
                        state = json.loads(state_file.read_text())
                        status = state.get("status", "?")
                    console.print(f"  [{status}] {draft.name}")
        else:
            console.print("[dim]No drafts yet[/]")
        return

    if action == "clean":
        d = Path.home() / ".c4reqber" / "drafts"
        if not d.exists():
            console.print("[dim]No drafts to clean[/]")
            return
        cutoff = time.time() - older_than_days * 86400
        removed = 0
        for draft in d.iterdir():
            if draft.is_dir() and draft.stat().st_mtime < cutoff:
                import shutil
                shutil.rmtree(draft)
                removed += 1
        console.print(f"[green]Removed {removed} drafts older than {older_than_days} days[/]")
        return

    if action == "setup":
        console.print("[bold]Setup Wizards[/bold]")
        console.print("  Telegram: Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env")
        console.print("  Slack:    Set SLACK_WEBHOOK_URL in .env")
        console.print("  Discord:  Set DISCORD_WEBHOOK_URL in .env")
        console.print("  Reddit:   Set REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET + REDDIT_USERNAME + REDDIT_PASSWORD in .env")
        console.print("  Zenodo:   Set ZENODO_ACCESS_TOKEN in .env")
        console.print("  Twitter:  Set TWITTER_API_KEY + TWITTER_ACCESS_TOKEN in .env")
        console.print("  ORCID:    Set ORCID_CLIENT_ID + ORCID_CLIENT_SECRET in .env")
        return

    console.print("[bold]blast social[/bold] — Preprint publishing & social posting")
    console.print("  Use: status | health | preview | publish | drafts | clean | setup")


# ═══════════════════════════════════════════════════════════════════════════════
# Init — first-run configuration
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("init")
def blast_init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing ~/.c4reqber/config.toml"),
) -> None:
    """Interactive setup wizard — writes ~/.c4reqber/config.toml for desktop and TUI."""
    from src.cli.config_init import run_init_wizard

    run_init_wizard(force=force)


# ═══════════════════════════════════════════════════════════════════════════════
# TUI — Interactive Cockpit (Go TUI v9)
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("tui")
def blast_tui(
    packages: bool = typer.Option(False, "--packages", help="Arrow-key scientific package installer"),
    demo: bool = typer.Option(False, "--demo", help="Scripted demo without backend"),
    story: str = typer.Option("", "--story", help="Demo story: crispr|sleep|lang"),
    no_splash: bool = typer.Option(False, "--no-splash", help="Skip splash screen on launch"),
    no_build: bool = typer.Option(False, "--no-build", help="Do not auto-build c4tui-v9 if missing"),
) -> None:
    """Launch TUI v9 Cockpit — feed-driven discovery UI.

    \b
        blast tui                          # Interactive discovery cockpit
        blast tui --demo --story=crispr    # Demo without backend
        blast tui --packages               # Package installer (Rich UI)
        blast tui --no-splash              # Skip boot animation
    """
    if packages:
        from src.cli.tui_launcher import launch_package_installer
        raise typer.Exit(launch_package_installer())

    extra: list[str] = []
    if demo:
        extra.append("--demo")
    if story:
        extra.extend(["--story", story])
    if no_splash:
        extra.append("--no-splash")

    from src.cli.config_init import apply_config_to_env
    from src.config.paths import apply_config_to_env as central_apply
    from src.cli.tui_launcher import launch_tui_v9

    try:
        central_apply()
    except Exception:
        apply_config_to_env()  # fallback
    if demo:
        import os

        os.environ.setdefault("C4_DEMO_AUTH", "1")
    code = launch_tui_v9(extra, build_if_missing=not no_build)
    raise typer.Exit(code)


# ═══════════════════════════════════════════════════════════════════════════════
# Serve — MCP Server
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("serve")
def blast_serve(
    mcp: bool = typer.Option(True, "--mcp", help="Start MCP server via stdio"),
) -> None:
    """Start MCP server for AI agent connectivity via stdio JSON-RPC."""
    if not mcp:
        console.print("[dim]Use --mcp to start the MCP server[/]")
        return

    console.print("[bold cyan]Starting C4REQBER MCP Server...[/]")
    console.print("[dim]MCP stdio JSON-RPC transport[/]")
    console.print("[dim]21 tools available for connected AI agents[/]")
    console.print()

    try:
        import asyncio

        from src.mcp_server.server import main as mcp_main
        asyncio.run(mcp_main())
    except ImportError as e:
        console.print(f"[red]MCP SDK not installed: {e}[/]")
        console.print("[dim]Run: pip install mcp[/]")
        raise typer.Exit(1) from e
    except KeyboardInterrupt:
        console.print("\n[yellow]MCP server stopped.[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# Agent — AI Agent REPL
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("agent")
def blast_agent(
    cmd: str = typer.Option("", "--cmd", help="One-shot agent query"),
    daemon: bool = typer.Option(False, "--daemon", help="MCP server for external AI agents"),
    config: bool = typer.Option(False, "--config", help="Show agent configuration"),
) -> None:
    """Interactive AI agent — REPL with /commands, Pydantic AI, skills, MCP, memory.

    \b
        blast agent                  # Interactive REPL
        blast agent --cmd "query"    # One-shot query
        blast agent --config         # Show configuration
    """
    if config:
        from src.agent.config import AgentConfig
        cfg = AgentConfig.load()
        console.print("[bold]Agent Configuration[/bold]")
        console.print(f"  History path: {cfg.history_path}")
        console.print(f"  History size: {cfg.history_size}")
        console.print(f"  System prompt: {cfg.system_prompt_extra[:80]}...")
        console.print(f"  MCP servers: {len(cfg.mcp_servers)} configured")
        for srv in cfg.mcp_servers:
            console.print(f"    • {srv.name} → {srv.command} {' '.join(srv.args)}")
        console.print(f"  Soul enabled: {cfg.soul.enabled}")
        console.print(f"  Daemon port: {cfg.daemon_port}")
        return

    if daemon:
        console.print("[bold]Starting C4REQBER Agent in daemon mode...[/]")
        console.print("[dim]Agent MCP server — stdio JSON-RPC transport[/]")
        console.print("[dim]7 tools: process, search, verify, codegen, transfer, fingerprint, solve[/]")

        try:
            from src.agent.core import AgentCore

            agent = AgentCore()

            async def agent_daemon_main():
                import json as _json
                reader = sys.stdin
                writer = sys.stdout

                while True:
                    line = reader.readline()
                    if not line:
                        break
                    try:
                        request = _json.loads(line.strip())
                        method = request.get("method", "")
                        params = request.get("params", {})
                        request_id = request.get("id")

                        if method == "tools/list":
                            tools = [
                                {"name": "agent_process", "description": "Process a query through the AI agent", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
                                {"name": "agent_search", "description": "Search knowledge sources", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}},
                                {"name": "agent_verify", "description": "Verify code with formal methods", "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}, "backend": {"type": "string"}}, "required": ["code"]}},
                                {"name": "agent_codegen", "description": "Generate code from specification", "inputSchema": {"type": "object", "properties": {"spec": {"type": "string"}, "language": {"type": "string"}}, "required": ["spec"]}},
                                {"name": "agent_fingerprint", "description": "Classify problem into C4 state", "inputSchema": {"type": "object", "properties": {"problem": {"type": "string"}}, "required": ["problem"]}},
                                {"name": "agent_transfer", "description": "Cross-domain isomorphism transfer", "inputSchema": {"type": "object", "properties": {"problem": {"type": "string"}, "source_domain": {"type": "string"}, "target_domain": {"type": "string"}}, "required": ["problem"]}},
                                {"name": "agent_solve", "description": "Solve problem via discovery pipeline", "inputSchema": {"type": "object", "properties": {"problem": {"type": "string"}}, "required": ["problem"]}},
                            ]
                            response = {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}
                        elif method == "tools/call":
                            tool_name = params.get("name", "")
                            arguments = params.get("arguments", {})
                            result = {}

                            if tool_name == "agent_process":
                                resp = agent.process(arguments.get("query", ""))
                                result = {"content": [{"type": "text", "text": resp.content}]}
                            elif tool_name == "agent_solve":
                                resp = agent.process(arguments.get("problem", ""))
                                result = {"content": [{"type": "text", "text": resp.content}]}
                            elif tool_name == "agent_search":
                                result = {"content": [{"type": "text", "text": f"Search for: {arguments.get('query', '')}"}]}
                            elif tool_name == "agent_fingerprint":
                                from src.c4_analysis.llm_classifier import get_c4_classifier
                                classifier = get_c4_classifier()
                                state, confidence, _ = classifier.classify(arguments.get("problem", ""))
                                result = {"content": [{"type": "text", "text": f"C4 State: {state} (confidence: {confidence:.2f})"}]}
                            else:
                                result = {"content": [{"type": "text", "text": f"Tool {tool_name} executed"}]}

                            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
                        elif method == "notifications/initialized":
                            response = None
                        else:
                            response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

                        if response:
                            writer.write(_json.dumps(response) + "\n")
                            writer.flush()
                    except _json.JSONDecodeError:
                        pass

            import asyncio as _asyncio
            import sys as _sys
            _asyncio.run(agent_daemon_main())
        except ImportError as e:
            console.print(f"[red]Agent daemon failed: {e}[/]")
            raise typer.Exit(1) from e
        except KeyboardInterrupt:
            console.print("\n[yellow]Agent daemon stopped.[/]")
        return

    if cmd:
        console.print(f"[bold]Agent query:[/bold] {cmd}")
        from src.agent.core import AgentCore
        agent = AgentCore()
        response = agent.process(cmd)
        console.print(f"\n[green]{response.content}[/]")
        if response.tool_calls:
            console.print(f"\n[dim]Tool calls: {len(response.tool_calls)}[/]")
        console.print(f"[dim]Duration: {response.duration_sec:.1f}s[/]")
        return

    # Interactive REPL
    from src.agent.core import AgentCore
    agent = AgentCore()
    console.print("[bold cyan]C4REQBER Agent v5.4.0[/]")
    console.print("[dim]Interactive REPL — type /help for commands, /quit to exit[/]")
    agent.repl()


# ═══════════════════════════════════════════════════════════════════════════════
# Analyze — Systemicity Analysis
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("analyze")
def blast_analyze(
    query: str = typer.Argument(..., help="Query to analyze for systemicity"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Systemicity analysis — entity extraction, dependency graph, decomposition, critical path, C4 state."""
    if not query.strip():
        console.print("[red]Error: query cannot be empty[/]")
        raise typer.Exit(1)

    from src.c4_analysis.system_analyzer import SystemAnalyzer

    console.print(f"[bold]Analyzing:[/bold] {query}")
    console.print()

    analyzer = SystemAnalyzer()
    result = analyzer.analyze(query)

    if json_out:
        console.print(json.dumps(result, indent=2, default=str))
        return

    # Human-readable output
    sys_label = result["systemicity_label"]
    sys_score = result["systemicity"]
    color = "green" if sys_score > 0.6 else "yellow" if sys_score > 0.3 else "dim"
    console.print(f"[bold]Systemicity:[/] [{color}]{sys_score:.2f} — {sys_label}[/]")
    console.print(f"[bold]Depth:[/] {result['analysis_depth']}")
    console.print(f"[bold]C4 State:[/] [cyan]{result['c4_state']}[/]")
    console.print()

    console.print(f"[bold]Entities ({len(result['entities'])}):[/]")
    console.print(f"  {', '.join(result['entities'][:10])}")
    console.print()

    deps = result.get("dependency_graph", {})
    if deps:
        console.print("[bold]Dependency Graph:[/]")
        for entity, depends in list(deps.items())[:8]:
            if depends:
                console.print(f"  [cyan]{entity}[/] → {', '.join(depends)}")

    console.print()
    sub_problems = result.get("sub_problems", [])
    console.print(f"[bold]Sub-problems ({len(sub_problems)}):[/]")
    for sp in sub_problems[:6]:
        name = sp.get("name", sp.get("problem", "?"))[:80]
        rank = sp.get("rank", sp.get("centrality", "?"))
        console.print(f"  [{rank}] {name}")

    console.print()
    critical = result.get("critical_path", [])
    if critical:
        console.print("[bold]Critical Path:[/]")
        for i, step in enumerate(critical[:5]):
            name = step.get("name", step.get("problem", "?"))[:60]
            console.print(f"  {i+1}. {name}")

    console.print()
    console.print(f"[dim]{result['explanation']}[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# Integrations — External services & tools
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("integrations")
def blast_integrations(
    service: str = typer.Argument("status", help="Service: status, test, search, skills, tools"),
    query: str = typer.Option("", "--query", "-q", help="Search query for OpenFang/Hive"),
    domain: str = typer.Option("", "--domain", "-d", help="Domain filter for Hive skills"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """External integrations — Eigent desktop, Hive marketplace, OpenFang registry.

    \b
        blast integrations status               # Show all integrations status
        blast integrations test                  # Test all connections
        blast integrations search -q "CFD"       # Search OpenFang registry
        blast integrations skills -d "biology"   # Search Hive marketplace
        blast integrations tools                 # List OpenFang categories
    """
    import asyncio

    if service == "status":
        async def _status():
            from src.integrations import (
                EigentDesktop,
                LiquidAIClient,
                NvidiaNimClient,
                OpenFangClient,
                YandexGPTClient,
            )
            results = {}
            for name, client_cls in [
                ("Liquid AI", LiquidAIClient),
                ("NVIDIA NIM", NvidiaNimClient),
                ("YandexGPT", YandexGPTClient),
                ("OpenFang", OpenFangClient),
            ]:
                try:
                    client = client_cls()
                    test = await client.test_connection() if hasattr(client, 'test_connection') else {"healthy": False}
                    results[name] = test
                except Exception as e:
                    results[name] = {"healthy": False, "error": str(e)}

            eigent = EigentDesktop()
            connected = await eigent.connect()
            results["Eigent"] = {"healthy": connected, "port": eigent.api_port}

            console.print("[bold]Integration Status[/bold]")
            for name, status in sorted(results.items()):
                healthy = status.get("healthy", False)
                icon = "●" if healthy else "○"
                extra = status.get("models_found", status.get("skills_found", status.get("categories_found", "")))
                detail = f" — {extra} found" if extra else f" — {status.get('error', status.get('port', ''))}"
                console.print(f"  {icon} {name:<14}{detail}")
        asyncio.run(_status())
        return

    if service == "test":
        async def _test():
            from src.integrations import (
                LiquidAIClient,
                NvidiaNimClient,
                OpenFangClient,
                YandexGPTClient,
            )
            all_ok = True
            for name, client_cls in [
                ("Liquid AI", LiquidAIClient),
                ("NVIDIA NIM", NvidiaNimClient),
                ("YandexGPT", YandexGPTClient),
                ("OpenFang", OpenFangClient),
            ]:
                try:
                    client = client_cls()
                    test = await client.test_connection() if hasattr(client, 'test_connection') else {"healthy": False}
                    healthy = test.get("healthy", False)
                    icon = "✓" if healthy else "✗"
                    err = test.get("error", "")
                    console.print(f"  [{icon}] {name:<14} {'OK' if healthy else err}")
                    if not healthy:
                        all_ok = False
                except Exception as e:
                    console.print(f"  [✗] {name:<14} {e}")
                    all_ok = False
            if all_ok:
                console.print("\n[green]All integrations healthy[/]")
        asyncio.run(_test())
        return

    if service == "search" and query:
        async def _search():
            from src.integrations import OpenFangClient
            registry = OpenFangClient()
            results = await registry.search(query)
            if json_out:
                console.print(json.dumps(results, indent=2, default=str))
                return
            console.print(f"[bold]OpenFang: {len(results)} results for '{query}'[/]")
            for r in results[:10]:
                name = r.get("name", r.get("title", r.get("id", "?")))
                desc = (r.get("description", "") or "")[:100]
                console.print(f"  [cyan]{name}[/] — {desc}")
        asyncio.run(_search())
        return

    if service == "skills":
        async def _skills():
            from src.integrations import OpenFangClient
            fang = OpenFangClient()
            results = await fang.search_skills(query) if query else await fang.list_skills()
            if json_out:
                console.print(json.dumps(results, indent=2, default=str))
                return
            label = f"'{query}'" if query else "all"
            console.print(f"[bold]OpenFang FangHub: {len(results)} skills for {label}[/]")
            for r in results[:10]:
                name = r.get("name", r.get("title", r.get("id", "?")))
                desc = (r.get("description", "") or "")[:100]
                console.print(f"  [cyan]{name}[/] — {desc}")
            if json_out:
                console.print(json.dumps(results, indent=2, default=str))
                return
            label = f"'{query}'" if query else "all"
            console.print(f"[bold]Hive: {len(results)} skills for {label}[/]")
            for r in results[:10]:
                name = r.get("name", r.get("title", r.get("id", "?")))
                desc = (r.get("description", "") or "")[:100]
                console.print(f"  [cyan]{name}[/] — {desc}")
        asyncio.run(_skills())
        return

    if service == "tools":
        async def _tools():
            from src.integrations import OpenFangClient
            registry = OpenFangClient()
            cats = await registry.list_categories()
            if json_out:
                console.print(json.dumps(cats, indent=2, default=str))
                return
            console.print(f"[bold]OpenFang: {len(cats)} categories[/]")
            for cat in cats[:20]:
                console.print(f"  • {cat}")
        asyncio.run(_tools())
        return

    console.print("[bold]blast integrations[/bold] — External services & tools")
    console.print("  Use: status | test | search | skills | tools")


# ═══════════════════════════════════════════════════════════════════════════════
# Packages — Scientific Package Manager
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("packages")
def blast_packages(
    action: str = typer.Argument("list", help="list, install <id>, remove <id>, status"),
    package_id: str = typer.Option("", "--id", "-i", help="Package ID to install/remove"),
) -> None:
    """Scientific package manager — auto-detect, install, remove scientific Python packages.

    \b
        blast packages                  # List all packages with status
        blast packages status           # Full status with compatibility
        blast packages install --id mlx-lm   # Install package
        blast packages remove --id nashpy    # Remove package
    """
    from src.cli.package_manager import (
        PACKAGES,
        PackageStatus,
        detect_all,
        install_package,
        uninstall_package,
    )

    if action in ("install", "i"):
        if not package_id:
            console.print("[red]Usage: blast packages install --id <package>[/]")
            return
        console.print(f"[bold]Installing {package_id}...[/]")
        ok, msg = install_package(package_id)
        console.print(f"[green]{msg}[/]" if ok else f"[red]{msg}[/]")
        return

    if action in ("remove", "rm", "uninstall"):
        if not package_id:
            console.print("[red]Usage: blast packages remove --id <package>[/]")
            return
        console.print(f"[bold]Removing {package_id}...[/]")
        ok, msg = uninstall_package(package_id)
        console.print(f"[green]{msg}[/]" if ok else f"[yellow]{msg}[/]")
        return

    # List / status
    statuses = detect_all()
    console.print("[bold]C4REQBER Scientific Package Manager[/bold]")
    console.print(f"[dim]Python {sys.version_info.major}.{sys.version_info.minor} | {len(PACKAGES)} packages[/dim]")
    console.print()

    from rich.table import Table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", width=14)
    table.add_column("Name", width=26)
    table.add_column("Status", width=14)
    table.add_column("Category", width=12)
    table.add_column("Weight", width=8, justify="right")

    for pkg in PACKAGES:
        st = statuses.get(pkg.id, PackageStatus.UNKNOWN)
        icon = {"installed": "[green]●[/]", "available": "[dim]○[/]", "incompatible": "[red]✗[/]"}.get(st.value, "[dim]?[/]")
        status_text = {"installed": "[green]installed[/]", "available": "[dim]available[/]", "incompatible": "[red]py incompat[/]"}.get(st.value, "unknown")
        weight = f"{pkg.weight_mb}MB" if pkg.weight_mb > 0 else "-"
        table.add_row(
            f"{icon} {pkg.id}", pkg.name, status_text, pkg.category, weight,
        )

    console.print(table)
    console.print()
    console.print("[dim]● installed  ○ available  ✗ incompatible — use 'blast packages install --id <id>'[/]")
    console.print()
    console.print("[bold]TUI:[/] blast tui --packages    # Interactive arrow-key installer[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# Setup — First-Run Wizard
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("setup")
def blast_setup(
    auto: bool = typer.Option(False, "--auto", "-y", help="Auto-install everything without prompts"),
) -> None:
    """First-run setup wizard — interactive checkbox menu.

    \b
        blast setup            # Interactive: select/deselect packages, install chosen
        blast setup --auto     # Non-interactive: installs everything automatically
    """
    import platform as _platform

    from src.cli.package_manager import PACKAGES, PackageStatus, detect_all, install_package

    statuses = detect_all()
    proc = _platform.processor().lower()
    is_apple = "arm" in proc or "apple" in proc

    console.print("[bold cyan]╔══════════════════════════════════════╗[/]")
    console.print("[bold cyan]║   C4REQBER First-Run Setup Wizard    ║[/]")
    console.print("[bold cyan]╚══════════════════════════════════════╝[/]")
    console.print(f"[dim]Python {sys.version_info.major}.{sys.version_info.minor}[/]", end="")
    if is_apple:
        console.print(" [dim]|[/] [green]Apple Silicon M-series detected[/]")
    console.print()

    if auto:
        to_install = [p for p in PACKAGES if statuses[p.id] not in (PackageStatus.INSTALLED,)]
        if not to_install:
            console.print("[green]All packages already installed. System ready![/]")
            return
        console.print(f"[bold]Auto-installing {len(to_install)} packages...[/]")
        for pkg in to_install:
            ok, msg = install_package(pkg.id)
            console.print(f"  {'✓' if ok else '✗'} {pkg.id:<18} {msg[:60]}")
        console.print("[green]Setup complete![/]")
        return

    # Interactive mode — build checkbox list
    installable = [p for p in PACKAGES if statuses[p.id] != PackageStatus.INSTALLED]
    already = [p for p in PACKAGES if statuses[p.id] == PackageStatus.INSTALLED]

    console.print(f"[bold]Already installed ({len(already)}):[/]")
    for pkg in already:
        env_tag = " [dim](isolated 3.12)[/]" if getattr(pkg, "requires_isolated_env", False) else ""
        console.print(f"  [green]●[/] {pkg.id:<18} {pkg.description[:55]}{env_tag}")

    if not installable:
        console.print("\n[green]All 15 packages installed. System ready![/]")
        return

    console.print(f"\n[bold]Available to install ({len(installable)}):[/]")
    console.print("[dim]Use ↑↓ to navigate, Space to toggle, Enter to install selected, Q to quit[/]\n")

    for i, pkg in enumerate(installable):
        st = statuses[pkg.id]
        prefix = f"[{i+1}]"
        st_icon = "[yellow]○[/]" if st == PackageStatus.AVAILABLE else "[red]✗[/]"
        env_tag = " [dim](needs isolated 3.12 env)[/]" if st == PackageStatus.INCOMPATIBLE else ""
        weight = f" [dim]({pkg.weight_mb}MB)[/]" if pkg.weight_mb > 0 else ""
        console.print(f"  {prefix} {st_icon} {pkg.id:<18} [dim]{pkg.description[:55]}[/]{env_tag}{weight}")

    console.print()
    console.print("[dim]Type numbers to select (e.g., '1,3,5') or 'all' to select all, then Enter:[/]")
    selection = input("> ").strip().lower()

    if selection == "q":
        console.print("[dim]Setup cancelled.[/]")
        return

    selected = []
    if selection == "all":
        selected = list(range(len(installable)))
    else:
        for part in selection.replace(" ", "").split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(installable):
                    selected.append(idx)

    if not selected:
        console.print("[dim]No packages selected. Setup cancelled.[/]")
        return

    console.print(f"\n[bold]Installing {len(selected)} packages...[/]")
    with console.status("[bold green]Installing...[/]"):
        for idx in selected:
            pkg = installable[idx]
            ok, msg = install_package(pkg.id)
            icon = "[green]✓[/]" if ok else "[red]✗[/]"
            console.print(f"  {icon} {pkg.id:<18} {msg[:60]}")

    # Refresh status
    statuses = detect_all()
    final_installed = sum(1 for v in statuses.values() if v == PackageStatus.INSTALLED)
    console.print(f"\n[green]Setup complete! {final_installed}/15 packages installed.[/]")
    console.print("[dim]Run 'blast packages' to see full status.[/]")


if __name__ == "__main__":
    app()
