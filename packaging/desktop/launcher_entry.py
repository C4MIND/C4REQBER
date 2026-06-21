"""Desktop app entry — runs blast init on first launch, then TUI v9.
Polished for full settings experience: config.toml + models.json + env export
(OPENROUTER, DEEPSEEK, BRAVE, TAVILY, EXA, XAI + Lean4).
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.cli.config_init import apply_config_to_env, config_exists, run_init_wizard
from src.cli.tui_launcher import launch_tui_v9
from src.config.paths import apply_config_to_env as central_apply  # prefer central
from src.llm.model_assignment import ModelAssignment


def main() -> int:
    central_apply()

    # Ensure core config
    if not config_exists():
        run_init_wizard(force=False)
        central_apply()

    # Polish: ensure models.json exists with sensible default (balanced tier)
    # so TUI/CLI have "all settings" ready out of box for desktop app
    from src.config.paths import MODELS_JSON
    if not MODELS_JSON.exists():
        try:
            assignment = ModelAssignment.create_default("balanced")
            assignment.save()
        except Exception:
            pass  # non-fatal for first run

    central_apply()  # re-apply after possible model setup
    return launch_tui_v9([], build_if_missing=True)


if __name__ == "__main__":
    raise SystemExit(main())