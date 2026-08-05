"""Suite 10 — TUI lastPapersCount counts verified sources only (Go behavioral)."""

from __future__ import annotations

import subprocess


def test_go_unverified_papers_not_counted_for_achievements() -> None:
    r = subprocess.run(
        [
            "go",
            "test",
            "-count=1",
            "-timeout",
            "60s",
            "-run",
            "UnverifiedPapersNotCounted|SSEEvent_Completed",
            ".",
        ],
        cwd="src/tui/v9",
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr
