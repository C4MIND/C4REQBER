from __future__ import annotations

import sys


def beep(sound_type: str = "default") -> None:
    """Terminal beep/haptic feedback."""
    beeps = {
        "thinking": "\a",
        "discovery": "\a\a",
        "error": "\a\a\a",
        "done": "\a",
    }
    beep_seq = beeps.get(sound_type, "\a")
    sys.stdout.write(beep_seq)
    sys.stdout.flush()
