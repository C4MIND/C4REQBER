"""c4reqber: Social Publishing History — immutable JSONL audit trail."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SOCIAL_HISTORY_PATH = Path.home() / ".c4reqber" / "social_history.jsonl"


@dataclass
class SocialEvent:
    timestamp: float
    action: str
    platform: str
    draft_id: str
    status: str  # success, failed, pending
    details: dict[str, Any]

    @property
    def summary(self) -> str:
        return f"[{self.platform}] {self.action}: {self.status}"


class SocialHistory:
    """Immutable JSONL audit log for all social publishing events."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or SOCIAL_HISTORY_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, action: str, platform: str, draft_id: str, status: str, **details: Any) -> None:
        event = SocialEvent(
            timestamp=time.time(),
            action=action,
            platform=platform,
            draft_id=draft_id,
            status=status,
            details=details,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def read_all(self) -> list[SocialEvent]:
        if not self.path.exists():
            return []
        events: list[SocialEvent] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                events.append(SocialEvent(**data))
        return events

    def for_draft(self, draft_id: str) -> list[SocialEvent]:
        return [e for e in self.read_all() if e.draft_id == draft_id]

    def last_for_platform(self, platform: str, n: int = 10) -> list[SocialEvent]:
        return [e for e in self.read_all() if e.platform == platform][-n:]

    def stats(self) -> dict[str, Any]:
        events = self.read_all()
        by_platform: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for e in events:
            by_platform[e.platform] = by_platform.get(e.platform, 0) + 1
            by_status[e.status] = by_status.get(e.status, 0) + 1
        return {"total": len(events), "by_platform": by_platform, "by_status": by_status}
