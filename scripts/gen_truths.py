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
    out = sh(["bash", "-c", "find src -name '*.py' -exec wc -l {} + | tail -1"])
    return int(out.strip().split()[0])


def count_go_loc() -> int:
    out = sh(["bash", "-c", "find src/tui/v9 -name '*.go' -exec wc -l {} + | tail -1"])
    return int(out.strip().split()[0])


def count_py_tests() -> int:
    """Run pytest --co to get authoritative count."""
    out = sh([".venv/bin/python", "-m", "pytest", "tests/", "--co", "-q"])
    m = re.search(r"(\d+) tests collected", out)
    if not m:
        raise RuntimeError(f"could not parse pytest collection output:\n{out}")
    return int(m.group(1))


def count_mcp_tools() -> int:
    """Count @server.tool decorators in src/mcp_server/server.py + codegen/mcp_tool.py."""
    main_count = len(re.findall(r"@server\.tool\(", (REPO / "src/mcp_server/server.py").read_text()))
    codegen_path = REPO / "src/codegen/mcp_tool.py"
    if codegen_path.exists():
        codegen_count = len(re.findall(r"@server\.tool\(", codegen_path.read_text()))
    else:
        codegen_count = 0
    return main_count + codegen_count


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


def count_verifiers() -> dict[str, int]:
    """Count real verifiers vs guard-stubs."""
    verifiers_dir = REPO / "src/verification"
    if not verifiers_dir.exists():
        return {"real": 0, "stubs": 0}
    real, stubs = 0, 0
    for f in verifiers_dir.glob("*.py"):
        if f.name.startswith("_") or f.name == "__init__.py":
            continue
        text = f.read_text()
        if "GUARD_STUB" in text or "guard-stub" in text or "guard_stub" in text:
            stubs += 1
        elif "def verify" in text or "def run" in text or "class " in text and "Verifier" in text:
            real += 1
    return {"real": real, "stubs": stubs}


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
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version_backend": read_version(),
        "version_tui": read_tui_version(),
        "git_head": git_head(),
        "git_branch": git_branch(),
        "python": {
            "loc": count_py_loc(),
            "tests_collected": count_py_tests(),
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
            "footnote": "5 internal + 26 P1 bridges + 1 virtual bio = 32 (matching TUI v9 capabilities overlay)",
        },
        "llm": {
            "providers": count_llm_providers(),
            "footnote": "auto-detected at runtime: OpenRouter, XAI, Mistral, Moonshot, DeepSeek, Liquid, NVIDIA NIM, YandexGPT, Ollama, LM Studio, MLX",
        },
        "verifiers": count_verifiers(),
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
        for key in ["python", "go", "mcp", "cli", "knowledge", "simulations", "llm", "verifiers",
                    "version_backend", "version_tui"]:
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