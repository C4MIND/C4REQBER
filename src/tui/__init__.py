"""C4REQBER TUI Package — delegates to v8 Go binary."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _find_binary() -> Path | None:
    """Locate the c4tui-v8 binary."""
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "bin" / "c4tui-v8",
        root / "src" / "tui" / "v8" / "c4tui-v8",
        root / "src" / "tui" / "v8" / "c4tui",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main() -> None:
    """Entry point for C4REQBER TUI v8."""
    binary = _find_binary()
    if binary is None:
        print("c4tui-v8 binary not found. Build it first:")
        print("  cd src/tui/v8 && go build -o c4tui-v8 .")
        sys.exit(1)

    # Forward all CLI args to the Go binary
    subprocess.run([str(binary)] + sys.argv[1:])
