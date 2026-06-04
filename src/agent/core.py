"""AgentCore — LLM-powered cognitive agent for c4reqber."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.markdown import Markdown

from src import __version__
from src.agent.config import AGENT_CONFIG_DIR, AgentConfig, MCPServerConfig
from src.agent.skills import SkillRegistry, ToolCall


@dataclass
class Message:
    role: str  # system, user, assistant, tool
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


@dataclass
class AgentResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    sub_agents: list[str] = field(default_factory=list)
    duration_sec: float = 0.0


class AgentCore:
    """Main c4reqber agent — LLM-powered, skill-based, MCP-connected, memory-backed.

    Usage::

        agent = AgentCore()
        response = agent.process("Solve problem X")

        # Interactive:
        agent.repl()
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config = (
            AgentConfig.load()
            if config_path is None
            else AgentConfig._from_dict(json.loads(Path(config_path).read_text()))
        )
        self.skills = SkillRegistry()
        self.history: list[Message] = []
        self._mcp_processes: dict[str, subprocess.Popen] = {}
        self._mcp_tools: list[dict[str, Any]] = []

        # Sub-agent manager (lazy init)
        self._sub_agent_mgr = None

        # Load persistent history
        self._load_history()

        # Auto-start configured MCP servers
        self._start_mcp_servers()

        # Discover external MCP servers via FastMCP
        self._fastmcp: Any | None = None
        self._discover_external_mcp()

    # ── Sub-Agent Manager ──────────────────────────────────────────────────

    @property
    def sub_agents(self):
        if self._sub_agent_mgr is None:
            from src.agent.sub_agent import SubAgentManager
            self._sub_agent_mgr = SubAgentManager()
        return self._sub_agent_mgr

    # ── Memory Persistence ─────────────────────────────────────────────────

    def _history_path(self) -> Path:
        return Path(self.config.history_path)

    def _load_history(self) -> None:
        path = self._history_path()
        if not path.exists():
            return
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    self.history.append(Message(**data))
            # Trim to max size from tail
            if len(self.history) > self.config.history_size:
                self.history = self.history[-self.config.history_size:]
        except Exception:
            pass

    _history_lock = None

    @classmethod
    def _get_history_lock(cls):
        if cls._history_lock is None:
            cls._history_lock = asyncio.Lock()
        return cls._history_lock

    def _append_history(self, msg: Message) -> None:
        self.history.append(msg)
        try:
            import asyncio
            lock = self._get_history_lock()
            path = self._history_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {"role": msg.role, "content": msg.content},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass

    # ── System Prompt ──────────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        soul_md = ""
        if self.config.soul.enabled:
            try:
                from src.agents.soul import Soul

                soul = Soul(path=Path(self.config.soul.path))
                soul_md = soul.to_markdown()
            except Exception:
                soul_md = "_Soul not loaded_"

        skills_desc = self.skills.describe()

        mcp_desc = ""
        if self._mcp_tools:
            mcp_desc = "\n## Connected MCP Tools\n" + "\n".join(
                f"- **{t.get('name', '?')}**: {t.get('description', '')}"
                for t in self._mcp_tools
            )

        return f"""You are c4reqber v{__version__} — a terminal-first cognitive exoskeleton.
You are an AI research and engineering assistant with deep access to the c4reqber system.

{soul_md}

## Available Skills
{skills_desc}

## Response Rules
- Be technical, concise, direct. NO flattery, NO padding.
- Use tools automatically when needed — do not ask "should I".
- When you spawn a sub-agent, the user sees the result, not the spawning.
- Cite sources when using knowledge tools.
- For research: prefer turbo pipeline (deep discovery).
- For quick answers: prefer flash mode.
- For complex problems: prefer solve pipeline.
- Always verify critical claims with verification tools.
- If a task needs parallelism, spawn sub-agents.{mcp_desc}

## Extra Instructions
{self.config.system_prompt_extra or "(none)"}
"""

    # ── MCP Bridge ─────────────────────────────────────────────────────────

    def _start_mcp_servers(self) -> None:
        for mcp_cfg in self.config.mcp_servers:
            if not mcp_cfg.enabled:
                continue
            if mcp_cfg.name in self._mcp_processes:
                continue
            try:
                proc = subprocess.Popen(
                    [mcp_cfg.command] + mcp_cfg.args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={**os.environ, **mcp_cfg.env} if mcp_cfg.env else None,
                )
                self._mcp_processes[mcp_cfg.name] = proc
            except Exception:
                pass

    def _discover_external_mcp(self) -> None:
        """Discover external MCP servers via FastMCP."""
        try:
            from src.mcp_server.fastmcp_bridge import FastMCPBridge
            self._fastmcp = FastMCPBridge()
        except Exception:
            pass

    def add_mcp_server(self, name: str, command: str, args: list[str] | None = None) -> str:
        cfg = MCPServerConfig(name=name, command=command, args=args or [])
        self.config.mcp_servers.append(cfg)
        self.config.save()
        self._start_mcp_servers()
        if cfg.name in self._mcp_processes:
            return f"Connected MCP: {name}"
        return f"Failed to connect MCP: {name}"

    def remove_mcp_server(self, name: str) -> str:
        self.config.mcp_servers = [s for s in self.config.mcp_servers if s.name != name]
        proc = self._mcp_processes.pop(name, None)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        self.config.save()
        return f"Removed MCP: {name}"

    def list_mcp_servers(self) -> list[dict[str, Any]]:
        result = []
        for cfg in self.config.mcp_servers:
            running = cfg.name in self._mcp_processes and self._mcp_processes[cfg.name].poll() is None
            result.append({
                "name": cfg.name,
                "command": f"{cfg.command} {' '.join(cfg.args)}",
                "enabled": cfg.enabled,
                "running": running,
            })
        return result

    # ── Skill Execution ────────────────────────────────────────────────────

    def _execute_tool(self, tool_call: ToolCall) -> str:
        try:
            result = self.skills.execute(tool_call)
            if isinstance(result, dict) or isinstance(result, list):
                return json.dumps(result, indent=2, ensure_ascii=False, default=str)
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    # ── LLM Bridge (Pydantic AI) ───────────────────────────────────────────

    def _call_llm(self, messages: list[dict[str, Any]]) -> str:
        """Call LLM via Pydantic AI.

        Builds conversation history manually from message dicts to
        avoid Pydantic AI ``message_history`` type mismatch.
        """
        provider = self.config.provider
        try:
            from pydantic_ai import Agent
            from pydantic_ai.models.openai import OpenAIModel

            model = OpenAIModel(
                model_name=provider.model,
                base_url=provider.api_base,
                api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            )

            # Build system prompt from first message
            system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
            pydantic_agent = Agent(model, system_prompt=system)

            chat = messages[1:] if messages and messages[0]["role"] == "system" else messages
            full_conversation = "\n".join(
                f"{msg['role']}: {msg.get('content', '')}" for msg in chat
                if msg.get("role") in ("user", "assistant")
            )
            result = pydantic_agent.run_sync(full_conversation)
            return result.data or ""
        except Exception as e:
            return f"LLM Error: {e}"

    # ── LangGraph Graph Executor ───────────────────────────────────────────

    def _process_langgraph(self, user_input: str, t0: float) -> AgentResponse:
        """Process query via LangGraph state graph with conditional edges.

        Graph: classify → {analyze→search, solve→pipeline, verify→prove} → merge
        """
        import operator
        from typing import Annotated, TypedDict

        from langgraph.graph import END, StateGraph

        class AgentState(TypedDict):
            messages: Annotated[list, operator.add]
            intent: str
            result: str

        builder = StateGraph(AgentState)

        def classify(state: AgentState):
            q = user_input.lower()
            if any(w in q for w in ("solve", "проблема", "discover", "find")):
                return {"intent": "solve", "messages": []}
            if any(w in q for w in ("verify", "провер", "prove", "теорема")):
                return {"intent": "verify", "messages": []}
            return {"intent": "analyze", "messages": []}

        def analyze(state: AgentState):
            msg = self._call_llm([{"role": "user", "content": f"Analyze: {user_input}"}])
            return {"result": msg, "messages": [{"role": "assistant", "content": msg}]}

        def knowledge_search(state: AgentState):
            msg = self._call_llm([{"role": "user", "content": f"Search knowledge for: {user_input}"}])
            return {"result": msg, "messages": [{"role": "assistant", "content": msg}]}

        def solve_pipeline(state: AgentState):
            msg = self._call_llm([{"role": "user", "content": f"Solve problem: {user_input}"}])
            return {"result": msg, "messages": [{"role": "assistant", "content": msg}]}

        def verify_formal(state: AgentState):
            msg = self._call_llm([{"role": "user", "content": f"Formally verify: {user_input}"}])
            return {"result": msg, "messages": [{"role": "assistant", "content": msg}]}

        def merge_result(state: AgentState):
            return state

        def route_after_classify(state: AgentState) -> str:
            intent = state.get("intent", "analyze")
            if intent == "solve":
                return "solve"
            if intent == "verify":
                return "verify"
            return "analyze"

        def route_after_analyze(state: AgentState) -> str:
            return "search" if len(user_input.split()) > 5 else "merge"

        builder.add_node("classify", classify)
        builder.add_node("analyze", analyze)
        builder.add_node("search", knowledge_search)
        builder.add_node("solve", solve_pipeline)
        builder.add_node("verify", verify_formal)
        builder.add_node("merge", merge_result)

        builder.set_entry_point("classify")
        builder.add_conditional_edges("classify", route_after_classify, {
            "analyze": "analyze",
            "solve": "solve",
            "verify": "verify",
        })
        builder.add_conditional_edges("analyze", route_after_analyze, {
            "search": "search",
            "merge": "merge",
        })
        builder.add_edge("search", "merge")
        builder.add_edge("solve", "merge")
        builder.add_edge("verify", "merge")
        builder.add_edge("merge", END)

        graph = builder.compile()
        result = graph.invoke({"messages": [], "intent": "", "result": ""})

        content = result.get("result", "")
        messages = result.get("messages", [])
        if not content and messages:
            last = messages[-1]
            content = last.get("content", "") if isinstance(last, dict) else str(last)

        tool_calls_data: list[Any] = []
        sub_agents_data: list[str] = []
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("type") == "tool":
                    tool_calls_data.append(msg.get("content", ""))
                if msg.get("role") == "sub_agent":
                    sub_agents_data.append(str(msg.get("content", ""))[:80])

        return AgentResponse(
            content=content or "Processing complete.",
            duration_sec=time.perf_counter() - t0,
            tool_calls=tool_calls_data,
            sub_agents=sub_agents_data,
        )

    # ── Message Processing ─────────────────────────────────────────────────

    def process(self, user_input: str) -> AgentResponse:
        start = time.perf_counter()

        # ── LangGraph graph-based execution (if available) ────────
        try:
            from src.integrations.scientific_bridges import LangGraphBridge
            if LangGraphBridge().available:
                return self._process_langgraph(user_input, start)
        except Exception:
            pass

        system_prompt = self._build_system_prompt()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *[
                {"role": m.role, "content": m.content}
                for m in self.history[-self.config.history_size :]
            ],
            {"role": "user", "content": user_input},
        ]

        response_text = self._call_llm(messages)

        tool_calls = self._detect_inline_tool_calls(response_text)
        tool_results: list[str] = []
        for tc in tool_calls:
            result = self._execute_tool(tc)
            tool_results.append(f"Tool '{tc.skill}.{tc.tool}' result: {result}")

        if tool_results:
            messages.append({"role": "assistant", "content": response_text})
            for tr in tool_results:
                messages.append({"role": "tool", "content": tr})
            response_text = self._call_llm(messages)

        self._append_history(Message(role="user", content=user_input))
        self._append_history(Message(role="assistant", content=response_text))

        self._append_history(Message(role="user", content=user_input))
        self._append_history(Message(role="assistant", content=response_text))

        duration = time.perf_counter() - start
        return AgentResponse(
            content=response_text,
            tool_calls=tool_calls,
            duration_sec=duration,
        )

    # ── Sub-Agent Spawning ─────────────────────────────────────────────────

    def spawn_sub_agent(self, task: str) -> str:
        name = self.sub_agents.spawn(task, self.config.provider.model)
        return name

    def poll_sub_agent(self, name: str) -> str:
        result = self.sub_agents.get(name)
        if result is None:
            return f"Unknown sub-agent: {name}"
        status_icon = {"running": "🔄", "completed": "✅", "failed": "❌"}.get(result.status, "❓")
        lines = [f"{status_icon} **{result.name}** — {result.status} ({result.duration_sec:.1f}s)"]
        if result.result:
            lines.append(result.result[:500])
        if result.error:
            lines.append(f"Error: {result.error}")
        return "\n".join(lines)

    def list_sub_agents(self) -> str:
        subs = self.sub_agents.list_all()
        if not subs:
            return "_No sub-agents spawned._"
        lines = []
        for s in subs:
            icon = {"running": "🔄", "completed": "✅", "failed": "❌"}.get(s.status, "❓")
            lines.append(f"- {icon} `{s.name}` — {s.status} ({s.duration_sec:.1f}s): {s.task[:60]}")
        return "\n".join(lines)

    # ── Tool Detection ─────────────────────────────────────────────────────

    def _detect_inline_tool_calls(self, text: str) -> list[ToolCall]:
        import re

        calls: list[ToolCall] = []
        pattern = r"`([a-z0-9_]+)\.([a-z0-9_]+)\(([^)]*)\)`"
        for match in re.finditer(pattern, text):
            calls.append(
                ToolCall(
                    skill=match.group(1),
                    tool=match.group(2),
                    args=self._parse_args(match.group(3)),
                )
            )
        return calls

    @staticmethod
    def _parse_args(args_str: str) -> dict[str, Any]:
        args: dict[str, Any] = {}
        if not args_str.strip():
            return args
        for part in args_str.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                args[k.strip()] = v.strip().strip("\"'")
            else:
                args[part.strip()] = True
        return args

    # ── REPL ───────────────────────────────────────────────────────────────

    def repl(self) -> None:
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt

        console = Console()

        soul_info = ""
        if self.config.soul.enabled:
            try:
                from src.agents.soul import Soul

                soul = Soul(path=Path(self.config.soul.path))
                soul_info = f" | {soul.get_identity().name}"
            except Exception:
                pass

        mcp_count = len(self.list_mcp_servers())

        console.print(
            Panel(
                f"[bold magenta]c4reqber Agent v{__version__}[/bold magenta]{soul_info}\n"
                f"[dim]Model: {self.config.provider.model} via {self.config.provider.id}[/dim]\n"
                f"[dim]Skills: {len(self.skills.skills)} built-in | MCP: {mcp_count} configured[/dim]\n"
                f"[dim]Memory: {len(self.history)} messages[/dim]\n"
                f"[dim]Type /help for commands, :q to quit[/dim]",
                title="🤖 c4reqber Agent",
                border_style="cyan",
            )
        )

        while True:
            try:
                line = Prompt.ask("[bold cyan]/[/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Shutting down agent...[/]")
                break

            if not line.strip():
                continue
            if line.strip() in (":q", "/exit"):
                console.print("[yellow]Agent session ended.[/]")
                break
            if line.startswith("/"):
                self._handle_slash_command(line[1:], console)
                continue

            with console.status("[cyan]Processing...[/]"):
                response = self.process(line)

            if response.sub_agents:
                for name in response.sub_agents:
                    console.print(f"[dim]→ Spawned sub-agent: {name}[/]")

            md = Markdown(response.content)
            console.print(md)
            if response.duration_sec > 0:
                console.print(f"[dim]({response.duration_sec:.1f}s)[/]")

    def _handle_slash_command(self, cmd: str, console) -> None:
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "help":
            console.print(
                Markdown(
                    """## Agent Commands
- `/help` — this help
- `/soul` — show agent persona
- `/skills` — list available skills
- `/mcp` — list connected MCP servers
- `/mcp add <name> <command> [args...]` — connect an MCP server
- `/mcp remove <name>` — disconnect an MCP server
- `/model` — show current model
- `/model set <provider>:<model>` — change model (e.g. /model set openrouter:gpt-4o)
- `/config` — show full agent config
- `/history` — show conversation history count
- `/clear` — clear history (memory stays on disk)
- `/subs` — list spawned sub-agents
- `/sub <name>` — poll a sub-agent result
- `/spawn <task>` — spawn a sub-agent
- `/solve <problem>` — solve a problem (via pipeline)
- `/turbo <topic>` — deep research
- `/flash <question>` — quick answer
- `/preprint <topic>` — generate preprint + save to drafts
- `/exit` or `:q` — quit
"""
                )
            )
            return

        # ── MCP management ─────────────────────────────────────────────────
        if command == "mcp":
            sub = cmd.strip().split(maxsplit=2)
            sub_cmd = sub[1].lower() if len(sub) > 1 else "list"
            sub_args = sub[2] if len(sub) > 2 else ""

            if sub_cmd == "list":
                servers = self.list_mcp_servers()
                if not servers:
                    console.print("[dim]No MCP servers configured.[/]")
                    console.print("[dim]Use `/mcp add <name> <command> [args...]` to connect[/]")
                    return
                for s in servers:
                    status = "[green]● running[/]" if s["running"] else "[red]● stopped[/]"
                    enabled = "[green]on[/]" if s["enabled"] else "[red]off[/]"
                    console.print(f"  {status} **{s['name']}** `{s['command']}` {enabled}")

            elif sub_cmd == "add":
                rest = sub_args.strip()
                if not rest:
                    console.print("[red]Usage: /mcp add <name> <command> [args...][/]")
                    return
                name_end = rest.find(" ")
                if name_end == -1:
                    console.print("[red]Usage: /mcp add <name> <command> [args...][/]")
                    return
                mcp_name = rest[:name_end]
                cmd_rest = rest[name_end + 1 :].strip()
                cmd_parts = cmd_rest.split()
                if not cmd_parts:
                    console.print("[red]Command required[/]")
                    return
                result = self.add_mcp_server(mcp_name, cmd_parts[0], cmd_parts[1:])
                console.print(f"[green]{result}[/]")

            elif sub_cmd == "remove":
                if not sub_args:
                    console.print("[red]Usage: /mcp remove <name>[/]")
                    return
                result = self.remove_mcp_server(sub_args)
                console.print(f"[yellow]{result}[/]")

            else:
                console.print(f"[red]Unknown MCP command: {sub_cmd}. Use list/add/remove[/]")
            return

        # ── Model management ───────────────────────────────────────────────
        if command == "model":
            sub = cmd.strip().split(maxsplit=2)
            sub_cmd = sub[1].lower() if len(sub) > 1 else "show"
            if sub_cmd == "show":
                console.print(
                    f"**Model:** {self.config.provider.model}\n"
                    f"**Provider:** {self.config.provider.id}\n"
                    f"**API:** {self.config.provider.api_base}"
                )
            elif sub_cmd == "set" and len(sub) > 2:
                model_val = sub[2]
                if ":" in model_val:
                    prov, mod = model_val.split(":", 1)
                    self.config.provider.id = prov
                    self.config.provider.model = mod
                else:
                    self.config.provider.model = model_val
                self.config.save()
                console.print(f"[green]Model set to {self.config.provider.model} via {self.config.provider.id}[/]")
            return

        # ── Pipeline commands ──────────────────────────────────────────────
        if command == "preprint":
            if not args:
                console.print("[yellow]Usage: /preprint <topic>[/]")
                return
            console.print(f"[cyan]Generating preprint via turbo pipeline: {args}...[/]")
            import asyncio

            async def _gen():
                import io
                import sys

                from src.cli.blast_core import cmd_turbo
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    cmd_turbo(topic=args, output=None, verify_backend="hybrid", functors=True,
                              plugins=None, verbose=False, competing=1, no_iterative=False)
                finally:
                    sys.stdout = old_stdout
                from pathlib import Path
                drafts_dir = Path.home() / ".c4reqber" / "drafts"
                if drafts_dir.exists():
                    recent = sorted([d for d in drafts_dir.iterdir() if d.is_dir()],
                                    key=lambda d: d.stat().st_mtime, reverse=True)[:1]
                    if recent:
                        console.print(f"[green]Preprint ready: {recent[0].name}[/]")
                        console.print("[dim]Review: /review[/]")
                        return
                console.print("[yellow]Pipeline completed. Check drafts.[/]")
            asyncio.run(_gen())
            return

        if command in ("solve", "turbo", "flash"):
            if not args:
                console.print(f"[yellow]Usage: /{command} <query>[/]")
                return
            console.print(f"[cyan]Running /{command}...[/]")
            self._call_pipeline(command, args, console)
            return

        # ── Sub-agent commands ─────────────────────────────────────────────
        if command == "subs":
            console.print(self.list_sub_agents())
            return

        if command == "sub":
            if not args:
                console.print("[yellow]Usage: /sub <name>[/]")
                return
            console.print(self.poll_sub_agent(args))
            return

        if command == "spawn":
            if not args:
                console.print("[yellow]Usage: /spawn <task>[/]")
                return
            name = self.spawn_sub_agent(args)
            console.print(f"[green]Spawned sub-agent: {name}[/]")
            return

        # ── Simple info commands ───────────────────────────────────────────
        info_map = {
            "soul": self._build_system_prompt().split("## Available Skills")[0],
            "skills": self.skills.describe(),
            "config": f"```json\n{json.dumps(self.config._to_dict(), indent=2, ensure_ascii=False)}\n```",
            "history": f"**History:** {len(self.history)} messages (max {self.config.history_size})",
        }

        if command == "clear":
            self.history.clear()
            console.print("[green]Session history cleared (disk memory preserved).[/]")
            return

        if command in info_map:
            result = info_map[command]
            if isinstance(result, str):
                console.print(
                    Markdown(result) if "## " in result or "**" in result or "```" in result else result
                )
            return

        console.print(f"[red]Unknown command: /{command}. Try /help[/]")

    def _call_pipeline(self, mode: str, args: str, console) -> None:
        """Run a pipeline mode and display output via Rich console."""
        import io
        import sys

        from rich.markdown import Markdown
        from rich.panel import Panel

        # Capture stdout from blast_core functions
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            if mode == "solve":
                from src.cli.blast_core import cmd_solve

                cmd_solve(
                    problem=args, mode="autopilot", output_format="auto",
                    domain=None, output=None, verbose=False,
                )
            elif mode == "turbo":
                from src.cli.blast_core import cmd_turbo

                cmd_turbo(
                    topic=args, output=None, verify_backend="hybrid", functors=True,
                    plugins=None, verbose=False, competing=2, no_iterative=False,
                )
            elif mode == "flash":
                from src.cli.blast_core import cmd_flash

                cmd_flash(question=args, with_sources=False, deep=False, format="concise")
        except Exception as e:
            sys.stdout = old_stdout
            console.print(f"[red]Pipeline error: {e}[/]")
            return

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        if output.strip():
            console.print(Panel(Markdown(output[:2000]), title=f"[bold]{mode}[/]", border_style="cyan"))
        else:
            console.print(f"[dim]{mode} pipeline completed (no text output)[/]")

    # ── Cleanup ────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        for _name, proc in self._mcp_processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
