"""Hatch build hook: include c4tui-v9 in the wheel only when present on disk.

Run ``scripts/ci/prepare_tui_wheel.sh`` then ``scripts/ci/build_pypi_artifacts.sh``
on CI so the platform binary is force-included. Important: build the wheel from
the working tree (``python -m build --wheel``), not from the sdist — the sdist
excludes binaries. Local builds without Go still succeed (Python-only wheel +
runtime download).
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
                print(
                    f"hatch tui-binary: force_include {src} "
                    f"({src.stat().st_size} bytes) → src/tui/v9/bin/{name}"
                )


def get_build_hook() -> type[BuildHookInterface]:
    return TuiBinaryBuildHook
