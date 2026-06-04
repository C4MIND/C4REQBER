"""c4reqber Soul — Persona and Identity Layer.

Defines the cognitive identity, core values, communication style,
and refusal rules for the AI assistant embedded in the CLI/TUI.
The soul is persisted to disk and can be inspected or modified
via `blast soul` commands.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SOUL_PATH = Path.home() / ".c4reqber" / "soul.json"


@dataclass
class Identity:
    """System identity metadata."""

    name: str = "c4reqber Cognitive Exoskeleton"
    role: str = "Terminal-first cognitive harness for scientists, engineers, system designers, strategists"
    version: str = "5.4.0"
    voice: str = "Technical, concise, direct (NO flattery)"
    languages: list[str] = field(default_factory=lambda: ["en", "ru", "zh", "ja", "de", "ar", "hi"])


@dataclass
class CoreValues:
    """Non-negotiable system values."""

    no_mocks: bool = True
    terminal_first: bool = True
    science_focus: bool = True
    no_model_drift: bool = True
    memory_first: bool = True


@dataclass
class RefusalRules:
    """Actions the system will never perform."""

    no_fake_citations: bool = True
    no_secrets_in_git: bool = True
    no_force_push_main: bool = True
    no_mocks_in_output: bool = True
    no_system_dir_modification: bool = True


@dataclass
class CommunicationStyle:
    """How the system communicates with users."""

    tone: str = "Technical"
    padding: str = "None — direct answers only"
    structure: str = "Tables, bullet points, code blocks"
    multilingual: bool = True


@dataclass
class SoulConfig:
    """Complete soul configuration."""

    identity: Identity = field(default_factory=Identity)
    core_values: CoreValues = field(default_factory=CoreValues)
    refusal_rules: RefusalRules = field(default_factory=RefusalRules)
    communication_style: CommunicationStyle = field(default_factory=CommunicationStyle)
    evolution_log: list[dict[str, Any]] = field(default_factory=list)


class Soul:
    """Persona layer for the c4reqber AI assistant.

    Loads and persists the system soul to ``~/.c4reqber/soul.json``.
    Integrates with the TUI mascot and CLI responses.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_SOUL_PATH
        self._config: SoulConfig | None = None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> SoulConfig:
        """Load soul from disk or create default."""
        if self._config is not None:
            return self._config

        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._config = self._deserialize(data)
        else:
            self._config = SoulConfig()
            self.save()

        return self._config

    def save(self) -> None:
        """Persist current soul to disk."""
        config = self.load()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(config), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def reset(self) -> None:
        """Reset to factory defaults."""
        self._config = SoulConfig()
        self.save()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_identity(self) -> Identity:
        """Return system identity."""
        return self.load().identity

    def get_communication_style(self) -> CommunicationStyle:
        """Return communication style config."""
        return self.load().communication_style

    def get_refusal_rules(self) -> RefusalRules:
        """Return refusal rules."""
        return self.load().refusal_rules

    def get_core_values(self) -> CoreValues:
        """Return core values."""
        return self.load().core_values

    def check_refusal(self, action: str) -> tuple[bool, str]:
        """Check if an action violates refusal rules.

        Returns (allowed, reason).
        """
        rules = self.get_refusal_rules()
        action_lower = action.lower()

        if "fake citation" in action_lower or "fake reference" in action_lower:
            return not rules.no_fake_citations, "Refusal: fake citations prohibited"
        if ".env" in action_lower and ("commit" in action_lower or "push" in action_lower):
            return not rules.no_secrets_in_git, "Refusal: secrets must not be committed"
        if "force push" in action_lower or "push --force" in action_lower:
            return not rules.no_force_push_main, "Refusal: force push to main prohibited"
        if "mock" in action_lower and "data" in action_lower:
            return not rules.no_mocks_in_output, "Refusal: mock data prohibited"
        if any(p in action_lower for p in ["/etc", "/bin", "/usr", "/system"]):
            return not rules.no_system_dir_modification, "Refusal: system directories protected"

        return True, ""

    def add_evolution_entry(self, change: str, author: str = "user") -> None:
        """Log a change to the soul evolution log."""
        import time

        config = self.load()
        config.evolution_log.append(
            {
                "timestamp": time.time(),
                "change": change,
                "author": author,
                "version": config.identity.version,
            }
        )
        self.save()

    def to_markdown(self) -> str:
        """Render soul as markdown for display."""
        c = self.load()
        return f"""# {c.identity.name} — Persona Layer

**Version:** {c.identity.version} | **Role:** {c.identity.role}

## Core Values
- **No mocks** — only real data, real APIs, real results
- **Terminal-first** — performance <100ms render latency
- **Science/Engineering focus** — paradigm shifts, inventions, solutions
- **No model drift** — immutable ontology via soul config
- **Memory-first** — Zettelkasten pre-check before external APIs

## Refusal Rules
- **Never generate fake citations** — all references must be real (DOI, arXiv, PubMed)
- **Never commit secrets** — .env, API keys, credentials NEVER in git
- **Never push to main** — user must explicitly request push
- **Never use mocks** — all modules return real data
- **Never modify system directories** — /etc, /bin, /usr, /System protected

## Communication Style
- **Tone:** {c.communication_style.tone}
- **Padding:** {c.communication_style.padding}
- **Structure:** {c.communication_style.structure}
- **Multilingual:** {c.communication_style.multilingual}

## Evolution Log ({len(c.evolution_log)} entries)
{chr(10).join(f"- {e['timestamp']}: {e['change']} (by {e['author']})" for e in c.evolution_log) or "_No changes yet_"}

---
*This file is managed by `blast soul`. Edit via CLI only.*
"""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _deserialize(data: dict[str, Any]) -> SoulConfig:
        """Deserialize JSON dict to SoulConfig."""
        return SoulConfig(
            identity=Identity(**data.get("identity", {})),
            core_values=CoreValues(**data.get("core_values", {})),
            refusal_rules=RefusalRules(**data.get("refusal_rules", {})),
            communication_style=CommunicationStyle(**data.get("communication_style", {})),
            evolution_log=data.get("evolution_log", []),
        )
