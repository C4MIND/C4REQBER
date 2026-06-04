# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SandboxResult:
    """SandboxResult."""
    id: str
    hypothesis: str
    conclusion: str
    confidence: float
    verification: str  # "verified" | "falsified" | "unresolved"
    dependencies: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)


class HypothesisSandbox:
    """Isolate reasoning paths that may contradict each other."""

    def __init__(self) -> None:
        self._sandboxes: dict[str, SandboxResult] = {}

    def spawn(self, hypothesis: str) -> str:
        """Spawn."""
        sid = str(uuid.uuid4())[:8]
        self._sandboxes[sid] = SandboxResult(
            id=sid, hypothesis=hypothesis, conclusion="",
            confidence=0.0, verification="unresolved",
        )
        return sid

    def conclude(self, sandbox_id: str, conclusion: str, confidence: float, verification: str = "unresolved") -> None:
        if sandbox_id in self._sandboxes:
            sb = self._sandboxes[sandbox_id]
            sb.conclusion = conclusion
            sb.confidence = confidence
            sb.verification = verification

    def conflicts(self) -> list[tuple[str, str, str]]:
        """Return pairs of sandbox IDs with conflicting conclusions."""
        resolved = [(sid, sb) for sid, sb in self._sandboxes.items() if sb.conclusion]
        conflicts = []
        for i in range(len(resolved)):
            for j in range(i + 1, len(resolved)):
                si, sbi = resolved[i]
                sj, sbj = resolved[j]
                if sbi.verification == "falsified" and sbj.verification == "verified":
                    conflicts.append((si, sj, f"{sbi.hypothesis} vs {sbj.hypothesis}"))
                elif sbi.conclusion != sbj.conclusion and sbi.hypothesis == sbj.hypothesis:
                    conflicts.append((si, sj, "Same hypothesis, different conclusions"))
        return conflicts

    def get(self, sandbox_id: str) -> SandboxResult | None:
        return self._sandboxes.get(sandbox_id)
