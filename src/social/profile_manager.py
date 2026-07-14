"""c4reqber: User Profile Manager — academic identity for preprint metadata."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


PROFILE_PATH = Path.home() / ".c4reqber" / "profile.json"


@dataclass
class AuthorProfile:
    name: str = ""
    orcid: str = ""
    affiliation: str = ""
    title: str = ""
    email: str = ""
    corresponding: bool = True


@dataclass
class UserProfile:
    authors: list[AuthorProfile] = field(default_factory=lambda: [AuthorProfile()])
    default_license: str = "CC-BY-4.0"
    editor_command: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> UserProfile:
        path = path or PROFILE_PATH
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            authors = [AuthorProfile(**a) for a in data.get("authors", [])]
            return cls(
                authors=authors or [AuthorProfile()],
                default_license=data.get("default_license", "CC-BY-4.0"),
                editor_command=data.get("editor_command", ""),
            )
        profile = cls()
        profile.save(path)
        return profile

    def save(self, path: Path | None = None) -> None:
        path = path or PROFILE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def _to_dict(self) -> dict[str, Any]:
        return {
            "authors": [asdict(a) for a in self.authors],
            "default_license": self.default_license,
            "editor_command": self.editor_command,
        }

    @property
    def primary_author(self) -> AuthorProfile:
        for a in self.authors:
            if a.corresponding:
                return a
        return self.authors[0] if self.authors else AuthorProfile()

    @property
    def author_string(self) -> str:
        return "; ".join(a.name for a in self.authors if a.name)

    @property
    def orcid_ids(self) -> list[str]:
        return [a.orcid for a in self.authors if a.orcid]

    @property
    def affiliations(self) -> list[str]:
        seen: list[str] = []
        for a in self.authors:
            if a.affiliation and a.affiliation not in seen:
                seen.append(a.affiliation)
        return seen

    def add_author(self, author: AuthorProfile) -> None:
        self.authors.append(author)

    def remove_author(self, index: int) -> None:
        if 0 <= index < len(self.authors) and len(self.authors) > 1:
            self.authors.pop(index)
