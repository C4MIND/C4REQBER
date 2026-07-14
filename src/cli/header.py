from __future__ import annotations

import time
from collections import deque

from src.cli.cube_mascot import CubeMascot
from src.terminal_.cyberpunk_theme import CyberpunkTheme as T
from src.terminal_.ui import sparkline_bar


class C44TCDIHeader:
    """Neural Strip header — cyberpunk cognitive style with sparklines."""

    def __init__(
        self,
        model: str = "unknown",
        mode: str = "chat",
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        knowledge_sources: list[str] | None = None,
        gpu_status: str = "idle",
        c4_state: str = "F[0,0,0]",
        c4_confidence: float = 0.0,
    ):
        self.model = model
        self.mode = mode
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.cost = cost
        self.latency_ms = latency_ms
        self.knowledge_sources = knowledge_sources or ["12 sources"]
        self.gpu_status = gpu_status
        self.c4_state = c4_state
        self.c4_confidence = c4_confidence
        self.cube = CubeMascot()
        self.start_time = time.time()
        self._token_history: deque[float] = deque(maxlen=30)
        self._cost_history: deque[float] = deque(maxlen=30)
        self._latency_history: deque[float] = deque(maxlen=30)

    def render(self, width: int = 120) -> str:
        """Render."""
        lines = []
        t = T
        border_char = t.HORIZ_DOUBLE if width >= 100 else t.HORIZ
        lines.append(f"{t.FG_GHOST}{t.TL_DOUBLE}{border_char * (width - 2)}{t.TR_DOUBLE}{t.RESET}")

        brand = f"{t.BOLD}{t.FG_PRIMARY}▓▓▓ {t.RESET}{t.BOLD}C4REQBER v5.4{t.RESET}"
        mode_colors = {
            "chat": t.FG_PRIMARY, "solve": t.FG_SECONDARY, "tui": t.FG_SECONDARY,
            "deep-work": t.FG_ACCENT, "turbo": t.FG_ACCENT,
        }
        mode_color = mode_colors.get(self.mode, t.FG_GHOST)
        mode_str = f"{mode_color}[{self.mode.upper()}]{t.RESET}"

        conf_pct = f"{self.c4_confidence * 100:.1f}%"
        conf_color = t.FG_PRIMARY if self.c4_confidence > 0.8 else t.FG_WARNING if self.c4_confidence > 0.5 else t.FG_DANGER
        c4_badge = f"{t.FG_GHOST}C4:{t.RESET}{conf_color}{self.c4_state}{t.RESET} {t.FG_GHOST}{conf_pct}{t.RESET}"

        line1 = f"{brand} {mode_str} {t.FG_GHOST}|{t.RESET} {c4_badge}"
        line1 += " " * max(0, width - len(line1) + 20)
        lines.append(line1)

        model_short = self.model.split("/")[-1] if "/" in self.model else self.model
        if len(model_short) > 25:
            model_short = model_short[:22] + "..."
        cube_render = self.cube.render(50)
        line2 = f"  {t.FG_GHOST}Model:{t.RESET} {t.FG_WARNING}{model_short}{t.RESET}  {cube_render}"
        lines.append(line2)

        cost_str = f"${self.cost:.3f}" if self.cost != 0 else "$0.000"
        lat_str = f"{self.latency_ms:.0f}ms" if self.latency_ms > 0 else "---"
        metrics = (
            f"  {t.FG_GHOST}TknIn:{t.RESET}{t.FG_PRIMARY}{self.tokens_in:,}{t.RESET}  "
            f"{t.FG_GHOST}TknOut:{t.RESET}{t.FG_SECONDARY}{self.tokens_out:,}{t.RESET}  "
            f"{t.FG_GHOST}Cost:{t.RESET}{t.FG_WARNING}{cost_str}{t.RESET}  "
            f"{t.FG_GHOST}Lat:{t.RESET}{t.FG_SECONDARY}{lat_str}{t.RESET}"
        )

        sparks = ""
        if self._latency_history and width >= 100:
            lat_spark = sparkline_bar(list(self._latency_history), 8, "#00D4FF")
            sparks = f"  {t.FG_GHOST}lat:{t.RESET}{lat_spark}"
        lines.append(metrics + sparks)

        sources_str = ", ".join(self.knowledge_sources[:4])
        if len(self.knowledge_sources) > 4:
            sources_str += f" +{len(self.knowledge_sources) - 4}"

        gpu_icon = f"{t.FG_PRIMARY}●{t.RESET}" if self.gpu_status == "active" else f"{t.FG_GHOST}○{t.RESET}"
        gpu_label = f"{t.FG_PRIMARY}ACTIVE{t.RESET}" if self.gpu_status == "active" else f"{t.FG_GHOST}idle{t.RESET}"

        line4 = f"  {t.FG_GHOST}Sources:{t.RESET} {t.FG_SECONDARY}{sources_str}{t.RESET}  {gpu_icon} {t.FG_GHOST}GPU {gpu_label}{t.RESET}"
        lines.append(line4)

        lines.append(f"{t.FG_GHOST}{t.BL_DOUBLE}{border_char * (width - 2)}{t.BR_DOUBLE}{t.RESET}")
        lines.append("")
        return "\n".join(lines)

    def update_metrics(self, tokens_in: int = 0, tokens_out: int = 0, cost: float = 0.0, latency_ms: float = 0.0) -> None:
        """Update metrics."""
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.cost = cost
        self.latency_ms = latency_ms

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def set_model(self, model: str) -> None:
        self.model = model

    def set_gpu_status(self, status: str) -> None:
        """Set gpu status."""
        self.gpu_status = status
        mapping = {"active": "processing", "discovery": "discovery", "error": "error", "done": "done"}
        self.cube.set_state(mapping.get(status, "idle"))

    def render_full_cube(self) -> str:
        return self.cube.render()
