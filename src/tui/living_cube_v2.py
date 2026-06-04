"""C4REQBER Living Cube v2.3 — Fixed-Frame Neon Cube.

Every frame is exactly 24×5 chars. Border never moves — only interior symbols change.
No faces — pure cognitive geometry. 7 states × 3 frames.
"""
from __future__ import annotations

import os
import random
import textwrap
import time


# ═══════════════════ Fixed-Size Neon Frames (7 states × 24 cols × 5 rows) ═══════════════════
# Border: TOP="╔══════════════════════╗", BOT="╚══════════════════════╝" — always 24 chars.
# Interior: "║ ···················· ║" — 3 lines of symbols, 24 chars fixed.
# Animation: only symbols inside the box change between frames.

_B = "╔════════════════╗"
_M0 = "║"
_MR = "║"
_BB = "╚════════════════╝"

FRAMES: dict[str, list[list[str]]] = {
    "idle": [
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ◈ ◈ █  " + _MR,
            "     " + _M0 + " █ ◉ ◈ █  " + _MR,
            "     " + _M0 + " █ ◈ ◈ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █  ◈  █  " + _MR,
            "     " + _M0 + " █ ◉◈◉ █  " + _MR,
            "     " + _M0 + " █  ◈  █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ◈ ◈ █  " + _MR,
            "     " + _M0 + " █ ◉ ◈ █  " + _MR,
            "     " + _M0 + " █ ◈ ◈ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
    ],
    "thinking": [
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ⊡ ⊡ █  " + _MR,
            "     " + _M0 + " █  ⊙  █  " + _MR,
            "     " + _M0 + " █ ⊡ ⊡ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ⊡ ⊙ █  " + _MR,
            "     " + _M0 + " █  ⊡  █  " + _MR,
            "     " + _M0 + " █ ⊡ ⊙ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ⊡ ⊡ █  " + _MR,
            "     " + _M0 + " █  ⊙  █  " + _MR,
            "     " + _M0 + " █ ⊡ ⊡ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
    ],
    "excited": [
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ✦ ✦ █  " + _MR,
            "     " + _M0 + " █  ◈  █  " + _MR,
            "     " + _M0 + " █ ✦ ✦ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ✦ ◈ █  " + _MR,
            "     " + _M0 + " █  ✦  █  " + _MR,
            "     " + _M0 + " █ ✦ ◈ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ✦ ✦ █  " + _MR,
            "     " + _M0 + " █  ◈  █  " + _MR,
            "     " + _M0 + " █ ✦ ✦ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
    ],
    "discovery": [
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ◈ ♦ █  " + _MR,
            "     " + _M0 + " █ ♦ ◉ █  " + _MR,
            "     " + _M0 + " █ ◈ ♦ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ♦ ◈ █  " + _MR,
            "     " + _M0 + " █ ◈ ♦ █  " + _MR,
            "     " + _M0 + " █ ♦ ◈ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ◈ ♦ █  " + _MR,
            "     " + _M0 + " █ ♦ ◉ █  " + _MR,
            "     " + _M0 + " █ ◈ ♦ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
    ],
    "error": [
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ✕ ✕ █  " + _MR,
            "     " + _M0 + " █  ✕  █  " + _MR,
            "     " + _M0 + " █ ✕ ✕ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ✕   █  " + _MR,
            "     " + _M0 + " █   ✕  █  " + _MR,
            "     " + _M0 + " █ ✕   █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ✕ ✕ █  " + _MR,
            "     " + _M0 + " █  ✕  █  " + _MR,
            "     " + _M0 + " █ ✕ ✕ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
    ],
    "sleeping": [
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ · · █  " + _MR,
            "     " + _M0 + " █  ·  █  " + _MR,
            "     " + _M0 + " █ · · █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ·   █  " + _MR,
            "     " + _M0 + " █   ·  █  " + _MR,
            "     " + _M0 + " █ ·   █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ · · █  " + _MR,
            "     " + _M0 + " █  ·  █  " + _MR,
            "     " + _M0 + " █ · · █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
    ],
    "paradigm": [
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ◉ ◈ █  " + _MR,
            "     " + _M0 + " █ ◈ ✦ █  " + _MR,
            "     " + _M0 + " █ ◉ ◈ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ✦ ◉ █  " + _MR,
            "     " + _M0 + " █ ◈ ✦ █  " + _MR,
            "     " + _M0 + " █ ✦ ◉ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
        [
            "░▒▓ " + _B + " ▓▒░",
            "     " + _M0 + " █ ◉ ◈ █  " + _MR,
            "     " + _M0 + " █ ◈ ✦ █  " + _MR,
            "     " + _M0 + " █ ◉ ◈ █  " + _MR,
            "░▒▓ " + _BB + " ▓▒░",
        ],
    ],
}


IDLE_COMMENTS = [
    "✦ Z\u2083\u00b3 topology: 27 states, 6 operators",
    "◈ Theorem 11: undirected \u00d8=3, directed fwd=6",
    "Click any cell in the 3\u00d73\u00d73 grid!",
    "Try: Ctrl+Enter to run discovery",
    "Ask me: 'What C4 state fits my problem?'",
]

THINKING_COMMENTS = [
    "Analyzing cognitive framing...",
    "Searching 24 knowledge sources...",
    "⊡ Computing gap analysis...",
    "⊙ Running TRIZ contradiction matrix...",
    "◈ Routing through FRA classifier...",
]

DISCOVERY_COMMENTS = [
    "✦ Discovery complete!",
    "◈ Hypothesis generated!",
    "Found a promising gap!",
    "Novelty score: high",
]

ERROR_COMMENTS = [
    "✕ Pipeline error — retrying...",
    "Something went wrong. Try simplifying the problem.",
    "✕ Verification failed — adjusting parameters...",
]

SLEEP_COMMENTS = [
    "⋯ Z\u2083\u00b3 dreaming...",
    "⋯ 27 states. Still going.",
    "⋯ Idle: energy conserving",
]

PROACTIVE = [
    "Explore: TRIZ contradiction view (key 5)",
    "Explore: Chat with the agent (key 4)",
    "Explore: Knowledge search (key 7)",
    "Explore: C4 Geometry view (key 3)",
    "Ask me about TRIZ contradictions!",
]


class LivingCube:
    """HD Interactive C4 cube mascot — polished 12×12 resolution."""

    def __init__(self) -> None:
        self.state = "idle"
        self.comment = self._random_comment()
        self.stats = {"energy": 100.0, "curiosity": 80.0, "bond": 50.0, "discoveries": 0.0}
        self._frame = 0
        self._last_activity = time.time()
        self._history: list[str] = []
        self._personality = "curious"
        self._tick = 0
        self._load_memory()

    def _load_memory(self) -> None:
        path = os.path.expanduser("~/.c4reqber/mascot_memory.json")
        try:
            if os.path.exists(path):
                import json
                with open(path) as f:
                    d = json.load(f)
                self.stats["discoveries"] = d.get("total", 0)
                self._history = d.get("topics", [])[-10:]
                self._update_personality()
        except Exception:
            pass

    def _save_memory(self) -> None:
        path = os.path.expanduser("~/.c4reqber/mascot_memory.json")
        try:
            import json
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(
                    {"total": self.stats["discoveries"], "topics": self._history[-20:]},
                    f,
                )
        except Exception:
            pass

    def _update_personality(self) -> None:
        d = self.stats["discoveries"]
        self._personality = ("master" if d >= 50 else "expert" if d >= 20 else
                              "confident" if d >= 5 else "learning" if d >= 1 else "curious")

    @property
    def mood(self) -> str:
        return self._personality

    @property
    def energy_emoji(self) -> str:
        e = self.stats["energy"]
        if e > 70:
            return "⚡⚡⚡"
        if e > 30:
            return "⚡⚡"
        if e > 10:
            return "⚡"
        return "💤"

    @property
    def bond_emoji(self) -> str:
        b = self.stats["bond"]
        if b > 70:
            return "💛💛💛"
        if b > 30:
            return "💛💛"
        return "💛"

    def render(self, width: int = 14) -> str:
        """Render neon cube — clean fixed-width, no Rich tag interference."""
        frames = FRAMES.get(self.state, FRAMES["idle"])
        self._frame = (self._frame + 1) % len(frames) if self._tick % 3 == 0 else self._frame
        self._tick += 1
        cube = frames[self._frame]

        color_map = {
            "idle": "cyan", "thinking": "bright_cyan", "excited": "magenta",
            "discovery": "bright_green", "error": "red", "sleeping": "bright_black",
            "paradigm": "yellow",
        }
        glow = color_map.get(self.state, "cyan")

        lines = [
            f"[dim]{self.bond_emoji}[/] "
            f"[{glow}]{self.energy_emoji}[/]  "
            f"[bold {glow}]◈ {self.stats['discoveries']} disc[/]",
            f"[dim]{self._personality.capitalize()} · {self.state}[/]",
            "",
        ]
        TARGET = 26
        for i, line in enumerate(cube):
            content = line.strip()
            padded = content.center(TARGET)
            if i == 2:
                lines.append(f"  [{glow}]{padded}[/]")
            else:
                lines.append(f"  [dim {glow}]{padded}[/]")
        return "\n".join(lines)

    def render_bubble(self) -> str:
        import textwrap
        comment = self.comment[:90]
        max_w = 26
        wrapped = []
        for para in comment.split("\n"):
            wrapped.extend(textwrap.wrap(para, width=max_w) or [" "])
        max_len = min(max(len(l) for l in wrapped), max_w)
        bubble = []
        bubble.append("┌─" + "─" * max_len + "─┐")
        for l in wrapped:
            l = l[:max_len]
            bubble.append("│ " + l.ljust(max_len) + " │")
        bubble.append("└─" + "─" * max_len + "─┘")
        return "\n".join(bubble)

    def set_state(self, state: str, comment: str = "") -> None:
        self.state = state
        self.comment = comment or self._random_comment()
        self._last_activity = time.time()

    def tick(self) -> None:
        elapsed = time.time() - self._last_activity
        if self.state == "idle" and elapsed > 45:
            self.stats["energy"] = max(0, self.stats["energy"] - 0.02)
            self.stats["curiosity"] = max(0, self.stats["curiosity"] - 0.01)
            self.stats["bond"] = max(0, self.stats["bond"] - 0.005)
            if elapsed > 120 and random.random() < 0.1:
                self.comment = random.choice(PROACTIVE)
        try:
            from src.tui.delight import NightMode
            if NightMode.is_night() and self.state not in ("sleeping", "error"):
                self.on_night_mode()
        except Exception:
            pass

    def record_discovery(self, topic: str, confidence: float = 0.0) -> None:
        self.stats["discoveries"] += 1
        self.stats["bond"] = min(100, self.stats["bond"] + 10)
        self.stats["energy"] = max(0, self.stats["energy"] - 5)
        self.stats["curiosity"] = min(100, self.stats["curiosity"] + 2)
        self._history.append(topic)
        self._update_personality()
        self._save_memory()
        if confidence > 0.8:
            self.set_state("paradigm", "✦ Paradigm shift! Theorem 11 smiles.")
        else:
            self.set_state("discovery", random.choice(DISCOVERY_COMMENTS))

    def on_pipeline_start(self) -> None:
        self.set_state("thinking", random.choice(THINKING_COMMENTS))
    def on_pipeline_error(self) -> None:
        self.set_state("error", random.choice(ERROR_COMMENTS))
        self.stats["energy"] = max(0, self.stats["energy"] - 2)
    def on_night_mode(self) -> None:
        if self.state not in ("sleeping", "error"):
            self.set_state("sleeping", random.choice(SLEEP_COMMENTS))
    def on_wake(self) -> None:
        if self.state == "sleeping":
            self.set_state("idle", "Good morning! 27 states refreshed.")
            self.stats["energy"] = min(100, self.stats["energy"] + 30)
    def feed(self, interest: int = 10) -> None:
        self.stats["curiosity"] = min(100, self.stats["curiosity"] + interest)
        self.stats["bond"] = min(100, self.stats["bond"] + interest // 2)
        self.set_state("excited", f"✦ Curiosity +{interest}!")

    def _random_comment(self) -> str:
        pool = {"idle": IDLE_COMMENTS, "thinking": THINKING_COMMENTS,
                "discovery": DISCOVERY_COMMENTS, "error": ERROR_COMMENTS,
                "sleeping": SLEEP_COMMENTS}
        return random.choice(pool.get(self.state, IDLE_COMMENTS))

    def stats_bar(self) -> str:
        e, c, b, d = self.stats["energy"], self.stats["curiosity"], self.stats["bond"], self.stats["discoveries"]
        return f"⚡{int(e)} 🔍{int(c)} 💛{int(b)} ◈{d}"
