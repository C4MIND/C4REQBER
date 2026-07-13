"""Compatibility entry point for the supported TUI v9 binary."""

from __future__ import annotations

import argparse
import sys

from src.cli.tui_launcher import launch_tui_v9


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="C4REQBER TUI v9")
    sub = parser.add_subparsers(dest="command")

    tui_cmd = sub.add_parser("tui", help="Interactive TUI v9 cockpit")
    tui_cmd.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to c4tui-v9")

    solve = sub.add_parser("solve", help="One-shot discovery (use CLI blast)")
    solve.add_argument("problem", help="Problem description")
    solve.add_argument("--domain", "-d", default="science")

    sub.add_parser("quickstart", help="Interactive 3-step onboarding (TUI)")
    sub.add_parser("cube", help="Show ASCII cube (TUI)")

    args = parser.parse_args()

    if args.command == "tui":
        raise SystemExit(launch_tui_v9(args.args))
    elif args.command == "solve":
        print("Use: blast solve 'your problem' --domain science")
        sys.exit(1)
    elif args.command == "quickstart":
        raise SystemExit(launch_tui_v9())
    elif args.command == "cube":
        raise SystemExit(launch_tui_v9())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
