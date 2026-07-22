"""C4REQBER Model Context Protocol server for AI agents."""

from __future__ import annotations

import asyncio
import logging
import sys
from functools import wraps
from types import ModuleType
from typing import Any

from src.config.paths import apply_config_to_env, load_kilo_env, load_verifiers_env


load_kilo_env()
load_verifiers_env()
try:
    apply_config_to_env()
except Exception as exc:
    logging.getLogger(__name__).debug("apply_config_to_env at MCP import: %s", exc)

from src.mcp_server import (  # noqa: E402
    tools_analysis,
    tools_blast,
    tools_discovery,
    tools_factory,
    tools_prove,
    tools_research,
    tools_verify,
)
from src.mcp_server.fallback_protocol import _FallbackServer  # noqa: E402
from src.mcp_server.tool_dependencies import (  # noqa: E402
    HAS_TOOLS,
    AgdaBridge,
    C4Space,
    C4State,
    CoqClient,
    DafnyClient,
    DoCalculus,
    ExportManager,
    Lean4Client,
    MultiSourceSearcher,
    NewtonBridge,
    VerificationCalibrator,
    VerificationContext,
    run_bma,
    run_mcmc,
    triz_search,
)
from src.mcp_server.tool_schemas import INPUT_SCHEMAS  # noqa: E402


logger = logging.getLogger(__name__)

try:
    from mcp.server import Server as MCPSDKServer
    from mcp.server.stdio import stdio_server

    HAS_MCP = True
    Server = MCPSDKServer
except ImportError:
    HAS_MCP = False
    Server = None
    stdio_server = None
    print("⚠️  MCP SDK not installed. Run: pip install mcp", file=sys.stderr)

if HAS_MCP and not hasattr(Server, "tool"):
    HAS_MCP = False

_server: Any = Server("c4reqber") if HAS_MCP and Server else _FallbackServer("c4reqber")
server: Any = _server

# c4_codegen owns its historical decorator registration and imports this facade.
try:
    from src.codegen.mcp_tool import c4_codegen
except ImportError as exc:
    logger.warning("c4_codegen not available: %s", exc)

_COMPAT_DEPENDENCIES = (
    "AgdaBridge",
    "C4Space",
    "C4State",
    "CoqClient",
    "DafnyClient",
    "DoCalculus",
    "ExportManager",
    "HAS_TOOLS",
    "Lean4Client",
    "MultiSourceSearcher",
    "NewtonBridge",
    "VerificationCalibrator",
    "VerificationContext",
    "run_bma",
    "run_mcmc",
    "triz_search",
)


async def _invoke(module: ModuleType, name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Invoke a split implementation while preserving facade monkeypatch seams."""
    current = globals()
    for dependency in _COMPAT_DEPENDENCIES:
        setattr(module, dependency, current[dependency])
    return await getattr(module, name)(*args, **kwargs)


@server.tool("c4_solve")
@wraps(tools_discovery.c4_solve)
async def c4_solve(problem: str, domain: str = "science") -> dict[str, Any]:
    return await _invoke(tools_discovery, "c4_solve", problem, domain)


@server.tool("c4_search")
@wraps(tools_discovery.c4_search)
async def c4_search(query: str, sources: list[str] | None = None) -> dict[str, Any]:
    return await _invoke(tools_discovery, "c4_search", query, sources)


@server.tool("c4_triz")
@wraps(tools_discovery.c4_triz)
async def c4_triz(
    improving: int = 1, worsening: int = 2, mode: str = "matrix", problem: str = ""
) -> dict[str, Any]:
    return await _invoke(tools_discovery, "c4_triz", improving, worsening, mode, problem)


@server.tool("c4_fingerprint")
@wraps(tools_discovery.c4_fingerprint)
async def c4_fingerprint(problem: str) -> dict[str, Any]:
    return await _invoke(tools_discovery, "c4_fingerprint", problem)


@server.tool("c4_verify")
@wraps(tools_verify.c4_verify)
async def c4_verify(code: str, language: str | None = None) -> dict[str, Any]:
    return await _invoke(tools_verify, "c4_verify", code, language)


@server.tool("c4_prove")
@wraps(tools_prove.c4_prove)
async def c4_prove(hypothesis: str, language: str = "lean4") -> dict[str, Any]:
    return await _invoke(tools_prove, "c4_prove", hypothesis, language)


@server.tool("c4_transfer")
@wraps(tools_analysis.c4_transfer)
async def c4_transfer(problem: str, source_domain: str, target_domain: str) -> dict[str, Any]:
    return await _invoke(tools_analysis, "c4_transfer", problem, source_domain, target_domain)


@server.tool("c4_simulate")
@wraps(tools_analysis.c4_simulate)
async def c4_simulate(pattern_id: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    return await _invoke(tools_analysis, "c4_simulate", pattern_id, hypothesis)


@server.tool("c4_bayesian")
@wraps(tools_analysis.c4_bayesian)
async def c4_bayesian(
    models: list[dict[str, Any]] | dict[str, float], samples: int = 1000
) -> dict[str, Any]:
    return await _invoke(tools_analysis, "c4_bayesian", models, samples)


@server.tool("c4_causal")
@wraps(tools_analysis.c4_causal)
async def c4_causal(nodes: list[dict[str, Any]], treatment: str, outcome: str) -> dict[str, Any]:
    return await _invoke(tools_analysis, "c4_causal", nodes, treatment, outcome)


@server.tool("c4_export")
@wraps(tools_analysis.c4_export)
async def c4_export(discovery: dict[str, Any], format: str = "markdown") -> dict[str, Any]:
    return await _invoke(tools_analysis, "c4_export", discovery, format)


@server.tool("c4_autoresearch")
@wraps(tools_research.c4_autoresearch)
async def c4_autoresearch(
    file: str, metric: str = "val_bpb", max_iter: int = 100
) -> dict[str, Any]:
    return await _invoke(tools_research, "c4_autoresearch", file, metric, max_iter)


@server.tool("c4_chain")
@wraps(tools_research.c4_chain)
async def c4_chain(
    problem: str, from_state: list[int] | None = None, to_state: list[int] | None = None
) -> dict[str, Any]:
    return await _invoke(tools_research, "c4_chain", problem, from_state, to_state)


@server.tool("c4_meta")
@wraps(tools_research.c4_meta)
async def c4_meta(reasoning_trace: str, depth: int = 2) -> dict[str, Any]:
    return await _invoke(tools_research, "c4_meta", reasoning_trace, depth)


@server.tool("c4_social")
@wraps(tools_research.c4_social)
async def c4_social(action: str, draft_id: str = "", platform: str = "") -> dict[str, Any]:
    return await _invoke(tools_research, "c4_social", action, draft_id, platform)


@server.tool("blast_solve")
@wraps(tools_blast.blast_solve)
async def blast_solve(
    problem: str, output_format: str = "auto", domain: str | None = None
) -> dict[str, Any]:
    return await _invoke(tools_blast, "blast_solve", problem, output_format, domain)


@server.tool("blast_turbo")
@wraps(tools_blast.blast_turbo)
async def blast_turbo(
    topic: str, verify_backend: str = "hybrid", functors: bool = True
) -> dict[str, Any]:
    return await _invoke(tools_blast, "blast_turbo", topic, verify_backend, functors)


@server.tool("blast_flash")
@wraps(tools_blast.blast_flash)
async def blast_flash(
    question: str, with_sources: bool = False, deep: bool = False
) -> dict[str, Any]:
    return await _invoke(tools_blast, "blast_flash", question, with_sources, deep)


@server.tool("blast_turbofactory")
@wraps(tools_factory.blast_turbofactory)
async def blast_turbofactory(
    domain: str, scale: str = "standard", max_concurrent: int = 5, pipeline_mode: str = "mixed"
) -> dict[str, Any]:
    return await _invoke(
        tools_factory, "blast_turbofactory", domain, scale, max_concurrent, pipeline_mode
    )


@server.tool("blast_auto")
@wraps(tools_factory.blast_auto)
async def blast_auto(query: str) -> dict[str, Any]:
    return await _invoke(tools_factory, "blast_auto", query)


for _tool_name, _schema in INPUT_SCHEMAS.items():
    _tool = globals().get(_tool_name)
    if callable(_tool):
        _tool.schema = _schema


async def main() -> None:
    if HAS_MCP and stdio_server:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    elif hasattr(server, "run_stdio_fallback"):
        await server.run_stdio_fallback()
    else:
        logger.error(
            "Cannot start MCP server — neither MCP SDK run() nor "
            "run_stdio_fallback() available. Install: pip install mcp"
        )
        sys.exit(1)


__all__ = [
    "server",
    "HAS_TOOLS",
    "HAS_MCP",
    "main",
]


if __name__ == "__main__":
    asyncio.run(main())
