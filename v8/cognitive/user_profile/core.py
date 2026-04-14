from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import os

BASE_PROFILE_PATH = Path.home() / ".turbo-cdi" / "profiles"


@dataclass
class UserProfile:
    user_id: str
    frequent_domains: List[str] = field(default_factory=list)
    historical_effectiveness: Dict[str, float] = field(default_factory=dict)
    bias_tendencies: Dict[str, int] = field(default_factory=dict)
    risk_tolerance: str = "moderate"
    bias_sensitivity: str = "medium"  # "low", "medium", "high"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def _validate_path(self, path: str) -> Path:
        """Prevent path traversal attacks."""
        full_path = (BASE_PROFILE_PATH / path).resolve()
        if not str(full_path).startswith(str(BASE_PROFILE_PATH.resolve())):
            raise ValueError(f"Path traversal detected: {path}")
        return full_path

    def save(self, path: str) -> None:
        full_path = self._validate_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w") as f:
            json.dump(self.__dict__, f, indent=2, default=str)
        os.chmod(full_path, 0o600)

    @classmethod
    def load(cls, path: str) -> Optional["UserProfile"]:
        try:
            full_path = (BASE_PROFILE_PATH / path).resolve()
            if not str(full_path).startswith(str(BASE_PROFILE_PATH.resolve())):
                return None
            with open(full_path) as f:
                data = json.load(f)
            # Filter to only valid fields
            valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**valid_fields)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return None

    def update_from_outcome(self, domain: str, effectiveness: float) -> None:
        self.historical_effectiveness[domain] = effectiveness
        if domain not in self.frequent_domains:
            self.frequent_domains.append(domain)
