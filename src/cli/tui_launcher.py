"""Launch c4tui-v9 from blast CLI."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from src.cli.tui_binary import ensure_tui_binary, find_tui_v9_binary


__all__ = [
    "build_tui_v9",
    "ensure_tui_binary",
    "find_tui_v9_binary",
    "launch_package_installer",
    "launch_tui_v9",
    "tui_v9_version",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def tui_v9_version() -> str:
    """Return the version string of the c4tui-v9 binary (e.g. "v9.13.0"),
    or a sane fallback ("v9") if the binary cannot be found or run.
    """
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
    m = re.search(r"v\d+\.\d+\.\d+", out)
    return m.group(0) if m else "v9"


def build_tui_v9() -> Path:
    """Build c4tui-v9 via go build (make on Unix if available)."""
    v9_dir = _repo_root() / "src" / "tui" / "v9"
    if not v9_dir.is_dir():
        raise FileNotFoundError(f"TUI v9 source not found: {v9_dir}")

    bin_dir = v9_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    out_name = "c4tui-v9.exe" if sys.platform == "win32" else "c4tui-v9"
    out_path = bin_dir / out_name

    go = shutil.which("go")
    if go:
        result = subprocess.run(
            [go, "build", "-o", str(out_path), "."],
            cwd=v9_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            msg = result.stderr.strip() or result.stdout.strip() or "go build failed"
            raise RuntimeError(f"Failed to build c4tui-v9: {msg}")
        if out_path.is_file():
            return out_path

    if shutil.which("make"):
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
        binary = bin_dir / "c4tui-v9"
        if binary.is_file():
            return binary

    raise RuntimeError(
        "Cannot build c4tui-v9: install Go (https://go.dev/dl/) or place a prebuilt binary on PATH"
    )


def launch_tui_v9(extra_args: list[str] | None = None, *, build_if_missing: bool = True) -> int:
    """Exec c4tui-v9 with optional extra CLI args. Returns exit code."""
    args = extra_args or []
    binary = find_tui_v9_binary()
    if binary is None and build_if_missing:
        # Prefer release asset download (works on Windows without Go)
        binary = ensure_tui_binary(download=True)
    if binary is None:
        if not build_if_missing:
            print("c4tui-v9 not found. Build it first:")
            print("  cd src/tui/v9 && make build")
            return 1
        if shutil.which("go") is None:
            print(
                "c4tui-v9 not found (not in wheel / PATH / ~/.c4reqber/bin).\n"
                "Options:\n"
                "  1) Set C4REQBER_TUI_URL to a direct download of the platform binary\n"
                "  2) Install Go (https://go.dev/dl/) then: cd src/tui/v9 && go build -o bin/c4tui-v9 .\n"
                "  3) Place c4tui-v9 on PATH (GitLab release asset)\n"
                "Meanwhile use: blast flash / blast solve / blast turbo"
            )
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
