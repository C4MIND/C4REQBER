"""
TURBO-CDI: Tool Plugin System
Extensible plugin framework for custom tools
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import importlib
import pkgutil


@dataclass
class ToolMetadata:
    """Metadata for a tool plugin."""

    name: str
    version: str
    description: str
    author: str
    requires: List[str]  # Dependencies


class ToolPlugin(ABC):
    """Base class for tool plugins."""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        pass

    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        return True

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {"type": "object", "properties": {}}


class PluginRegistry:
    """
    Registry for tool plugins.

    Manages loading and execution of custom tools.
    """

    def __init__(self):
        self._plugins: Dict[str, ToolPlugin] = {}
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, plugin: ToolPlugin):
        """Register a plugin."""
        name = plugin.metadata.name
        self._plugins[name] = plugin

    def unregister(self, name: str):
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]

    def get_plugin(self, name: str) -> Optional[ToolPlugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> List[ToolMetadata]:
        """List all registered plugins."""
        return [p.metadata for p in self._plugins.values()]

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            raise ValueError(f"Plugin not found: {name}")

        if not plugin.validate_input(**kwargs):
            raise ValueError(f"Invalid input for plugin: {name}")

        return plugin.execute(**kwargs)

    def register_hook(self, event: str, callback: Callable):
        """Register a hook for an event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def trigger_hook(self, event: str, **kwargs):
        """Trigger all hooks for an event."""
        for callback in self._hooks.get(event, []):
            callback(**kwargs)

    def discover_plugins(self, package_name: str = "turbo_cdi.plugins"):
        """Auto-discover plugins in a package."""
        try:
            package = importlib.import_module(package_name)
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                try:
                    module = importlib.import_module(f"{package_name}.{name}")
                    # Look for Plugin class
                    if hasattr(module, "Plugin"):
                        plugin_class = getattr(module, "Plugin")
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
            author="TURBO-CDI",
            requires=[],
        )

    def execute(self, query: str, max_results: int = 5) -> List[Dict]:
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
            author="TURBO-CDI",
            requires=[],
        )

    def execute(self, expression: str) -> float:
        """Evaluate mathematical expression."""
        # Safe evaluation - only allow basic math
        allowed = {
            "__builtins__": {},
            "abs": abs,
            "max": max,
            "min": min,
            "pow": pow,
            "round": round,
        }
        return eval(expression, allowed)


# Singleton
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get singleton plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        # Register built-in plugins
        _registry.register(WebSearchPlugin())
        _registry.register(CalculatorPlugin())
    return _registry
