"""
Ghost in the Shell TUI - Minimal Version
Run with: python src/tui/ghost_tui.py
"""
from __future__ import annotations

import sys
from pathlib import Path


_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, ProgressBar, Static


class GhostHeader(Static):  # type: ignore[misc]
    """Futuristic status bar with live mascot state"""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("◈ C4REQBER", classes="logo")
            yield Label("v5.4.0", classes="version")
            yield Label("◉ ONLINE", classes="status")
            yield Label(id="mascot", classes="mascot")
            yield Label(id="clock", classes="clock")

    def on_mount(self) -> None:
        """On mount."""
        self.update_clock()
        self.set_interval(1, self.update_clock)
        self.update_mascot()
        self.set_interval(3, self.update_mascot)
        self._apply_night_mode()

    def _apply_night_mode(self) -> None:
        try:
            from src.tui.delight import NightMode
            if NightMode.is_night():
                self.styles.background = "#1a1a2e"
                self.query_one("#clock", Label).styles.color = "#4ECDC4"
        except Exception:
            pass

    def update_clock(self) -> None:
        self.query_one("#clock", Label).update(datetime.now().strftime("◔ %H:%M:%S"))

    def update_mascot(self) -> None:
        try:
            from src.cli.cube_mascot import CubeMascot
            mascot = CubeMascot()
            emoji = {"idle":"▫▫▫","thinking":"▫◈▫","processing":"◈▣▫","discovery":"◈▣◈","error":"✖▫▫","done":"◈▣◈ ✓","paradigm":"✦◈▣◈✦"}.get(mascot.state, "▫▫▫")
            self.query_one("#mascot", Label).update(emoji)
        except Exception:
            self.query_one("#mascot", Label).update("▫▫▫")


class C4Visualizer(Static):  # type: ignore[misc]
    """ASCII C4 27-state cube visualization"""

    def render(self) -> str:
        from src.c4.state import C4State

        selected = C4State(T=1, S=1, A=1)
        return f"""
┌─────────────────────────────────────────────────────────────────┐
│                    C4 COGNITIVE GEOMETRY                        │
│                         Z₃³ STATE SPACE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    PAST (0)          PRESENT (1)         FUTURE (2)            │
│    ═════════         ═══════════         ══════════             │
│                                                                 │
│  ┌───┬───┬───┐     ┌───┬───┬───┐      ┌───┬───┬───┐           │
│  │000│001│002│     │100│101│102│      │200│201│202│  Concrete │
│  ├───┼───┼───┤     ├───┼───┼───┤      ├───┼───┼───┤   (0)     │
│  │010│011│012│     │110│111│112│      │210│211│212│  Abstract │
│  ├───┼───┼───┤     ├───┼───┼───┤      ├───┼───┼───┤   (1)     │
│  │020│021│022│     │120│121│122│      │220│221│222│    Meta   │
│  └───┴───┴───┘     └───┴───┴───┘      └───┴───┴───┘   (2)     │
│                                                                 │
│  [Self] [Other] [System]  ← Agency Dimension                   │
│   (0)    (1)     (2)                                           │
│                                                                 │
│  Selected: {selected.to_tuple()} ({selected.time_label} × {selected.scale_label} × {selected.agency_label})                      │
│  Mode: Collaborative Abstraction                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        """


class DiscoveryWorkflow(Static):  # type: ignore[misc]
    """Interactive discovery panel"""

    stage = reactive(0)
    running = reactive(False)

    STAGES = [
        "◈ Analyze problem structure",
        "◉ Search literature",
        "◈ Generate C4 hypotheses",
        "◉ Apply TRIZ principles",
        "◈ Find analogies",
        "◉ Multi-agent evaluation",
        "◈ Synthesize results",
    ]

    def compose(self) -> ComposeResult:
        """Compose."""
        yield Label("[ DISCOVERY WORKFLOW ]", classes="title")
        yield Input(placeholder="Enter research problem...", id="problem")
        yield ProgressBar(total=100, show_eta=False, id="progress")

        with Vertical(id="stages"):
            for i, stage in enumerate(self.STAGES):
                yield Label(f"○ {stage}", classes="stage", id=f"s{i}")

        yield Button("▶ INITIATE DISCOVERY", id="start", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            asyncio.create_task(self.run_discovery())

    async def run_discovery(self) -> None:
        """Run discovery."""
        self.running = True
        btn = self.query_one("#start", Button)
        btn.disabled = True
        self.query_one("#progress", ProgressBar)

        from src.agents.pipeline import UniversalSolvePipeline

        pipeline = UniversalSolvePipeline()
        for i, _stage in enumerate(self.STAGES):
            # Update visual
            for j in range(i + 1):
                label = self.query_one(f"#s{j}", Label)
                if j < i:
                    label.update(f"● {self.STAGES[j]}")
                    label.add_class("complete")
                elif j == i:
                    label.update(f"◉ {self.STAGES[j]}")
                    label.add_class("active")

            if i == 2:
                problem = self.query_one("#problem", Input).value.strip()
                if not problem:
                    await self._safe_status("Please enter a problem.")
                    break
                result = await pipeline.solve(problem=problem, mode="autopilot")
                await self._safe_status(f"Hypothesis: {result.final_solution[:120]}")
            await asyncio.sleep(0.1)

    async def _safe_status(self, message: str) -> None:
        try:
            self.query_one("#progress", ProgressBar).update(progress=100)
            await self.query_one("#start", Button).update(label="▶ NEW DISCOVERY")  # type: ignore[attr-defined]
            await self.query_one("#stages", Vertical).mount(Label(message))
        except Exception:
            pass


class HypothesisList(Static):  # type: ignore[misc]
    """List of generated hypotheses"""

    def render(self) -> str:
        return """
┌────────────────────────────────────────────────────────────────┐
│ [ GENERATED HYPOTHESES ]                        Confidence     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  HYP-001  Novel electrode material with gradient porosity      │
│           Method: C4+TRIZ Hybrid                     [████] 92%│
│                                                                │
│  HYP-002  Biomimetic dendritic structure for ion transport     │
│           Method: Analogy Engine                     [████] 88%│
│                                                                │
│  HYP-003  Dynamic charging protocol based on impedance         │
│           Method: TRIZ Principle 19                  [███ ] 79%│
│                                                                │
└────────────────────────────────────────────────────────────────┘
        """


class GhostTUI(App):  # type: ignore[misc]
    """Ghost in the Shell inspired TUI for C4REQBER"""

    CSS = """
    .logo { color: #00d4ff; text-style: bold; }
    .version { color: #ffd700; }
    .status { color: #00ff41; }
    .mascot { color: #ffd700; text-style: bold; }
    .clock { color: #888888; }
    Screen { background: #0a0a1a; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "discover", "Discover"),
        Binding("c", "c4", "C4 View"),
        Binding("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        """Compose."""
        yield GhostHeader()

        with Horizontal(id="main"):
            with Vertical():
                yield DiscoveryWorkflow()
                yield HypothesisList()

            with Vertical():
                yield C4Visualizer()

    def action_discover(self) -> None:
        self.query_one(DiscoveryWorkflow).scroll_visible()

    def action_c4(self) -> None:
        self.query_one(C4Visualizer).scroll_visible()

    def action_help(self) -> None:
        self.notify(
            """
[b]Keyboard Shortcuts:[/b]
  [cyan]q[/cyan] - Quit
  [cyan]d[/cyan] - Focus Discovery
  [cyan]c[/cyan] - Focus C4
  [cyan]?[/cyan] - This help

[b]Navigation:[/b]
  Click or Tab to navigate
  Enter to activate buttons
        """,
            title="[ C4REQBER TUI ]",
            severity="information",
        )


if __name__ == "__main__":
    print("Starting Ghost in the Shell TUI...")
    print("If you see this, the TUI didn't launch.")
    print("Make sure you're running in a terminal with proper display.")
    print("")

    try:
        app = GhostTUI()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
