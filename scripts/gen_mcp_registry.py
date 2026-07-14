#!/usr/bin/env python3
"""Regenerate docs/mcp_registry.md from actual @server.tool decorators.

Usage: python3 scripts/gen_mcp_registry.py [--check]

  --check  only verify the doc is up to date; exit 1 if stale
"""

from __future__ import annotations

import argparse
import ast
import datetime
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SERVER_PY = REPO / "src/mcp_server/server.py"
CODEGEN_PY = REPO / "src/codegen/mcp_tool.py"
SCHEMAS_PY = REPO / "src/mcp_server/tool_schemas.py"
REGISTRY_MD = REPO / "docs/mcp_registry.md"


def extract_function_docs(texts: list[str]) -> dict[str, str]:
    """Collect first docstring lines from split tool implementation modules."""
    docs: dict[str, str] = {}
    for text in texts:
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                doc = ast.get_docstring(node)
                if doc:
                    docs[node.name] = doc.strip().splitlines()[0]
    return docs


def extract_tools(text: str, docs: dict[str, str] | None = None) -> list[tuple[str, str, str]]:
    """Return (name, params, first_docstring_line) for every @server.tool decorator."""
    tools: list[tuple[str, str, str]] = []
    docs = docs or {}
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "server"
                and decorator.func.attr == "tool"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                doc = ast.get_docstring(node)
                tools.append(
                    (
                        decorator.args[0].value,
                        ast.unparse(node.args),
                        doc.strip().splitlines()[0]
                        if doc
                        else docs.get(node.name, "No description."),
                    )
                )
                break
    return tools


def build_markdown(tools: list[tuple[str, str, str]]) -> str:
    tools = sorted(tools, key=lambda t: t[0])
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    md = f"""# MCP Server Tool Registry

> **Last regenerated:** {now}
> **Source of truth:** this file is regenerated from `@server.tool` decorators and
> split implementations in `src/mcp_server/` + `src/codegen/mcp_tool.py`. To update, run
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
    implementation_texts = [
        path.read_text() for path in sorted((REPO / "src/mcp_server").glob("tools_*.py"))
    ]
    docs = extract_function_docs([server, codegen, *implementation_texts])
    tools = extract_tools(server, docs) + extract_tools(codegen, docs)

    if args.check:
        existing = REGISTRY_MD.read_text() if REGISTRY_MD.exists() else ""
        expected = build_markdown(tools)

        def stable_lines(markdown: str) -> list[str]:
            return [
                line
                for line in markdown.splitlines()
                if not line.startswith("> **Last regenerated:**")
            ]

        if stable_lines(existing) != stable_lines(expected):
            print(f"FAIL: {REGISTRY_MD} is stale; run scripts/gen_mcp_registry.py")
            return 1
        print(f"OK: registry lists {len(tools)} tools")
        return 0

    REGISTRY_MD.write_text(build_markdown(tools))
    print(f"Wrote {REGISTRY_MD} ({len(tools)} tools)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
