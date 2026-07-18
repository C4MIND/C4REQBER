#!/usr/bin/env python3
"""Vast/remote simulation entrypoint — reads JSON config, prints JSON result.

Usage:
  python -m src.simulations.vast_remote_runner --config /tmp/c4_sim_config.json
  # or
  python src/simulations/vast_remote_runner.py --config /tmp/c4_sim_config.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _run(config: dict[str, Any]) -> dict[str, Any]:
    engine = str(config.get("engine") or "newton").lower()
    if engine in {"newton", "newton-physics", "newton_physics"}:
        from src.simulations.newton_runner import run_newton_simulation

        out = run_newton_simulation(config)
        out.setdefault("engine", "newton")
        return out

    if engine in {"amuse", "rebound", "nbody"}:
        from src.simulations.amuse_bridge import AmuseBridge

        bridge = AmuseBridge()
        result = bridge.run(config)
        data = result.data if hasattr(result, "data") else {}
        status = result.status.value if hasattr(result.status, "value") else str(result.status)
        return {
            "status": "completed" if status == "success" else status,
            "executed": data.get("executed", status == "success"),
            "stub": data.get("stub", status != "success"),
            "engine": engine,
            "backend": data.get("backend"),
            "data": data,
        }

    return {
        "status": "unavailable",
        "executed": False,
        "stub": True,
        "error": f"Unsupported engine={engine!r} for vast_remote_runner",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True, help="Path to JSON config")
    args = p.parse_args(argv)
    path = Path(args.config)
    config = json.loads(path.read_text(encoding="utf-8"))
    result = _run(config)
    print(json.dumps(result))
    ok = bool(result.get("executed")) and not result.get("stub")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
