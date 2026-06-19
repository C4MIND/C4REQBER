"""
C4 Archetype Agents API Router
27 cognitive state agents for universal problem solving
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from src.archetypes.data import C4Archetype, get_all_archetypes, get_archetype
from src.archetypes.engine import (
    build_agent_prompt,
    build_council_prompt,
    build_synergy_matrix,
    get_neighbors,
    get_optimal_team,
    get_synergy_coefficient,
    select_agents_for_task,
)
from src.llm.multi_provider import OpenRouterClient as AsyncLLMClient


router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Simple in-memory rate limiter for unauthenticated endpoints
_devil_requests: defaultdict[str, list[float]] = defaultdict(list)


def _check_devil_rate_limit(request: Request) -> bool:
    """Check rate limit for Devil's Advocate (10 requests per minute per IP).
    Uses the LAST IP from X-Forwarded-For (closest proxy) to prevent spoofing.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[-1].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"
    now = time.time()
    window = 60  # 1 minute
    limit = 10

    _devil_requests[client_ip] = [
        t for t in _devil_requests[client_ip] if now - t < window
    ]
    if len(_devil_requests[client_ip]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: 10 requests per minute",
        )
    _devil_requests[client_ip].append(now)
    return True


# ═══════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════


class ArchetypeResponse(BaseModel):
    """ArchetypeResponse."""
    code: str
    time: str
    scale: str
    agency: str
    name_en: str
    name_ru: str
    description: str
    metaphor: str
    strengths: list[str]
    color: str


class TeamRequest(BaseModel):
    """TeamRequest."""
    task_codes: list[str]
    team_size: int = 3
    diversity_boost: bool = True


class TeamResponse(BaseModel):
    """TeamResponse."""
    agents: list[ArchetypeResponse]
    synergy_matrix: dict[str, Any]


class CouncilRequest(BaseModel):
    """CouncilRequest."""
    problem: str
    agent_codes: list[str]
    language: str = "en"


class CouncilResponse(BaseModel):
    """CouncilResponse."""
    prompt: str
    agents: list[ArchetypeResponse]


class TaskAgentsRequest(BaseModel):
    """TaskAgentsRequest."""
    problem: str
    num_agents: int = 3


class DevilAdvocateRequest(BaseModel):
    """DevilAdvocateRequest."""
    hypothesis: str
    agent_code: str = "666"
    depth: int = 3


class DevilAdvocateResponse(BaseModel):
    """DevilAdvocateResponse."""
    critique: str
    weaknesses: list[str]
    counterarguments: list[str]
    confidence_reduction: float
    agent_code: str


# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


def _to_response(state: C4Archetype) -> ArchetypeResponse:
    """Convert C4Archetype to response model."""
    return ArchetypeResponse(
        code=state.code,
        time=state.time,
        scale=state.scale,
        agency=state.agency,
        name_en=state.name_en,
        name_ru=state.name_ru,
        description=state.description,
        metaphor=state.metaphor,
        strengths=state.strengths,
        color=state.color,
    )


@router.get("/", response_model=list[ArchetypeResponse])
async def list_archetypes(
    time: str | None = Query(
        None, description="Filter by time: Past/Present/Future"
    ),
    scale: str | None = Query(
        None, description="Filter by scale: Concrete/Abstract/Meta"
    ),
    agency: str | None = Query(
        None, description="Filter by agency: Self/Other/System"
    ),
) -> Any:
    """Get all 27 C4 archetypes with optional filtering."""
    agents = get_all_archetypes()

    if time:
        agents = [a for a in agents if a.time.lower() == time.lower()]
    if scale:
        agents = [a for a in agents if a.scale.lower() == scale.lower()]
    if agency:
        agents = [a for a in agents if a.agency.lower() == agency.lower()]

    return [_to_response(a) for a in agents]


@router.get("/{code}", response_model=ArchetypeResponse)
async def get_archetype_by_code(code: str) -> Any:
    """Get specific archetype by C4 code (e.g., 111)."""
    agent = get_archetype(code)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Archetype {code} not found")
    return _to_response(agent)


@router.get("/{code1}/synergy/{code2}")
async def get_agent_synergy(code1: str, code2: str) -> Any:
    """Get synergy coefficient between two agents (0-1)."""
    all_codes = {a.code for a in get_all_archetypes()}
    if code1 not in all_codes or code2 not in all_codes:
        raise HTTPException(status_code=404, detail="Invalid agent code")
    return {
        "agent1": code1,
        "agent2": code2,
        "synergy": get_synergy_coefficient(code1, code2),
    }


@router.get("/synergy/matrix")
async def get_synergy_matrix() -> Any:
    """Get full 27x27 synergy matrix."""
    return build_synergy_matrix()


@router.get("/{code}/neighbors")
async def get_agent_neighbors(code: str, distance: int = 1) -> Any:
    """Get neighboring archetypes within Hamming distance."""
    agent = get_archetype(code)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Archetype {code} not found")

    neighbors = get_neighbors(code, distance)
    return {
        "agent": _to_response(agent),
        "neighbors": [_to_response(n) for n in neighbors],
        "distance": distance,
    }


@router.post("/team", response_model=TeamResponse)
async def build_team(request: TeamRequest) -> Any:
    """Build optimal agent team for a task."""
    team = get_optimal_team(
        task_codes=request.task_codes,
        team_size=request.team_size,
        diversity_boost=request.diversity_boost,
    )

    # Build synergy matrix for the team
    team_codes = [a.code for a in team]
    synergy: Any = {}
    for c1 in team_codes:
        synergy[c1] = {}
        for c2 in team_codes:
            synergy[c1][c2] = get_synergy_coefficient(c1, c2)

    return TeamResponse(
        agents=[_to_response(a) for a in team],
        synergy_matrix=synergy,
    )


@router.post("/select", response_model=list[ArchetypeResponse])
async def select_agents(request: TaskAgentsRequest) -> Any:
    """Select agents based on problem characteristics."""
    agents = select_agents_for_task(
        problem=request.problem, num_agents=request.num_agents
    )
    return [_to_response(a) for a in agents]


@router.post("/council", response_model=CouncilResponse)
async def create_council(request: CouncilRequest) -> Any:
    """Create a council prompt for multi-agent analysis."""
    # Validate agent codes
    for code in request.agent_codes:
        if not get_archetype(code):
            raise HTTPException(status_code=404, detail=f"Archetype {code} not found")

    agents = [get_archetype(code) for code in request.agent_codes]
    prompt = build_council_prompt(
        problem=request.problem,
        agent_codes=request.agent_codes,
        language=request.language,
    )

    return CouncilResponse(
        prompt=prompt,
        agents=[_to_response(a) for a in agents],  # type: ignore[arg-type]
    )


@router.post("/{code}/prompt")
async def get_agent_prompt(code: str, problem: str, language: str = "en") -> Any:
    """Get LLM prompt for a specific archetype agent."""
    agent = get_archetype(code)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Archetype {code} not found")

    prompt = build_agent_prompt(code=code, problem=problem, language=language)
    return {
        "agent": _to_response(agent),
        "prompt": prompt,
        "language": language,
    }


@router.post("/devil", response_model=DevilAdvocateResponse)
async def devil_advocate(
    request: DevilAdvocateRequest,
    http_request: Request,
    _rate_limit: bool = Depends(_check_devil_rate_limit),
) -> None:
    """Devil's Advocate: critique a hypothesis using LLM."""
    hypothesis = request.hypothesis
    depth = max(1, min(request.depth, 5))

    # Try real LLM first
    client = AsyncLLMClient()
    try:
        system_prompt = (
            "You are a world-class scientific skeptic and devil's advocate. "
            "Analyze the given hypothesis critically. Identify specific weaknesses, "
            "provide counterarguments, and estimate confidence reduction. "
            "Respond in valid JSON with keys: critique, weaknesses (list), counterarguments (list), confidence_reduction (float 0-1)."
        )
        user_prompt = f"Hypothesis: {hypothesis}\nDepth: {depth} critiques required."

        response = await client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
            response_format="json",
        )

        data = json.loads(response.content)
        return DevilAdvocateResponse(  # type: ignore[return-value]
            critique=data.get("critique", ""),
            weaknesses=data.get("weaknesses", []),
            counterarguments=data.get("counterarguments", []),
            confidence_reduction=float(data.get("confidence_reduction", 0.25)),
            agent_code=request.agent_code,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM unavailable: {e}") from e
    finally:
        await client.close()
