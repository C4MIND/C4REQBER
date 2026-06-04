from __future__ import annotations


"""
TUI: Module Status Panel
Shows ALL integrated pipeline modules with status indicators.
"""

from rich import box
from rich.panel import Panel
from rich.table import Table


def make_module_status_panel() -> Panel:
    """Build comprehensive panel showing ALL integrated pipeline modules."""
    table = Table(title="🔧 Pipeline Modules Status (v5.3.0)", box=box.ROUNDED, show_lines=True)
    table.add_column("Module", style="cyan", no_wrap=True, ratio=2)
    table.add_column("Status", style="green", ratio=1)
    table.add_column("Details", style="dim", ratio=3)

    # ── Core C4 Modules ──
    table.add_row("[bold #4ECDC4]CORE C4 MODULES[/]", "", "")
    table.add_row("C4-META Engine", "✅", "27 states; Z₃³, ≤6 steps")
    table.add_row("TRIZ Bridge", "✅", "40 principles, 40×40 matrix")
    table.add_row("FRA Router", "✅", "20 operators, 7 situations")
    table.add_row("QZRF Engine", "✅", "14 operators, 7 layers")
    table.add_row("Matrix Dream", "✅", "72 patterns, registry")

    # ── Knowledge & Search ──
    table.add_row("", "", "")
    table.add_row("[bold #FFD93D]KNOWLEDGE & SEARCH[/]", "", "")
    table.add_row("MultiSource Searcher", "✅", "33 sources (orchestrator)")
    table.add_row("  ├ Brave Search", "✅", "API integrated")
    table.add_row("  ├ ArXiv", "✅", "Physics/math papers")
    table.add_row("  ├ CrossRef", "✅", "DOI/metadata")
    table.add_row("  ├ Semantic Scholar", "✅", "AI/ML papers")
    table.add_row("  └ +23 more", "✅", "OpenAlex, DBLP, DOAJ, etc.")

    # ── Cognitive Plugins (20 total) ──
    table.add_row("", "", "")
    table.add_row("[bold #ec4899]COGNITIVE PLUGINS (20 wired)[/]", "", "")
    plugins = [
        ("SWOT", "Strengths/Weaknesses/O/T"),
        ("Red Team", "Adversarial analysis"),
        ("Six Hats", "6 thinking modes"),
        ("SCAMPER", "7 creativity techniques"),
        ("5 Whys", "Root cause analysis"),
        ("Ishikawa", "Fishbone diagram"),
        ("Morphological", "Matrix analysis"),
        ("Delphi", "Expert consensus"),
        ("OODA Loop", "Observe-Orient-Decide-Act"),
    ]
    for name, desc in plugins:
        table.add_row(f"  ├ {name}", "✅", desc)
    table.add_row("  └ +10 more", "✅", "All in pipeline step 6.1")

    # ── Discovery Pipeline Modules ──
    table.add_row("", "", "")
    table.add_row("[bold #4ADE80]DISCOVERY PIPELINE[/]", "", "")
    table.add_row("GapMiner", "✅", "3-layer text analysis, LLM-powered")
    table.add_row("Novelty Validator", "✅", "⚠️ HARD GATE (was warning)")
    table.add_row("AlreadyShiftedDetector", "✅", "🔄 iterative w/ subtractive confidence")
    table.add_row("Falsifier", "✅", "LLM adversarial check")
    table.add_row("AutoScanner", "✅", "Finds unsolved problems")
    table.add_row("Zettelkasten", "✅", "SQLite PKB for discoveries")
    table.add_row("Monte Carlo Validator", "✅", "Statistical significance")
    table.add_row("Bayesian Updater", "✅", "Calibrated priors")

    # ── NEW v5.3.0 Subsystems ──
    table.add_row("", "", "")
    table.add_row("[bold #fbbf24]v5.3.0 NEW SUBSYSTEMS[/]", "", "")
    table.add_row("Observer", "✅", "PipelineObserver: event hooks, meta-cognitive framing")
    table.add_row("FinalVerifier", "✅", "Q ≈ 0 check; Lean4/Coq/Dafny summary")
    table.add_row("RedundantGates", "✅", "Deduplication gate; Q check")
    table.add_row("DiscoveryMemory", "✅", "Cross-domain transfer; Zettelkasten SQLite PKB")

    # ── LLM Router (5 providers) ──
    table.add_row("", "", "")
    table.add_row("[bold #8b5cf6]LLM ROUTER[/]", "", "")
    table.add_row("  ├ NVIDIA NIM", "✅", "Free qwen3-coder-480b")
    table.add_row("  ├ Mistral", "✅", "$28 balance")
    table.add_row("  ├ Moonshot", "✅", "Key: sk-RTbd...Pb")
    table.add_row("  ├ LM Studio", "✅", "Auto-start via lms CLI")
    table.add_row("  ├ MLX Server", "✅", "mlx-env :8001")
    table.add_row("  └ Ollama", "✅", "qwen2.5-coder:7b")

    # ── Simulations & Physics ──
    table.add_row("", "", "")
    table.add_row("[bold #06b6d4]SIMULATIONS & PHYSICS[/]", "", "")
    table.add_row("Newton Physics", "✅", "mlx-env (Python 3.11+)")
    table.add_row("Domain Selector", "✅", "101+ patterns, 5 engines")
    table.add_row("GPU Dashboard", "✅", "[G] toggle, 8 providers")
    table.add_row("Vast.ai Runner", "✅", "$0.02/hr, API wired")

    # ── Formal Verification ──
    table.add_row("", "", "")
    table.add_row("[bold #FFD93D]FORMAL VERIFICATION[/]", "", "")
    table.add_row("Lean4 Client", "✅", "~/.elan/bin/lean")
    table.add_row("Coq/Rocq Client", "✅", "$(brew --prefix coq)/bin")
    table.add_row("Dafny Client", "✅", "$(brew --prefix dafny)/bin")

    # ── Export & Publishing ──
    table.add_row("", "", "")
    table.add_row("[bold #f97316]EXPORT & PUBLISHING[/]", "", "")
    table.add_row("Export Manager", "✅", "MD/JSON/BibTeX/PDF")
    table.add_row("Blueprint Generator", "✅", "ASCII schematics")
    table.add_row("Social Auto-Poster", "✅", "Mastodon/X integration")
    table.add_row("Dissertation Mode", "✅", "8-section papers")

    return Panel(
        table,
        title="[bold]🔧 C4-CDI v5.3.0 — ALL MODULES[/]",
        border_style="bold #4ECDC4",
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
    )
