# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, ClassVar


logger = logging.getLogger(__name__)

INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|messages?)", "instruction_override"),
    (r"\bsystem\s*:\s*", "system_prompt_hijack"),
    (r"<\|im_start\|>", "chatml_delimiter"),
    (r"<\|im_end\|>", "chatml_delimiter"),
    (r"you\s+are\s+now\s+(a\s+|the\s+)?", "role_switch"),
    (r"\bDAN\s+mode\b", "dan_jailbreak"),
    (r"\\x00", "null_byte_escape"),
    (r"\\u0000", "unicode_null"),
    (r"<\s*(script|iframe|object|embed|applet)\b", "html_injection"),
    (r"\$\{.*?\}", "template_injection"),
    (r"\{\{.*?\}\}", "mustache_injection"),
    (r"__import__\s*\(", "python_import"),
    (r"os\.system\s*\(", "python_os_system"),
    (r"subprocess\.(run|Popen|call)\s*\(", "python_subprocess"),
    (r"eval\s*\(", "python_eval"),
    (r"exec\s*\(", "python_exec"),
]

MCP_DIRECTIVE_PATTERNS: list[tuple[str, str]] = [
    (r'"method"\s*:\s*"tools/call"', "mcp_method_override"),
    (r'"method"\s*:\s*"tools/list"', "mcp_method_override"),
    (r'"jsonrpc"\s*:\s*"2\.0"', "jsonrpc_injection"),
    (r'"result"\s*:', "mcp_result_injection"),
    (r'"error"\s*:', "mcp_error_injection"),
    (r'"id"\s*:\s*null', "mcp_null_id"),
]

MAX_PIPELINE_CHARS = 100_000
MAX_FLASH_CHARS = 10_000


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


class SanitizerInput:
    """SanitizerInput."""
    _injection_regex: ClassVar[re.Pattern[str]] = re.compile(
        "|".join(f"(?:{pattern})" for pattern, _name in INJECTION_PATTERNS),
        re.IGNORECASE,
    )
    _mcp_regex: ClassVar[re.Pattern[str]] = re.compile(
        "|".join(f"(?:{pattern})" for pattern, _name in MCP_DIRECTIVE_PATTERNS),
        re.IGNORECASE,
    )

    @classmethod
    def detect_injection(cls, text: Any) -> bool:
        """Detect injection."""
        if not isinstance(text, str):
            return False
        if cls._injection_regex.search(text):
            return True
        if cls._mcp_regex.search(text):
            return True
        if "\x00" in text:
            logger.warning(
                "Prompt injection detected: null_byte_raw hash=%s",
                _hash_text(text),
            )
            return True
        return False

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Sanitize text."""
        if not isinstance(text, str):
            raise ValueError(f"Expected str, got {type(text).__name__}")
        if cls.detect_injection(text):
            logger.warning(
                "Prompt injection rejected hash=%s len=%d",
                _hash_text(text),
                len(text),
            )
            raise ValueError("Input contains prompt injection patterns — rejected")
        return text

    @classmethod
    def validate_length(cls, text: str, max_len: int) -> bool:
        return len(text) <= max_len
