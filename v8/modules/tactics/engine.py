# Tactics Engine - Stub for testing
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class TacticsEngine:
    """Stub tactics engine for integration testing."""

    def __init__(self):
        self.tactics_db: Dict[str, Any] = {}

    def get_tactics_for_domain(self, domain: str) -> List[Dict]:
        """Return tactics for given domain."""
        return self.tactics_db.get(domain, [])

    def register_tactic(self, domain: str, tactic: Dict) -> None:
        """Register a new tactic."""
        if domain not in self.tactics_db:
            self.tactics_db[domain] = []
        self.tactics_db[domain].append(tactic)
