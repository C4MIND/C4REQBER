"""Agent Daemon — MCP server that exposes AgentCore as tools for external AI agents."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from src import __version__
from src.agent.core import AgentCore


def create_agent_server() -> Any:
    """Create an MCP server exposing AgentCore capabilities.

    Returns an MCP server instance that can be run via stdio.
    """
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.types import CallToolResult, TextContent, Tool

    agent = AgentCore()
    server = Server("c4reqber-agent")

    tool_defs: list[Tool] = [
        Tool(
            name="c4_agent_query",
            description="Send a query to the c4reqber agent. The agent will use its skills (C4, TRIZ, Pipeline, etc.) to respond.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Your question or task for the agent",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="c4_agent_spawn",
            description="Spawn a sub-agent for a background task. Returns sub-agent name for polling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task description for the sub-agent",
                    }
                },
                "required": ["task"],
            },
        ),
        Tool(
            name="c4_agent_poll",
            description="Poll a sub-agent for results by name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Sub-agent name returned by c4_agent_spawn",
                    }
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="c4_agent_solve",
            description="Run a full solve pipeline on a problem.",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem": {
                        "type": "string",
                        "description": "Problem statement to solve",
                    }
                },
                "required": ["problem"],
            },
        ),
        Tool(
            name="c4_agent_turbo",
            description="Run deep research on a topic (28 knowledge sources, paradigm detection).",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Research topic",
                    }
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="c4_agent_soul",
            description="Show the agent's persona (identity, values, communication style).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="c4_agent_skills",
            description="List all available c4reqber skills the agent can use.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

    async def handle_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
        try:
            if name == "c4_agent_query":
                result = agent.process(arguments["query"])
                return CallToolResult(content=[TextContent(type="text", text=result.content)])
            elif name == "c4_agent_spawn":
                sub_name = agent.spawn_sub_agent(arguments["task"])
                return CallToolResult(content=[TextContent(type="text", text=f"Sub-agent spawned: {sub_name}")])
            elif name == "c4_agent_poll":
                status = agent.poll_sub_agent(arguments["name"])
                return CallToolResult(content=[TextContent(type="text", text=status)])
            elif name == "c4_agent_solve":
                import io

                from src.cli.blast_core import cmd_solve
                out = io.StringIO()
                sys.stdout = out
                try:
                    cmd_solve(problem=arguments["problem"], mode="autopilot", output_format="auto", domain=None, output=None, verbose=False)
                finally:
                    sys.stdout = sys.__stdout__
                return CallToolResult(content=[TextContent(type="text", text=out.getvalue()[:5000])])
            elif name == "c4_agent_turbo":
                import io

                from src.cli.blast_core import cmd_turbo
                out = io.StringIO()
                sys.stdout = out
                try:
                    cmd_turbo(topic=arguments["topic"], output=None, verify_backend="hybrid", functors=True, plugins=None, verbose=False, competing=2, no_iterative=False)
                finally:
                    sys.stdout = sys.__stdout__
                return CallToolResult(content=[TextContent(type="text", text=out.getvalue()[:5000])])
            elif name == "c4_agent_soul":
                from src.agents.soul import Soul
                soul = Soul()
                return CallToolResult(content=[TextContent(type="text", text=soul.to_markdown())])
            elif name == "c4_agent_skills":
                return CallToolResult(content=[TextContent(type="text", text=agent.skills.describe())])
            else:
                return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")])

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return tool_defs

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
        return await handle_tool(name, arguments)

    return server


def run_daemon_stdio() -> None:
    """Run the agent daemon via stdio (for `blast agent --daemon`)."""
    from mcp.server import NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server

    server = create_agent_server()

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="c4reqber-agent",
                    server_version=__version__,
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    asyncio.run(_run())


if __name__ == "__main__":
    run_daemon_stdio()
