"""Launch c4tui-v9 from blast CLI."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def tui_v9_version() -> str:
    """Return the version string of the c4tui-v9 binary (e.g. "v9.13.0"),
    or a sane fallback ("v9") if the binary cannot be found or run.

    Used by the desktop splash banner so the displayed version matches
    the actual bundled TUI release rather than drifting from a hardcoded
    string.
    """
    import re

    binary = find_tui_v9_binary()
    if binary is None:
        return "v9"
    try:
        proc = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "v9"
    out = (proc.stdout or "") + (proc.stderr or "")
    # Expected output: "c4tui-v9 v9.13.0 (commit=abc1234)" — grab the
    # first vMAJOR.MINOR.PATCH token. Fall back to "v9" if not found.
    m = re.search(r"v\d+\.\d+\.\d+", out)
    return m.group(0) if m else "v9"


def find_tui_v9_binary() -> Path | None:
    """Locate a built c4tui-v9 binary, or None if not found.
    Handles source tree, PATH, and PyInstaller desktop bundle (Resources for mac, next to exe for win).
    """
    # 1. Bundled PyInstaller desktop app case
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if sys.platform == "darwin":
            # .app/Contents/MacOS/blast -> .app/Contents/Resources/c4tui-v9
            res = exe_dir.parent / "Resources" / "c4tui-v9"
            if res.is_file() and os.access(res, os.X_OK):
                return res
        else:
            # Windows: alongside the exe or in dist
            for cand in [
                exe_dir / "c4tui-v9.exe",
                exe_dir / "c4tui-v9",
            ]:
                if cand.is_file():
                    return cand
        # fallback to PATH even in frozen
    # 2. Source tree / dev
    root = _repo_root()
    candidates = [
        root / "src" / "tui" / "v9" / "bin" / "c4tui-v9",
        root / "bin" / "c4tui-v9",
        Path(shutil.which("c4tui-v9") or ""),
        Path(shutil.which("c4tui-v9.exe") or ""),
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
    from src.cli.package_installer_tui import tui_package_manager

    try:
        tui_package_manager()
    except KeyboardInterrupt:
        return 130
    return 0
