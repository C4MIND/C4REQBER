#!/usr/bin/env python3
"""
C4REQBER: R1 CLI v3.0
Compatibility wrapper — re-exports everything from the modular r1 package.
"""
from __future__ import annotations

import sys
from pathlib import Path


_project_root = Path(__file__).resolve().parent.parent
_src = _project_root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# Re-export core UI components
from r1.core import UI, Style

# Re-export operations and main entry point
from r1.operations import (
    cmd_discover,
    cmd_operators,
    cmd_research,
    cmd_solve,
    cmd_stats,
    cmd_validate,
    main,
)


__all__ = [
    "Style",
    "UI",
    "cmd_solve",
    "cmd_discover",
    "cmd_research",
    "cmd_stats",
    "cmd_validate",
    "cmd_operators",
    "main",
]

if __name__ == "__main__":
    sys.exit(main())
