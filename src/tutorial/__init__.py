"""
TUI Tutorial — Interactive Student Tutorial
Step-by-step interactive tutorial for beginners to learn Reqber.
"""
import sys
import time
from typing import List, Tuple

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


console = Console()

TUTORIAL_STEPS: list[tuple[str, str]] = [
    (
        "Welcome to Reqber! 🚀",
        "[bold #4ECDC4]This is a cognitive exoskeleton for scientific discovery.[/]\n\n"
        "You will learn:\n"
        "  1. C4 Navigation\n"
        "  2. Knowledge Search\n"
        "  3. TRIZ Principles\n"
        "  4. Hypothesis Generation\n"
        "  5. Verification & Export."
    ),
    (
        "Step 1: C4 Navigation (Z₃³ Cube)",
        "[bold #4ECDC4]The C4-META framework has 27 cognitive states arranged in a 3×3×3 cube.[/]\n\n"
        "Key states:\n"
        "  • (0,0,0) origin — Beginning of cognition\n"
        "  • (2,1,2) insight — Discovery moment\n"
        "  • (2,2,2) emerge — Emergence\n\n"
        "Try: Press Tab to switch modes (discover/invent/transform)\n"
        "Note: The cube reacts to your content! 🎨"
    ),
    (
        "Step 2: Knowledge Search (27 sources)",
        "[bold #4ECDC4]Reqber searches across 27 academic and web sources:[/]\n\n"
        "Sources:\n"
        "  • arXiv — Physics/math papers\n"
        "  • PubMed — Biomedical\n"
        "  • Semantic Scholar — AI/ML\n"
        "  • ScholarAPI — Millions of papers (key configured! ✅)\n"
        "  • OpenAlex, CrossRef, CORE, and more...\n\n"
        "Try: [bold]c44tcdi solve \"quantum computing\"[/]"
    ),
    (
        "Step 3: TRIZ Principles",
        "[bold #4ECDC4]TRIZ provides 40 inventive principles for problem-solving.[/]\n\n"
        "Example: If you need to improve a device, use:\n"
        "  • Principle 7: Nesting — Place one object inside another\n"
        "  • Principle 24: Mediator — Use an intermediate object\n"
        "  • Principle 35: Parameter changes — Change temperature, volume, etc.\n\n"
        "The system auto-selects relevant principles!"
    ),
    (
        "Step 4: Hypothesis Generation",
        "[bold #4ECDC4]After searching knowledge, the system generates a hypothesis.[/]\n\n"
        "Example output:\n"
        '[bold]"Based on 26 papers and 3 isomorphisms, we propose..."[/]\n\n'
        "The hypothesis is verified using formal methods (Lean4, Coq, Dafny, Agda)."
    ),
    (
        "Step 5: Verification & Export",
        "[bold #4ECDC4]Verification backends check your hypothesis:[/]\n\n"
        "  • Lean4 — Interactive theorem prover ✅\n"
        "  • Coq/Rocq — Formal proof assistant ✅\n"
        "  • Dafny — Verification-aware programming ✅\n\n"
        "Export in 5 formats: LaTeX, Markdown, JSON, HTML, Text, PDF!"
    ),
    (
        "Congratulations! 🎊",
        "[bold #4ADE80]You now understand the basics of Reqber![/]\n\n"
        "Next steps:\n"
        "  1. Try [bold]c44tcdi tui[/] for full interactive mode\n"
        "  2. Run [bold]c44tcdi solve \"your problem\"[/]\n"
        "  3. Read USER_JOURNEY_REPORT.md for full audit\n"
        "  4. Check README.md for detailed documentation\n\n"
        "Happy discoveries! 🚀"
    ),
]


def run_tutorial() -> None:
    """Run the interactive tutorial."""
    console.clear()

    # Welcome animation
    for i in range(3):
        console.clear()
        console.print(f"[bold #4ECDC4]Loading tutorial{'.' * (i % 4)}[/]")
        time.sleep(0.3)

    for step_idx, (title, content) in enumerate(TUTORIAL_STEPS):
        console.clear()

        # Progress bar
        progress = "█" * (step_idx + 1) + "░" * (len(TUTORIAL_STEPS) - (step_idx + 1))
        progress_text = f"[dim]Step {step_idx + 1}/{len(TUTORIAL_STEPS)}:[/] [bold #4ECDC4]{progress}[/]"

        panel = Panel(
            Text.from_markup(f"[bold #4ECDC4]{title}[/]\n\n{content}"),
            title=progress_text,
            border_style="bold #4ECDC4",
            box=ROUNDED,
            padding=(1, 2),
        )
        console.print(panel)

        if step_idx < len(TUTORIAL_STEPS) - 1:
            console.print("\n[dim]Press Enter to continue, 'q' to quit...[/]")
            try:
                user_input = input()
                if user_input.lower() in ('q', 'quit', 'exit'):
                    console.clear()
                    console.print("[dim]Tutorial exited. Try [bold]c44tcdi tui[/] for interactive mode![/]")
                    return
            except (EOFError, KeyboardInterrupt):
                break
        else:
            # Last step — wait for any key
            console.print("\n[dim]Press Enter to finish...[/]")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass

    console.clear()
    console.print("[bold #4ADE80]✅ Tutorial completed![/]")
    console.print("\nTry: [bold]c44tcdi tui[/] — Interactive TUI with ASCII cube 🚀\n")


if __name__ == "__main__":
    run_tutorial()
