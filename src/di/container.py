from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DIContainer:
    """Simple dependency injection container."""

    _registry: dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, instance: Any) -> None:
        self._registry[name] = instance

    def resolve(self, name: str) -> Any:
        """Resolve."""
        if name not in self._registry:
            raise KeyError(f"No registration for '{name}'")
        return self._registry[name]

    def has(self, name: str) -> bool:
        return name in self._registry

    def get_or_register(self, name: str, factory: Any) -> Any:
        """Get or register."""
        if name not in self._registry:
            self._registry[name] = factory()
        return self._registry[name]


# Eager initialization — no global needed for get
_container = DIContainer()


def get_container() -> DIContainer:
    return _container


def reset_container() -> None:
    _container._registry.clear()
