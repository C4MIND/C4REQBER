from __future__ import annotations


"""User Profile — identity, auth, and academic credentials."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserProfile:
    """User identity for attribution in generated documents."""

    name: str = "Anonymous Researcher"
    email: str = ""
    affiliation: str = ""
    orcid: str = ""
    degree: str = ""
    department: str = ""
    country: str = ""
    bio: str = ""
    auth_provider: str = "local"  # web3, telegram, supabase, local
    auth_id: str = ""
    preferences: dict[str, Any] = field(default_factory=dict)

    def formatted_name(self) -> str:
        """Return name suitable for academic documents."""
        if not self.name or self.name == "Anonymous Researcher":
            return "[Author Name Required]"
        return self.name

    def citation_name(self) -> str:
        """Surname, F.M. format."""
        parts = self.name.split()
        if len(parts) >= 2:
            surname = parts[-1]
            initials = "".join(p[0] + "." for p in parts[:-1])
            return f"{surname}, {initials}"
        return self.name

    def full_affiliation(self) -> str:
        """Full affiliation."""
        parts = [p for p in [self.department, self.affiliation, self.country] if p]
        return ", ".join(parts) if parts else ""

    def get_pipeline_config(self) -> dict[str, Any]:
        """Return pipeline config dict from preferences (or empty)."""
        return self.preferences.get("pipeline_config", {})

    def set_pipeline_config(self, config: dict[str, Any]) -> None:
        """Store pipeline config in preferences."""
        self.preferences["pipeline_config"] = config

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "affiliation": self.affiliation,
            "orcid": self.orcid,
            "degree": self.degree,
            "department": self.department,
            "country": self.country,
            "bio": self.bio,
            "auth_provider": self.auth_provider,
            "auth_id": self.auth_id,
            "preferences": self.preferences,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> UserProfile:
        return cls(
            name=d.get("name", "Anonymous Researcher"),
            email=d.get("email", ""),
            affiliation=d.get("affiliation", ""),
            orcid=d.get("orcid", ""),
            degree=d.get("degree", ""),
            department=d.get("department", ""),
            country=d.get("country", ""),
            bio=d.get("bio", ""),
            auth_provider=d.get("auth_provider", "local"),
            auth_id=d.get("auth_id", ""),
            preferences=d.get("preferences", {}),
        )
