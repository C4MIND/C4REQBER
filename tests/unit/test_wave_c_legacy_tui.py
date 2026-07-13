"""Wave C: legacy Python TUI removed."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_legacy_tui_modules_removed():
    removed = [
        REPO / "src/tui/main_loop.py",
        REPO / "src/tui/living_cube.py",
        REPO / "src/tui/package_installer.py",
        REPO / "src/repl/input_handler.py",
    ]
    for path in removed:
        assert not path.exists(), f"legacy file still present: {path}"


def test_tui_shims_and_installer_survive():
    keep = [
        REPO / "src/tui/__init__.py",
        REPO / "src/tui/v9",
        REPO / "src/cli/package_installer_tui.py",
    ]
    for path in keep:
        assert path.exists(), f"missing required path: {path}"
