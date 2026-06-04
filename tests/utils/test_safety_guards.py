from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from utils.safety_guards import (
    MAX_INPUT_LENGTH,
    SAFE_RATE_LIMIT_PAUSE,
    check_council_ready,
    check_disk_space,
    rate_limit_aware,
    validate_file_size,
    validate_prompt,
)


class TestValidatePrompt:
    def test_empty_raises_valueerror(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_prompt("")

    def test_whitespace_only_raises_valueerror(self):
        with pytest.raises(ValueError):
            validate_prompt("   ")

    def test_normal_prompt_returns_cleaned(self):
        result = validate_prompt("  What is quantum entanglement?  ")
        assert result == "What is quantum entanglement?"

    def test_too_long_raises_valueerror(self):
        long_prompt = "x" * (MAX_INPUT_LENGTH + 1)
        with pytest.raises(ValueError, match="too long"):
            validate_prompt(long_prompt)

    def test_shell_operators_raises_valueerror(self):
        with pytest.raises(ValueError, match="shell operators"):
            validate_prompt("query --flag --other --third")


class TestCheckDiskSpace:
    def test_current_directory_returns_bool(self):
        result = check_disk_space(".")
        assert isinstance(result, bool)


class TestValidateFileSize:
    def test_existing_file_returns_true(self, tmp_path):
        f = tmp_path / "small.txt"
        f.write_text("hello")
        assert validate_file_size(str(f)) is True

    def test_nonexistent_file_returns_true(self):
        assert validate_file_size("/nonexistent/path/file.txt") is True


class TestCheckCouncilReady:
    def test_premium_tier_returns_true(self):
        assert check_council_ready("premium") is True

    def test_cheap_tier_without_key_returns_false(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        assert check_council_ready("cheap") is False

    def test_cheap_tier_with_key_returns_true(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-fake")
        assert check_council_ready("cheap") is True


class TestRateLimitAware:
    def test_low_concurrency_unchanged(self):
        assert rate_limit_aware(1) == 1

    def test_high_concurrency_throttled(self):
        assert rate_limit_aware(10) == 2

    def test_boundary_concurrency_not_throttled(self):
        assert rate_limit_aware(2) == 2
