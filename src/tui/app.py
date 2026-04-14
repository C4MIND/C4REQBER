"""
TURBO-CDI Ghost in the Shell TUI
Futuristic terminal interface with visualizations
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Label,
    ProgressBar,
    DataTable,
    Markdown,
    Input,
    TabbedContent,
    TabPane,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.timer import Timer
import asyncio
from datetime import datetime


class GhostHeader(Static):
    """Futuristic header bar with system status"""

    DEFAULT_CSS = """
    GhostHeader {
        height: 3;
        background: #0f0f1a;
        color: #4ECDC4;
        border-bottom: solid #4ECDC4;
        content-align: center middle;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="header-content"):
            yield Label("◈ TURBO-CDI v5.0", classes="logo")
            yield Label("◉ SYSTEM ONLINE", classes="status")
            yield Label(id="clock", classes="clock")
            yield Label("● AGENTS: 4 ACTIVE", classes="agents")

    def on_mount(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = datetime.now().strftime("%H:%M:%S")
        self.query_one("#clock", Label).update(f"◔ {clock}")


class C4Grid(Static):
    """Interactive C4 27-state visualization"""

    DEFAULT_CSS = """
    C4Grid {
        height: auto;
        padding: 1;
        border: solid #1a1a2e;
        background: #0f0f1a;
    }
    C4Grid .grid-row {
        height: auto;
    }
    C4Grid .state-cell {
        width: 7;
        height: 3;
        content-align: center middle;
        border: solid #1a1a2e;
        color: #6c757d;
        text-style: bold;
    }
    C4Grid .state-cell:hover {
        background: #4ECDC4;
        color: #0f0f1a;
    }
    C4Grid .state-cell.selected {
        background: #4ECDC4;
        color: #0f0f1a;
        border: solid #FFE66D;
    }
    C4Grid .past { color: #3498db; }
    C4Grid .present { color: #2ecc71; }
    C4Grid .future { color: #9b59b6; }
    """

    STATES = [
        # Time 0 (Past)
        ("000", "past"),
        ("001", "past"),
        ("002", "past"),
        ("010", "past"),
        ("011", "past"),
        ("012", "past"),
        ("020", "past"),
        ("021", "past"),
        ("022", "past"),
        # Time 1 (Present)
        ("100", "present"),
        ("101", "present"),
        ("102", "present"),
        ("110", "present"),
        ("111", "present"),
        ("112", "present"),
        ("120", "present"),
        ("121", "present"),
        ("122", "present"),
        # Time 2 (Future)
        ("200", "future"),
        ("201", "future"),
        ("202", "future"),
        ("210", "future"),
        ("211", "future"),
        ("212", "future"),
        ("220", "future"),
        ("221", "future"),
        ("222", "future"),
    ]

    selected_state = reactive("111")

    def compose(self) -> ComposeResult:
        with Grid(classes="c4-container"):
            for code, time_class in self.STATES:
                cell = Label(code, classes=f"state-cell {time_class}")
                cell.data_code = code
                yield cell

    def on_click(self, event) -> None:
        if hasattr(event.widget, "data_code"):
            self.selected_state = event.widget.data_code
            self.update_selection()

    def update_selection(self) -> None:
        for cell in self.query(".state-cell"):
            if cell.data_code == self.selected_state:
                cell.add_class("selected")
            else:
                cell.remove_class("selected")


class ConfidenceSparkline(Static):
    """Braille-based sparkline for confidence visualization"""

    DEFAULT_CSS = """
    ConfidenceSparkline {
        height: 3;
        color: #FFE66D;
        text-style: bold;
    }
    """

    # Braille patterns for density visualization
    BRAILLE = ["⣀", "⡠", "⡄", "⡆", "⡇", "⣇", "⣏", "⣟", "⣿"]

    values = reactive([0.5, 0.7, 0.85, 0.92, 0.88])

    def watch_values(self, values: list) -> None:
        self.update_display()

    def update_display(self) -> None:
        chars = []
        for v in self.values:
            idx = int(v * (len(self.BRAILLE) - 1))
            chars.append(self.BRAILLE[idx])
        self.update("".join(chars))

    def on_mount(self) -> None:
        self.update_display()


class DiscoveryPanel(Static):
    """Real-time discovery workflow panel"""

    DEFAULT_CSS = """
    DiscoveryPanel {
        height: 100%;
        padding: 1;
        border: solid #1a1a2e;
    }
    DiscoveryPanel .stage {
        height: 1;
        color: #6c757d;
    }
    DiscoveryPanel .stage.active {
        color: #4ECDC4;
        text-style: bold;
    }
    DiscoveryPanel .stage.complete {
        color: #2ecc71;
    }
    DiscoveryPanel .progress-bar {
        width: 100%;
        height: 1;
    }
    """

    STAGES = [
        ("analyze", "◈ Analyzing problem structure"),
        ("search", "◉ Searching literature"),
        ("c4", "◈ Generating C4 hypotheses"),
        ("triz", "◉ Applying TRIZ principles"),
        ("analogy", "◈ Finding analogies"),
        ("agent", "◉ Multi-agent evaluation"),
        ("synthesize", "◈ Synthesizing results"),
    ]

    current_stage = reactive(0)
    is_running = reactive(False)

    def compose(self) -> ComposeResult:
        yield Label("[ DISCOVERY WORKFLOW ]", classes="panel-title")
        yield ProgressBar(total=100, show_eta=False, classes="main-progress")

        with Vertical(classes="stages"):
            for stage_id, label in self.STAGES:
                yield Label(f"○ {label}", classes="stage", id=f"stage-{stage_id}")

        yield Button("▶ START DISCOVERY", id="start-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.start_discovery()

    async def start_discovery(self) -> None:
        self.is_running = True
        self.current_stage = 0
        progress = self.query_one(ProgressBar)
        btn = self.query_one("#start-btn", Button)
        btn.disabled = True

        for i, (stage_id, label) in enumerate(self.STAGES):
            self.current_stage = i
            self.update_stages()

            # Simulate work
            for p in range(0, 100, 10):
                progress.update(progress=p + (i * 100))
                await asyncio.sleep(0.1)

        progress.update(progress=100)
        self.is_running = False
        btn.disabled = False
        btn.label = "▶ START NEW DISCOVERY"

    def update_stages(self) -> None:
        for i, (stage_id, label) in enumerate(self.STAGES):
            stage_label = self.query_one(f"#stage-{stage_id}", Label)
            if i < self.current_stage:
                stage_label.update(f"● {self.STAGES[i][1]}")
                stage_label.add_class("complete")
            elif i == self.current_stage:
                stage_label.update(f"◉ {self.STAGES[i][1]}")
                stage_label.add_class("active")
            else:
                stage_label.update(f"○ {self.STAGES[i][1]}")
                stage_label.remove_class("active", "complete")


class HypothesisCard(Static):
    """Compact hypothesis display card"""

    DEFAULT_CSS = """
    HypothesisCard {
        height: auto;
        padding: 1;
        margin: 1 0;
        background: #1a1a2e;
        border-left: solid #4ECDC4;
    }
    HypothesisCard .hyp-id {
        color: #6c757d;
        text-style: bold;
    }
    HypothesisCard .hyp-title {
        color: #ffffff;
        text-style: bold;
    }
    HypothesisCard .hyp-method {
        color: #4ECDC4;
    }
    HypothesisCard .hyp-confidence {
        color: #FFE66D;
        text-style: bold;
    }
    """

    def __init__(self, hypothesis: dict, **kwargs):
        self.hypothesis = hypothesis
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="hyp-content"):
                yield Label(self.hypothesis["id"], classes="hyp-id")
                yield Label(self.hypothesis["title"], classes="hyp-title")
                yield Label(
                    f"Method: {self.hypothesis['method']}", classes="hyp-method"
                )

            confidence = int(self.hypothesis["confidence"] * 100)
            yield Label(f"{confidence}%", classes="hyp-confidence")


class GhostSidebar(Static):
    """Navigation sidebar"""

    DEFAULT_CSS = """
    GhostSidebar {
        width: 25;
        height: 100%;
        background: #0f0f1a;
        border-right: solid #1a1a2e;
        padding: 1 0;
    }
    GhostSidebar .nav-item {
        height: 3;
        padding: 0 2;
        color: #6c757d;
        content-align: left middle;
    }
    GhostSidebar .nav-item:hover {
        background: #1a1a2e;
        color: #4ECDC4;
    }
    GhostSidebar .nav-item.active {
        background: #1a1a2e;
        color: #4ECDC4;
        border-left: solid #4ECDC4;
    }
    """

    NAV_ITEMS = [
        ("dashboard", "◈ Dashboard"),
        ("discover", "◉ Discovery"),
        ("c4", "◈ C4 Geometry"),
        ("triz", "◉ TRIZ"),
        ("search", "◈ Research"),
        ("graph", "◉ Graph"),
    ]

    current_view = reactive("dashboard")

    def compose(self) -> ComposeResult:
        for view_id, label in self.NAV_ITEMS:
            item = Label(label, classes="nav-item")
            item.data_view = view_id
            yield item

    def on_click(self, event) -> None:
        if hasattr(event.widget, "data_view"):
            self.current_view = event.widget.data_view
            self.update_active()
            self.post_message(self.NavSelected(self.current_view))

    def update_active(self) -> None:
        for item in self.query(".nav-item"):
            if item.data_view == self.current_view:
                item.add_class("active")
            else:
                item.remove_class("active")

    class NavSelected(Message):
        def __init__(self, view: str) -> None:
            self.view = view
            super().__init__()


class TurboTUI(App):
    """Ghost in the Shell inspired TUI"""

    CSS = """
    Screen {
        background: #0f0f1a;
    }
    
    /* Main layout */
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #content {
        width: 1fr;
        height: 100%;
        padding: 1 2;
    }
    
    /* Typography */
    .panel-title {
        text-style: bold underline;
        color: #4ECDC4;
        height: 2;
    }
    
    /* Buttons */
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
    
    /* Progress bars */
    ProgressBar {
        background: #1a1a2e;
        color: #4ECDC4;
    }
    ProgressBar > .bar {
        background: #4ECDC4;
    }
    
    /* Grid layouts */
    Grid {
        grid-size: 9;
        grid-gutter: 0;
    }
    
    /* Tables */
    DataTable {
        background: #0f0f1a;
        color: #ffffff;
        border: solid #1a1a2e;
    }
    DataTable > .datatable--header {
        background: #1a1a2e;
        color: #4ECDC4;
        text-style: bold;
    }
    DataTable > .datatable--cursor {
        background: #4ECDC4;
        color: #0f0f1a;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("1", "view('dashboard')", "Dashboard", show=False),
        Binding("2", "view('discover')", "Discovery", show=False),
        Binding("3", "view('c4')", "C4", show=False),
        Binding("4", "view('triz')", "TRIZ", show=False),
        Binding("?", "help", "Help", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield GhostHeader()

        with Horizontal(id="main-container"):
            sidebar = GhostSidebar()
            sidebar.current_view = "dashboard"
            yield sidebar

            with Vertical(id="content"):
                yield self.create_dashboard()

        yield Footer()

    def create_dashboard(self) -> Container:
        """Create main dashboard view"""
        with Container(classes="view dashboard"):
            with Grid(classes="stats-grid"):
                yield self.stat_card("◈ DISCOVERIES", "156", "+12%")
                yield self.stat_card("◉ HYPOTHESES", "892", "+8%")
                yield self.stat_card("◈ VALIDATION", "84%", "+5%")
                yield self.stat_card("◉ CONFIDENCE", "0.82", "+3%")

            with Horizontal(classes="main-panels"):
                with Vertical(classes="left-panel"):
                    yield DiscoveryPanel()

                with Vertical(classes="right-panel"):
                    yield Label("[ ACTIVE HYPOTHESES ]", classes="panel-title")
                    yield HypothesisCard(
                        {
                            "id": "HYP-001",
                            "title": "Novel electrode material with gradient porosity",
                            "method": "C4+TRIZ Hybrid",
                            "confidence": 0.92,
                        }
                    )
                    yield HypothesisCard(
                        {
                            "id": "HYP-002",
                            "title": "Biomimetic dendritic structure for ion transport",
                            "method": "Analogy Engine",
                            "confidence": 0.88,
                        }
                    )

    def stat_card(self, label: str, value: str, change: str) -> Container:
        """Create a stat card"""
        card = Container(classes="stat-card")
        card.styles.background = "#1a1a2e"
        card.styles.border = ("solid", "#4ECDC4")
        card.styles.padding = 1
        card.styles.height = 5

        return Static(f"{label}\n[bold]{value}[/bold] [{change}]", classes="stat-card")

    def action_view(self, view_name: str) -> None:
        """Switch between views"""
        content = self.query_one("#content")
        content.remove_children()

        if view_name == "dashboard":
            content.mount(self.create_dashboard())
        elif view_name == "c4":
            content.mount(self.create_c4_view())
        elif view_name == "discover":
            content.mount(self.create_discover_view())
        else:
            content.mount(
                Static(
                    f"[ View: {view_name} ]\n\n[italic]Implementation in progress...[/italic]"
                )
            )

    def create_c4_view(self) -> Container:
        """Create C4 visualization view"""
        with Container(classes="view c4"):
            yield Label("[ C4 COGNITIVE GEOMETRY ]", classes="panel-title")
            yield Label("Z₃³ State Space — 27 Cognitive States", classes="subtitle")
            yield C4Grid()

            with Horizontal(classes="c4-info"):
                yield Static(
                    """
[b]Time Dimension:[/b]  Past → Present → Future
[b]Scale Dimension:[/b] Concrete → Abstract → Meta  
[b]Agency Dimension:[/b] Self → Other → System

Selected state defines the cognitive perspective for hypothesis generation.
                """,
                    classes="c4-legend",
                )

    def create_discover_view(self) -> Container:
        """Create discovery view"""
        with Container(classes="view discover"):
            yield Label("[ NEW DISCOVERY ]", classes="panel-title")
            yield Input(placeholder="Enter research problem...", id="problem-input")
            yield DiscoveryPanel()

    def on_ghost_sidebar_nav_selected(self, message: GhostSidebar.NavSelected) -> None:
        self.action_view(message.view)


if __name__ == "__main__":
    app = TurboTUI()
    app.run()
