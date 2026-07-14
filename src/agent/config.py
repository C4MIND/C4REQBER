"""Agent configuration — model, provider, MCP servers, soul."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.config.paths import CONFIG_DIR


AGENT_CONFIG_DIR = CONFIG_DIR
AGENT_CONFIG_PATH = CONFIG_DIR / "agent.json"
AGENT_HISTORY_PATH = CONFIG_DIR / "agent_history.jsonl"


@dataclass
class ProviderConfig:
    id: str = "openrouter"
    model: str = "claude-sonnet-4.6"
    temperature: float = 0.3
    max_tokens: int = 16384
    api_base: str = "https://openrouter.ai/api/v1"


@dataclass
class SoulConfig:
    path: str = str(AGENT_CONFIG_DIR / "soul.json")
    enabled: bool = True


@dataclass
class MCPServerConfig:
    name: str = ""
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class AgentConfig:
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    soul: SoulConfig = field(default_factory=SoulConfig)
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)
    history_path: str = str(AGENT_HISTORY_PATH)
    history_size: int = 50
    daemon_port: int = 8317
    skills: dict[str, bool] = field(default_factory=lambda: {
        "c4.engine": True,
        "c4.pipeline": True,
        "c4.triz": True,
        "c4.discovery": True,
        "c4.verification": True,
        "c4.knowledge": True,
        "c4.wasm": True,
        "c4.memory": True,
        "c4.export": True,
        "c4.security": True,
        "c4.soul": True,
    })
    system_prompt_extra: str = ""

    @classmethod
    def load(cls) -> AgentConfig:
        if AGENT_CONFIG_PATH.exists():
            data = json.loads(AGENT_CONFIG_PATH.read_text(encoding="utf-8"))
            return cls._from_dict(data)
        config = cls()
        config.save()
        return config

    def save(self) -> None:
        AGENT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        AGENT_CONFIG_PATH.write_text(
            json.dumps(self._to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _to_dict(self) -> dict[str, Any]:
        return {
            "provider": {
                "id": self.provider.id,
                "model": self.provider.model,
                "temperature": self.provider.temperature,
                "max_tokens": self.provider.max_tokens,
                "api_base": self.provider.api_base,
            },
            "soul": {"path": self.soul.path, "enabled": self.soul.enabled},
            "mcp_servers": [
                {"name": s.name, "command": s.command, "args": s.args, "env": s.env, "enabled": s.enabled}
                for s in self.mcp_servers
            ],
            "skills": self.skills,
            "system_prompt_extra": self.system_prompt_extra,
            "history_path": self.history_path,
            "history_size": self.history_size,
            "daemon_port": self.daemon_port,
        }

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> AgentConfig:
        p = data.get("provider", {})
        provider = ProviderConfig(
            id=p.get("id", "openrouter"),
            model=p.get("model", "claude-sonnet-4.6"),
            temperature=p.get("temperature", 0.3),
            max_tokens=p.get("max_tokens", 16384),
            api_base=p.get("api_base", "https://openrouter.ai/api/v1"),
        )
        soul = data.get("soul", {})
        soul_cfg = SoulConfig(
            path=soul.get("path", str(AGENT_CONFIG_DIR / "soul.json")),
            enabled=soul.get("enabled", True),
        )
        mcp_list = [
            MCPServerConfig(**s) for s in data.get("mcp_servers", [])
        ]
        skills = data.get("skills", {})
        return cls(
            provider=provider,
            soul=soul_cfg,
            mcp_servers=mcp_list,
            skills=skills,
            system_prompt_extra=data.get("system_prompt_extra", ""),
            history_path=data.get("history_path", str(AGENT_HISTORY_PATH)),
            history_size=data.get("history_size", 50),
            daemon_port=data.get("daemon_port", 8317),
        )
