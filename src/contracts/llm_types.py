"""Shared LLM types — no implementation, no imports from src.*"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Message:
    """A single message in an LLM conversation."""
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """LLM response wrapper."""
    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""


class LLMClient(Protocol):
    """Protocol for LLM client implementations."""

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> Response:
        ...

    async def close(self) -> None:
        ...
