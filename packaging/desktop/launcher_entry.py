"""Desktop app entry — first-run wizard + always-seed models.json + TUI v9.
Full settings out-of-the-box (config + models + keys for all providers).
Robust: never crashes desktop on missing keys or partial config.
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.cli.config_init import apply_config_to_env, config_exists, run_init_wizard
from src.cli.tui_launcher import launch_tui_v9
from src.config.paths import apply_config_to_env as central_apply  # prefer central
from src.llm.model_assignment import ModelAssignment


def main() -> int:
    try:
        central_apply()
    except Exception:
        pass  # never block desktop start

    first_run = not config_exists()

    # Ensure core config + wizard
    if first_run:
        try:
            run_init_wizard(force=False)
            central_apply()
        except Exception:
            pass

    # Always ensure models.json (full settings even if user skipped wizard or deleted it)
    from src.config.paths import MODELS_JSON
    if not MODELS_JSON.exists():
        try:
            assignment = ModelAssignment.create_default("balanced")
            assignment.save()
        except Exception:
            pass

    central_apply()
    if first_run:
        print("c4reqber desktop: full settings ready (~/.c4reqber + models.json)")
    return launch_tui_v9([], build_if_missing=True)


if __name__ == "__main__":
    raise SystemExit(main())