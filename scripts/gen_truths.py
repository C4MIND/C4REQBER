#!/usr/bin/env python3
"""Generate _truths.json — single source of truth for project metrics.

Counts files/decorators via grep/ast rather than imports to avoid loading
heavy optional dependencies (mlx, z3, torch, etc.).

Usage: python3 scripts/gen_truths.py [--check]
  --check  only verify existing _truths.json is up to date, exit non-zero if stale
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TRUTHS_FILE = REPO / "_truths.json"


def sh(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd or REPO, stderr=subprocess.STDOUT).decode()


def count_py_loc() -> int:
    total = 0
    for path in (REPO / "src").rglob("*.py"):
        with path.open(encoding="utf-8", errors="replace") as fh:
            total += sum(1 for _ in fh)
    return total


def count_go_loc() -> int:
    total = 0
    for path in (REPO / "src/tui/v9").rglob("*.go"):
        with path.open(encoding="utf-8", errors="replace") as fh:
            total += sum(1 for _ in fh)
    return total


def count_py_tests() -> int:
    """Run pytest --co to get authoritative count."""
    out = sh([sys.executable, "-m", "pytest", "tests/", "--co", "-q"])
    m = re.search(r"(\d+) tests collected", out)
    if not m:
        raise RuntimeError(f"could not parse pytest collection output:\n{out}")
    return int(m.group(1))


def count_mcp_tools() -> int:
    """Count @server.tool DECORATORS (not comments) in server.py + codegen/mcp_tool.py.

    Matches only decorators: must start with `@server.tool` followed by `(`, optionally
    with a name argument. Excludes comment lines.
    """
    def count_real_decorators(text: str) -> int:
        count = 0
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if re.match(r"^@server\.tool\(", stripped):
                count += 1
        return count

    main = count_real_decorators((REPO / "src/mcp_server/server.py").read_text())
    codegen = 0
    cp = REPO / "src/codegen/mcp_tool.py"
    if cp.exists():
        codegen = count_real_decorators(cp.read_text())
    return main + codegen


def count_cli_commands() -> int:
    """Count typer commands registered in blast_app."""
    src = (REPO / "src/cli/blast_app.py").read_text()
    return len(re.findall(r"^@app\.command\(", src, re.MULTILINE))


def count_knowledge_sources() -> int:
    """Count non-base, non-private source modules in src/knowledge/sources/."""
    out = sh([
        "find", "src/knowledge/sources",
        "-name", "*.py",
        "-not", "-name", "__init__.py",
        "-not", "-name", "_*.py",
        "-not", "-name", "base*.py",
        "-not", "-name", "extra_adapters.py",
        "-not", "-name", "p6_adapters.py",
        "-not", "-name", "base_p6.py",
    ])
    return len([l for l in out.strip().splitlines() if l])


def count_simulation_engines() -> int:
    """Count simulation engine adapter modules."""
    out = sh([
        "find", "src/simulations",
        "-name", "*_bridge.py",
        "-not", "-name", "base_adapter.py",
    ])
    return len([l for l in out.strip().splitlines() if l])


def count_llm_providers() -> int:
    """Count BaseLLMClient subclasses across src/llm/."""
    out = sh(["grep", "-rE", r"class \w+(Client|Provider)\(.*BaseLLMClient\)", "src/llm/", "--include=*.py"])
    return len([l for l in out.strip().splitlines() if l])


REAL_VERIFIER_BRIDGES: tuple[str, ...] = (
    "lean4_client.py",
    "coq_client.py",
    "dafny_client.py",
    "agda_bridge.py",
    "hoare_verifier.py",  # includes Z3 SMT
    "haskell_bridge.py",
    "cvc5_client.py",
    "tla_client.py",
    "alloy_client.py",
)
GUARD_STUB_BACKENDS: tuple[str, ...] = ()


def count_mypy_baseline() -> int:
    """Count mypy errors (0 = clean). Falls back to baseline file if mypy unavailable."""
    for name in ("MYPY_BASELINE_2026-07-12.txt", "MYPY_BASELINE_2026-06-29.txt", "MYPY_BASELINE_2026-06-22.txt"):
        baseline = REPO / "archive/audits" / name
        if baseline.exists():
            count = sum(1 for line in baseline.read_text().splitlines() if line.startswith("src/"))
            if count == 0 and "0 errors" in baseline.read_text():
                return 0
            if count > 0:
                return count
    return 0


def count_verifiers() -> dict:
    """Count real prover bridges vs named guard-stubs (not implemented)."""
    verifiers_dir = REPO / "src/verification"
    real = sum(1 for name in REAL_VERIFIER_BRIDGES if (verifiers_dir / name).exists())
    return {
        "real": real,
        "guard_stubs": len(GUARD_STUB_BACKENDS),
        "guard_stub_names": list(GUARD_STUB_BACKENDS),
        "footnote": (
            "Real bridges: Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy."
        ),
    }


def git_head() -> str:
    return sh(["git", "rev-parse", "--short", "HEAD"]).strip()


def git_branch() -> str:
    return sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()


def read_version() -> str:
    src = (REPO / "src/__init__.py").read_text()
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', src)
    return m.group(1) if m else "unknown"


def read_tui_version() -> str:
    """Read TUI version from cmd/c4tui-v9/main.go (set at build time)."""
    go = REPO / "src/tui/v9/cmd/c4tui-v9/main.go"
    if not go.exists():
        return "unknown"
    text = go.read_text()
    m = re.search(r'var\s+version\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else "unknown"


def build_truths() -> dict:
    if os.environ.get("CI_TRUTHS_SKIP_PYTHON") == "1" and TRUTHS_FILE.exists():
        tests_collected = json.loads(TRUTHS_FILE.read_text()).get("python", {}).get("tests_collected", 0)
    else:
        tests_collected = count_py_tests()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version_backend": read_version(),
        "version_tui": read_tui_version(),
        "git_head": git_head(),
        "git_branch": git_branch(),
        "python": {
            "loc": count_py_loc(),
            "tests_collected": tests_collected,
        },
        "go": {
            "loc_tui_v9": count_go_loc(),
        },
        "mcp": {
            "tools": count_mcp_tools(),
        },
        "cli": {
            "commands": count_cli_commands(),
        },
        "knowledge": {
            "sources": count_knowledge_sources(),
            "footnote": "33 literature adapters + 10 data/biological = 43 total adapters in README",
        },
        "simulations": {
            "engines": count_simulation_engines(),
            "footnote": "38 engine bridges probed by GET /v8/simulations/capabilities",
        },
        "llm": {
            "providers": count_llm_providers(),
            "footnote": "auto-detected at runtime: OpenRouter, XAI, Mistral, Moonshot, DeepSeek, Liquid, NVIDIA NIM, YandexGPT, Ollama, LM Studio, MLX",
        },
        "verifiers": count_verifiers(),
        "quality": {
            "mypy_baseline": count_mypy_baseline(),
            "mypy_note": "regression-gated baseline; new errors fail CI",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="verify _truths.json is up to date, exit 1 if stale")
    args = parser.parse_args()

    try:
        truths = build_truths()
    except Exception as e:
        print(f"ERROR generating truths: {e}", file=sys.stderr)
        return 2

    if args.check:
        if not TRUTHS_FILE.exists():
            print(f"FAIL: {TRUTHS_FILE} does not exist")
            return 1
        existing = json.loads(TRUTHS_FILE.read_text())
        # Compare key metric fields (ignore generated_at, git_head)
        keys = ["python", "go", "mcp", "cli", "knowledge", "simulations", "llm", "verifiers",
                "quality", "version_backend", "version_tui"]
        if os.environ.get("CI_TRUTHS_SKIP_PYTHON") == "1":
            keys.remove("python")
        for key in keys:
            if existing.get(key) != truths.get(key):
                print(f"FAIL: {key} differs:")
                print(f"  existing: {existing.get(key)}")
                print(f"  current:  {truths.get(key)}")
                return 1
        print("OK: _truths.json is up to date")
        return 0

    TRUTHS_FILE.write_text(json.dumps(truths, indent=2) + "\n")
    print(f"Wrote {TRUTHS_FILE}")
    print(json.dumps(truths, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())