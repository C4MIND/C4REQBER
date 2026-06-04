"""
C4REQBER: LLM-powered MP Profile Generator
Dynamic generation of Multi-Perspective profiles tailored to a specific problem.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from src.c4.state import C4State
from src.llm.multi_provider import LLMProvider, ProviderConfig, ProviderRouter
from src.metamodels.mp.profiles import AgentPerspective


_logger = logging.getLogger("c4_cdi_turbo.pipeline")


_SYSTEM_PROMPT = (
    "You are an expert cognitive profiler. Given a problem and a C4 cognitive state, "
    "generate N distinct analytical perspectives (MP profiles) that would be most "
    "valuable for solving this specific problem. Each perspective should represent "
    "a fundamentally different cognitive style."
    "\n\n"
    "Respond ONLY with a valid JSON array. Each object must have:\n"
    '- "profile_name": str — unique identifier (e.g., "Systems Architect")\n'
    '- "cognitive_style": str — 1-2 sentence description of how this perspective thinks\n'
    '- "key_insights": list[str] — 3 specific insights this perspective would generate\n'
    '- "blind_spots": list[str] — 2 blind spots this perspective typically has\n'
    '- "c4_bias": object with optional "T", "S", "A" keys (int 0-2) — C4 state adjustments'
)


@dataclass
class DynamicProfile:
    """A dynamically generated MP profile from LLM."""

    profile_name: str
    cognitive_style: str
    key_insights: list[str] = field(default_factory=list)
    blind_spots: list[str] = field(default_factory=list)
    c4_bias: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DynamicProfile:
        return cls(
            profile_name=data.get("profile_name", "Unknown"),
            cognitive_style=data.get("cognitive_style", ""),
            key_insights=data.get("key_insights", []),
            blind_spots=data.get("blind_spots", []),
            c4_bias=data.get("c4_bias", {}),
        )

    def to_agent_perspective(
        self, agent_id: str, base_c4_state: C4State
    ) -> AgentPerspective:
        """Convert dynamic profile to AgentPerspective with C4 bias applied."""
        bias = self.c4_bias
        adjusted = C4State(
            T=bias.get("T", base_c4_state.T),
            S=bias.get("S", base_c4_state.S),
            A=bias.get("A", base_c4_state.A),
        )
        return AgentPerspective(
            agent_id=agent_id,
            profile_name=self.profile_name,
            profile_name_ru=self.profile_name,
            c4_state=adjusted,
            analysis=(
                f"{self.cognitive_style}\n\n"
                f"Problem analysis from {self.profile_name} perspective."
            ),
            confidence=0.75,
            key_insights=self.key_insights,
            blind_spots=self.blind_spots,
            duration_ms=0.0,
        )


class MPLLMDynamicGenerator:
    """
    LLM-powered generator for dynamic MP profiles.

    Generates problem-specific analytical perspectives instead of relying
    on hardcoded profiles from MPLibrary.
    """

    def __init__(
        self,
        provider_router: ProviderRouter | None = None,
    ) -> None:
        self.provider_router = provider_router
        self._logger = _logger

    def _build_prompt(self, problem: str, c4_state: C4State, n: int) -> str:
        return (
            f"Problem: {problem}\n\n"
            f"C4 Cognitive State: {c4_state} "
            f"(Time={c4_state.time_label}, "
            f"Scale={c4_state.scale_label}, "
            f"Agency={c4_state.agency_label})\n\n"
            f"Generate exactly {n} diverse analytical perspectives for this problem. "
            f"Return ONLY a JSON array."
        )

    def _parse_json_response(self, content: str) -> list[DynamicProfile]:
        """Parse LLM response, extracting JSON from markdown fences if needed."""
        raw = content.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._logger.warning("MP LLM response is not valid JSON: %s", exc)
            raise

        if not isinstance(data, list):
            self._logger.warning("MP LLM response is not a JSON array: %s", type(data))
            raise ValueError("Expected JSON array of profiles")

        profiles: list[DynamicProfile] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                profiles.append(DynamicProfile.from_dict(item))
            except Exception as exc:
                self._logger.warning("Failed to parse dynamic profile: %s", exc)
                continue

        return profiles

    async def generate_dynamic_profiles(
        self,
        problem: str,
        c4_state: C4State,
        n: int = 3,
    ) -> list[AgentPerspective]:
        """Generate N dynamic MP profiles via LLM and convert to AgentPerspectives."""
        prompt = self._build_prompt(problem, c4_state, n)

        try:
            if self.provider_router is not None:
                response = await self.provider_router.generate(
                    stage_name="mp_rotation",
                    prompt=prompt,
                    system_prompt=_SYSTEM_PROMPT,
                )
                content = getattr(response, "content", str(response))
            else:
                raise RuntimeError("No LLM client available for dynamic MP generation")

            dynamic_profiles = self._parse_json_response(content)
            if len(dynamic_profiles) < n:
                self._logger.info(
                    "LLM returned %d/%d profiles; using what we got",
                    len(dynamic_profiles),
                    n,
                )

            perspectives: list[AgentPerspective] = []
            for i, profile in enumerate(dynamic_profiles):
                perspective = profile.to_agent_perspective(
                    agent_id=f"agent_{i + 1}",
                    base_c4_state=c4_state,
                )
                perspectives.append(perspective)

            self._logger.info(
                "Generated %d dynamic MP profiles for problem: %s...",
                len(perspectives),
                problem[:50],
            )
            return perspectives

        except Exception as exc:
            self._logger.error("Dynamic MP generation failed: %s", exc)
            raise


async def generate_dynamic_profiles(
    problem: str,
    c4_state: C4State,
    n: int = 3,
    provider_router: ProviderRouter | None = None,
) -> list[AgentPerspective]:
    """Convenience standalone function."""
    generator = MPLLMDynamicGenerator(provider_router=provider_router)
    return await generator.generate_dynamic_profiles(problem, c4_state, n)
