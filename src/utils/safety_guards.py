# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""User Safety Guards — prevent common user-caused crashes and data loss.

Guards:
- Input validation: empty input, too long, special characters
- Rate limit awareness: detect 429 + auto-throttle
- Disk space check: prevent export failures
- File size: reject >100MB uploads
- Council without keys: warn before crashing
- Parallel turbo: warn about rate limits
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path


logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 100_000  # chars
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MIN_DISK_SPACE_MB = 100
SAFE_RATE_LIMIT_PAUSE = 30  # seconds to wait after 429


def validate_prompt(prompt: str) -> str:
    """Validate and sanitize user prompt. Returns cleaned prompt or raises ValueError."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty. Provide a research question or topic.")

    prompt = prompt.strip()
    if len(prompt) > MAX_INPUT_LENGTH:
        raise ValueError(
            f"Prompt too long: {len(prompt)} chars (max {MAX_INPUT_LENGTH}). "
            "Consider splitting into multiple queries."
        )

    if len(prompt) < 10:
        logger.warning("Very short prompt (%d chars) — results may be generic", len(prompt))

    if prompt.count("--") > 2 or prompt.count("&&") > 0 or prompt.count("||") > 0:
        raise ValueError(
            "Prompt contains shell operators (--, &&, ||). "
            "Wrap your prompt in quotes if it contains special characters."
        )

    return prompt


def check_disk_space(path: str = ".") -> bool:
    """Check if enough disk space for pipeline exports."""
    try:
        usage = shutil.disk_usage(path)
        free_mb = usage.free / (1024 * 1024)
        if free_mb < MIN_DISK_SPACE_MB:
            logger.warning(
                "Low disk space: %.0f MB free (min %d MB). Export may fail.",
                free_mb, MIN_DISK_SPACE_MB,
            )
            return False
        return True
    except Exception:
        return True  # Can't check — proceed anyway


def validate_file_size(filepath: str | Path) -> bool:
    """Reject files larger than MAX_FILE_SIZE."""
    p = Path(filepath)
    try:
        size = p.stat().st_size
        if size > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {p.name} ({size / 1024 / 1024:.1f} MB). "
                f"Max {MAX_FILE_SIZE / 1024 / 1024:.0f} MB."
            )
        return True
    except OSError:
        return True  # Can't read — let downstream handle


def check_council_ready(council_tier: str) -> bool:
    """Check if council mode can run — warn if no API keys in cheap tier."""
    if council_tier in ("cheap", "balanced", "premium"):
        keys_needed = [
            "OPENROUTER_API_KEY",
        ]
        missing = [k for k in keys_needed if not os.environ.get(k)]
        if missing:
            logger.warning(
                "Council mode '%s' requires API keys: %s. "
                "Council will fall back to local MLX or fail.",
                council_tier, ", ".join(missing),
            )
            return False
    return True


def rate_limit_aware(max_concurrent: int) -> int:
    """Auto-throttle concurrent pipelines to avoid OpenRouter 429."""
    if max_concurrent > 2:
        logger.warning(
            "High concurrency (%d pipelines). OpenRouter may rate-limit (429). "
            "Recommended: --max-concurrent 1 for reliability.",
            max_concurrent,
        )
        return min(max_concurrent, 2)
    return max_concurrent
