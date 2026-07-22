"""Locate / fetch the c4tui-v9 binary for ``blast tui``.

Search order:
  1. PyInstaller frozen bundle
  2. Wheel/package data under ``src/tui/v9/bin/``
  3. Dev source tree ``src/tui/v9/bin/``
  4. ``~/.c4reqber/bin/`` (auto-download cache)
  5. ``PATH``

If still missing, ``ensure_tui_binary()`` downloads a platform asset from
GitLab Releases (or ``C4REQBER_TUI_URL``).
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path


logger = logging.getLogger(__name__)

_GITLAB_PROJECT = "cognitive-functors/c4reqber"
_GITLAB_API = f"https://gitlab.com/api/v4/projects/{_GITLAB_PROJECT.replace('/', '%2F')}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _package_bin_dir() -> Path:
    """Installed package bin dir (next to this module's package root)."""
    return Path(__file__).resolve().parents[1] / "tui" / "v9" / "bin"


def _cache_bin_dir() -> Path:
    override = os.environ.get("C4REQBER_CONFIG")
    if override:
        return Path(override).expanduser() / "bin"
    return Path.home() / ".c4reqber" / "bin"


def _binary_names() -> list[str]:
    if sys.platform == "win32":
        return ["c4tui-v9.exe", "c4tui-v9"]
    return ["c4tui-v9", "c4tui-v9.exe"]


def _platform_asset_suffix() -> str | None:
    """Return GitLab release asset suffix for this host, e.g. ``linux-amd64``."""
    system = sys.platform
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        return None
    if system == "linux":
        return f"linux-{arch}"
    if system == "darwin":
        return f"darwin-{arch}"
    if system == "win32":
        return f"windows-{arch}.exe"
    return None


def _is_runnable(path: Path) -> bool:
    if not path.is_file():
        return False
    if sys.platform == "win32":
        return True
    return os.access(path, os.X_OK)


def find_tui_v9_binary() -> Path | None:
    """Locate a built c4tui-v9 binary, or None if not found."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if sys.platform == "darwin":
            res = exe_dir.parent / "Resources" / "c4tui-v9"
            if _is_runnable(res):
                return res
        else:
            for name in _binary_names():
                cand = exe_dir / name
                if _is_runnable(cand):
                    return cand

    # Prefer sibling of running interpreter / blast launcher (Windows Scripts/,
    # wheel layouts where blast.exe and c4tui-v9.exe sit together).
    exe_parent = Path(sys.executable).resolve().parent
    search_dirs = [
        exe_parent,
        _package_bin_dir(),
        _repo_root() / "src" / "tui" / "v9" / "bin",
        _repo_root() / "bin",
        _cache_bin_dir(),
    ]
    # Sibling of blast(.exe) on PATH
    for blast_name in ("blast", "blast.exe"):
        which_blast = shutil.which(blast_name)
        if which_blast:
            search_dirs.insert(0, Path(which_blast).resolve().parent)
            break

    for directory in search_dirs:
        for name in _binary_names():
            cand = directory / name
            if _is_runnable(cand):
                return cand

    for name in ("c4tui-v9", "c4tui-v9.exe"):
        which = shutil.which(name)
        if which:
            path = Path(which)
            if _is_runnable(path):
                return path
    return None


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    logger.info("Downloading c4tui-v9 from %s", url)
    req = urllib.request.Request(url, headers={"User-Agent": "c4reqber-tui-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.chmod(0o755)
    tmp.replace(dest)


def _resolve_release_asset_url() -> str | None:
    """Pick a GitLab release asset matching this platform."""
    override = os.environ.get("C4REQBER_TUI_URL", "").strip()
    if override:
        return override

    suffix = _platform_asset_suffix()
    if not suffix:
        return None

    import json

    api = f"{_GITLAB_API}/releases"
    req = urllib.request.Request(api, headers={"User-Agent": "c4reqber-tui-fetcher/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            releases = json.loads(resp.read().decode())
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        json.JSONDecodeError,
    ) as exc:
        logger.debug("GitLab releases lookup failed: %s", exc)
        return None

    needle = f"c4tui-v9-{suffix}" if not suffix.endswith(".exe") else f"c4tui-v9-{suffix}"
    # Assets may be tagged: c4tui-v9-v9.14.0-linux-amd64 or c4tui-v9-linux-amd64
    for release in releases if isinstance(releases, list) else []:
        links = (release.get("assets") or {}).get("links") or []
        for link in links:
            name = str(link.get("name") or "")
            url = str(link.get("url") or link.get("direct_asset_url") or "")
            if not url:
                continue
            if name == needle or name.endswith(f"-{suffix}") or needle in name:
                return url
        # Also scan description / uploaded package filenames in links
        for link in links:
            name = str(link.get("name") or "").lower()
            url = str(link.get("url") or "")
            if "c4tui" in name and suffix.replace(".exe", "") in name:
                return url
    return None


def ensure_tui_binary(*, download: bool = True) -> Path | None:
    """Return a runnable binary, downloading into ``~/.c4reqber/bin`` if needed."""
    found = find_tui_v9_binary()
    if found is not None:
        return found
    if not download:
        return None

    url = _resolve_release_asset_url()
    if not url:
        logger.warning(
            "No c4tui-v9 binary found and no GitLab release asset for this platform. "
            "Set C4REQBER_TUI_URL or install Go and build src/tui/v9."
        )
        return None

    name = "c4tui-v9.exe" if sys.platform == "win32" else "c4tui-v9"
    dest = _cache_bin_dir() / name
    try:
        _download(url, dest)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Failed to download c4tui-v9: %s", exc)
        return None
    return dest if _is_runnable(dest) else None
