from __future__ import annotations


"""
TUI: Animation
Startup animation and completion celebration methods for C4TUI.
"""

from rich.console import Console


console = Console()
import sys
import time


def make_startup_animation() -> None:
    """C4 logo ASCII art with typing effect cinematic intro."""
    logo = [
        ("   ▄████████  ▄█     ▄████████", "#4ECDC4"),
        ("  ███    ███ ███    ███    ███ ", "#4ECDC4"),
        ("  ███    █▀  ███▌   ███    █▀  ", "#4ECDC4"),
        ("  ███        ███▌  ▄███▄▄▄     ", "#4ECDC4"),
        ("▀███████████ ███▌ ▀▀███▀▀▀     ", "#4ECDC4"),
        ("         ███ ███    ███         ", "#4ECDC4"),
        ("   ▄█    ███ ███    ███         ", "#4ECDC4"),
        (" ▄████████▀  █▀     █▀          ", "#4ECDC4"),
        ("", ""),
        ("COGNITIVE EXOSKELETON v5.3.0", "#FFD93D"),
    ]
    console.clear()
    for line, _color in logo:
        if not line:
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(0.05)
            continue
        for char in line:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.0015)
        sys.stdout.write("\n")
        sys.stdout.flush()
        time.sleep(0.02)
    time.sleep(0.6)
    console.clear()


def pipeline_completion(live, all_glow, completion_flash, mascot_comment,
                          play_sound_fn=None, hacker=False) -> tuple[set, bool]:
    """Handle completion celebration."""
    from src.tui.cube_viz import ALL_CUBE_COORDS

    # All 27 faces glow + flash 4 times
    all_glow = set(ALL_CUBE_COORDS)
    for _ in range(4):
        completion_flash = True
        live.update(live.render())
        time.sleep(0.1)
        completion_flash = False
        live.update(live.render())
        time.sleep(0.1)

    # Final hold: all faces lit
    completion_flash = True
    live.update(live.render())
    time.sleep(0.3)
    completion_flash = False

    all_glow = set()

    if play_sound_fn and hacker:
        import random
        if random.random() < 0.05:
            play_sound_fn("rare")
        else:
            play_sound_fn("complete")

    return all_glow, completion_flash
