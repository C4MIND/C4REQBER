"""
TUI: Renderer
Render method for C4TUI — all widgets wired.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from rich.layout import Layout

from src.tui.cube_viz import render_ascii_cube
from src.tui.header_footer import make_header
from src.tui.layout_manager import make_layout
from src.tui.results_display import (
    make_input_area,
    make_progress,
    make_results,
    make_story_messages,
)


def make_renderer(tui_instance, console, TRANSLATIONS, STEP_TO_C4,
                   STEP_ICONS, ALL_CUBE_COORDS, plugin_manager) -> Callable[..., Any]:
    """Create renderer closure for C4TUI."""

    def render() -> Layout:
        cube = render_ascii_cube(
            tui_instance.active_c4_state,
            glow=tui_instance.running or tui_instance.phase == "results",
            all_glow=tui_instance.all_glow,
            completion_flash=tui_instance.completion_flash,
        )

        token_text = tui_instance._build_token_display()
        llm_type = tui_instance._get_llm_type()
        llm_text = f"🧠 LLM: {llm_type} (local)" if llm_type else "☁️ LLM: openrouter (cloud)"

        gpu_text = tui_instance._get_gpu_header_text()

        header_panel = make_header(
            tui_instance.mode, token_text, llm_text, gpu_text
        )

        story_panel = make_story_messages(
            tui_instance.t, tui_instance.messages, tui_instance.current_step,
            tui_instance.running, tui_instance._hacker,
            tui_instance.all_glow, tui_instance.completion_flash
        )

        progress_panel = make_progress(
            tui_instance.current_step, tui_instance.total_steps,
            tui_instance.running, tui_instance._hacker, tui_instance._spinner_frame
        )

        results_panel = make_results(
            tui_instance.t, tui_instance.results, tui_instance.phase,
            tui_instance.export_file, tui_instance._show_operators,
            tui_instance._hacker
        )

        from src.tui.gpu_display import make_gpu_dashboard_panel

        layout = make_layout(
            lambda: header_panel,
            cube,
            lambda: story_panel,
            lambda: make_input_area(tui_instance.t, tui_instance.problem, tui_instance._hacker),
            lambda: progress_panel,
            lambda: results_panel,
            gpu_dashboard_fn=lambda: make_gpu_dashboard_panel(),
            show_gpu=tui_instance._show_gpu_dashboard,
            show_modules=tui_instance._show_modules,
            show_plugins=tui_instance._show_plugins,
            show_alerts=getattr(tui_instance, '_show_alerts', False),
            show_budget=getattr(tui_instance, '_show_budget', False),
            show_depth_ladder=getattr(tui_instance, '_show_depth_ladder', False),
            show_proof_graph=getattr(tui_instance, '_show_proof_graph', False),
            show_article=getattr(tui_instance, '_show_article', False),
            show_live_feed=getattr(tui_instance, '_show_live_feed', False),
            show_thinking=getattr(tui_instance, '_show_thinking', False),
            hacker=tui_instance._hacker,
            matrix_fn=lambda: tui_instance._make_matrix_panel(),
        )

        return layout

    return render
