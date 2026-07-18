#!/usr/bin/env python3
"""Standalone Vast entrypoint (no package imports beyond newton_runner)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    args = p.parse_args(argv)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    # Ensure newton_runner is importable from /app
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from newton_runner import run_newton_simulation  # type: ignore

    engine = str(config.get("engine") or "newton").lower()
    if engine not in {"newton", "newton-physics", "newton_physics", "amuse", "rebound", "nbody"}:
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "executed": False,
                    "stub": True,
                    "error": f"unsupported engine={engine}",
                }
            )
        )
        return 2
    # Map amuse/rebound requests to newton multi-sphere if rebound not used here
    if engine in {"amuse", "rebound", "nbody"}:
        config = {**config, "type": config.get("type") or "n_body"}
    out = run_newton_simulation(config)
    out.setdefault("engine", engine)
    print(json.dumps(out))
    ok = (
        bool(out.get("executed"))
        and not out.get("stub")
        and out.get("status")
        in {
            "success",
            "completed",
            "partial",
        }
    )
    # partial numpy is ok for remote smoke; prefer success
    return 0 if ok and out.get("status") != "unavailable" else 2


if __name__ == "__main__":
    sys.exit(main())
