"""Launch c4tui-v9 from blast CLI."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_tui_v9_binary() -> Path | None:
    """Locate a built c4tui-v9 binary, or None if not found."""
    root = _repo_root()
    candidates = [
        root / "src" / "tui" / "v9" / "bin" / "c4tui-v9",
        root / "bin" / "c4tui-v9",
        Path(shutil.which("c4tui-v9") or ""),
    ]
    for path in candidates:
        if path and path.is_file() and os.access(path, os.X_OK):
            return path
    return None


def build_tui_v9() -> Path:
    """Build c4tui-v9 via make and return the binary path."""
    v9_dir = _repo_root() / "src" / "tui" / "v9"
    if not v9_dir.is_dir():
        raise FileNotFoundError(f"TUI v9 source not found: {v9_dir}")

    result = subprocess.run(
        ["make", "build"],
        cwd=v9_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "make build failed"
        raise RuntimeError(f"Failed to build c4tui-v9: {msg}")

    binary = v9_dir / "bin" / "c4tui-v9"
    if not binary.is_file():
        raise FileNotFoundError(f"Build succeeded but binary missing: {binary}")
    return binary


def launch_tui_v9(extra_args: list[str] | None = None, *, build_if_missing: bool = True) -> int:
    """Exec c4tui-v9 with optional extra CLI args. Returns exit code."""
    args = extra_args or []
    binary = find_tui_v9_binary()
    if binary is None:
        if not build_if_missing:
            print("c4tui-v9 not found. Build it first:")
            print("  cd src/tui/v9 && make build")
            return 1
        try:
            binary = build_tui_v9()
            print(f"Built c4tui-v9 → {binary}")
        except (OSError, RuntimeError, FileNotFoundError) as exc:
            print(f"Error: {exc}")
            return 1

    proc = subprocess.run([str(binary), *args])
    return proc.returncode


def launch_package_installer() -> int:
    """Open the Rich arrow-key package installer (Python TUI)."""
    from src.tui.package_installer import tui_package_manager

    try:
        tui_package_manager()
    except KeyboardInterrupt:
        return 130
    return 0