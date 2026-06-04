"""
TUI: Layout Manager — Full Assembly
Layout creation for C4TUI with all widgets.
"""
from __future__ import annotations

from typing import Any, Callable

from rich.layout import Layout


def make_layout(
    header_fn, cube_panel, story_fn, input_fn,
    progress_fn, results_fn,
    gpu_dashboard_fn: Callable[..., Any] | None = None,
    show_gpu: bool = False,
    show_modules: bool = False,
    show_plugins: bool = False,
    show_alerts: bool = False,
    show_budget: bool = False,
    show_depth_ladder: bool = False,
    show_proof_graph: bool = False,
    show_article: bool = False,
    show_live_feed: bool = False,
    show_thinking: bool = False,
    hacker: bool = False,
    matrix_fn=None,
):
    """Assemble the full TUI layout with all 14 widget panels."""
    parts = []

    # Header
    parts.append(Layout(header_fn(), name="header", size=3))

    # Live Feed Ticker (compact, top)
    if show_live_feed:
        try:
            from src.tui.live_feed_ticker import LiveFeedTicker
            ticker = LiveFeedTicker()
            parts.append(Layout(ticker.render(), name="live_feed", size=3))
        except Exception:
            pass

    # GPU Dashboard
    if show_gpu and gpu_dashboard_fn:
        parts.append(Layout(gpu_dashboard_fn(), name="gpu_dashboard", size=12))

    # Budget Gauge (compact)
    if show_budget:
        try:
            from src.tui.budget_gauge import make_budget_gauge  # type: ignore[attr-defined]
            parts.append(Layout(make_budget_gauge(), name="budget", size=3))  # type: ignore[call-arg]
        except Exception:
            pass

    # Alert Panel
    if show_alerts:
        try:
            from src.tui.alert_widget import AlertPanel
            alerts = AlertPanel()
            parts.append(Layout(alerts.render(), name="alerts", size=8))
        except Exception:
            pass

    # Modules / Plugins panels
    if show_modules:
        from src.tui.module_status import make_module_status_panel
        parts.append(Layout(make_module_status_panel(), name="module", size=22))
    if show_plugins:
        from src.tui.plugin_manager import make_plugin_panel
        parts.append(Layout(make_plugin_panel(), name="plugins", size=22))  # type: ignore[call-arg]

    # Main content area
    main_layout = Layout(name="main")
    main_layout.split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=3),
    )

    # Left column
    left_panels = [Layout(cube_panel, name="cube", ratio=3)]
    if show_depth_ladder:
        try:
            from src.tui.depth_ladder import make_depth_ladder  # type: ignore[attr-defined]
            left_panels.append(Layout(make_depth_ladder(), name="depth_ladder", size=5))
        except Exception:
            pass
    left_panels.append(Layout(story_fn(), name="story", ratio=2))
    main_layout["left"].split(*left_panels)

    # Right column
    right_panels = [
        Layout(input_fn(), name="input", size=3),
        Layout(progress_fn(), name="progress", size=3),
    ]
    if show_thinking:
        try:
            from src.tui.thinking_indicator import render_thinking_bar
            right_panels.append(Layout(render_thinking_bar(0), name="thinking", size=3))
        except Exception:
            pass
    if show_article:
        try:
            from src.tui.article_canvas import ArticleCanvas
            canvas = ArticleCanvas()
            right_panels.append(Layout(canvas.render(), name="article", ratio=2))
        except Exception:
            pass
    right_panels.append(Layout(results_fn(), name="results"))
    main_layout["right"].split(*right_panels)
    parts.append(main_layout)

    # Proof Graph (bottom panel)
    if show_proof_graph:
        try:
            from src.tui.proof_graph import ProofGraph
            pg = ProofGraph()
            parts.append(Layout(pg.render_ascii(), name="proof_graph", size=10))
        except Exception:
            pass

    # Matrix rain
    if hacker or matrix_fn:
        matrix_content = matrix_fn() if matrix_fn else ""
        if matrix_content:
            parts.append(Layout(matrix_content, name="matrix", size=6))

    # Footer
    from src.tui.header_footer import make_footer
    parts.append(Layout(make_footer(), name="footer", size=3))

    layout = Layout()
    layout.split(*parts)
    return layout
