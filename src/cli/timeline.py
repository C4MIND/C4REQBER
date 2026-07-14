from __future__ import annotations

import time

from src.terminal_.cyberpunk_theme import CyberpunkTheme as T


class SessionTimeline:
    """Temporal Log — cyberpunk session history with branches + time-travel."""

    EVENT_ICONS = {
        "chat": "💬", "tool_call": "🔧", "discovery": "🔬",
        "error": "✗", "done": "✓", "c4_shift": "◈",
        "agent_run": "⚡", "verify": "🔍", "branch": "├─", "merge": "├─",
    }

    EVENT_COLORS = {
        "chat": T.FG_WHITE, "tool_call": T.FG_SECONDARY, "discovery": T.FG_ACCENT,
        "error": T.FG_DANGER, "done": T.FG_PRIMARY, "c4_shift": T.FG_PRIMARY,
        "agent_run": T.FG_WARNING, "verify": T.FG_SECONDARY,
        "branch": T.FG_GHOST, "merge": T.FG_GHOST,
    }

    def __init__(self) -> None:
        self.events: list[dict] = []
        self.current_index: int = -1
        self._branches: dict[int, list[int]] = {}
        self._branch_set: set[int] = set()

    def add_event(self, event_type: str, description: str,
                  c4_state: str | None = None,
                  branch_parent: int | None = None) -> int:
        """Add event."""
        event = {
            "time": time.time(),
            "type": event_type,
            "desc": description,
            "c4_state": c4_state,
        }
        idx = len(self.events)
        self.events.append(event)
        self.current_index = idx

        if branch_parent is not None and 0 <= branch_parent < len(self.events):
            self._branches.setdefault(branch_parent, []).append(idx)
            self._branch_set.add(idx)

        return idx

    def add_branch(self, parent_idx: int, event_type: str, description: str) -> int:
        return self.add_event(event_type, description, branch_parent=parent_idx)

    def time_travel(self, index: int) -> None:
        if 0 <= index < len(self.events):
            self.current_index = index

    def render(self, width: int = 60, max_events: int = 12) -> str:
        """Render."""
        t = T
        lines = []
        lines.append(f"{t.FG_GHOST}{t.TL_DOUBLE}{t.HORIZ_DOUBLE * (width - 2)}{t.TR_DOUBLE}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.VERT_DOUBLE}{t.RESET}  {t.BOLD}TEMPORAL LOG{t.RESET}{' ' * (width - 16)}{t.FG_GHOST}{t.VERT_DOUBLE}{t.RESET}")
        lines.append(f"{t.FG_GHOST}{t.T_RIGHT}{t.HORIZ * (width - 2)}{t.T_LEFT}{t.RESET}")

        start = max(0, len(self.events) - max_events)

        for i in range(start, len(self.events)):
            event = self.events[i]
            elapsed = time.time() - event["time"]
            elapsed_str = f"{elapsed:.0f}s" if elapsed < 60 else f"{elapsed/60:.0f}m"

            icon = self.EVENT_ICONS.get(event["type"], "•")
            color = self.EVENT_COLORS.get(event["type"], t.FG_MUTED)

            is_branch = i in self._branch_set
            branch_prefix = "├─ " if is_branch else "  "

            cursor = t.FG_PRIMARY + "▶" + t.RESET if i == self.current_index else t.FG_GHOST + "│" + t.RESET

            c4_annotation = ""
            if event.get("c4_state"):
                c4_annotation = f" {t.FG_GHOST}→ {event['c4_state']}{t.RESET}"

            desc = event["desc"][:30]
            line = f"  {cursor} {branch_prefix}{color}{icon}{t.RESET} {desc:<30} {c4_annotation} {t.FG_GHOST}{elapsed_str:>6}{t.RESET}"
            lines.append(line)

            if i in self._branches and width >= 80:
                for child_idx in self._branches[i]:
                    if child_idx < len(self.events):
                        child = self.events[child_idx]
                        child_desc = child["desc"][:25]
                        lines.append(f"  {t.FG_GHOST}│     ├─{t.RESET} {t.FG_SECONDARY}{child['type']}{t.RESET} {child_desc}")

        lines.append(f"{t.FG_GHOST}{t.BL_DOUBLE}{t.HORIZ_DOUBLE * (width - 2)}{t.BR_DOUBLE}{t.RESET}")
        return "\n".join(lines)

    def render_time_travel_help(self) -> str:
        """Render time travel help."""
        t = T
        return f"{t.FG_GHOST}Time-Travel: [T]ravel <index> (0-{len(self.events)-1}){t.RESET}"
