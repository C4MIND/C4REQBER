from __future__ import annotations

import abc
from typing import Any


class BaseSourceAdapter(abc.ABC):
    """Base adapter for academic source APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    @property
    @abc.abstractmethod
    def source_id(self) -> str:
        """Return the source identifier."""

    @abc.abstractmethod
    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search the source and return normalized paper records."""
