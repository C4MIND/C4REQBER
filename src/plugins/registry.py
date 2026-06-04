from __future__ import annotations


"""
C4REQBER: Tool Plugin System
Extensible plugin framework for custom tools
"""
import importlib
import logging
import pkgutil
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.di.container import get_container


@dataclass
class ToolMetadata:
    """Metadata for a tool plugin."""

    name: str
    version: str
    description: str
    author: str
    requires: list[str]  # Dependencies


class ToolPlugin(ABC):
    """Base class for tool plugins."""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool."""
        pass

    def validate_input(self, **kwargs: Any) -> bool:
        """Validate input parameters."""
        return True

    def get_schema(self) -> dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {"type": "object", "properties": {}}


class PluginRegistry:
    """
    Registry for tool plugins.

    Manages loading and execution of custom tools.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, ToolPlugin] = {}
        self._hooks: dict[str, list[Callable]] = {}  # type: ignore[type-arg]

    def register(self, plugin: ToolPlugin) -> None:
        """Register a plugin."""
        name = plugin.metadata.name
        self._plugins[name] = plugin

    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]

    def get_plugin(self, name: str) -> ToolPlugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> list[ToolMetadata]:
        """List all registered plugins."""
        return [p.metadata for p in self._plugins.values()]

    def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            raise ValueError(f"Plugin not found: {name}")

        if not plugin.validate_input(**kwargs):
            raise ValueError(f"Invalid input for plugin: {name}")

        return plugin.execute(**kwargs)

    def register_hook(self, event: str, callback: Callable) -> None:  # type: ignore[type-arg]
        """Register a hook for an event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def trigger_hook(self, event: str, **kwargs: Any) -> None:
        """Trigger all hooks for an event."""
        for callback in self._hooks.get(event, []):
            callback(**kwargs)

    def discover_plugins(self, package_name: str = "c4_cdi_turbo.plugins") -> None:
        """Auto-discover plugins in a package."""
        try:
            package = importlib.import_module(package_name)
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                try:
                    module = importlib.import_module(f"{package_name}.{name}")
                    # Look for Plugin class
                    if hasattr(module, "Plugin"):
                        plugin_class = module.Plugin
                        plugin = plugin_class()
                        self.register(plugin)
                except Exception as e:
                    print(f"Failed to load plugin {name}: {e}")
        except ImportError:
            pass  # Package doesn't exist


# Built-in example plugins


class WebSearchPlugin(ToolPlugin):
    """Example plugin: Web search integration."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="web_search",
            version="1.0.0",
            description="Search the web for information",
            author="C4Reqber",
            requires=[],
        )

    def execute(self, query: str, max_results: int = 5) -> list[dict]:  # type: ignore[override, type-arg]
        """Execute web search."""
        # Placeholder - would integrate with search API
        return [
            {"title": f"Result {i}", "url": f"http://example.com/{i}"}
            for i in range(max_results)
        ]


class CalculatorPlugin(ToolPlugin):
    """Example plugin: Mathematical calculations."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calculator",
            version="1.0.0",
            description="Perform mathematical calculations",
            author="C4Reqber",
            requires=[],
        )

    def execute(self, expression: str) -> float:  # type: ignore[override]
        """Evaluate mathematical expression."""
        from src.utils.safe_eval import safe_eval

        try:
            return safe_eval(expression.strip(), {
                "abs": abs,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
            })
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("Calculator expression evaluation failed: %s", e)
            raise


def get_plugin_registry() -> PluginRegistry:
    """Get singleton plugin registry (backed by DI container)."""
    container = get_container()
    if not container.has("plugin_registry"):
        registry = PluginRegistry()
        # Register built-in plugins
        registry.register(WebSearchPlugin())
        registry.register(CalculatorPlugin())
        container.register("plugin_registry", registry)
    return container.resolve("plugin_registry")
