# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Delight features — easter eggs, night mode, shutdown ritual, philosopher memory.

NightMode: auto-shifts palette after 23:00 to warmer, dimmer tones.
CubeMemory: recalls user context across sessions for idle musings.
ShutdownRitual: ASCII cube turn + fade + last message on exit.
BirthdayEasterEgg: ASCII cake + message on repository birthday.
"""
from __future__ import annotations

import datetime
import time
from pathlib import Path


EDGE_NAMES = [
    "F⟨0,0,0⟩", "F⟨0,0,1⟩", "F⟨0,0,2⟩",
    "F⟨0,1,0⟩", "F⟨0,1,1⟩", "F⟨0,1,2⟩",
    "F⟨0,2,0⟩", "F⟨0,2,1⟩", "F⟨0,2,2⟩",
    "F⟨1,0,0⟩", "F⟨1,0,1⟩", "F⟨1,0,2⟩",
    "F⟨1,1,0⟩", "F⟨1,1,1⟩", "F⟨1,1,2⟩",
    "F⟨1,2,0⟩", "F⟨1,2,1⟩", "F⟨1,2,2⟩",
    "F⟨2,0,0⟩", "F⟨2,0,1⟩", "F⟨2,0,2⟩",
    "F⟨2,1,0⟩", "F⟨2,1,1⟩", "F⟨2,1,2⟩",
    "F⟨2,2,0⟩", "F⟨2,2,1⟩", "F⟨2,2,2⟩",
]


class NightMode:
    """Auto-dims palette after 23:00 for eye comfort.

    Shifts cyan → teal/warmer, magenta → muted, reduces overall brightness.
    Resets in the morning. Like iOS Night Shift for the terminal.
    """

    NIGHT_START = 23
    NIGHT_END = 6
    BRIGHTNESS_REDUCTION = 0.80

    @staticmethod
    def is_night() -> bool:
        """Check if night."""
        now = datetime.datetime.now()
        hour = now.hour
        return hour >= NightMode.NIGHT_START or hour < NightMode.NIGHT_END

    @classmethod
    def palette(cls) -> dict[str, str]:
        """Return night-adjusted hex colors keyed by role name."""
        if not cls.is_night():
            return {
                "cyan": "#06d6a0",
                "magenta": "#e040fb",
                "yellow": "#FFD93D",
                "teal": "#4ECDC4",
                "ghost": "#666666",
            }

        factor = cls.BRIGHTNESS_REDUCTION
        return {
            "cyan": _dim_hex("#06d6a0", factor),
            "magenta": _dim_hex("#e040fb", factor * 0.9),
            "yellow": _dim_hex("#FFD93D", factor),
            "teal": _dim_hex("#4ECDC4", factor * 0.85),
            "ghost": _dim_hex("#444444", factor),
        }


def _dim_hex(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


class CubeMemory:
    """Recalls user context for idle philosophical musings.

    Stores last N analysis topics and uses them in idle comments
    for personalized cube wisdom.
    """

    MEMORY_FILE = Path.home() / ".c4reqber" / "cube_memory.json"
    MAX_TOPICS = 20

    def __init__(self) -> None:
        self._topics: list[str] = []
        self._last_mode: str = ""
        self._session_count = 0
        self._load()

    def _load(self) -> None:
        import json
        try:
            if self.MEMORY_FILE.exists():
                data = json.loads(self.MEMORY_FILE.read_text())
                self._topics = data.get("topics", [])[-self.MAX_TOPICS:]
                self._session_count = data.get("sessions", 0)
        except (OSError, json.JSONDecodeError, ValueError):
            pass

    def _save(self) -> None:
        import json
        self.MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "topics": self._topics[-self.MAX_TOPICS:],
            "sessions": self._session_count,
            "updated": datetime.datetime.now().isoformat(),
        }
        self.MEMORY_FILE.write_text(json.dumps(data, indent=2))

    def record_topic(self, topic: str) -> None:
        if topic and topic not in self._topics:
            self._topics.append(topic)
            self._save()

    def record_session_start(self) -> None:
        """Record session start."""
        self._session_count += 1
        self._save()

    def recall_insight(self) -> str | None:
        """Return a personalized idle musing, or None if no context."""
        import random
        if not self._topics:
            return None

        topic = random.choice(self._topics)
        templates = [
            f"Still processing {{{{{topic}}}}}... 24 states explored, 3 unknown paths remain.",
            f"Regarding {{{{{topic}}}}} — Theorem 11 says it connects to everything in ≤6 steps.",
            f"Last session's {{{{{topic}}}}} trail left 2 unexplored C4 branches. Curious.",
            f"Memory trace: {{{{{topic}}}}} @ Z₃³ F⟨1,1,1⟩. The centre sees all.",
            f"I've been thinking about {{{{{topic}}}}}. The cubic perspective offers 26 alternatives.",
        ]
        return random.choice(templates).replace(
            "{{{{{topic}}}}}", topic
        ).replace("{{{{", "{").replace("}}}}", "}")


class ShutdownRitual:
    """The exit animation — cube turns, text fades, final message.

    Runs over ~800ms total. Transforms 'closing terminal' into
    'completing a session'.
    """

    CUBE_TURN_FRAMES = [
        " ◈ ",
        " ◇ ",
        " ◆ ",
        " ◉ ",
        " ◎ ",
        " ● ",
    ]

    FAREWELLS = [
        "All 27 states archived. Until next theorem.",
        "Z₃³ at rest. 6 operators dormant. Goodnight.",
        "Cognitive topology disengaged. 27 edges preserved.",
        "Cube enters stasis. Theorem 11 holds until next activation.",
        "Session complete. 26 known states await your return.",
    ]

    def __init__(self) -> None:
        import random
        self._farewell = random.choice(self.FAREWELLS)

    def run(self) -> None:
        """Execute shutdown ritual — prints to stdout with timing."""
        import sys

        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write("\033[?25l")  # hide cursor

        center = "\n" * 6

        for frame_char in self.CUBE_TURN_FRAMES:
            fade = self.CUBE_TURN_FRAMES.index(frame_char) / len(self.CUBE_TURN_FRAMES)
            r = int(0xE0 * (1.0 - fade * 0.5))
            g = int(0x40 * (1.0 - fade * 0.5))
            b = int(0xFB * (1.0 - fade * 0.3))

            display = (
                f"\033[H{center}"
                f"          \033[38;2;{r};{g};{b}m{frame_char}\033[0m\n"
                f"          \033[2m\033[38;2;{r};{g};{b}mc4reqber\033[0m"
            )
            sys.stdout.write(display)
            sys.stdout.flush()
            time.sleep(0.12)

        # Final message — fade in
        for opacity in (0.2, 0.4, 0.6, 0.8, 1.0):
            r = int(0x06 * (1.0 - opacity) + 0xE0 * opacity * 0.5)
            g = int(0xD6 * (1.0 - opacity) + 0x40 * opacity * 0.3)
            b = int(0xA0 * (1.0 - opacity) + 0xFB * opacity * 0.2)
            sys.stdout.write(
                f"\033[H{center}"
                f"\033[38;2;{r};{g};{b}m{self._farewell}\033[0m\n"
            )
            sys.stdout.flush()
            time.sleep(0.08)

        sys.stdout.write("\033[?25h\033[0m\n")
        sys.stdout.flush()


class BirthdayEasterEgg:
    """Check if today is the repository birthday and show a cake."""

    BIRTHDAY = (5, 15)

    ASCII_CAKE = r"""
          .  .  .
       .  \033[93m*\033[0m  .  \033[93m*\033[0m  .
        \033[93m✧\033[0m  \033[91m♥\033[0m  \033[93m✧\033[0m  \033[91m♥\033[0m  \033[93m✧\033[0m
      \033[38;2;255;180;50m▐███████████▌\033[0m
      \033[38;2;255;210;100m▐▌\033[0m\033[38;2;255;80;120m▐██▌\033[0m\033[38;2;255;210;100m▐██▌\033[0m\033[38;2;255;80;120m▐██▌\033[0m\033[38;2;255;210;100m▐▌\033[0m
      \033[38;2;255;150;80m█████████████\033[0m
"""

    @classmethod
    def check(cls) -> str | None:
        """Check."""
        today = datetime.date.today()
        if (today.month, today.day) == cls.BIRTHDAY:
            return (
                f"\n{cls.ASCII_CAKE}\n"
                f"\033[1m\033[95m  Z₃³ was born today. 27 states. Still going.\033[0m\n"
            )
        return None
