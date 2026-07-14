# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PathManifest:
    """PathManifest."""
    name: str
    description: str
    c4_layer: int  # 1-3
    scientist: str  # e.g. "Curie", "Einstein", "Turing"
    depends_on: list[str] = field(default_factory=list)
    verification_strategy: str = "none"  # "model-checking" | "theorem-proving" | "smt" | "none"
    tools: list[str] = field(default_factory=list)
    formal_spec: str = ""
    priority: int = 5

    @classmethod
    def from_toml(cls, path: Path) -> PathManifest | None:
        """From toml."""
        try:
            content = path.read_text()
        except OSError:
            return None
        data: dict[str, Any] = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("\"'")
                if key in ("depends_on", "tools"):
                    data[key] = [v.strip().strip("\"'") for v in val.strip("[]").split(",") if v.strip()]
                elif key in ("c4_layer", "priority"):
                    data[key] = int(val)
                else:
                    data[key] = val
        return cls(
            name=data.get("name", path.parent.name),
            description=data.get("description", ""),
            c4_layer=data.get("c4_layer", 1),
            scientist=data.get("scientist", "general"),
            depends_on=data.get("depends_on", []),
            verification_strategy=data.get("verification_strategy", "none"),
            tools=data.get("tools", []),
            formal_spec=data.get("formal_spec", ""),
            priority=data.get("priority", 5),
        )


class PathRegistry:
    """Load and manage PATH.toml manifests from workspace paths."""

    SCAN_PATHS: list[Path] = [
        Path.home() / ".c4reqber" / "paths",
        Path("paths"),
    ]

    def __init__(self) -> None:
        self._manifests: dict[str, PathManifest] = {}
        self.scan()

    def scan(self) -> None:
        for base in self.SCAN_PATHS:
            if not base.exists():
                continue
            for entry in base.iterdir():
                if entry.is_dir():
                    manifest_file = entry / "PATH.toml"
                    if manifest_file.exists():
                        manifest = PathManifest.from_toml(manifest_file)
                        if manifest:
                            self._manifests[manifest.name] = manifest

    def by_layer(self, layer: int) -> list[PathManifest]:
        return [m for m in self._manifests.values() if m.c4_layer == layer]

    def by_scientist(self, scientist: str) -> list[PathManifest]:
        return [m for m in self._manifests.values() if m.scientist.lower() == scientist.lower()]

    @property
    def all(self) -> list[PathManifest]:
        return sorted(self._manifests.values(), key=lambda m: (m.c4_layer, -m.priority))
