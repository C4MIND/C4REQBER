"""Collaboration tracking"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Contributor:
    """Contributor."""
    id: str
    name: str
    role: str
    contributions: list[dict[str, Any]] = field(default_factory=list[Any])

@dataclass
class Collaboration:
    """Collaboration."""
    id: str
    project: str
    contributors: list[Contributor]
    created_at: str
    status: str  # active, completed, archived

class CollaborationManager:
    """CollaborationManager."""
    def __init__(self) -> None:
        self.collaborations: dict[str, Collaboration] = {}

    def create(self, project: str, contributors: list[dict[str, Any]]) -> Collaboration:
        """Create."""
        cid = str(uuid.uuid4())[:8]
        collab = Collaboration(
            id=cid,
            project=project,
            contributors=[Contributor(id=str(uuid.uuid4())[:8], **c) for c in contributors],
            created_at=datetime.now().isoformat(),
            status="active",
        )
        self.collaborations[cid] = collab
        return collab

    def add_contribution(
        self, collab_id: str, contributor_id: str, action: str, detail: str
    ) -> None:
        """Add contribution."""
        collab = self.collaborations.get(collab_id)
        if collab:
            for c in collab.contributors:
                if c.id == contributor_id:
                    c.contributions.append(
                        {
                            "action": action,
                            "detail": detail,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

    def get_stats(self, collab_id: str) -> dict[str, Any]:
        """Get stats."""
        collab = self.collaborations.get(collab_id)
        if not collab:
            return {}
        total = sum(len(c.contributions) for c in collab.contributors)
        return {
            "project": collab.project,
            "contributors": len(collab.contributors),
            "total_contributions": total,
            "status": collab.status,
        }

    def list_all(self) -> list[dict[str, Any]]:
        return [
            {
                "id": cid,
                "project": c.project,
                "contributors": len(c.contributors),
                "status": c.status,
                "created_at": c.created_at,
            }
            for cid, c in self.collaborations.items()
        ]
