"""Machine-readable registry of all c4reqber environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_EXAMPLE = _REPO_ROOT / ".env.example"

# Manual metadata overrides (category, label, required, doc hint).
_OVERRIDES: dict[str, dict[str, str | bool]] = {
    "OPENROUTER_API_KEY": {"category": "llm", "label": "OpenRouter", "required": True},
    "DEEPSEEK_API_KEY": {"category": "llm", "label": "DeepSeek"},
    "BRAVE_API_KEY": {"category": "search", "label": "Brave Search"},
    "TAVILY_API_KEY": {"category": "search", "label": "Tavily"},
    "ZENODO_ACCESS_TOKEN": {"category": "social", "label": "Zenodo"},
    "MASTODON_ACCESS_TOKEN": {"category": "social", "label": "Mastodon"},
    "BLUESKY_HANDLE": {"category": "social", "label": "Bluesky handle", "secret": False},
    "BLUESKY_APP_PASSWORD": {"category": "social", "label": "Bluesky app password"},
    "TELEGRAM_BOT_TOKEN": {"category": "social", "label": "Telegram bot"},
    "TELEGRAM_CHAT_ID": {"category": "social", "label": "Telegram chat ID", "secret": False},
    "DISCORD_WEBHOOK_URL": {"category": "social", "label": "Discord webhook", "secret": True},
    "SLACK_WEBHOOK_URL": {"category": "social", "label": "Slack webhook", "secret": True},
    "REDDIT_CLIENT_ID": {"category": "social", "label": "Reddit client ID", "secret": False},
    "REDDIT_CLIENT_SECRET": {"category": "social", "label": "Reddit secret"},
    "REDDIT_USERNAME": {"category": "social", "label": "Reddit username", "secret": False},
    "REDDIT_PASSWORD": {"category": "social", "label": "Reddit password"},
    "ORCID_CLIENT_ID": {"category": "social", "label": "ORCID client ID", "secret": False},
    "ORCID_CLIENT_SECRET": {"category": "social", "label": "ORCID secret"},
    "X_API_KEY": {"category": "social", "label": "X API key"},
    "X_BEARER_TOKEN": {"category": "social", "label": "X bearer token"},
    "LEAN4_PATH": {"category": "verification", "label": "Lean4 path", "secret": False},
    "COQ_PATH": {"category": "verification", "label": "Coq path", "secret": False},
    "DAFNY_PATH": {"category": "verification", "label": "Dafny path", "secret": False},
    "NCBI_API_KEY": {"category": "science", "label": "NCBI"},
    "MATERIALS_PROJECT_API_KEY": {"category": "science", "label": "Materials Project"},
    "KAGGLE_USERNAME": {"category": "science", "label": "Kaggle username", "secret": False},
    "KAGGLE_KEY": {"category": "science", "label": "Kaggle key"},
    "JWT_SECRET": {"category": "security", "label": "JWT secret"},
    "OLLAMA_URL": {"category": "local_llm", "label": "Ollama URL", "secret": False},
    "LM_STUDIO_URL": {"category": "local_llm", "label": "LM Studio URL", "secret": False},
}

_CATEGORY_FROM_SECTION = {
    "LLM Provider Keys": "llm",
    "Local LLM": "local_llm",
    "Search & Knowledge APIs": "search",
    "Scientific Data Sources": "science",
    "Social & Publishing": "social",
    "Social / Integrations": "social",
    "Security": "security",
    "Database": "database",
    "Cache & Storage": "cache",
    "Verification Tools": "verification",
    "API Server": "server",
    "Observability": "observability",
    "Feature Flags": "feature",
    "Additional LLM Providers": "llm",
    "Archive / Export": "archive",
    "Misc": "misc",
    "Auto-Formalization": "feature",
    "Database Pool": "database",
    "Rate Limiting": "server",
    "Payment Providers": "misc",
    "Retry Configuration": "misc",
}

CATEGORY_LABELS: dict[str, str] = {
    "llm": "LLM providers",
    "local_llm": "Local LLM",
    "search": "Search & web",
    "science": "Scientific sources",
    "social": "Social & publishing",
    "verification": "Verification tools",
    "security": "Security",
    "database": "Database",
    "cache": "Cache",
    "server": "API server",
    "observability": "Observability",
    "feature": "Feature flags",
    "archive": "Archive & export",
    "misc": "Misc",
}


@dataclass(frozen=True)
class KeyDef:
    env_name: str
    category: str
    label: str
    required: bool = False
    secret: bool = True
    comment: str = ""

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "env_name": self.env_name,
            "category": self.category,
            "label": self.label,
            "required": self.required,
            "secret": self.secret,
            "comment": self.comment,
        }


def _infer_category(section: str, env_name: str) -> str:
    for fragment, cat in _CATEGORY_FROM_SECTION.items():
        if fragment in section:
            return cat
    if env_name.endswith("_PATH") or env_name.endswith("_JAR"):
        return "verification"
    if "API_KEY" in env_name or "TOKEN" in env_name or "SECRET" in env_name:
        return "misc"
    return "misc"


def _human_label(env_name: str) -> str:
    return env_name.replace("_", " ").title()


def parse_env_example(path: Path | None = None) -> list[KeyDef]:
    """Parse .env.example into KeyDef entries."""
    src = path or _ENV_EXAMPLE
    if not src.is_file():
        return []
    current_section = ""
    keys: list[KeyDef] = []
    seen: set[str] = set()
    for raw in src.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("# ──") and line.endswith("──"):
            current_section = line.strip("# ").strip("─ ").strip()
            continue
        if not line or line.startswith("#"):
            if line.startswith("#") and "=" not in line and len(line) > 2:
                pass  # inline comment on next line handled below
            continue
        if "=" not in line:
            continue
        name, _, rest = line.partition("=")
        env_name = name.strip()
        if not env_name or env_name in seen:
            continue
        seen.add(env_name)
        comment = ""
        if "#" in rest:
            comment = rest.split("#", 1)[1].strip()
        override = _OVERRIDES.get(env_name, {})
        category = str(override.get("category", _infer_category(current_section, env_name)))
        label = str(override.get("label", _human_label(env_name)))
        required = bool(override.get("required", False))
        secret = bool(
            override.get(
                "secret",
                any(x in env_name for x in ("SECRET", "PASSWORD", "TOKEN", "API_KEY")),
            )
        )
        keys.append(
            KeyDef(
                env_name=env_name,
                category=category,
                label=label,
                required=required,
                secret=secret,
                comment=comment,
            )
        )
    return keys


def all_keys() -> list[KeyDef]:
    return parse_env_example()


def keys_by_category() -> dict[str, list[KeyDef]]:
    grouped: dict[str, list[KeyDef]] = {}
    for key in all_keys():
        grouped.setdefault(key.category, []).append(key)
    return grouped


def categories() -> list[str]:
    order = list(CATEGORY_LABELS.keys())
    present = {k.category for k in all_keys()}
    return [c for c in order if c in present] + sorted(present - set(order))
