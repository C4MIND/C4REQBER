"""C4REQBER: WASM runtime for plugin execution."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol


class WASMModule(Protocol):
    """Protocol for a loaded WASM module."""

    def get_export(self, name: str) -> Any:
        ...


@dataclass
class WASMFunction:
    """Represents an exported WASM function."""

    name: str
    params: list[str] = field(default_factory=list)
    results: list[str] = field(default_factory=list)


class WASMPluginRuntime:
    """
    Runtime for loading and executing WASM modules.

    Uses ``wasmtime`` when available, otherwise falls back to a stub
    that records metadata and raises on execution.
    """

    def __init__(self) -> None:
        self._modules: dict[str, Any] = {}
        self._has_wasmtime = False
        self._engine: Any = None
        self._store: Any = None
        try:
            import wasmtime

            self._has_wasmtime = True
            self._engine = wasmtime.Engine()
            self._store = wasmtime.Store(self._engine)
        except ImportError:
            pass

    def _module_key(self, wasm_bytes: bytes) -> str:
        return hashlib.sha256(wasm_bytes).hexdigest()[:16]

    def load(self, wasm_bytes: bytes) -> Any:
        """Load a WASM module from raw bytes.

        Returns a module handle that can be passed to ``execute`` and
        ``list_functions``.
        """
        key = self._module_key(wasm_bytes)
        if key in self._modules:
            return self._modules[key]

        if self._has_wasmtime:
            import wasmtime

            module = wasmtime.Module(self._engine, wasm_bytes)
            store = wasmtime.Store(self._engine)

            # Try WASI first (standard imports)
            try:
                linker = wasmtime.Linker(self._engine)
                wasi_config = wasmtime.WasiConfig()
                wasi_config.inherit_stdin()
                wasi_config.inherit_stdout()
                wasi_config.inherit_stderr()
                store.set_wasi(wasi_config)
                linker.define_wasi()
                instance = linker.instantiate(store, module)
                self._modules[key] = (store, instance)
                return (store, instance)
            except Exception:
                pass

            # Fallback: pure compute (no imports)
            instance = wasmtime.Instance(store, module, [])
            self._modules[key] = (store, instance)
            return (store, instance)

        # Stub mode: keep bytes for inspection, raise on execution
        stub = {"_wasm_bytes": wasm_bytes, "_stub": True}
        self._modules[key] = stub
        return stub

    def execute(self, module: Any, function: str, args: list[Any]) -> Any:
        """Execute an exported WASM function with the given arguments."""
        if isinstance(module, dict) and module.get("_stub"):
            raise RuntimeError(
                "WASM execution requires 'wasmtime' package. "
                "Install it: pip install wasmtime"
            )

        if self._has_wasmtime:
            import wasmtime
            store, instance = module if isinstance(module, tuple) else (self._store, module)

            export = instance.exports(store).get(function)
            if export is None:
                raise ValueError(f"Function '{function}' not found in WASM exports")
            if not isinstance(export, wasmtime.Func):
                raise ValueError(f"Export '{function}' is not a function")
            return export(store, *args)

        raise RuntimeError("No WASM runtime available")

    def _parse_exports(self, wasm_bytes: bytes) -> list[tuple[str, int]]:
        """Parse export section from WASM binary. Returns [(name, kind), ...].
        Kind: 0=func, 1=table, 2=memory, 3=global.
        """
        if len(wasm_bytes) < 8 or wasm_bytes[:4] != b"\x00asm":
            return []
        pos = 8  # skip magic + version
        while pos < len(wasm_bytes):
            section_id = wasm_bytes[pos]
            pos += 1
            size, shift = 0, 0
            while True:
                byte = wasm_bytes[pos]
                pos += 1
                size |= (byte & 0x7F) << shift
                if (byte & 0x80) == 0:
                    break
                shift += 7
            if section_id == 7:  # export section
                end = pos + size
                num_exports, shift = 0, 0
                while True:
                    byte = wasm_bytes[pos]
                    pos += 1
                    num_exports |= (byte & 0x7F) << shift
                    if (byte & 0x80) == 0:
                        break
                    shift += 7
                exports = []
                for _ in range(num_exports):
                    name_len, shift = 0, 0
                    while True:
                        byte = wasm_bytes[pos]
                        pos += 1
                        name_len |= (byte & 0x7F) << shift
                        if (byte & 0x80) == 0:
                            break
                        shift += 7
                    name = wasm_bytes[pos:pos + name_len].decode()
                    pos += name_len
                    kind = wasm_bytes[pos]
                    pos += 1
                    _idx, shift = 0, 0  # export index
                    while True:
                        byte = wasm_bytes[pos]
                        pos += 1
                        _idx |= (byte & 0x7F) << shift
                        if (byte & 0x80) == 0:
                            break
                        shift += 7
                    exports.append((name, kind))
                return exports
            else:
                pos += size
        return []

    def list_functions(self, module: Any) -> list[str]:
        """List names of exported functions in the module."""
        if isinstance(module, dict) and module.get("_stub"):
            exports = self._parse_exports(module["_wasm_bytes"])
            return [name for name, kind in exports if kind == 0]  # kind 0 = function

        if self._has_wasmtime:
            import wasmtime
            store, instance = module if isinstance(module, tuple) else (self._store, module)

            return [
                name
                for name, item in instance.exports(store).items()
                if isinstance(item, wasmtime.Func)
            ]

        return []

    def get_memory(self, module: Any, name: str = "memory") -> bytes | None:
        """Read exported linear memory as bytes (if present)."""
        if isinstance(module, dict) and module.get("_stub"):
            return None

        if self._has_wasmtime:
            import wasmtime

            mem = module.exports(self._store).get(name)
            if isinstance(mem, wasmtime.Memory):
                return mem.read(self._store, 0, mem.size(self._store))
        return None


class WASMPluginAdapter:
    """
    Adapter that wraps a WASM module so it looks like a regular
    ``ToolPlugin`` to the rest of the system.
    """

    def __init__(self, runtime: WASMPluginRuntime, wasm_bytes: bytes, plugin_id: str) -> None:
        self.runtime = runtime
        self.wasm_bytes = wasm_bytes
        self.plugin_id = plugin_id
        self._module = runtime.load(wasm_bytes)

    def call(self, function: str, args: list[Any]) -> Any:
        """Call a WASM-exported function."""
        return self.runtime.execute(self._module, function, args)

    def list_exports(self) -> list[str]:
        """List exported functions."""
        return self.runtime.list_functions(self._module)

    def describe(self) -> dict[str, Any]:
        """Return metadata about the loaded WASM plugin."""
        return {
            "plugin_id": self.plugin_id,
            "exports": self.list_exports(),
            "has_runtime": self.runtime._has_wasmtime,
        }


class WASMToolPlugin:
    """Backward-compatible shim for the deleted ``plugin_adapter.WASMToolPlugin``.

    Wraps a WASM module as a ToolPlugin for the plugin registry.
    Used by ``blast wasm-load`` to register WASM plugins in the pipeline.
    """

    def __init__(self, runtime: WASMPluginRuntime, wasm_bytes: bytes, metadata: Any) -> None:
        self._adapter = WASMPluginAdapter(runtime, wasm_bytes, "")
        self.metadata = metadata

    def execute(self, **kwargs: Any) -> Any:
        """Execute the default 'execute' function in the WASM module."""
        return self._adapter.call("execute", list(kwargs.values()))

    def get_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}
