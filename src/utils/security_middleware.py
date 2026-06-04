"""Unified security middleware for C4REQBER.

Provides centralized input validation, prompt sanitization, and path traversal guards.
"""
from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Any, Callable


# ── Prompt Sanitization ─────────────────────────────────────────────────────

PROMPT_MAX_LENGTH = 100_000


def sanitize_prompt(text: str, max_len: int = 500) -> str:
    """Sanitize user input before inserting into LLM prompts.

    Strips control characters, decodes HTML entities, neutralizes
    prompt-injection tags, and truncates to max_len.
    """
    if not text:
        return text

    # Decode HTML entities so &lt;system&gt; becomes <system>
    text = html.unescape(text)

    # Strip control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Neutralize triple quotes and dashes that could break markdown fences
    text = text.replace('"""', '"').replace("---", "-")

    # Prompt-injection hardening
    text = text.replace("</user_query>", "[END_TAG]")
    text = text.replace("<user_query>", "[USER_TAG]")
    text = text.replace("<system>", "[SYSTEM_TAG_REMOVED]")
    text = text.replace("</system>", "[END_SYSTEM_TAG]")
    text = text.replace("<assistant>", "[ASSISTANT_TAG_REMOVED]")
    text = text.replace("</assistant>", "[END_ASSISTANT_TAG]")
    text = text.replace("<|im_start|>", "[IM_START_REMOVED]")
    text = text.replace("<|im_end|>", "[IM_END_REMOVED]")

    # Block bare role tags without brackets
    for tag in ("system:", "user:", "assistant:", "system>", "user>", "assistant>"):
        text = text.replace(tag, f"[{tag.upper()}_REMOVED]")

    # Unicode bidirectional override characters
    text = text.replace("\u202E", "").replace("\u202D", "").replace("\u200E", "").replace("\u200F", "")

    # Nested backticks / code fences
    text = text.replace("`" * 3, "` ` `")
    text = text.replace("`" * 2, "` `")

    # Strip Unicode bidi overrides (additional range)
    text = re.sub(r"[\u202A-\u202E\u2066-\u2069]", "", text)

    # Block bare role prefixes at line start
    text = re.sub(r"(?i)^\s*(system|user|assistant)\s*[:>]", "[BLOCKED]", text)

    # Truncate
    return text[:max_len]


# ── Path Traversal Guard ────────────────────────────────────────────────────


def validate_path(path: str | Path, allowed_base: Path | None = None) -> Path:
    """Validate that a path is within the allowed base directory.

    Raises ValueError if the path attempts directory traversal.
    """
    path_obj = Path(path).resolve()
    if allowed_base is None:
        allowed_base = Path(os.path.expanduser("~/.c4reqber")).resolve()
    if not str(path_obj).startswith(str(allowed_base)):
        raise ValueError(f"Path traversal detected: {path} is outside {allowed_base}")
    return path_obj


# ── Paper ID Validation ─────────────────────────────────────────────────────

_PAPER_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_paper_id(paper_id: str) -> str:
    """Validate a paper ID against allowed characters.

    Raises ValueError if the ID contains suspicious characters.
    """
    if not paper_id or not _PAPER_ID_RE.match(paper_id):
        raise ValueError(f"Invalid paper ID: {paper_id}")
    return paper_id


# ── Configurable LLM Model Validation ───────────────────────────────────────


def validate_llm_model(model: str) -> str:
    """Validate an LLM model identifier.

    Currently a lightweight check; can be extended to a known-model allowlist.
    """
    if not model or len(model) > 200:
        raise ValueError("LLM model identifier too long or empty")
    if model.count("/") > 3:
        raise ValueError("LLM model identifier malformed")
    return model


# ── Unified Validation Entrypoint ───────────────────────────────────────────


def validate_input(data: dict[str, Any], rules: dict[str, Callable[[Any], Any]]) -> dict[str, Any]:
    """Validate a dict of inputs against a schema of validation rules.

    Returns cleaned data or raises ValueError with all failures.
    """
    errors: list[str] = []
    cleaned: dict[str, Any] = {}
    for key, rule in rules.items():
        value = data.get(key)
        try:
            cleaned[key] = rule(value)
        except Exception as e:
            errors.append(f"{key}: {e}")
    if errors:
        raise ValueError("; ".join(errors))
    return cleaned
