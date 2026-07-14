# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
import re
from typing import Any


logger = logging.getLogger(__name__)

CREDENTIALS_BLOCKLIST: list[tuple[str, str]] = [
    (r"sk-[a-zA-Z0-9_-]{20,}", "api_secret_key"),
    (r"Bearer\s+[A-Za-z0-9\-_\.\+]+", "bearer_token"),
    (r"api_key\s*[:=]\s*[\'\"]?\w+[\'\"]?", "api_key_assignment"),
    (r"sk-or-[a-zA-Z0-9_-]{20,}", "openrouter_key"),
    (r"nvapi-[a-zA-Z0-9_-]{20,}", "nvidia_key"),
    (r"--api-key\s+\S+", "cli_api_key"),
    (r"x-api-key\s*[:=]\s*\S+", "http_api_key"),
    (r"Authorization\s*[:=]\s*\S+", "authorization_header"),
    (r"ghp_[a-zA-Z0-9]{36}", "github_pat"),
    (r"gho_[a-zA-Z0-9]{36}", "github_oauth"),
    (r"ghu_[a-zA-Z0-9]{36}", "github_user"),
    (r"ghs_[a-zA-Z0-9]{36}", "github_server"),
    (r"ghr_[a-zA-Z0-9]{36}", "github_refresh"),
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r"secret\s*[:=]\s*[\'\"][^\'\"]{8,}[\'\"]", "generic_secret"),
]

_CREDENTIAL_REGEX: re.Pattern[str] = re.compile(
    "|".join(pattern for pattern, _name in CREDENTIALS_BLOCKLIST),
    re.IGNORECASE,
)

_REDACTION_TEXT = "[REDACTED-CREDENTIAL]"


def redact_credentials(text: Any) -> Any:
    """Redact credentials."""
    if not isinstance(text, str):
        return text
    result = _CREDENTIAL_REGEX.sub(_REDACTION_TEXT, text)
    if result != text:
        logger.debug("Credential patterns redacted from output (len=%d → %d)", len(text), len(result))
    return result


def audit_log_safe(text: Any) -> bool:
    """Audit log safe."""
    if not isinstance(text, str):
        return True
    match = _CREDENTIAL_REGEX.search(text)
    if match:
        logger.warning(
            "Potential credentials detected in audit output — suppressed. Match at position %d",
            match.start(),
        )
        return False
    return True
