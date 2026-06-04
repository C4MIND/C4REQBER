from __future__ import annotations


"""
Append-Only Audit Trail for Reqber v4.1
Logs all actions with timestamp, session_id, params, approval, result, cost
"""

import json
import time
from pathlib import Path
from typing import Any


class AuditTrail:
    """Append-only audit trail (JSON lines format)."""

    def __init__(self, log_path: str = "data/audit.log") -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._rotation_size = 10 * 1024 * 1024  # 10MB

    def log_action(
        self,
        action: str,
        params: dict[str, Any],
        result: str = "success",
        cost: dict[str, Any] | None = None,
        session_id: str = "",
        approval: str = "",
    ) -> None:
        """Append action to audit trail (JSON line)."""
        entry = {
            "timestamp": time.time(),
            "session_id": session_id,
            "action": action,
            "params": params,
            "approval": approval,
            "result": result,
            "cost": cost or {},
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

        # Rotation check
        if self.log_path.stat().st_size > self._rotation_size:
            self._rotate_log()

    def query_trail(
        self,
        action_filter: str | None = None,
        session_filter: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit trail (returns last N entries)."""
        if not self.log_path.exists():
            return []

        results = []
        with open(self.log_path) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if action_filter and entry.get("action") != action_filter:
                        continue
                    if session_filter and entry.get("session_id") != session_filter:
                        continue
                    results.append(entry)
                except json.JSONDecodeError:
                    continue

        return results[-limit:]

    def _rotate_log(self) -> None:
        """Rotate log file when it exceeds size limit."""
        import shutil
        backup = self.log_path.with_suffix(".log.1")
        if backup.exists():
            backup.unlink()
        shutil.move(str(self.log_path), str(backup))

    def get_statistics(self) -> dict[str, Any]:
        """Get audit trail statistics."""
        entries = self.query_trail(limit=10000)
        stats: dict[str, Any] = {
            "total_entries": len(entries),
            "actions_by_type": {},
            "success_rate": 0.0,
            "total_cost_usd": 0.0,
        }

        success_count = 0
        for e in entries:
            action = e.get("action", "unknown")
            stats["actions_by_type"][action] = stats["actions_by_type"].get(action, 0) + 1
            if e.get("result") == "success":
                success_count += 1
            stats["total_cost_usd"] += e.get("cost", {}).get("usd", 0)

        if entries:
            stats["success_rate"] = success_count / len(entries)

        return stats
