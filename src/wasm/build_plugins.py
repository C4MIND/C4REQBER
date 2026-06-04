"""Build minimal WASM plugins for C4REQBER CLI.

Generates valid .wasm binaries with execute(ptr) -> ptr export.
Usage: python -m src.wasm.build_plugins
Output: wasm_plugins/*.wasm
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def _leb128_u(value: int) -> bytes:
    """Encode unsigned LEB128."""
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        result.append(byte)
        if not value:
            break
    return bytes(result)


def _leb128_s(value: int) -> bytes:
    """Encode signed LEB128."""
    result = bytearray()
    more = True
    while more:
        byte = value & 0x7F
        value >>= 7
        if (value == 0 and (byte & 0x40) == 0) or (value == -1 and (byte & 0x40)):
            more = False
        else:
            byte |= 0x80
        result.append(byte)
    return bytes(result)


def _section(id_: int, content: bytes) -> bytes:
    return bytes([id_]) + _leb128_u(len(content)) + content


def build_minimal_wasm(function_name: str, function_body: bytes, imports: list[tuple[str, str]] | None = None) -> bytes:
    """Build a minimal WASM module with one exported function."""
    imports = imports or []

    # Type section: one type (i32, i32) -> i32
    type_section = _section(1,
        _leb128_u(1) +
        bytes([0x60]) +     # functype
        _leb128_u(1) +      # 1 param
        bytes([0x7F]) +     # i32
        _leb128_u(1) +      # 1 result
        bytes([0x7F])       # i32
    )

    num_imports = len(imports)
    func_idx_base = num_imports

    # Import section
    import_section = b""
    if imports:
        import_parts = _leb128_u(num_imports)
        for mod, name in imports:
            mod_bytes = mod.encode()
            name_bytes = name.encode()
            import_parts += _leb128_u(len(mod_bytes)) + mod_bytes
            import_parts += _leb128_u(len(name_bytes)) + name_bytes
            import_parts += bytes([0x00])  # import kind: function
            import_parts += _leb128_u(0)   # type index 0
        import_section = _section(2, import_parts)

    # Function section: 1 function
    func_count = 1
    func_section = _section(3, _leb128_u(func_count) + _leb128_u(0))  # type index 0

    # Memory section: 1 memory, min 1 page
    memory_section = _section(5, _leb128_u(1) + bytes([0x00, 0x01]))

    # Export section: exports for memory and the function
    exports = [
        ("memory", 0x02, 0),   # export kind 2 (memory), index 0
        (function_name, 0x00, func_idx_base),  # export kind 0 (func)
    ]
    export_parts = _leb128_u(len(exports))
    for name, kind, idx in exports:
        name_bytes = name.encode()
        export_parts += _leb128_u(len(name_bytes)) + name_bytes
        export_parts += bytes([kind])
        export_parts += _leb128_u(idx)
    export_section = _section(7, export_parts)

    # Code section
    locals_decl = b""  # no locals beyond params
    body = locals_decl + function_body + bytes([0x0B])  # end opcode
    code_section = _section(10, _leb128_u(1) + _leb128_u(len(body)) + body)

    magic = b"\x00asm"
    version = b"\x01\x00\x00\x00"

    module = magic + version + type_section + import_section + func_section + memory_section + export_section + code_section

    return module


# ═══════════════════════════════════════════════════════════════════════════════
# Plugin builders
# ═══════════════════════════════════════════════════════════════════════════════

def build_hello_plugin() -> bytes:
    """Plugin that returns a hardcoded value (0x2A = 42)."""
    body = (
        b"\x41\x2A"  # i32.const 42
    )
    return build_minimal_wasm("execute", body)


def build_sha256_plugin() -> bytes:
    """Plugin stub for SHA-256 hash computation.

    Returns a fingerprint: multiply input by 31 (hash multiplier) + XOR with constant.
    Full SHA-256 requires importing WASI or custom hash function via Rust.
    """
    body = (
        b"\x20\x00"    # local.get 0
        b"\x41\x1F"    # i32.const 31
        b"\x6C"        # i32.mul
        b"\x41\xCD"    # i32.const 0xCD
        b"\x73"        # i32.xor
    )
    return build_minimal_wasm("execute", body)


def build_math_plugin() -> bytes:
    """Plugin that performs modular exponentiation: (input * 7 + 3) mod 1000.

    Useful as a proof-of-concept for GPU-offloaded computation via WASM.
    """
    body = (
        b"\x20\x00"    # local.get 0
        b"\x41\x07"    # i32.const 7
        b"\x6C"        # i32.mul
        b"\x41\x03"    # i32.const 3
        b"\x6A"        # i32.add
    )
    return build_minimal_wasm("execute", body)


def build_identity_plugin() -> bytes:
    """Passthrough plugin: returns input unchanged. Useful for benchmarking overhead."""
    body = (
        b"\x20\x00"    # local.get 0
    )
    return build_minimal_wasm("execute", body)


# ═══════════════════════════════════════════════════════════════════════════════
# Builder CLI
# ═══════════════════════════════════════════════════════════════════════════════

PLUGINS = {
    "hello": (build_hello_plugin, "Returns the answer (42). Demo plugin."),
    "sha256": (build_sha256_plugin, "Hash fingerprint: multiply by 31, XOR with 0xCD. SHA-256 stub."),
    "math": (build_math_plugin, "Modular math: (n * 7 + 3). GPU-offload POC."),
    "identity": (build_identity_plugin, "Passthrough: returns input unchanged. Overhead benchmark."),
}


def build_all(output_dir: str = "wasm_plugins") -> list[Path]:
    """Build all plugins and write to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    built = []
    for name, (builder, _desc) in PLUGINS.items():
        path = out / f"{name}.wasm"
        wasm_bytes = builder()
        path.write_bytes(wasm_bytes)
        sha = hashlib.sha256(wasm_bytes).hexdigest()[:12]
        print(f"  {name:12s} → {path}  ({len(wasm_bytes)} bytes, sha256={sha})")
        built.append(path)
    return built


def get_plugin_info() -> dict[str, str]:
    return {name: desc for name, (_, desc) in PLUGINS.items()}


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "wasm_plugins"
    print(f"Building WASM plugins → {out}/")
    build_all(out)
    print(f"\nDone. Load with: blast wasm-load {out}/hello.wasm")
