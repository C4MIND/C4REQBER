"""Desktop app entry — runs blast init on first launch, then TUI v9."""
from __future__ import annotations

import sys

from src.cli.config_init import apply_config_to_env, config_exists, run_init_wizard
from src.cli.tui_launcher import launch_tui_v9


def main() -> int:
    apply_config_to_env()
    if not config_exists():
        run_init_wizard(force=False)
        apply_config_to_env()
    return launch_tui_v9([], build_if_missing=True)


if __name__ == "__main__":
    raise SystemExit(main())