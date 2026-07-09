#!/usr/bin/env python3
"""Export FastAPI OpenAPI schema and validate TUI v9 contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Project root must be on sys.path so 'src' is importable as a package.
# Adding ROOT/src alone only exposes its submodules directly (e.g.
# 'api.server'), but FastAPI's app is reachable as 'src.api.server:app'.
sys.path.insert(0, str(ROOT))


def export_full_openapi(out: Path) -> None:
    from src.api.server import app

    schema = app.openapi()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(schema.get('paths', {}))} paths)")


def main() -> None:
    export_full_openapi(ROOT / "openapi" / "fastapi.json")
    tui_spec = ROOT / "openapi" / "tui-v9.yaml"
    if not tui_spec.exists():
        print(f"Missing contract: {tui_spec}", file=sys.stderr)
        sys.exit(1)
    print(f"TUI contract present: {tui_spec}")


if __name__ == "__main__":
    main()