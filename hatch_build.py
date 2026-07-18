"""Hatch build hook: include c4tui-v9 in the wheel only when present on disk.

Run ``scripts/ci/prepare_tui_wheel.sh`` before ``python -m build`` on CI so the
platform binary is force-included. Local builds without Go still succeed
(Python-only wheel + runtime download).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class TuiBinaryBuildHook(BuildHookInterface):
    PLUGIN_NAME = "tui-binary"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        root = Path(self.root)
        bin_dir = root / "src" / "tui" / "v9" / "bin"
        force: dict[str, str] = build_data.setdefault("force_include", {})
        for name in ("c4tui-v9", "c4tui-v9.exe"):
            src = bin_dir / name
            if src.is_file() and src.stat().st_size > 0:
                force[str(src)] = f"src/tui/v9/bin/{name}"


def get_build_hook() -> type[BuildHookInterface]:
    return TuiBinaryBuildHook
