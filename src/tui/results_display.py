from __future__ import annotations

from rich import box
from rich.align import Align


"""
TUI: Results Display
Input area, story messages, progress bar, results panel.
"""

_SPINNER_CHARS = ["◐", "◓", "◑", "◒"]
_spinner_chars = _SPINNER_CHARS
_spinner_frame = 0
STEP_ICONS = ["🔍", "📚", "🔬", "💡", "🧪", "✅", "📊", "📝", "🎯", "🏆"]

def _transition_color(step: int) -> str:
    colors = ["#4ECDC4", "#4ECDC4", "#FFE66D", "#FF6B6B"]
    return colors[min(step // 3, 3)]

def tron_glow_panel(content, title="", border_color="#4ECDC4"):
    from rich import box
    from rich.panel import Panel
    return Panel(content, title=title, border_style=border_color, box=box.ROUNDED, padding=(1, 2))

def make_operator_panel():
    from rich.panel import Panel
    from rich.text import Text
    return Panel(Text("Operators loaded"), title="[bold]⚙️ Operators[/]", border_style="#4ECDC4")


from rich.panel import Panel
from rich.text import Text


def make_input_area(t, problem: str, hacker: bool = False) -> Panel:
    """Problem input area."""
    if problem:
        problem_text = Text(problem, style="bold #4ECDC4")
    else:
        problem_text = Text(t("input_placeholder"), style="dim italic")

    if hacker:
        return tron_glow_panel(problem_text, title=f"[bold]{t('input_title')}[/]", border_color="#4ECDC4")

    return Panel(
        problem_text,
        title=f"[bold]{t('input_title')}[/]",
        border_style="#4ECDC4",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def make_story_messages(t, messages: list, current_step: int, running: bool, hacker: bool = False, all_glow=None, completion_flash=False) -> Panel:
    """Story-driven messages from pipeline."""
    if not messages:
        msg = Text(t("narrative_wait"), style="dim italic")
        if hacker:
            return tron_glow_panel(msg, title=f"[bold]{t('narrative_title')}[/]", border_color="#4ECDC4")
        return Panel(
            msg,
            title=f"[bold]{t('narrative_title')}[/]",
            border_style="#4ECDC4",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    story_text = Text()
    for idx, (title, msg) in enumerate(messages[-5:]):
        icon = STEP_ICONS[min(current_step - len(messages[-5:]) + idx, len(STEP_ICONS) - 1)] if current_step > 0 else "🧠"
        story_text.append(f"{icon} {title}\n", style="bold #4ECDC4")
        story_text.append(f"  {msg}\n\n", style="dim")

    border_clr = _transition_color(current_step) if current_step > 0 else "#4ECDC4"
    if hacker:
        return tron_glow_panel(story_text, title=f"[bold]{t('narrative_title')}[/]", border_color=border_clr)

    return Panel(
        story_text,
        title=f"[bold]{t('narrative_title')}[/]",
        border_style=border_clr,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def make_progress(current_step: int, total_steps: int, running: bool, hacker: bool = False, spinner_frame: int = 0) -> Panel:
    """Progress bar with half-block graphics (█▀) and spinner."""
    global _spinner_frame
    if current_step == 0:
        if running:
            spin = _spinner_chars[_spinner_frame % 4]
            bar = f"[bold #4ECDC4]{spin}[/] Initializing..."
            return Panel(Align.center(Text.from_markup(bar)), box=box.SIMPLE, border_style=_transition_color(1), padding=(0, 1))
        return Panel("", box=box.SIMPLE)

    _spinner_frame += 1

    total_units = total_steps * 2
    filled_units = current_step * 2

    bar_chars = ""
    for i in range(total_steps):
        remaining = filled_units - i * 2
        if remaining >= 2:
            bar_chars += "█"
        elif remaining >= 1:
            bar_chars += "▀"
        else:
            bar_chars += "░"

    bpct = int((filled_units / total_units) * 100)
    spin = _spinner_chars[_spinner_frame % 4]
    spin_display = f"[bold #4ECDC4]{spin}[/] " if running else ""
    bar = f"{spin_display}[bold #4ECDC4]{bar_chars}[/] [bold #4ECDC4]{current_step}/{total_steps}[/] [dim]{bpct}%[/]"

    border_clr = _transition_color(current_step)
    return Panel(Align.center(Text.from_markup(bar)), box=box.SIMPLE, border_style=border_clr, padding=(0, 1))


def make_results(t, results: dict, phase: str, export_file: str | None, show_operators: bool, hacker: bool = False) -> Panel:
    """Discovery results + export options."""
    if show_operators:
        return make_operator_panel()

    if not results:
        msg = Text(t("results_wait"), style="dim italic")
        if hacker:
            return tron_glow_panel(msg, title=f"[bold]{t('results_title')}[/]", border_color="#4ADE80")
        return Panel(
            msg,
            title=f"[bold]{t('results_title')}[/]",
            border_style="#4ADE80",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    r = results
    result_text = Text()
    result_text.append(f"✅ {t('status_label')}: {r.get('status', '?')}\n", style="bold #4ADE80")
    result_text.append("🔄 Paradigm detect: [bold #FFE66D]iterative[/] (was one-shot)\n")
    result_text.append("⚠️  Novelty gate: [bold #ef4444]HARD GATE[/] (was warning)\n")
    result_text.append(f"📚 {t('papers_found')}: {r.get('papers_found', '?')}\n")
    result_text.append(f"🧬 {t('isomorphisms')}: {r.get('isomorphisms', {}).get('found', '?') if isinstance(r.get('isomorphisms'), dict) else '?'}\n")
    result_text.append(f"⏱️ {t('time_label')}: {r.get('total_time', '')}с\n")

    hyp = r.get('hypothesis', {})
    hyp_text = hyp.get('text', str(hyp)) if isinstance(hyp, dict) else str(hyp)
    result_text.append(f"\n💡 {t('hypothesis')}:\n{hyp_text[:300]}...\n", style="italic")

    if phase == "results":
        result_text.append("\n")
        result_text.append("—" * 40 + "\n", style="dim")
        result_text.append(f"[bold]{t('export_title')}:[/]\n")
        fmt_labels = [
            ("[1]", "LaTeX"),
            ("[2]", "Markdown"),
            ("[3]", "JSON"),
            ("[4]", "HTML"),
            ("[5]", "Plain Text"),
        ]
        for key, name in fmt_labels:
            result_text.append(f"  {key} {name}  ", style="#4ECDC4")

        if export_file:
            result_text.append(f"\n\n✅ {t('export_saved')}: [bold]{export_file}[/]")

    border_clr = "#4ADE80"
    if hacker:
        return tron_glow_panel(result_text, title=f"[bold]{t('results_title')}[/]", border_color=border_clr)

    return Panel(
        result_text,
        title=f"[bold]{t('results_title')}[/]",
        border_style=border_clr,
        box=box.ROUNDED,
        padding=(1, 2),
    )
