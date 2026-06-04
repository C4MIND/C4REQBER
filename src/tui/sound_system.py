"""
TUI: Sound System
Sound effects using pygame.mixer.
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from typing import Any


try:
    import pygame  # type: ignore[import-untyped]

    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.mixer.init()
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

SOUNDS_DIR = Path(__file__).parent / "sounds"
_sound_cache: dict[str, Any] = {}

SOUNDS: dict[str, str] = {
    "step": "step.wav",
    "complete": "complete.wav",
    "rare": "rare.wav",
    "error": "error.wav",
    "welcome": "welcome.wav",
}


def _ensure_sounds() -> None:
    if not SOUNDS_DIR.exists():
        SOUNDS_DIR.mkdir(parents=True, exist_ok=True)


def generate_tone(filename: str, freq: float, duration: float, volume: float = 0.3) -> str:
    """Generate a sine wave tone and save as WAV."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    filepath = SOUNDS_DIR / filename
    with wave.open(str(filepath), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for i in range(n_samples):
            value = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            f.writeframes(struct.pack("<h", value))
    return str(filepath)


def play_sound(name: str) -> None:
    """Play a sound by name."""
    if not HAS_SOUND:
        return
    if name not in SOUNDS:
        return
    filepath = SOUNDS_DIR / SOUNDS[name]
    if not filepath.exists():
        return
    try:
        sound = pygame.mixer.Sound(str(filepath))
        sound.play()
        _sound_cache[name] = sound
    except (AttributeError, ImportError):
        pass
