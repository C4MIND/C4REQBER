"""Safe draft directory resolution — reject path traversal via draft_id."""

from __future__ import annotations

from pathlib import Path

from src.config.paths import CONFIG_DIR


def drafts_base() -> Path:
    return (CONFIG_DIR / "drafts").resolve()


def safe_draft_dir(draft_id: str) -> Path:
    """Resolve draft_id under ~/.c4reqber/drafts; raise ValueError on traversal."""
    if not draft_id or not isinstance(draft_id, str):
        raise ValueError("invalid draft_id")
    if any(tok in draft_id for tok in ("..", "/", "\\", "\x00")):
        raise ValueError("invalid draft_id")
    base = drafts_base()
    base.mkdir(parents=True, exist_ok=True)
    draft_dir = (base / draft_id).resolve()
    if not draft_dir.is_relative_to(base):
        raise ValueError("invalid draft_id")
    return draft_dir
