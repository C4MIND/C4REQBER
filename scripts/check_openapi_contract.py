#!/usr/bin/env python3
"""Validate that openapi/tui-v9.yaml operations are all present in the
FastAPI-generated spec (openapi/fastapi.json).

Audit 2026-06-22 item 13 / REWORK_PLAN P3-1: the TUI's Go client is
generated from openapi/tui-v9.yaml. If the FastAPI backend drifts
(rename, delete, or change operationId), the TUI silently breaks at
runtime. This script enforces that the TUI's contract is a subset
of the live backend's exported spec.

Usage:
    python3 scripts/export_openapi.py              # regenerate fastapi.json
    python3 scripts/check_openapi_contract.py      # validate contract
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
TUI_SPEC = REPO / "openapi" / "tui-v9.yaml"
FA_SPEC = REPO / "openapi" / "fastapi.json"

# TUI spec is YAML but we only need operationIds + their HTTP method+path.
# Simple regex extraction: every "      operationId: <id>" line + the path
# it appears under. (YAML is line-oriented enough for this.)
OPERATION_ID_RE = re.compile(r"^\s*operationId:\s*(\w+)\s*$")
PATH_RE = re.compile(r"^  (\S+):\s*$")
METHOD_RE = re.compile(r"^\s+(get|post|put|patch|delete):\s*$")


def parse_tui_operations() -> dict[str, tuple[str, str]]:
    """Return {operationId: (method, path)} from tui-v9.yaml.

    Simple stateful parser: track current path + method, then capture
    the operationId at the right indentation. Robust enough for the
    project's TUI contract file (which is hand-written, not generated).
    """
    ops: dict[str, tuple[str, str]] = {}
    if not TUI_SPEC.exists():
        return ops
    current_path: str | None = None
    current_method: str | None = None
    for line in TUI_SPEC.read_text().splitlines():
        m_path = PATH_RE.match(line)
        if m_path:
            current_path = m_path.group(1)
            current_method = None
            continue
        m_method = METHOD_RE.match(line)
        if m_method:
            current_method = m_method.group(1)
            continue
        m_op = OPERATION_ID_RE.match(line)
        if m_op and current_path and current_method:
            ops[m_op.group(1)] = (current_method.upper(), current_path)
    return ops


def parse_fastapi_operations() -> dict[str, tuple[str, str]]:
    """Return {operationId: (method, path)} from fastapi.json."""
    if not FA_SPEC.exists():
        return {}
    spec = json.loads(FA_SPEC.read_text())
    ops: dict[str, tuple[str, str]] = {}
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if op_id:
                ops[op_id] = (method.upper(), path)
    return ops


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if the TUI contract has more operations than the FastAPI spec "
             "(e.g. someone added to tui-v9.yaml but didn't implement the route).",
    )
    args = parser.parse_args()

    tui_ops = parse_tui_operations()
    fa_ops = parse_fastapi_operations()

    if not tui_ops:
        print(f"ERROR: TUI contract {TUI_SPEC.relative_to(REPO)} not found or empty", file=sys.stderr)
        return 2
    if not fa_ops:
        print(f"ERROR: FastAPI spec {FA_SPEC.relative_to(REPO)} not found or empty — run scripts/export_openapi.py first", file=sys.stderr)
        return 2

    missing_in_fastapi = {
        op_id: (method, path)
        for op_id, (method, path) in tui_ops.items()
        if op_id not in fa_ops
    }
    extra_in_fastapi = {
        op_id: (method, path)
        for op_id, (method, path) in fa_ops.items()
        if op_id not in tui_ops
    }
    drift = {
        op_id: {"tui": tui_ops[op_id], "fastapi": fa_ops[op_id]}
        for op_id in tui_ops
        if op_id in fa_ops and tui_ops[op_id] != fa_ops[op_id]
    }

    print(f"TUI contract operations:    {len(tui_ops)}")
    print(f"FastAPI spec operations:    {len(fa_ops)}")
    print(f"Missing in FastAPI:         {len(missing_in_fastapi)}" + (" ← FAIL" if missing_in_fastapi else " ✓"))
    print(f"Method/path drift:          {len(drift)}" + (" ← FAIL" if drift else " ✓"))
    if args.strict:
        print(f"Extra in FastAPI (not in TUI): {len(extra_in_fastapi)}" + (" ← FAIL" if extra_in_fastapi else " ✓"))

    if missing_in_fastapi:
        print("\nMissing operations (TUI expects but FastAPI doesn't expose):")
        for op_id, (method, path) in sorted(missing_in_fastapi.items()):
            print(f"  - {op_id}  {method} {path}")
    if drift:
        print("\nDrifted operations (TUI and FastAPI disagree on method/path):")
        for op_id, d in sorted(drift.items()):
            print(f"  - {op_id}  TUI={d['tui']}  FastAPI={d['fastapi']}")
    if args.strict and extra_in_fastapi:
        print(f"\nExtra operations in FastAPI (not referenced by TUI): {len(extra_in_fastapi)} total")
        # Just show first 5 — this is informational
        for op_id, (method, path) in list(sorted(extra_in_fastapi.items()))[:5]:
            print(f"  - {op_id}  {method} {path}")
        if len(extra_in_fastapi) > 5:
            print(f"  ... and {len(extra_in_fastapi) - 5} more")

    if missing_in_fastapi or drift or (args.strict and extra_in_fastapi):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
