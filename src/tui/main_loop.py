"""
TUI: Main Loop
Main TUI loop and input handling for C4TUI.
"""
from __future__ import annotations

import time

from rich.live import Live

from src.tui.animation import pipeline_completion
from src.tui.diagnostics import make_diagnostic_wizard, run_diagnostic_wizard
from src.tui.keyboard_handler import KeyboardReader
from src.tui.onboarding import check_onboarding
from src.tui.pipeline_runner import run_discovery_pipeline_sync


def run_main_loop(tui_instance, renderer, console, ONBOARDED_FLAG, EXPORT_DIR) -> None:
    """Main TUI loop."""
    # Phase 0: Onboarding
    result = check_onboarding(
        tui_instance.t, KeyboardReader, console,
        ONBOARDED_FLAG, tui_instance.lang_manager.get_lang(),
        tui_instance.lang_manager._cycle_lang, tui_instance.lang_manager._save_lang
    )
    if result == "quit":
        return

    # Main loop - SINGLE Live context for entire session
    with Live(renderer(), console=console, refresh_per_second=60, screen=True) as live:
        while not tui_instance._stop_flag:
            tui_instance.phase = "input"
            tui_instance.problem = ""
            tui_instance.results = None
            tui_instance.messages = []
            tui_instance.current_step = 0
            tui_instance.active_c4_state = (2, 1, 2)
            tui_instance.running = False
            tui_instance.all_glow = set()
            tui_instance.completion_flash = False
            tui_instance.export_file = None
            tui_instance._show_operators = False
            tui_instance._show_plugins = False
            tui_instance._show_alerts = False
            tui_instance._show_budget = False
            tui_instance._show_depth_ladder = False
            tui_instance._show_proof_graph = False
            tui_instance._show_article = False
            tui_instance._show_live_feed = False
            tui_instance._show_thinking = False

            # Show input screen
            live.update(renderer())
            time.sleep(0.3)

            # Get problem input
            problem = _get_problem_input(tui_instance, live, renderer)
            if problem is None or problem.lower() in ('q', 'quit', 'exit', ''):
                break
            tui_instance.problem = problem

            # Diagnostic wizard before discovery
            diagnostic = run_diagnostic_wizard(
                KeyboardReader, make_diagnostic_wizard, None
            )

            # Run pipeline with live animation
            tui_instance.results = run_discovery_pipeline_sync(
                problem, live, renderer,
                _advance_pipeline_step, pipeline_completion,
                tui_instance._mascot, None
            )

            # Wait for export/next action
            while tui_instance.phase == "results":
                action = _read_key_in_results(tui_instance)
                if action == 'quit':
                    tui_instance._stop_flag = True
                    break
                elif action == 'new_discovery':
                    break
                elif action == 'switch_mode':
                    modes = ["discover", "invent", "transform"]
                    idx = modes.index(tui_instance.mode)
                    tui_instance.mode = modes[(idx + 1) % 3]
                    live.update(renderer())
                elif action == 'switch_lang':
                    tui_instance._cycle_lang()
                    live.update(renderer())
                elif action == 'show_operators':
                    tui_instance._show_operators = not tui_instance._show_operators
                    live.update(renderer())
                elif action == 'show_gpu':
                    tui_instance._show_gpu_dashboard = not tui_instance._show_gpu_dashboard
                    live.update(renderer())
                elif action == 'show_modules':
                    tui_instance._show_modules = not tui_instance._show_modules
                    live.update(renderer())
                elif action == 'show_plugins':
                    tui_instance._show_plugins = not tui_instance._show_plugins
                    live.update(renderer())
                elif action == 'show_alerts':
                    tui_instance._show_alerts = not tui_instance._show_alerts
                    live.update(renderer())
                elif action == 'show_budget':
                    tui_instance._show_budget = not tui_instance._show_budget
                    live.update(renderer())
                elif action == 'show_depth_ladder':
                    tui_instance._show_depth_ladder = not tui_instance._show_depth_ladder
                    live.update(renderer())
                elif action == 'show_proof_graph':
                    tui_instance._show_proof_graph = not tui_instance._show_proof_graph
                    live.update(renderer())
                elif action == 'show_article':
                    tui_instance._show_article = not tui_instance._show_article
                    live.update(renderer())
                elif action == 'show_live_feed':
                    tui_instance._show_live_feed = not tui_instance._show_live_feed
                    live.update(renderer())
                elif action == 'show_thinking':
                    tui_instance._show_thinking = not tui_instance._show_thinking
                    live.update(renderer())
                elif action == 'show_cube_navigator':
                    live.update(renderer())
                elif action and action.startswith('export_'):
                    fmt_map = {'1': 'latex', '2': 'markdown', '3': 'json', '4': 'html', '5': 'text'}
                    fmt = fmt_map.get(action[-1])
                    if fmt:
                        from src.tui.export_helpers import export_discovery
                        tui_instance.export_file = export_discovery(
                            tui_instance.results, tui_instance.problem, fmt
                        )
                        live.update(renderer())

            if tui_instance._stop_flag:
                break

    console.clear()
    console.print(f"[dim]{tui_instance.t('footer')}[/]")


def _get_problem_input(tui_instance, live, renderer) -> str | None:
    """Read problem inside Live context."""
    tui_instance.problem = ""
    cursor_pos = 0
    input_chars: list[str] = []

    live.update(renderer())
    time.sleep(0.1)

    with KeyboardReader() as kr:
        while True:
            key = kr.read_key(timeout=0.1)
            if key is not None:
                if key == ('enter',) or key == ('char', '\r') or key == ('char', '\n'):
                    result = ''.join(input_chars)
                    if result.strip():
                        return result.strip()
                    return None
                elif key == ('esc',) or (key[0] == 'char' and key[1] in ('q', 'Q')):
                    return None
                elif key == ('backspace',):
                    if cursor_pos > 0:
                        input_chars.pop(cursor_pos - 1)
                        cursor_pos -= 1
                elif key[0] == 'char':
                    ch = key[1]
                    if ch and 32 <= ord(ch) < 127:
                        input_chars.insert(cursor_pos, ch)
                        cursor_pos += 1

                tui_instance.problem = ''.join(input_chars)
                live.update(renderer())

            time.sleep(0.05)


def _read_key_in_results(tui_instance) -> str | None:
    """Read key in results phase."""
    with KeyboardReader() as kr:
        while True:
            key = kr.read_key(timeout=0.2)
            if key:
                if key[0] == 'char' and key[1] == '1':
                    return 'export_1'
                elif key[0] == 'char' and key[1] == '2':
                    return 'export_2'
                elif key[0] == 'char' and key[1] == '3':
                    return 'export_3'
                elif key[0] == 'char' and key[1] == '4':
                    return 'export_4'
                elif key[0] == 'char' and key[1] == '5':
                    return 'export_5'
                elif key == ('enter',):
                    return 'new_discovery'
                elif key == ('tab',):
                    return 'switch_mode'
                elif key[0] == 'char' and key[1] in ('l', 'L', 'д', 'Д'):
                    return 'switch_lang'
                elif key[0] == 'char' and key[1] in ('o', 'O'):
                    return 'show_operators'
                elif key[0] == 'char' and key[1] in ('g', 'G'):
                    return 'show_gpu'
                elif key[0] == 'char' and key[1] in ('m', 'M'):
                    return 'show_modules'
                elif key[0] == 'char' and key[1] in ('p', 'P'):
                    return 'show_plugins'
                elif key[0] == 'char' and key[1] in ('a', 'A'):
                    return 'show_alerts'
                elif key[0] == 'char' and key[1] in ('b', 'B'):
                    return 'show_budget'
                elif key[0] == 'char' and key[1] in ('d', 'D'):
                    return 'show_depth_ladder'
                elif key[0] == 'char' and key[1] in ('t', 'T'):
                    return 'show_article'
                elif key[0] == 'char' and key[1] in ('r', 'R'):
                    return 'show_proof_graph'
                elif key[0] == 'char' and key[1] in ('v', 'V'):
                    return 'show_cube_navigator'
                elif key[0] == 'char' and key[1] in ('i', 'I'):
                    return 'show_live_feed'
                elif key[0] == 'char' and key[1] in ('f', 'F'):
                    return 'show_thinking'
                elif key == ('esc',) or (key[0] == 'char' and key[1] in ('q', 'Q')):
                    return 'quit'

            time.sleep(0.1)


def _advance_pipeline_step(tui_instance, live, step_index, stories, all_glow, completion_flash, mascot, renderer=None) -> None:
    """Advance to next step and update display."""
    i = step_index
    if i >= len(stories):
        return

    title, msg = stories[i]
    tui_instance.current_step = i + 1
    tui_instance.messages.append((title, msg))

    # Mascot commentary at each step
    if mascot:
        tui_instance._mascot_comment = mascot.comment("discovery")
        tui_instance.messages.append(("C4", mascot.comment("discovery")))

    # Update active C4 state
    from src.tui.pipeline_stories import STEP_TO_C4
    if i < len(STEP_TO_C4):
        tui_instance.active_c4_state = STEP_TO_C4[i]
    else:
        tui_instance.active_c4_state = (2, 1, 2)

    # Glow effect: highlight already-completed steps
    current_glow = set()
    for j in range(i + 1):
        if j < len(STEP_TO_C4):
            current_glow.add(STEP_TO_C4[j])
    tui_instance.all_glow = current_glow

    if tui_instance._hacker and renderer is not None and callable(renderer):
        pass

    if renderer is not None:
        live.update(renderer())


def _pipeline_completion(tui_instance, live, all_glow, completion_flash, mascot, play_sound_fn) -> None:
    """Handle completion celebration."""
    pipeline_completion(
        live, all_glow, completion_flash, mascot,
        play_sound_fn, tui_instance._hacker
    )
