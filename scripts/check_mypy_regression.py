#!/usr/bin/env python3
"""Mypy regression check — fails if new mypy errors appear vs baseline.

Audit 2026-06-22: pre-existing mypy errors are tracked in
archive/audits/MYPY_BASELINE_2026-06-22.txt (61 errors pre-fixup).
This script runs mypy on src/ and reports any NEW errors not in the
baseline. Use as a CI gate that prevents future regressions without
requiring all 61 historical errors to be fixed first.

Usage:
    python3 scripts/check_mypy_regression.py
    python3 scripts/check_mypy_regression.py --baseline <file>  # custom
    python3 scripts/check_mypy_regression.py --update            # refresh baseline
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
BASELINE_DEFAULT = REPO / "archive" / "audits" / "MYPY_BASELINE_2026-06-22.txt"

# Match mypy error lines (skip notes/hints). Pattern: "path:line: error: msg [code]"
ERROR_RE = re.compile(r"^(src/[^:]+):(\d+):\s*error:\s*(.+?)(?:\s*\[([\w-]+)\])?$")


def run_mypy() -> str:
    """Run mypy on src/ and return the raw output (errors + notes)."""
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "src"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    # mypy writes to stdout; capture both for safety
    return (result.stdout or "") + (result.stderr or "")


def parse_errors(output: str) -> set[tuple[str, int, str]]:
    """Extract (path, line, message) tuples from mypy output."""
    errors: set[tuple[str, int, str]] = set()
    for line in output.splitlines():
        m = ERROR_RE.match(line.strip())
        if m:
            path, line_no, msg = m.group(1), int(m.group(2)), m.group(3).strip()
            errors.add((path, line_no, msg))
    return errors


def load_baseline(path: Path) -> set[tuple[str, int, str]]:
    """Load baseline errors. Each non-empty, non-# line is a mypy error line."""
    if not path.exists():
        return set()
    errors: set[tuple[str, int, str]] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = ERROR_RE.match(line)
        if m:
            path_str, line_no, msg = m.group(1), int(m.group(2)), m.group(3).strip()
            errors.add((path_str, line_no, msg))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE_DEFAULT,
        help=f"Baseline file (default: {BASELINE_DEFAULT.relative_to(REPO)})",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Overwrite the baseline with the current mypy output (review the diff first!)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail if errors were REMOVED (i.e. someone fixed a baseline error). "
             "Off by default because removing errors is good.",
    )
    args = parser.parse_args()

    output = run_mypy()
    current = parse_errors(output)
    baseline = load_baseline(args.baseline)

    if args.update:
        args.baseline.write_text(
            "# Auto-generated mypy baseline. Refresh with --update.\n"
            + "\n".join(sorted(f"{p}:{l}: error: {m}" for p, l, m in current))
            + "\n"
        )
        print(f"Baseline updated: {len(current)} errors written to {args.baseline.relative_to(REPO)}")
        return 0

    new_errors = current - baseline
    fixed_errors = baseline - current if args.strict else set()

    print(f"Baseline errors: {len(baseline)}")
    print(f"Current errors:  {len(current)}")
    print(f"New errors:      {len(new_errors)}" + (" ← FAIL" if new_errors else " ✓"))
    if args.strict:
        print(f"Fixed errors:    {len(fixed_errors)}" + (" ← FAIL" if fixed_errors else " ✓"))

    if new_errors:
        print("\nNew errors (regressions):")
        for p, l, m in sorted(new_errors):
            print(f"  {p}:{l}: {m}")
    if args.strict and fixed_errors:
        print("\nFixed errors (need baseline refresh):")
        for p, l, m in sorted(fixed_errors):
            print(f"  {p}:{l}: {m}")

    if new_errors or (args.strict and fixed_errors):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
