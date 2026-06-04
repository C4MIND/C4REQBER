# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Smart context-aware REPL prompt + ghost-text tab completion.

Prompt states:
    c4reqber ❯                           — normal
    c4reqber [openrouter] ❯              — after /models selection
    c4reqber ⏳ ❯                        — pipeline running
    c4reqber ✓ ❯                         — success (3s)

Ghost text: dim preview shown inline in the input buffer.
"""
from __future__ import annotations

import time
from enum import Enum, auto


class PromptMode(Enum):
    """PromptMode."""
    NORMAL = auto()
    PROVIDER_SELECTED = auto()
    RUNNING = auto()
    SUCCESS = auto()
    CUBE_ACTIVE = auto()


_GHOST_STYLE = "\033[2m\033[90m"  # dim gray
_RESET = "\033[0m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_GREEN = "\033[92m"
_GOLD = "\033[93m"
_BOLD = "\033[1m"


class SmartPrompt:
    """Context-aware prompt with temporal states."""

    def __init__(self) -> None:
        self._mode = PromptMode.NORMAL
        self._provider: str = ""
        self._success_at: float = 0.0
        self._c4_state = "F⟨0,0,0⟩"
        self._success_duration = 3.0

    @property
    def mode(self) -> PromptMode:
        """Mode."""
        if self._mode == PromptMode.SUCCESS:
            if time.monotonic() - self._success_at > self._success_duration:
                self._mode = PromptMode.NORMAL
        return self._mode

    @mode.setter
    def mode(self, m: PromptMode) -> None:
        """Mode."""
        self._mode = m
        if m == PromptMode.SUCCESS:
            self._success_at = time.monotonic()

    def set_provider(self, name: str) -> None:
        """Set provider."""
        self._provider = name
        self._mode = PromptMode.PROVIDER_SELECTED if name else PromptMode.NORMAL

    def set_c4_state(self, state: str) -> None:
        self._c4_state = state

    def render(self) -> str:
        """Build the prompt string with ANSI styling."""
        prefix = f"{_CYAN}{_BOLD}c4reqber{_RESET}"

        mode = self.mode
        if mode == PromptMode.RUNNING:
            indicator = f" {_GOLD}⏳{_RESET}"
        elif mode == PromptMode.SUCCESS:
            indicator = f" {_GREEN}✓{_RESET}"
        elif mode == PromptMode.PROVIDER_SELECTED and self._provider:
            indicator = f" {_GOLD}[{self._provider}]{_RESET}"
        elif mode == PromptMode.CUBE_ACTIVE:
            indicator = f" {_MAGENTA}◈{_RESET}"
        else:
            indicator = ""

        return f"{prefix}{indicator} {_CYAN}❯{_RESET} "

    def blink_success(self) -> str:
        """Render + flash the success indicator once. Call in a loop."""
        self.mode = PromptMode.SUCCESS
        return self.render()


GHOST_COMPLETIONS: dict[str, list[str]] = {
    "/mod": ["/models"],
    "/coun": ["/council"],
    "/conn": ["/connect"],
    "/api": ["/api"],
    "/tes": ["/test"],
    "/pro": ["/profile"],
    "/plu": ["/plugins"],
    "/deb": ["/debug"],
    "/con": ["/config", "/connect"],
    "/hel": ["/help"],
    "/sim": ["/sim"],
    "analy": ["analyze"],
    "tur": ["turbo"],
    "ver": ["verify"],
    "pro": ["protocol", "providers"],
    "kuh": ["kuhn"],
    "cu": ["cube"],
    "si": ["sim", "status"],
    "st": ["status"],
    "ex": ["exit"],
    "he": ["help"],
}


def find_ghost_completion(input_text: str) -> str | None:
    """Find ghost-text completion for the current input prefix.

    Returns the completion suffix (without the prefix), or None.
    Example: input='/mod' → returns 'els' (so ghost shows '/models')
    """
    if not input_text or len(input_text) < 2:
        return None

    for prefix, completions in GHOST_COMPLETIONS.items():
        if input_text.lower().startswith(prefix) and input_text != prefix:
            for comp in completions:
                if comp.startswith(input_text):
                    return comp[len(input_text):]

    for prefix, completions in GHOST_COMPLETIONS.items():
        if input_text.lower() == prefix.lower():
            if len(completions) == 1:
                return completions[0][len(input_text):]
            common = _longest_common_prefix(completions)
            if common and common != input_text:
                return common[len(input_text):]

    return None


def render_ghost_text(input_text: str, ghost: str | None) -> str:
    """Build an ANSI string showing input + ghost text inline."""
    if not ghost:
        return input_text
    return f"{input_text}{_GHOST_STYLE}{ghost}{_RESET}"


def _longest_common_prefix(strings: list[str]) -> str:
    if not strings:
        return ""
    shortest = min(strings, key=len)
    for i, ch in enumerate(shortest):
        if any(s[i] != ch for s in strings):
            return shortest[:i]
    return shortest


class PromptManager:
    """Manages prompt state + ghost completion + cursor style.

    Integrates with REPL or TUI input loop.
    """

    def __init__(self) -> None:
        self.smart = SmartPrompt()
        self._cogload = 1
        self._last_input = ""

    def set_cogload(self, level: int) -> None:
        self._cogload = max(1, min(3, level))

    def on_input_change(self, text: str) -> str:
        """Called on every keystroke. Returns ghost completion or ''."""
        self._last_input = text
        ghost = find_ghost_completion(text)
        if ghost:
            return ghost
        return ""

    def cursor_style(self) -> str:
        """ANSI escape to set cursor style based on CogLoad."""
        base = "\033[5 q"  # blinking bar
        if self._cogload >= 3:
            base = "\033[1 q"  # blinking block
        elif self._cogload >= 2:
            base = "\033[3 q"  # blinking underline
        return base

    def cursor_color(self) -> str:
        """ANSI cursor color based on CogLoad depth."""
        if self._cogload >= 3:
            return "\033]12;#e040fb\a"  # magenta
        elif self._cogload >= 2:
            return "\033]12;#06d6a0\a"  # bright cyan
        return "\033]12;#4ECDC4\a"  # dim cyan
