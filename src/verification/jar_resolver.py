"""Resolve Java JAR tools (TLA+, Alloy) from env vars and common install paths."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def resolve_java() -> str | None:
    """Return path to java executable or None."""
    candidates = [
        shutil.which("java"),
        "/opt/homebrew/opt/openjdk/bin/java",
        "/usr/local/opt/openjdk/bin/java",
    ]
    java_home = os.environ.get("JAVA_HOME", "").strip()
    if java_home:
        candidates.insert(0, str(Path(java_home) / "bin" / "java"))

    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        if path.is_file():
            return str(path.resolve())
    return None


def resolve_jar(env_key: str, candidates: list[Path | str]) -> str | None:
    """Resolve a JAR path from env var or candidate locations."""
    env_val = os.environ.get(env_key, "").strip()
    if env_val and Path(env_val).is_file():
        return str(Path(env_val).resolve())

    for raw in candidates:
        path = Path(raw).expanduser()
        if path.is_file():
            return str(path.resolve())
    return None


def tla_tools_jar() -> str | None:
    """Locate tla2tools.jar for TLC model checker."""
    return resolve_jar(
        "TLA_TOOLS_JAR",
        [
            Path.home() / ".tlaplus" / "tla2tools.jar",
            "/Applications/TLA+ Toolbox.app/Contents/Eclipse/tla2tools.jar",
            "/Applications/TLA+ Toolbox.app/Contents/Resources/tla2tools.jar",
            Path.home() / "toolbox" / "tla2tools.jar",
            Path.home() / "Downloads" / "tla2tools.jar",
        ],
    )


def alloy_jar() -> str | None:
    """Locate Alloy distribution JAR."""
    return resolve_jar(
        "ALLOY_JAR",
        [
            Path.home() / ".alloy" / "org.alloytools.alloy.dist.jar",
            Path.home() / "Downloads" / "org.alloytools.alloy.dist.jar",
        ],
    )


def alloy_binary() -> str | None:
    """Locate Alloy CLI binary (brew alloy-analyzer or ALLOY_PATH)."""
    env_path = os.environ.get("ALLOY_PATH", "").strip()
    if env_path and Path(env_path).is_file():
        return str(Path(env_path).resolve())
    return shutil.which("alloy") or shutil.which("alloy6")
