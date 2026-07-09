"""Tests for dissertation LLM validation."""

from __future__ import annotations

from src.publishing.dissertation import _is_valid_llm_output


def test_rejects_llm_unavailable_placeholder() -> None:
    assert not _is_valid_llm_output("[LLM unavailable: HTTPStatusError]")


def test_accepts_real_prose() -> None:
    text = " ".join(["word"] * 100)
    assert _is_valid_llm_output(text)
