# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from typing import Any

from src import __version__


try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server

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
            assert current_hash == self.verified_hashes[tool_name], (
                f"Rug pull detected: {tool_name}"
            )
        else:
            self.verified_hashes[tool_name] = current_hash

    def _list_tools(self) -> list[dict[str, Any]]:
        tools = []
        for tool_name, tool_func in self._tools.items():
            self._verify_tool_hash(tool_name)
            tools.append(
                {
                    "name": tool_name,
                    "description": tool_func.__doc__ or "",
                    "inputSchema": getattr(
                        tool_func,
                        "schema",
                        {"type": "object", "properties": {}},
                    ),
                }
            )
        return tools

    async def _call_tool(self, request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name")
        if not isinstance(tool_name, str) or tool_name not in self._tools:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }

        tool_args = params.get("arguments", {})
        if not isinstance(tool_args, dict):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": "Tool arguments must be an object"},
            }

        self._verify_tool_hash(tool_name)
        tool = self._tools[tool_name]
        schema = getattr(tool, "schema", {})
        if schema:
            properties = schema.get("properties", {})
            extra_keys = set(tool_args) - set(properties)
            if extra_keys and not schema.get("additionalProperties", True):
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Extra arguments not allowed: {sorted(extra_keys)}",
                    },
                }

        try:
            tool_args = validate_tool_input(tool_name, dict(tool_args))
        except ValueError as exc:
            _mcp_logger.warning(
                "Input validation failed for tool '%s': %s",
                redact_credentials(tool_name),
                redact_credentials(str(exc)),
            )
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": f"Invalid input: {exc}"},
            }

        try:
            result = await asyncio.wait_for(
                tool(**tool_args),
                timeout=tool_timeout_seconds(tool_name),
            )
        except TimeoutError:
            timeout_s = tool_timeout_seconds(tool_name)
            result = {
                "status": "error",
                "code": "TIMEOUT",
                "errors": [f"Tool execution timed out after {int(timeout_s)} seconds"],
                "tool": tool_name,
                "hint": "For long pipelines use blast CLI directly or retry with a narrower query.",
            }
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            result = {"status": "error", "errors": [str(exc)]}

        if isinstance(result, str):
            result = redact_credentials(result)
        elif isinstance(result, dict):
            result = {
                key: redact_credentials(str(value)) if isinstance(value, str) else value
                for key, value in result.items()
            }

        is_error = isinstance(result, dict) and result.get("status") == "error"
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, default=str),
                    }
                ],
                "structuredContent": result,
                "isError": is_error,
            },
        }

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Handle one MCP JSON-RPC message and return a response when required."""
        request_id = request.get("id")
        method = request.get("method")

        if request.get("jsonrpc") != "2.0" or not isinstance(method, str):
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32600, "message": "Invalid Request"},
            }
        if method == "initialize":
            requested = request.get("params", {}).get("protocolVersion")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": requested or "2025-03-26",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": self.name, "version": __version__},
                },
            }
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": self._list_tools()},
            }
        if method == "tools/call":
            params = request.get("params", {})
            if not isinstance(params, dict):
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "Params must be an object"},
                }
            return await self._call_tool(request_id, params)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    async def run_stdio_fallback(self) -> None:
        """Read newline-delimited MCP JSON-RPC requests from stdin."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError("Request must be an object")
                response = await self.handle_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError as exc:
                error_response = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": f"Parse error: {exc}"},
                    }
                )
                sys.stdout.write(error_response + "\n")
                sys.stdout.flush()
            except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
                error_response = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32600, "message": f"Invalid Request: {exc}"},
                    }
                )
                sys.stdout.write(error_response + "\n")
                sys.stdout.flush()


import logging

from src.security.credential_guard import redact_credentials
from src.security.prompt_sanitizer import MAX_FLASH_CHARS, MAX_PIPELINE_CHARS, SanitizerInput


_mcp_logger = logging.getLogger("c4reqber.mcp_server")

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
    "c4_codegen": 180.0,
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
    "c4_codegen": ["specification"],
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
