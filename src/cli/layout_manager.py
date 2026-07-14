from __future__ import annotations

import shutil
from typing import Any

from src.terminal_.cyberpunk_theme import CyberpunkTheme as T


class LayoutManager:
    """Manages adaptive layouts based on task + natural language detection."""

    LAYOUTS: dict[str, Any] = {
        "minimal": {
            "description": "Just metrics + prompt (quick chat, XS terminal)",
            "panes": ["metrics", "input"],
            "cube": "inline",
            "min_cols": 0, "max_cols": 80,
        },
        "standard": {
            "description": "Metrics + cube + chat + prompt (normal work)",
            "panes": ["metrics", "header", "cube", "chat_history", "input"],
            "cube": "full",
            "min_cols": 80, "max_cols": 120,
        },
        "deep-work": {
            "description": "Multi-pane for refactoring/proof/discovery",
            "panes": ["metrics", "header", "cube", "pipeline_steps", "crisis_radar", "chat", "context_map", "input"],
            "cube": "full",
            "min_cols": 120, "max_cols": 180,
        },
        "turbo": {
            "description": "4-agent parallel + synthesis + GPU + Crisis Radar (dissertation mode)",
            "panes": ["metrics", "header", "agent_1", "agent_2", "agent_3", "agent_4",
                      "synthesis", "gpu_monitor", "crisis_radar", "input"],
            "cube": "full",
            "min_cols": 180, "max_cols": 999999,
        },
        # NOTE: tui-mode is experimental — not yet implemented in the TUI app.
        "tui-mode": {
            "description": "Full TUI (Rich) for interactive use [EXPERIMENTAL]",
            "panes": ["tui_full"],
            "cube": "embedded",
            "min_cols": 80, "max_cols": 9999,
        },
    }

    LAYOUT_KEYWORDS = {
        "deep-work": {
            "en": ["refactor", "architect", "prove", "theorem", "formalize", "verify", "lemma", "design"],
            "ru": ["рефактор", "архитектура", "доказать", "теорема", "формализовать"],
            "zh": ["重构", "架构", "证明", "定理", "形式化"],
            "es": ["refactorizar", "arquitectura", "probar", "teorema", "formalizar"],
            "fr": ["refactoriser", "architecture", "prouver", "théorème", "formaliser"],
            "de": ["refactoring", "architektur", "beweisen", "theorem", "formalisieren"],
            "ja": ["リファクタリング", "アーキテクチャ", "証明", "定理", "形式化"],
        },
        "turbo": {
            "en": ["turbo", "full-power", "dissertation", "paradigm", "accelerate", "boost", "multi-agent", "team"],
            "ru": ["турбо", "полная мощность", "диссертация", "парадигма", "ускорить"],
            "zh": ["涡轮", "全功率", "论文", "范式", "加速"],
            "es": ["turbo", "máxima potencia", "disertación", "paradigma", "acelerar"],
            "ja": ["ターボ", "全功率", "論文", "パラダイム", "加速"],
        },
        "standard": {
            "en": ["solve", "discover", "analyze", "research", "find"],
            "ru": ["решить", "обнаружить", "анализировать", "исследование"],
            "zh": ["解决", "发现", "分析", "研究"],
            "es": ["resolver", "descubrir", "analizar", "investigar"],
            "fr": ["résoudre", "découvrir", "analyser", "rechercher"],
            "de": ["lösen", "entdecken", "analysieren", "forschen"],
            "ja": ["解決", "発見", "分析", "研究"],
            "pt": ["resolver", "descobrir", "analisar", "pesquisar"],
            "it": ["risolvere", "scoprire", "analizzare", "ricercare"],
            "ko": ["해결", "발견", "분석", "연구"],
        },
    }

    def __init__(self, llm_client=None) -> None:
        self.current_layout = "standard"
        self.manual_override = False
        self.llm_client = llm_client

    def _rule_based_detect(self, user_input: str) -> str:
        text = user_input.lower()
        for layout_type, lang_keywords in self.LAYOUT_KEYWORDS.items():
            for keywords in lang_keywords.values():
                if any(word in text for word in keywords):
                    return layout_type
        return "standard"

    async def _llm_based_detect(self, user_input: str) -> str:
        if not self.llm_client:
            raise RuntimeError("LLM client not available")
        prompt = (
            f"Classify the following user request into one of: "
            f"deep-work, turbo, standard, minimal. "
            f"Return only the label. Request: {user_input[:500]}"
        )
        response = await self.llm_client.complete(prompt, max_tokens=20)
        result = response.strip().lower().replace("-", " ").replace("_", " ")
        for layout in self.LAYOUTS:
            if layout in result or layout.replace("-", " ") in result:
                return layout
        return "standard"

    def detect_terminal_size(self) -> tuple[int, int]:
        try:
            return shutil.get_terminal_size()
        except (OSError, ValueError):
            return 80, 24

    def auto_layout_for_size(self, cols: int) -> str:
        """Auto layout for size."""
        for name, config in self.LAYOUTS.items():
            if config.get("min_cols", 0) <= cols <= config.get("max_cols", 9999):
                return name
        return "minimal"

    def switch_to_optimal_layout(self) -> str:
        """Switch to optimal layout."""
        if self.manual_override:
            return self.current_layout
        cols, _ = self.detect_terminal_size()
        optimal = self.auto_layout_for_size(cols)
        if optimal != self.current_layout:
            self.current_layout = optimal
        return optimal

    async def detect_task_type(self, user_input: str) -> str:
        """Detect task type."""
        result = self._rule_based_detect(user_input)
        if result != "standard":
            return result
        if self.llm_client:
            try:
                return await self._llm_based_detect(user_input)
            except (RuntimeError, ValueError):
                pass
        return "standard"

    def switch_layout(self, layout_name: str) -> None:
        if layout_name in self.LAYOUTS:
            self.current_layout = layout_name
            self.manual_override = True

    def get_current_layout(self) -> dict:
        return self.LAYOUTS.get(self.current_layout, self.LAYOUTS["standard"])

    def render_layout_hint(self) -> str:
        """Render layout hint."""
        config = self.get_current_layout()
        panes_str = ", ".join(config["panes"][:3])
        if len(config["panes"]) > 3:
            panes_str += f" +{len(config['panes']) - 3}"
        cols, rows = self.detect_terminal_size()
        return (f"{T.FG_GHOST}Layout: {T.RESET}{T.FG_SECONDARY}{self.current_layout}{T.RESET}"
                f"{T.FG_GHOST} | {cols}x{rows} | Panes: {panes_str}{T.RESET}")

    def render_context_map(self) -> str:
        """Render context map."""
        t = T
        lines = []
        lines.append(f"{t.FG_GHOST}{t.TL}{t.HORIZ * 20}{t.TR}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.VERT}{t.RESET} {t.BOLD}Context Map{t.RESET}{' ' * 8}{t.FG_GHOST}{t.VERT}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.T_RIGHT}{t.HORIZ * 20}{t.T_LEFT}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.VERT}{t.RESET} Files: {t.FG_SECONDARY}src/, tests/{t.RESET}{t.FG_GHOST}{t.VERT}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.VERT}{t.RESET} C4: {t.FG_PRIMARY}27 states Z₃³{t.RESET}{t.FG_GHOST}{t.VERT}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.VERT}{t.RESET} Sources: {t.FG_SECONDARY}27{t.RESET}{t.FG_GHOST}{t.VERT}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.BL}{t.HORIZ * 20}{t.BR}{t.RESET}")
        return "\n".join(lines)

    def render_shortcut_bar(self) -> str:
        """Render shortcut bar."""
        t = T
        shortcuts = [
            ("C", "onfig"), ("G", "PU"), ("R", "adar"),
            ("T", "ravel"), ("/", "Layout"), ("?", "Help"),
        ]
        parts = []
        for key, label in shortcuts:
            parts.append(f"{t.FG_PRIMARY}[{key}]{t.RESET}{t.FG_GHOST}{label}{t.RESET}")
        return "  ".join(parts)
