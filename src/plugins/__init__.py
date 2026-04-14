"""
TURBO-CDI: Plugins Module
Extensible tool plugin system
"""

from src.plugins.registry import (
    PluginRegistry,
    ToolPlugin,
    ToolMetadata,
    get_plugin_registry,
)

__all__ = [
    "PluginRegistry",
    "ToolPlugin",
    "ToolMetadata",
    "get_plugin_registry",
]
