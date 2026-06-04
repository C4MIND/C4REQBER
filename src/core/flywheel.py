from __future__ import annotations


"""
Data Flywheel — Every discovery improves the system.

Bayesian updating of global prior based on discovery results.
The flywheel accelerates: successful discoveries raise the prior,
making future discoveries more likely to succeed.
"""
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FlywheelSnapshot:
    """FlywheelSnapshot."""
    global_prior: float
    discoveries_count: int
    success_count: int
    last_updated: float
    avg_papers_per_discovery: float


class DataFlywheel:
    """Every discovery improves the system. Bayesian updating of global prior."""

    def __init__(self, persist_path: str | None = None) -> None:
        self.global_prior: float = 0.30
        self.discoveries_count: int = 0
        self.success_count: int = 0
        self.total_papers_found: int = 0
        self.last_updated: float = 0.0
        self.persist_path = persist_path or str(
            Path(__file__).parent.parent.parent / "data" / "flywheel.json"
        )
        self._load()

    def update(self, discovery_result: dict[str, Any]) -> None:
        """Update global prior based on discovery success.

        Uses Bayesian updating:
            posterior = (evidence * prior) / (evidence * prior + (1-evidence) * (1-prior))
        where evidence = 0.60 + papers_found * 0.02 (capped at 0.95).
        """
        papers = discovery_result.get("papers_found", 0)
        success = 1.0 if discovery_result.get("status") == "complete" else 0.0

        evidence = min(0.95, 0.60 + papers * 0.02)
        evidence = evidence * success + (1.0 - evidence) * (1.0 - success)

        prior = self.global_prior
        self.global_prior = round(
            (evidence * prior) / (evidence * prior + (1.0 - evidence) * (1.0 - prior)),
            4,
        )

        self.discoveries_count += 1
        if success >= 0.5:
            self.success_count += 1
        self.total_papers_found += papers
        self.last_updated = time.time()
        self._save()

    def get_stats(self) -> dict[str, Any]:
        """Return flywheel statistics for display."""
        return {
            "global_prior": self.global_prior,
            "discoveries": self.discoveries_count,
            "successes": self.success_count,
            "success_rate": round(
                self.success_count / max(1, self.discoveries_count), 3
            ),
            "total_papers": self.total_papers_found,
            "avg_papers": round(
                self.total_papers_found / max(1, self.discoveries_count), 1
            ),
        }

    def snapshot(self) -> FlywheelSnapshot:
        return FlywheelSnapshot(
            global_prior=self.global_prior,
            discoveries_count=self.discoveries_count,
            success_count=self.success_count,
            last_updated=self.last_updated,
            avg_papers_per_discovery=round(
                self.total_papers_found / max(1, self.discoveries_count), 1
            ),
        )

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            with open(self.persist_path, "w") as f:
                json.dump(
                    {
                        "global_prior": self.global_prior,
                        "discoveries_count": self.discoveries_count,
                        "success_count": self.success_count,
                        "total_papers_found": self.total_papers_found,
                        "last_updated": self.last_updated,
                    },
                    f,
                )
        except (OSError, ImportError, AttributeError, RuntimeError):
            pass

    def _load(self) -> None:
        try:
            if os.path.exists(self.persist_path):
                with open(self.persist_path) as f:
                    data = json.load(f)
                    self.global_prior = data.get("global_prior", 0.30)
                    self.discoveries_count = data.get("discoveries_count", 0)
                    self.success_count = data.get("success_count", 0)
                    self.total_papers_found = data.get("total_papers_found", 0)
                    self.last_updated = data.get("last_updated", 0.0)
        except (OSError, json.JSONDecodeError, ImportError, AttributeError, RuntimeError):
            pass
