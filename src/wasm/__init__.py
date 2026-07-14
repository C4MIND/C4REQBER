"""WASM plugin runtime — sandboxed plugin execution via WebAssembly.

Provides:
- WASMPluginRuntime: load and execute .wasm modules (wasmtime or stub mode)
- WASMToolPlugin: integrate WASM modules as PluginRegistry tools
"""
from __future__ import annotations

from src.wasm.runtime import WASMFunction, WASMModule, WASMPluginRuntime, WASMToolPlugin


__all__ = ["WASMPluginRuntime", "WASMToolPlugin", "WASMFunction", "WASMModule"]
