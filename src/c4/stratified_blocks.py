# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class C4Block:
    """C4Block."""
    id: str
    text: str
    layer: int  # 1-3
    state: str  # C4 state e.g. "Present:Concrete:Other"
    stage: str  # pipeline stage name
    verification: str | None = None  # "verified" | "falsified" | None
    path: str | None = None  # scientist path name
    citations: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def badge(self) -> str:
        """Badge."""
        layer_symbol = {1: "①", 2: "②", 3: "③"}.get(self.layer, "◌")
        verify_symbol = {"verified": "✓", "falsified": "✗"}.get(self.verification or "", "")
        return f"[C{self.layer}{verify_symbol}] {self.stage}"


class BlockRegistry:
    """Collects and groups C4-stratified output blocks."""

    def __init__(self) -> None:
        self._blocks: list[C4Block] = []

    def add(self, block: C4Block) -> None:
        self._blocks.append(block)

    def by_layer(self, layer: int) -> list[C4Block]:
        return [b for b in self._blocks if b.layer == layer]

    def by_path(self, path: str) -> list[C4Block]:
        return [b for b in self._blocks if b.path == path]

    def by_verification(self, status: str) -> list[C4Block]:
        return [b for b in self._blocks if b.verification == status]

    def provenance(self, block_id: str) -> list[C4Block]:
        """Provenance."""
        target = next((b for b in self._blocks if b.id == block_id), None)
        if not target:
            return []
        return [b for b in self._blocks if b.timestamp < target.timestamp]

    def filter(self, layer: int | None = None, path: str | None = None, verification: str | None = None) -> list[C4Block]:
        """Filter."""
        result = self._blocks
        if layer is not None:
            result = [b for b in result if b.layer == layer]
        if path is not None:
            result = [b for b in result if b.path == path]
        if verification is not None:
            result = [b for b in result if b.verification == verification]
        return result

    def __len__(self) -> int:
        return len(self._blocks)
