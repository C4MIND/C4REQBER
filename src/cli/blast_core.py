from __future__ import annotations

import time


"""BLAST Core Commands — 4-mode pipeline system.

Modes:
  solve        → UniversalSolvePipeline v2 (strategic artifacts)
  turbo        → HILDiscoveryPipeline v4 (dissertations)
  flash        → Quick LLM mode (chat answers)
  turbofactory → Parallel paradigm factory (10-100 pipelines)
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from src.agents.pipeline import UniversalSolvePipeline
from src.cli.mode_router import auto_route, get_mode_description
from src.utils.honesty_status import outer_status_from_hil_like, record_field_status


logger = logging.getLogger(__name__)
console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# Mode A: blast solve — Problem Solving (UniversalSolvePipeline v2)
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_solve(
    problem: str = typer.Argument(..., help="Problem statement to solve"),
    mode: str = typer.Option(
        "autopilot", "--mode", "-m", help="Pipeline mode: autopilot|turbo|deep-work"
    ),
    output_format: str = typer.Option(
        "auto", "--format", "-f", help="Output format: auto|prd|code|plan|blueprint|protocol"
    ),
    domain: str | None = typer.Option(None, "--domain", "-d", help="Domain hint"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> dict[str, Any]:
    """Solve a problem — 12-stage pipeline with observer (PRD, plans, blueprints, code)."""
    import asyncio

    from src.core.profile_manager import UserProfileManager

    manager = UserProfileManager()
    manager.load()

    console.print(f"[bold]BLAST solve[/bold] — {get_mode_description('solve')}")
    console.print(f"[dim]Problem:[/dim] {problem[:80]}...")
    console.print(f"[dim]Mode:[/dim] {mode} | [dim]Format:[/dim] {output_format}")

    pipeline = UniversalSolvePipeline()
    result = asyncio.run(pipeline.solve(problem, mode=mode, domain_hint=domain))

    text = (result.final_solution or "").strip()
    llm_failed = (
        "[LLM unavailable" in text
        or len(text.split()) < 50
        or float(getattr(result, "confidence", 0) or 0) <= 0.0
    )
    if llm_failed:
        console.print(
            f"\n[bold red]✗ Solve failed[/bold red] "
            f"(confidence: {result.confidence:.2f}, {len(text.split())} words)"
        )
        if verbose and text:
            console.print(f"\n[dim]Partial output:[/dim]\n{text[:500]}...")
        if output:
            console.print("[bold red]Refusing to save failed synthesis[/bold red]")
        raise typer.Exit(1)

    console.print(f"\n[green]✓ Solution generated[/green] (confidence: {result.confidence:.2f})")

    if verbose:
        console.print(f"\n[bold]Solution:[/bold]\n{text[:500]}...")

    if output:
        if len(text.split()) < 400:
            console.print(
                f"[bold red]Refusing to save — synthesis too short "
                f"({len(text.split())} words)[/bold red]"
            )
            raise typer.Exit(1)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text, encoding="utf-8")
        console.print(f"[green]Saved to:[/green] {output}")

    return result.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# Explainability — C4 state reasoning + provenance
# ═══════════════════════════════════════════════════════════════════════════════


def _print_explain_report(record: Any, topic: str) -> None:
    """Print a human-readable explanation of the pipeline's decisions."""
    console.print()
    console.print(f"[bold cyan]{'=' * 60}[/]")
    console.print("[bold cyan]  EXPLAIN: Why these results?[/]")
    console.print(f"[bold cyan]{'=' * 60}[/]")

    # C4 State reasoning
    c4 = getattr(record, "c4_state", "")
    if c4:
        try:
            parts = c4.replace("C4(", "").replace(")", "").split(",")
            t, s, a = int(parts[0]), int(parts[1]), int(parts[2])
            t_name = {0: "Past (T=0)", 1: "Present (T=1)", 2: "Future (T=2)"}.get(t, "")
            s_name = {0: "Concrete (S=0)", 1: "Abstract (S=1)", 2: "Meta (S=2)"}.get(s, "")
            a_name = {0: "Self (A=0)", 1: "Other (A=1)", 2: "System (A=2)"}.get(a, "")
            console.print(f"\n[bold]C4 State: {c4}[/]")
            console.print(
                f"  Time: {t_name} — {'looking backward' if t == 0 else 'present-focused' if t == 1 else 'forward-looking'}"
            )
            console.print(
                f"  Scale: {s_name} — {'tangible/practical' if s == 0 else 'theoretical' if s == 1 else 'meta/framework-level'}"
            )
            console.print(
                f"  Agency: {a_name} — {'personal perspective' if a == 0 else 'interpersonal' if a == 1 else 'system-wide'}"
            )
            ops = {0: ["τ+", "λ+", "κ+"], 1: ["τ-", "λ-", "κ-"], 2: ["ι"]}.get(
                sum([t, s, a]) % 3, []
            )
            console.print(f"  Recommended operators: {', '.join(ops)}")
        except Exception as _exc:
            logger.debug("swallowed exception: %s", _exc, exc_info=True)

    # Knowledge sources
    sources = getattr(record, "sources", [])
    if sources:
        console.print(f"\n[bold]Knowledge Sources ({len(sources)} papers):[/]")
        src_counts: dict[str, int] = {}
        for src in sources:
            src_name = src.get("source", "unknown") if isinstance(src, dict) else str(src)
            src_counts[src_name] = src_counts.get(src_name, 0) + 1
        for name, count in sorted(src_counts.items(), key=lambda x: -x[1])[:5]:
            console.print(f"  • {name}: {count} papers")

    # Quality Report reasoning
    qr = getattr(record, "quality_report", None)
    if qr:
        console.print("\n[bold]Quality Gate Reasoning:[/]")
        for gate in getattr(qr, "gates", []):
            if not gate.passed:
                console.print(f"  ⚠ {gate.step}: {gate.message}")
        if getattr(qr, "recommendations", []):
            console.print(f"  → {'; '.join(qr.recommendations)}")


def cmd_turbo(
    topic: str = typer.Argument(..., help="Research topic to discover"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    verify_backend: str = typer.Option("hybrid", "--verify-backend", help="Verification backend"),
    functors: bool = typer.Option(
        True, "--functors/--no-functors", help="Enable 9 cognitive functor agents"
    ),
    plugins: str | None = typer.Option(None, "--plugins", "-p", help="Comma-separated plugins"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show quality report"),
    competing: int = typer.Option(
        2, "--competing", help="Number of competing hypotheses (default 2)"
    ),
    no_iterative: bool = typer.Option(
        False, "--no-iterative", help="Skip iterative refinement loop"
    ),
    explain: bool = typer.Option(
        True,
        "--explain/--no-explain",
        "-e",
        help="Show explainability footer (C4 state, sources, reasoning)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview without executing (shows cost, time, model)"
    ),
) -> None:
    """Generate paradigm-shifting research proposal."""
    if dry_run:
        console.print("[bold yellow]DRY RUN — no execution[/]")
        console.print(f"  Topic: {topic[:60]}")
        console.print("  Pipeline: HILDiscoveryPipeline (7 phases A→G)")
        console.print(f"  Competing hypotheses: {competing}")
        console.print(f"  Iterative: {'yes' if not no_iterative else 'no'}")
        console.print(f"  Functors: {'on' if functors else 'off'}")
        console.print("  Estimated LLM calls: 3-5")
        console.print("  Estimated time: ~30s")
        console.print("  Estimated cost: ~$0.01 (DeepSeek)")
        console.print(
            f"  Would save to: {output or 'dissertations/live/blast_' + topic[:30].replace(' ', '_') + '.md'}"
        )
        console.print("\n[dim]Remove --dry-run to execute.[/]")
        return
    from src.core.profile_manager import UserProfileManager
    from src.pipeline.hil_pipeline import HILDiscoveryPipeline

    manager = UserProfileManager()
    user_profile = manager.load()
    config = manager.get_config()
    config.verification_backend = verify_backend
    config.enable_functors = functors

    console.print(f"[bold]BLAST turbo[/bold] — {get_mode_description('turbo')}")
    console.print(f"[dim]Topic:[/dim] {topic[:80]}...")
    console.print(
        f"[dim]User:[/dim] {user_profile.name} | {user_profile.affiliation or 'no affiliation'}"
    )

    # Auto-select plugins based on topic complexity + domain + mode
    if plugins is None or plugins == "auto":
        from src.plugins.unified_registry import select_plugins_for_problem

        selected = select_plugins_for_problem(topic, domain_hint="", auto_mode="turbo")
        console.print(f"[dim]Auto-plugins:[/dim] {selected}")
    else:
        selected = [p.strip() for p in plugins.split(",") if p.strip()]
        console.print(f"[dim]Manual plugins:[/dim] {selected}")

    async def _run() -> Any:
        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
        return await pipeline.discover(
            topic, competing_hypotheses=competing, no_iterative=no_iterative
        )

    record = asyncio.run(_run())

    if record.quality_report:
        console.print()
        console.print(f"[bold]{'=' * 60}[/bold]")
        console.print(
            f"[bold cyan]Quality Report: {record.quality_report.grade} (Score: {record.quality_report.overall_score}/100)[/bold cyan]"
        )
        console.print(f"[bold]{'=' * 60}[/bold]")
        for gate in record.quality_report.gates:
            status = "✅" if gate.passed else "⚠️"
            color = "green" if gate.passed else "yellow"
            console.print(
                f"  [{color}]{status}[/{color}] {gate.step:12s} | score={gate.score:.2f} | {gate.message}"
            )
        if record.quality_report.recommendations:
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for r in record.quality_report.recommendations:
                console.print(f"  • {r}")

    from src.publishing.dissertation import _sanitize_filename

    hil_fname = _sanitize_filename(f"HIL_v2_{topic.replace(' ', '_')[:30]}.md")
    hil_path = Path("dissertations/live") / hil_fname
    out_path = (
        output or f"dissertations/live/blast_{_sanitize_filename(topic.replace(' ', '_')[:30])}.md"
    )
    if hil_path.is_file():
        text = hil_path.read_text(encoding="utf-8")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(text, encoding="utf-8")
        console.print(f"\n[green]Dissertation saved:[/green] {out_path}")
    else:
        console.print(f"\n[yellow]Dissertation not found at {hil_path}[/yellow]")

    if explain:
        _print_explain_report(record, topic)

    # ── Mascot ──────────────────────────────────────────────────────
    from src.cli.cube_mascot import inject_mascot_status

    console.print()
    console.print(
        inject_mascot_status(
            mode="turbo",
            state="done",
            sources=len(record.sources),
            confidence=record.quality_report.overall_score / 100 if record.quality_report else 0,
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Mode C: blast flash — Quick Answers
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_flash(
    question: str = typer.Argument(..., help="Question to answer quickly"),
    with_sources: bool = typer.Option(False, "--sources", "-s", help="Include source citations"),
    deep: bool = typer.Option(
        False, "--deep", "-d", help="Deep flash: multi-source search + quality check"
    ),
    format: str = typer.Option(
        "concise", "--format", "-f", help="Output format: concise|detailed|bullet|code"
    ),
) -> None:
    """Get a quick answer (no pipeline, just fast LLM + optional web search)."""
    from src.llm.gateway import get_gateway
    from src.pipeline.config import PipelineConfig
    from src.pipeline.quality import QualityGates

    console.print(f"[bold]BLAST flash[/bold] — {get_mode_description('flash')}")
    console.print(
        f"[dim]Format:[/dim] {format} | [dim]Sources:[/dim] {'yes' if with_sources else 'no'} | [dim]Deep:[/dim] {'yes' if deep else 'no'}"
    )

    async def _run() -> dict[str, Any]:
        llm = get_gateway()
        context = ""
        sources = []
        quality_score = 0
        usp_context: dict[str, Any] = {}

        # ═══════════════════════════════════════════════════════════════════
        # USP Cognitive Components (deep mode)
        # ═══════════════════════════════════════════════════════════════════
        if deep:
            from src.c4.engine import C4Space
            from src.core.cdi_engine import CDIEngine
            from src.metamodels.impact import ImpactEngine
            from src.metamodels.matrix_dream import MatrixDreamLibrary
            from src.metamodels.mp.library import MPLibrary
            from src.metamodels.mp.profiles import MPRotationEngine
            from src.metamodels.qzrf.operators import QzrfLibrary
            from src.metamodels.tote import ToteEngine

            console.print("[dim]Running USP cognitive components...[/dim]")

            # IMPACT
            try:
                impact = ImpactEngine()
                impact_result = impact.identify(question)  # type: ignore[attr-defined]
                impact_mapped = impact.map(impact_result)  # type: ignore[attr-defined]
                usp_context["impact"] = (
                    f"{len(impact_mapped.get('entities', []))} entities, {len(impact_mapped.get('stakeholders', []))} stakeholders"
                )
                console.print(f"  [dim]IMPACT: {usp_context['impact']}[/dim]")
            except Exception as e:
                logger.debug("IMPACT failed: %s", e)

            # C4 Fingerprint
            try:
                c4_space = C4Space()
                c4_state = c4_space.fingerprint(question)  # type: ignore[attr-defined]
                usp_context["c4_state"] = str(c4_state)
                console.print(f"  [dim]C4 Fingerprint: {c4_state}[/dim]")
            except Exception as e:
                logger.debug("C4 fingerprint failed: %s", e)
                c4_state = "unknown"

            # MP Rotation
            try:
                mp_lib = MPLibrary()
                mp_rotation = MPRotationEngine(mp_lib)
                perspectives = mp_rotation.rotate(question, state=str(c4_state))  # type: ignore[attr-defined]
                usp_context["perspectives"] = [p.get("name", "") for p in perspectives[:3]]
                console.print(f"  [dim]MP Rotation: {len(perspectives)} perspectives[/dim]")
            except Exception as e:
                logger.debug("MP rotation failed: %s", e)

            # QZRF Select
            try:
                qzrf = QzrfLibrary()
                operators = qzrf.select(str(c4_state))  # type: ignore[attr-defined]
                usp_context["qzrf"] = operators[:5]
                console.print(f"  [dim]QZRF: {', '.join(operators[:3])}[/dim]")
            except Exception as e:
                logger.debug("QZRF failed: %s", e)

            # MatrixDream
            try:
                matrix = MatrixDreamLibrary()
                patterns = matrix.match(question)
                usp_context["patterns"] = [p[0].id for p in patterns[:3]]
                console.print(f"  [dim]MatrixDream: {len(patterns)} patterns[/dim]")
            except Exception as e:
                logger.debug("MatrixDream failed: %s", e)

            # CDI Analysis
            try:
                cdi = CDIEngine()
                cdi_result = cdi.analyze(question, context={"c4_state": str(c4_state)})  # type: ignore[attr-defined]
                contradictions = cdi_result.get("contradictions", [])
                usp_context["contradictions"] = len(contradictions)
                console.print(f"  [dim]CDI: {len(contradictions)} contradictions[/dim]")
            except Exception as e:
                logger.debug("CDI failed: %s", e)

            # TOTE Validation (on empty solution for now — just get framework)
            try:
                tote = ToteEngine()
                tote_result = tote.validate(question)  # type: ignore[attr-defined]
                usp_context["tote_status"] = tote_result.get("status", "unknown")
                console.print(f"  [dim]TOTE: {usp_context['tote_status']}[/dim]")
            except Exception as e:
                logger.debug("TOTE failed: %s", e)

        # ═══════════════════════════════════════════════════════════════════
        # Source gathering
        # ═══════════════════════════════════════════════════════════════════
        if deep or with_sources:
            console.print("[dim]Searching multi-source knowledge base...[/dim]")
            from src.knowledge.flash_sources import gather_flash_sources

            try:
                papers, context = await gather_flash_sources(question, deep=deep, include_web=True)
                sources = papers
                console.print(f"[dim]Found {len(papers)} papers[/dim]")
                if not papers:
                    console.print(
                        "[yellow]No papers found — check API keys "
                        "(TAVILY_API_KEY helps for web)[/yellow]"
                    )
            except Exception as e:
                console.print(f"[yellow]Multi-source search failed: {e}[/yellow]")
                sources = []
                context = ""

        # ═══════════════════════════════════════════════════════════════════
        # Build enriched prompt with USP context
        # ═══════════════════════════════════════════════════════════════════
        usp_section = ""
        if usp_context:
            usp_section = f"""
Cognitive Analysis Context:
- C4 State: {usp_context.get("c4_state", "N/A")}
- IMPACT: {usp_context.get("impact", "N/A")}
- Perspectives: {", ".join(usp_context.get("perspectives", []))}
- QZRF Operators: {", ".join(usp_context.get("qzrf", []))}
- Patterns: {", ".join(usp_context.get("patterns", []))}
- Contradictions: {usp_context.get("contradictions", "N/A")}
- TOTE: {usp_context.get("tote_status", "N/A")}
"""

        format_instructions = {
            "concise": "Answer in 2-4 sentences. Be direct and specific.",
            "detailed": "Provide a thorough explanation with examples where helpful.",
            "bullet": "Answer using bullet points. Each point should be atomic and clear.",
            "code": "If the answer involves code, provide a clean working example. Explain briefly after the code block.",
        }.get(format, "Answer concisely and accurately.")

        prompt = f"""{format_instructions}

Use the following context if relevant:
{context}
{usp_section}

Question: {question}

Answer:"""

        answer = await llm.chat(
            [{"role": "user", "content": prompt}],
            max_tokens=1200 if deep else 800,
            temperature=0.3,
        )

        # Quick quality check for deep mode
        if deep and sources:
            config = PipelineConfig(name="default")
            qg = QualityGates(config)
            gate = qg.check_sources(sources)
            quality_score = int(gate.score * 100)

        return {
            "answer": answer,
            "sources": sources,
            "quality_score": quality_score,
            "context_length": len(context),
            "usp_context": usp_context,
        }

    result = asyncio.run(_run())
    answer = result["answer"]
    sources = result["sources"]
    quality_score = result["quality_score"]

    # Output formatting
    console.print(f"\n[bold]Answer:[/bold]\n{answer}")

    if sources:
        console.print("\n[bold]Sources:[/bold]")
        for i, s in enumerate(sources[:5], 1):
            title = s.get("title", "Untitled")
            url = s.get("url", "")
            source_name = s.get("_source", s.get("source_engine", "web"))
            if url:
                console.print(f"  {i}. [{source_name}] {title[:60]}")
                console.print(f"     [dim]{url}[/dim]")
            else:
                console.print(f"  {i}. [{source_name}] {title[:60]}")

    # Display USP cognitive context in deep mode
    usp_context = result.get("usp_context", {})
    if deep and usp_context:
        console.print("\n[bold]Cognitive Analysis:[/bold]")
        if usp_context.get("c4_state"):
            console.print(f"  [dim]C4 State:[/dim] {usp_context['c4_state']}")
        if usp_context.get("impact"):
            console.print(f"  [dim]IMPACT:[/dim] {usp_context['impact']}")
        if usp_context.get("perspectives"):
            console.print(f"  [dim]Perspectives:[/dim] {', '.join(usp_context['perspectives'])}")
        if usp_context.get("qzrf"):
            console.print(f"  [dim]QZRF:[/dim] {', '.join(usp_context['qzrf'][:3])}")
        if usp_context.get("patterns"):
            console.print(f"  [dim]Patterns:[/dim] {', '.join(usp_context['patterns'][:3])}")
        if usp_context.get("contradictions") is not None:
            console.print(f"  [dim]Contradictions:[/dim] {usp_context['contradictions']}")

    if deep and quality_score > 0:
        color = "green" if quality_score >= 80 else "yellow" if quality_score >= 60 else "red"
        console.print(f"\n[bold]Quality Score:[/bold] [{color}]{quality_score}/100[/{color}]")

    # ── Mascot ──────────────────────────────────────────────────────
    from src.cli.cube_mascot import inject_mascot_status

    console.print()
    console.print(inject_mascot_status(mode="flash", state="done", sources=len(sources)))


# ═══════════════════════════════════════════════════════════════════════════════
# Mode D: blast turbofactory — Parallel Paradigm Factory
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_MAP = {
    "mini": 5,
    "standard": 10,
    "mega": 25,
    "giga": 100,
}


def cmd_turbofactory(
    domain: str = typer.Argument(..., help="Domain or problem to research in depth"),
    scale: str = typer.Option(
        "standard", "--scale", "-s", help="Scale: mini(5)|standard(10)|mega(25)|giga(100)"
    ),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    max_concurrent: int = typer.Option(
        5, "--max-concurrent", "-c", help="Max concurrent pipelines"
    ),
    pipeline_mode: str = typer.Option(
        "mixed", "--pipeline", "-p", help="Pipeline mode: solve|turbo|mixed"
    ),
) -> None:
    """Run parallel paradigm factory (10-100 pipelines) for ultimate domain reports.

    Each agent runs either UniversalSolvePipeline (solve), HILDiscoveryPipeline (turbo),
    or both (mixed) on a sub-problem, then results are synthesized.
    """
    from src.agents.pipeline import UniversalSolvePipeline
    from src.core.profile_manager import UserProfileManager
    from src.llm.gateway import get_gateway
    from src.pipeline.hil_pipeline import HILDiscoveryPipeline

    n_pipelines = SCALE_MAP.get(scale, 10)
    console.print(f"[bold]BLAST turbofactory[/bold] — {get_mode_description('turbofactory')}")
    console.print(f"[dim]Domain:[/dim] {domain}")
    console.print(
        f"[dim]Scale:[/dim] {scale} ({n_pipelines} pipelines, max {max_concurrent} concurrent)"
    )
    console.print(f"[dim]Pipeline mode:[/dim] {pipeline_mode}")

    manager = UserProfileManager()
    user_profile = manager.load()
    config = manager.get_config()

    async def _generate_subproblems(domain: str, n: int) -> list[str]:
        """Generate N distinct sub-problems for parallel research."""
        llm = get_gateway()
        prompt = f"""Given the domain "{domain}", generate {n} distinct, specific research sub-problems.
Each sub-problem should explore a different angle or facet of the domain.
Make them specific enough for scientific research but distinct from each other.

Format as a numbered list (1., 2., 3., etc.). Each item should be a single concise sentence.

Sub-problems:"""
        response = await llm.generate(prompt, max_tokens=1200, temperature=0.8)
        text = response.content
        import re

        problems = []
        for line in text.split("\n"):
            m = re.match(r"^\s*\d+[\.\)]\s*(.+)", line.strip())
            if m and len(m.group(1)) > 10:
                problems.append(m.group(1).strip())
        # Ensure exact count
        while len(problems) < n:
            problems.append(f"{domain} — aspect {len(problems) + 1}")
        return problems[:n]

    async def _run_single_pipeline(
        topic: str, sem: asyncio.Semaphore, use_solve: bool = False, use_turbo: bool = True
    ) -> dict[str, Any]:
        """Run one pipeline (solve or turbo or both) with semaphore-controlled concurrency."""
        async with sem:
            result: dict[str, Any] = {
                "topic": topic,
                "status": "success",
                "pipeline_used": [],
                "solve_result": None,
                "turbo_result": None,
            }
            child_partial = False

            if use_solve:
                try:
                    solve_pipeline = UniversalSolvePipeline()
                    solve_record = await solve_pipeline.solve(topic, mode="autopilot")
                    conf = float(getattr(solve_record, "confidence", 0) or 0)
                    result["solve_result"] = {
                        "final_solution": solve_record.final_solution[:500],
                        "confidence": conf,
                        "sources": len(getattr(solve_record, "sources", [])),
                        "gaps": len(getattr(solve_record, "gaps", [])),
                        "quality_report": getattr(solve_record, "quality_report", None),
                    }
                    result["pipeline_used"].append("solve")
                    if conf < 0.3:
                        child_partial = True
                except Exception as e:
                    logger.warning("Solve pipeline failed for '%s': %s", topic, e)
                    result["solve_result"] = {"error": str(e)}

            if use_turbo:
                try:
                    turbo_pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
                    turbo_record = await turbo_pipeline.discover(topic)
                    qscore = (
                        turbo_record.quality_report.overall_score
                        if turbo_record.quality_report
                        else 0
                    )
                    sim_raw = turbo_record.simulation
                    sim_st = record_field_status(sim_raw)
                    result["turbo_result"] = {
                        "hypotheses": len(turbo_record.hypotheses),
                        "sources": len(turbo_record.sources),
                        "quality_grade": turbo_record.quality_report.grade
                        if turbo_record.quality_report
                        else "N/A",
                        "quality_score": qscore,
                        "gaps": [g.get("area", "") for g in turbo_record.gaps[:3]],
                        "simulation": sim_st,
                        "verification": record_field_status(turbo_record.verification),
                    }
                    result["pipeline_used"].append("turbo")
                    child_st = outer_status_from_hil_like(
                        quality_passed_all=(
                            bool(turbo_record.quality_report.passed_all)
                            if turbo_record.quality_report
                            else None
                        ),
                        quality_score=qscore,
                        sim_status=str(sim_st),
                    )
                    if child_st != "success":
                        child_partial = True
                except Exception as e:
                    logger.warning("Turbo pipeline failed for '%s': %s", topic, e)
                    result["turbo_result"] = {"error": str(e)}

            if not result["pipeline_used"]:
                result["status"] = "error"
                result["error"] = "Both pipelines failed"
            elif (
                child_partial
                or (result.get("solve_result") or {}).get("error")
                or (result.get("turbo_result") or {}).get("error")
            ):
                solve_err = (result.get("solve_result") or {}).get("error")
                turbo_err = (result.get("turbo_result") or {}).get("error")
                if result["pipeline_used"] and solve_err and turbo_err:
                    result["status"] = "error"
                else:
                    result["status"] = "partial"

            return result

    async def _run() -> None:
        # Generate sub-problems
        console.print("\n[dim]Generating sub-problems...[/dim]")
        subproblems = await _generate_subproblems(domain, n_pipelines)
        for i, sp in enumerate(subproblems, 1):
            console.print(f"  {i}. {sp[:70]}...")

        # Run pipelines in parallel with semaphore
        console.print(f"\n[dim]Running {n_pipelines} pipelines ({pipeline_mode} mode)...[/dim]")
        sem = asyncio.Semaphore(max_concurrent)
        use_solve = pipeline_mode in ("solve", "mixed")
        use_turbo = pipeline_mode in ("turbo", "mixed")
        tasks = [
            _run_single_pipeline(sp, sem, use_solve=use_solve, use_turbo=use_turbo)
            for sp in subproblems
        ]

        completed = 0
        results = []
        for coro in asyncio.as_completed(tasks):
            res = await coro
            results.append(res)
            completed += 1
            status_icon = (
                "[green]✓[/green]"
                if res["status"] == "success"
                else "[yellow]~[/yellow]"
                if res["status"] == "partial"
                else "[red]✗[/red]"
            )
            console.print(f"  {status_icon} [{completed}/{n_pipelines}] {res['topic'][:50]}...")

        # Synthesis
        console.print("\n[dim]Synthesizing results...[/dim]")
        successful = [r for r in results if r["status"] == "success"]
        partial = [r for r in results if r["status"] == "partial"]
        failed = [r for r in results if r["status"] == "error"]

        # Aggregate turbo results (include partial — ran but weak gates)
        scored_pool = successful + partial
        total_hypotheses = sum(r.get("turbo_result", {}).get("hypotheses", 0) for r in scored_pool)
        total_sources = sum(r.get("turbo_result", {}).get("sources", 0) for r in scored_pool)
        avg_quality = sum(
            r.get("turbo_result", {}).get("quality_score", 0) for r in scored_pool
        ) / max(len(scored_pool), 1)

        # Aggregate solve results
        solve_successful = [r for r in successful if "solve" in r.get("pipeline_used", [])]
        avg_solve_confidence = sum(
            r.get("solve_result", {}).get("confidence", 0) for r in solve_successful
        ) / max(len(solve_successful), 1)

        # Build ultimate report
        report = f"""# Turbofactory Report: {domain}

**Scale:** {scale} ({n_pipelines} pipelines, {pipeline_mode} mode)
**Successful:** {len(successful)}/{n_pipelines}
**Partial:** {len(partial)}/{n_pipelines}
**Failed:** {len(failed)}/{n_pipelines}
**Total Hypotheses:** {total_hypotheses}
**Total Sources:** {total_sources}
**Average Quality Score:** {avg_quality:.1f}/100
**Average Solve Confidence:** {avg_solve_confidence:.2f}

---

## Sub-Problems Researched

"""
        for r in results:
            status = (
                "✅" if r["status"] == "success" else "🟡" if r["status"] == "partial" else "❌"
            )
            pipelines = ", ".join(r.get("pipeline_used", []))
            report += f"- {status} **{r['topic']}** — pipelines: {pipelines}"
            if r.get("turbo_result"):
                report += f" | {r['turbo_result'].get('hypotheses', 0)} hypotheses, {r['turbo_result'].get('quality_grade', 'N/A')} quality"
            report += "\n"

        report += "\n## Key Research Gaps (from turbo pipelines)\n\n"
        seen_gaps = set()
        for r in scored_pool:
            turbo = r.get("turbo_result", {})
            for gap in turbo.get("gaps", []):
                if gap and gap not in seen_gaps:
                    seen_gaps.add(gap)
                    report += f"- {gap}\n"

        if solve_successful:
            report += "\n## Strategic Artifacts (from solve pipelines)\n\n"
            for r in solve_successful:
                solve = r.get("solve_result", {})
                report += f"### {r['topic']}\n"
                report += f"- Confidence: {solve.get('confidence', 0):.2f}\n"
                report += f"- Sources: {solve.get('sources', 0)} | Gaps: {solve.get('gaps', 0)}\n"
                if solve.get("quality_report"):
                    qr = solve["quality_report"]
                    report += (
                        f"- Quality: {qr.get('grade', 'N/A')} ({qr.get('overall_score', 0)}/100)\n"
                    )
                report += "\n"

        report += """

## Quality Distribution (turbo)

| Grade | Count |
|-------|-------|
"""
        from collections import Counter

        grades = Counter(
            [r.get("turbo_result", {}).get("quality_grade", "N/A") for r in scored_pool]
        )
        for grade, count in grades.most_common():
            report += f"| {grade} | {count} |\n"

        if failed:
            report += "\n## Failed Pipelines\n\n"
            for r in failed:
                report += f"- {r['topic']}: {r.get('error', 'Unknown error')[:100]}\n"

        report += f"""

---

 *Generated by c4reqber Turbofactory v5.3.0 — {len(successful)} parallel research pipelines*
"""

        # Save report with unique subdirectory to avoid race conditions
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = (
            output or f"dissertations/live/{domain.replace(' ', '_')[:20]}/turbofactory_{ts}.md"
        )
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(report, encoding="utf-8")

        console.print("\n[bold green]Turbofactory complete![/bold green]")
        console.print(f"[green]Report saved:[/green] {out_path}")
        console.print(f"[dim]Successful pipelines:[/dim] {len(successful)}/{n_pipelines}")
        console.print(f"[dim]Total hypotheses:[/dim] {total_hypotheses}")
        console.print(f"[dim]Average quality:[/dim] {avg_quality:.1f}/100")

    asyncio.run(_run())

    # ── Mascot ──────────────────────────────────────────────────────
    from src.cli.cube_mascot import inject_mascot_status

    console.print()
    console.print(inject_mascot_status(mode="turbofactory", state="done", sources=0))


# ═══════════════════════════════════════════════════════════════════════════════
# Auto-dispatch (mode not specified)
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_auto(query: str) -> None:
    """Auto-dispatch to best mode based on query characteristics."""
    mode = auto_route(query)
    console.print(f"[dim]Auto-routed to:[/dim] [bold]{mode}[/bold] mode")
    console.print()

    if mode == "solve":
        cmd_solve(
            problem=query,
            mode="autopilot",
            output_format="auto",
            domain=None,
            output=None,
            verbose=False,
        )
    elif mode == "turbo":
        cmd_turbo(
            topic=query,
            output=None,
            verify_backend="hybrid",
            functors=True,
            plugins=None,
            verbose=False,
            competing=2,
            no_iterative=False,
        )
    elif mode == "flash":
        cmd_flash(question=query, with_sources=False, deep=False, format="concise")
    elif mode == "turbofactory":
        cmd_turbofactory(
            domain=query, scale="standard", output=None, max_concurrent=5, pipeline_mode="mixed"
        )
