"""TUI: Entry Point — delegates to v8 Go binary."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _find_binary() -> Path | None:
    """Locate the c4tui-v8 binary."""
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "bin" / "c4tui-v8",
        root / "src" / "tui" / "v8" / "c4tui-v8",
        root / "src" / "tui" / "v8" / "c4tui",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="c44tcdi — Cognitive Exoskeleton TUI v8")
    sub = parser.add_subparsers(dest="command")

    tui_cmd = sub.add_parser("tui", help="Interactive TUI (Go-based v8)")
    tui_cmd.add_argument("--lang", "-l", choices=["en", "ru", "zh", "ja", "de", "ar", "hi"], default=None, help="UI language")
    tui_cmd.add_argument("--theme", "-t", choices=["dark", "matrix", "paper"], default=None, help="Color theme")
    tui_cmd.add_argument("--api", default=None, help="Override API base URL")

    solve = sub.add_parser("solve", help="One-shot discovery (use CLI blast)")
    solve.add_argument("problem", help="Problem description")
    solve.add_argument("--domain", "-d", default="science")

    sub.add_parser("quickstart", help="Interactive 3-step onboarding (TUI)")
    sub.add_parser("cube", help="Show ASCII cube (TUI)")

    args = parser.parse_args()

    if args.command == "tui":
        binary = _find_binary()
        if binary is None:
            print("c4tui-v8 binary not found. Build it first:")
            print("  cd src/tui/v8 && go build -o c4tui-v8 .")
            sys.exit(1)
        cmd = [str(binary)]
        if args.lang:
            cmd += ["--lang", args.lang]
        if args.theme:
            cmd += ["--theme", args.theme]
        if args.api:
            cmd += ["--api", args.api]
        subprocess.run(cmd)
    elif args.command == "solve":
        print("Use: blast solve 'your problem' --domain science")
        sys.exit(1)
    elif args.command == "quickstart":
        binary = _find_binary()
        if binary:
            subprocess.run([str(binary)])
        else:
            print("c4tui-v8 binary not found.")
            sys.exit(1)
    elif args.command == "cube":
        binary = _find_binary()
        if binary:
            subprocess.run([str(binary)])
        else:
            print("c4tui-v8 binary not found.")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
