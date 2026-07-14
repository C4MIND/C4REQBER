"""Tests for credential_guard — credential redaction and audit safety."""

from __future__ import annotations

import pytest

from src.security.credential_guard import CREDENTIALS_BLOCKLIST, audit_log_safe, redact_credentials


class TestRedactCredentials:
    def test_redact_openai_key(self) -> None:
        text = "API key is sk-abcdefghijklmnopqrstuvwxyz123456"
        result = redact_credentials(text)
        assert "[REDACTED-CREDENTIAL]" in result
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in result

    def test_redact_openrouter_key(self) -> None:
        text = "Key: sk-or-v1-abcdefghijklmnopqrstuvwxyz"
        result = redact_credentials(text)
        assert "[REDACTED-CREDENTIAL]" in result

    def test_redact_bearer_token(self) -> None:
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact_credentials(text)
        assert "[REDACTED-CREDENTIAL]" in result

    def test_redact_api_key_assignment(self) -> None:
        text = "api_key = 'abc123secretkey'"
        result = redact_credentials(text)
        assert "[REDACTED-CREDENTIAL]" in result

    def test_redact_multiple_credentials(self) -> None:
        text = "key1=sk-abcdefghijklmnopqrstuvwxyz and key2=Bearer token123"
        result = redact_credentials(text)
        count = result.count("[REDACTED-CREDENTIAL]")
        assert count == 2

    def test_clean_text_unchanged(self) -> None:
        text = "This is a normal log message with no secrets"
        result = redact_credentials(text)
        assert result == text

    def test_non_string_unchanged(self) -> None:
        assert redact_credentials(42) == 42
        assert redact_credentials(None) is None

    def test_nvidia_key(self) -> None:
        text = "Using nvapi-abcdefg1234567890hijklmnopqrst"
        result = redact_credentials(text)
        assert "[REDACTED-CREDENTIAL]" in result

    def test_github_pat(self) -> None:
        text = "Token: ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890"
        result = redact_credentials(text)
        assert "[REDACTED-CREDENTIAL]" in result

    def test_aws_key(self) -> None:
        text = "AWS key: AKIA1234567890ABCDEF"
        result = redact_credentials(text)
        assert "[REDACTED-CREDENTIAL]" in result


class TestAuditLogSafe:
    def test_clean_text_safe(self) -> None:
        assert audit_log_safe("Normal log message")

    def test_credential_unsafe(self) -> None:
        assert not audit_log_safe("sk-Proj-abcdefghijklmnopqrstuvwxyz1234567890")

    def test_bearer_unsafe(self) -> None:
        assert not audit_log_safe("Bearer abc123.def456")

    def test_non_string_safe(self) -> None:
        assert audit_log_safe(42)
        assert audit_log_safe(None)

    def test_empty_string_safe(self) -> None:
        assert audit_log_safe("")


class TestBlocklistPatterns:
    def test_all_patterns_compile(self) -> None:
        import re

        for pattern, _name in CREDENTIALS_BLOCKLIST:
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None
