# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from typing import Any


try:
    from mcp.server.stdio import stdio_server

    from mcp.server import Server

    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    Server = None
    stdio_server = None
    print("⚠️  MCP SDK not installed. Run: pip install mcp", file=sys.stderr)


class _FallbackServer:
    """Minimal JSON-RPC stdio server when MCP SDK is unavailable."""

    def __init__(self, name: str):
        self.name = name
        self._tools: dict[str, Any] = {}
        self.verified_hashes: dict[str, str] = {}

    def tool(self, name: str):
        """Decorator to register a tool."""

        def decorator(func):
            """Decorator."""
            self._tools[name] = func
            return func

        return decorator

    def _compute_tool_hash(self, tool_name: str) -> str:
        tool = self._tools[tool_name]
        schema = getattr(tool, "schema", {})
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()

    def _verify_tool_hash(self, tool_name: str) -> None:
        if tool_name not in self._tools:
            return
        current_hash = self._compute_tool_hash(tool_name)
        if tool_name in self.verified_hashes:
            assert current_hash == self.verified_hashes[tool_name], f"Rug pull detected: {tool_name}"
        else:
            self.verified_hashes[tool_name] = current_hash

    async def run_stdio_fallback(self):
        """Read JSON-RPC requests from stdin, write responses to stdout."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                request = json.loads(line)
                method = request.get("method", "")
                if method == "tools/list":
                    tools = []
                    for tool_name, tool_func in self._tools.items():
                        current_hash = self._compute_tool_hash(tool_name)
                        if tool_name in self.verified_hashes:
                            assert current_hash == self.verified_hashes[tool_name], f"Rug pull detected: {tool_name}"
                        else:
                            self.verified_hashes[tool_name] = current_hash
                        tools.append(
                            {
                                "name": tool_name,
                                "description": tool_func.__doc__ or "",
                                "inputSchema": getattr(
                                    tool_func,
                                    "schema",
                                    {
                                        "type": "object",
                                        "properties": {},
                                    },
                                ),
                            }
                        )
                    response = json.dumps({"jsonrpc": "2.0", "id": request.get("id"), "result": {"tools": tools}})
                elif method == "tools/call":
                    tool_name = request["params"]["name"]
                    tool_args = request["params"].get("arguments", {})
                    if tool_name not in self._tools:
                        response = json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                            }
                        )
                        sys.stdout.write(response + "\n")
                        sys.stdout.flush()
                        continue
                    self._verify_tool_hash(tool_name)
                    tool = self._tools[tool_name]
                    schema = getattr(tool, "schema", {})
                    if schema:
                        properties = schema.get("properties", {})
                        allowed_keys = set(properties.keys())
                        input_keys = set(tool_args.keys())
                        extra_keys = input_keys - allowed_keys
                        if extra_keys and not schema.get("additionalProperties", True):
                            raise ValueError(f"Extra arguments not allowed: {extra_keys}")
                    try:
                        tool_args = validate_tool_input(tool_name, tool_args)
                    except ValueError as e:
                        _mcp_logger.warning(
                            "Input validation failed for tool '%s': %s",
                            redact_credentials(tool_name),
                            redact_credentials(str(e)),
                        )
                        err_response = json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {"code": -32602, "message": f"Invalid input: {e}"},
                            }
                        )
                        sys.stdout.write(err_response + "\n")
                        sys.stdout.flush()
                        continue
                    timeout_s = tool_timeout_seconds(tool_name)
                    try:
                        result = await asyncio.wait_for(self._tools[tool_name](**tool_args), timeout=timeout_s)
                    except TimeoutError:
                        result = {
                            "status": "error",
                            "code": "TIMEOUT",
                            "errors": [f"Tool execution timed out after {int(timeout_s)} seconds"],
                            "tool": tool_name,
                            "hint": "For long pipelines use blast CLI directly or retry with a narrower query.",
                        }
                    except (IndexError, KeyError, TypeError) as e:
                        result = {"status": "error", "errors": [str(e)]}
                    if isinstance(result, str):
                        result = redact_credentials(result)
                    elif isinstance(result, dict):
                        result = {k: redact_credentials(str(v)) if isinstance(v, str) else v for k, v in result.items()}
                    response = json.dumps({"jsonrpc": "2.0", "id": request.get("id"), "result": result})
                else:
                    response = json.dumps({"jsonrpc": "2.0", "id": request.get("id"), "result": {}})
                sys.stdout.write(response + "\n")
                sys.stdout.flush()
            except (TimeoutError, AttributeError, IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
                error_response = json.dumps(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {e}"}}
                )
                sys.stdout.write(error_response + "\n")
                sys.stdout.flush()
                continue


import logging

from src.security.credential_guard import redact_credentials
from src.security.prompt_sanitizer import MAX_FLASH_CHARS, MAX_PIPELINE_CHARS, SanitizerInput


_mcp_logger = logging.getLogger("c44tcdi.mcp_server")

# Per-tool execution timeouts (seconds). Long pipelines need headroom for LLM + verification.
DEFAULT_TOOL_TIMEOUT = 60.0
TOOL_TIMEOUTS: dict[str, float] = {
    "blast_turbo": 600.0,
    "blast_solve": 600.0,
    "blast_turbofactory": 900.0,
    "c4_solve": 600.0,
    "c4_autoresearch": 600.0,
    "c4_chain": 600.0,
    "blast_flash": 120.0,
    "c4_verify": 180.0,
    "c4_prove": 180.0,
    "c4_simulate": 120.0,
}


def tool_timeout_seconds(tool_name: str) -> float:
    """Return the configured timeout for an MCP tool."""
    return TOOL_TIMEOUTS.get(tool_name, DEFAULT_TOOL_TIMEOUT)


TOOL_STRING_ARGS: dict[str, list[str]] = {
    "c4_solve": ["problem", "domain"],
    "c4_search": ["query"],
    "c4_triz": ["problem"],
    "c4_fingerprint": ["problem"],
    "c4_verify": ["code", "language"],
    "c4_transfer": ["problem", "source_domain", "target_domain"],
    "c4_simulate": ["pattern_id"],
    "c4_bayesian": [],
    "c4_causal": ["treatment", "outcome"],
    "c4_export": ["format"],
    "c4_autoresearch": ["file", "metric"],
    "c4_chain": ["problem"],
    "c4_meta": ["reasoning_trace"],
    "blast_solve": ["problem", "output_format", "domain"],
    "blast_turbo": ["topic", "verify_backend"],
    "blast_flash": ["question"],
    "blast_turbofactory": ["domain", "scale", "pipeline_mode"],
    "blast_auto": ["query"],
}


def validate_tool_input(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Sanitize all string arguments for a given MCP tool before execution.

    Rejects inputs containing prompt injection patterns.
    Clamps string arguments to their max length (100K pipeline / 10K flash).
    """
    string_args = TOOL_STRING_ARGS.get(tool_name, [])
    is_flash = tool_name in ("blast_flash",)
    max_len = MAX_FLASH_CHARS if is_flash else MAX_PIPELINE_CHARS

    for key in string_args:
        if key in arguments and isinstance(arguments[key], str):
            arguments[key] = SanitizerInput.sanitize_text(arguments[key])
            if not SanitizerInput.validate_length(arguments[key], max_len):
                raise ValueError(
                    f"Argument '{key}' exceeds max length ({max_len} chars) for tool '{tool_name}'"
                )

    return arguments
