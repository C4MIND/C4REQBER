"""
Ghost in the Shell TUI - Minimal Version
Run with: python src/tui/ghost_tui.py
"""

import sys

sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI")

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Button, Input, Label, ProgressBar
from textual.reactive import reactive
from textual.binding import Binding
import asyncio
from datetime import datetime


class GhostHeader(Static):
    """Futuristic status bar"""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("◈ TURBO-CDI", classes="logo")
            yield Label("v5.0", classes="version")
            yield Label("◉ ONLINE", classes="status")
            yield Label(id="clock", classes="clock")

    def on_mount(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        self.query_one("#clock", Label).update(datetime.now().strftime("◔ %H:%M:%S"))


class C4Visualizer(Static):
    """ASCII C4 27-state cube visualization"""

    def render(self) -> str:
        return """
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
│  Selected: 111 (Present × Abstract × Self)                      │
│  Mode: Collaborative Abstraction                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        """


class DiscoveryWorkflow(Static):
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
        self.running = True
        btn = self.query_one("#start", Button)
        btn.disabled = True
        progress = self.query_one("#progress", ProgressBar)

        for i, stage in enumerate(self.STAGES):
            # Update visual
            for j in range(i + 1):
                label = self.query_one(f"#s{j}", Label)
                if j < i:
                    label.update(f"● {self.STAGES[j]}")
                    label.add_class("complete")
                elif j == i:
                    label.update(f"◉ {self.STAGES[j]}")
                    label.add_class("active")

            # Animate progress
            for p in range(0, 100, 20):
                progress.update(progress=p + (i * 100))
                await asyncio.sleep(0.1)

        progress.update(progress=100)
        btn.disabled = False
        btn.label = "▶ NEW DISCOVERY"
        self.running = False


class HypothesisList(Static):
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


class GhostTUI(App):
    """Ghost in the Shell inspired TUI for TURBO-CDI"""

    CSS = """
    Screen {
        background: #0f0f1a;
        color: #ffffff;
    }
    
    GhostHeader {
        height: 1;
        background: #0f0f1a;
        color: #4ECDC4;
        border-bottom: solid #4ECDC4;
    }
    
    GhostHeader .logo { 
        width: 15; 
        text-style: bold; 
        color: #4ECDC4;
    }
    GhostHeader .version { 
        width: 5; 
        color: #6c757d; 
    }
    GhostHeader .status { 
        width: 10; 
        color: #2ecc71; 
        text-style: bold;
    }
    GhostHeader .clock { 
        width: 12; 
        text-align: right;
        color: #FFE66D;
    }
    
    #main {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 1fr;
        padding: 1;
    }
    
    .title {
        text-style: bold underline;
        color: #4ECDC4;
        height: 2;
    }
    
    DiscoveryWorkflow {
        padding: 1;
        border: solid #1a1a2e;
    }
    
    DiscoveryWorkflow .stage {
        height: 1;
        color: #6c757d;
    }
    DiscoveryWorkflow .stage.active {
        color: #4ECDC4;
        text-style: bold;
    }
    DiscoveryWorkflow .stage.complete {
        color: #2ecc71;
    }
    
    C4Visualizer, HypothesisList {
        padding: 1;
        border: solid #1a1a2e;
    }
    
    Button {
        background: #4ECDC4;
        color: #0f0f1a;
        border: none;
    }
    Button:hover {
        background: #6EDDD4;
    }
    Button:disabled {
        background: #1a1a2e;
        color: #6c757d;
    }
    
    ProgressBar {
        background: #1a1a2e;
        color: #4ECDC4;
    }
    ProgressBar > .bar {
        background: #4ECDC4;
    }
    
    Input {
        background: #1a1a2e;
        border: solid #4ECDC4;
        color: #ffffff;
    }
    Input:focus {
        border: solid #FFE66D;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "discover", "Discover"),
        Binding("c", "c4", "C4 View"),
        Binding("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
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
            title="[ TURBO-CDI TUI ]",
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
