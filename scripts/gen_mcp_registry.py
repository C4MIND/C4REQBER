#!/usr/bin/env python3
"""Regenerate docs/mcp_registry.md from actual @server.tool decorators.

Usage: python3 scripts/gen_mcp_registry.py [--check]

  --check  only verify the doc is up to date; exit 1 if stale
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SERVER_PY = REPO / "src/mcp_server/server.py"
CODEGEN_PY = REPO / "src/codegen/mcp_tool.py"
SCHEMAS_PY = REPO / "src/mcp_server/tool_schemas.py"
REGISTRY_MD = REPO / "docs/mcp_registry.md"


def extract_tools(text: str) -> list[tuple[str, str, str]]:
    """Return (name, params, first_docstring_line) for every @server.tool decorator."""
    pattern = re.compile(
        r'@server\.tool\(\s*"([^"]+)"\s*\)\s*\n\s*async\s+def\s+\w+\(([^)]*)\)\s*->\s*[^:]+:\s*\n\s*"""([^"]+)"""',
        re.MULTILINE,
    )
    return [(m.group(1), m.group(2).strip(), m.group(3).strip().splitlines()[0])
            for m in pattern.finditer(text)]


def build_markdown(tools: list[tuple[str, str, str]]) -> str:
    tools = sorted(tools, key=lambda t: t[0])
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = f"""# MCP Server Tool Registry

> **Last regenerated:** {now}
> **Source of truth:** this file is regenerated from `@server.tool` decorators in
> `src/mcp_server/server.py` + `src/codegen/mcp_tool.py`. To update, run
> `python3 scripts/gen_mcp_registry.py` (or `--check` in CI).

**Total tools: {len(tools)}**

## Tools

| # | Tool name | Parameters | Description |
|---|-----------|------------|-------------|
"""
    for i, (name, params, doc) in enumerate(tools, 1):
        # Escape pipe characters in cells
        params = params.replace("|", "\\|")
        doc = doc.replace("|", "\\|")
        md += f"| {i} | `{name}` | `{params}` | {doc} |\n"

    md += """
## Verification

```bash
# Count @server.tool decorators
grep -c "@server.tool(" src/mcp_server/server.py src/codegen/mcp_tool.py

# Run integration smoke test (every tool returns a structured dict)
blast serve --mcp  # then connect with any MCP client
```

## Schema registry

JSON Schemas for inputs/outputs live in `src/mcp_server/tool_schemas.py`
(`INPUT_SCHEMAS`, `OUTPUT_SCHEMAS`). The fallback server reads `tool_func.schema`
when the SDK is unavailable; `c4_codegen` was added in audit 2026-06-22
(see `audit/MASTER_AUDIT_2026-06-22.md`).
"""
    return md


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    server = SERVER_PY.read_text()
    codegen = CODEGEN_PY.read_text() if CODEGEN_PY.exists() else ""
    tools = extract_tools(server) + extract_tools(codegen)

    if args.check:
        existing = REGISTRY_MD.read_text() if REGISTRY_MD.exists() else ""
        expected_count = f"Total tools: {len(tools)}"
        if expected_count not in existing:
            print(f"FAIL: expected '{expected_count}' in {REGISTRY_MD}")
            return 1
        print(f"OK: registry lists {len(tools)} tools")
        return 0

    REGISTRY_MD.write_text(build_markdown(tools))
    print(f"Wrote {REGISTRY_MD} ({len(tools)} tools)")
    return 0


if __name__ == "__main__":
    sys.exit(main())