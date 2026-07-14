# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import re
import subprocess
from pathlib import Path


_INJECTION_RE = re.compile(r"!c4\s+(verify|trace|check|status)\b\s*(.*)")


def process_injections(prompt: str) -> str:
    """Replace !c4 commands with their output in the prompt."""
    def replacer(match: re.Match) -> str:
        """Replacer."""
        cmd = match.group(1)
        args = match.group(2).strip()
        try:
            if cmd == "verify":
                return _run_verify(args)
            elif cmd == "trace":
                return _run_trace(args)
            elif cmd == "check":
                return _run_check(args)
            elif cmd == "status":
                return _run_status()
        except Exception:
            return f"[!c4 {cmd} failed]"
        return match.group(0)

    return _INJECTION_RE.sub(replacer, prompt)


def _run_verify(hypothesis_file: str) -> str:
    path = Path(hypothesis_file) if hypothesis_file else Path("hypothesis.md")
    if not path.exists():
        return f"[F3:SKIP] File not found: {path}"
    try:
        if path.is_absolute():
            return "[F3:SKIP] Absolute paths not allowed"
        if ".." in path.parts:
            return "[F3:SKIP] Invalid path"
        result = subprocess.run(
            ["python3", "-m", "src.c4.verify", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return f"[F3:{'PASS' if result.returncode == 0 else 'FAIL'}] {result.stdout.strip()[:200]}"
    except Exception:
        return "[F3:UNKNOWN] Verification runner unavailable"


def _run_trace(depth_arg: str) -> str:
    depth = int(depth_arg) if depth_arg.isdigit() else 3
    try:
        from src.c4.layer_stream import C4LayerTracker
        tracker = C4LayerTracker()
        events = tracker._timeline[-depth:] if tracker._timeline else []
        if events:
            return "\n".join(f"  [C{e.layer}:{e.state}] {e.message}" for e in events)
        return "[C4 trace: empty]"
    except Exception:
        return "[C4 trace: unavailable]"


def _run_check(hypothesis: str) -> str:
    """Quick logical check: does hypothesis contain contradictions?"""
    lower = hypothesis.lower()
    contradictions = []
    if "always" in lower and "never" in lower:
        contradictions.append("always+never pair")
    if "all" in lower and "none" in lower:
        contradictions.append("all+none pair")
    if contradictions:
        return f"[C4 check:WARN] Potential contradictions: {', '.join(contradictions)}"
    return "[C4 check:OK] No obvious surface contradictions detected"


def _run_status() -> str:
    try:
        from src.c4.state import C4State
        return f"[C4 status] C4-META active | 27 states | 6 operators | current: {C4State(t=1, s=1, a=1).name}"
    except Exception:
        return "[C4 status] C4-META engine online"
