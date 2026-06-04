from __future__ import annotations


"""
TUI: Onboarding
Onboarding panel and diagnostic wizard for first-time users.
"""


from rich import box
from rich.panel import Panel
from rich.text import Text


def make_onboarding_panel(t, mode: str) -> Panel:
    """Create onboarding panel for first-time users."""
    mode_labels = {
        "discover": f"🔬 {t('discover')}",
        "invent": f"🔧 {t('invent')}",
        "transform": f"🌌 {t('transform')}",
    }
    lines = (
        f"  [bold #4ECDC4]{t('onboarding_title')}[/]\n\n"
        f"  {t('onboarding_mode_prefix')}: [bold]{mode_labels[mode]}[/]\n\n"
        f"  {t('onboarding_body')}\n"
        f"  [bold #4ECDC4]🔬[/] {t('onboarding_discover')}\n"
        f"  [bold #FFD93D]🔧[/] {t('onboarding_invent')}\n"
        f"  [bold #ec4899]🌌[/] {t('onboarding_transform')}\n\n"
        f"  [bold #4ECDC4]\\[Enter][/] {t('onboarding_enter')}\n"
        f"  [bold #4ECDC4]\\[Tab][/]   {t('onboarding_tab')}\n"
        f"  [bold #4ECDC4]\\[L][/]     {t('onboarding_mode_prefix')} {t('_lang', '').upper()}\n"
        rf"  [bold #4ECDC4]\\[q][/]     {t('onboarding_quit')}"
    )
    return Panel(
        Text.from_markup(lines),
        title="[bold]Reqber v5.3.0[/]",
        border_style="bold #4ECDC4",
        box=box.ROUNDED,
        padding=(2, 4),
    )


def check_onboarding(t, KeyboardReader, console, ONBOARDED_FLAG, LANG_FILE, _cycle_lang, _save_lang) -> str:
    """Check if user needs onboarding. Returns 'ok' or 'quit'."""
    if ONBOARDED_FLAG.exists():
        return "ok"

    console.clear()
    console.print(make_onboarding_panel(t, "discover"))

    with KeyboardReader() as kr:
        current_mode = "discover"
        modes = ["discover", "invent", "transform"]
        while True:
            key = kr.read_key(timeout=0.2)
            if key:
                if key == ('enter',):
                    break
                elif key == ('tab',):
                    idx = modes.index(current_mode)
                    current_mode = modes[(idx + 1) % 3]
                    console.clear()
                    console.print(make_onboarding_panel(t, current_mode))
                elif key[0] == 'char' and key[1] in ('l', 'L', 'д', 'Д'):
                    _cycle_lang()
                    console.clear()
                    console.print(make_onboarding_panel(t, current_mode))
                elif key[0] == 'char' and key[1] in ('q', 'Q'):
                    console.print(f"\n[dim]{t('footer_quit')}[/]")
                    ONBOARDED_FLAG.parent.mkdir(parents=True, exist_ok=True)
                    ONBOARDED_FLAG.write_text("1")
                    return "quit"
                elif key == ('esc',):
                    console.print(f"\n[dim]{t('footer_quit')}[/]")
                    ONBOARDED_FLAG.parent.mkdir(parents=True, exist_ok=True)
                    ONBOARDED_FLAG.write_text("1")
                    return "quit"

    ONBOARDED_FLAG.parent.mkdir(parents=True, exist_ok=True)
    ONBOARDED_FLAG.write_text("1")
    console.clear()
    return "ok"
