"""
C4 Archetypes Engine — synergy, team building, prompt generation
"""
from __future__ import annotations

from typing import Any

from .data import ARCHETYPE_MAP, C4State, decode_code, get_all_archetypes
from src.c4.state import C4State as CanonicalC4State


# Agent affinity by cognitive dimension
_DIMENSION_AFFINITY = {
    "time": {("Past", "Present"): 0.3, ("Past", "Future"): 0.1, ("Present", "Future"): 0.3},
    "scale": {
        ("Concrete", "Abstract"): 0.4,
        ("Concrete", "Meta"): 0.1,
        ("Abstract", "Meta"): 0.3,
    },
    "agency": {("Self", "Other"): 0.3, ("Self", "System"): 0.1, ("Other", "System"): 0.4},
}


def _dimension_distance(v1: str, v2: str, dimension: str) -> float:
    """Compute affinity between two values of a dimension (0-1)."""
    if v1 == v2:
        return 1.0
    key = tuple(sorted([v1, v2]))
    return _DIMENSION_AFFINITY[dimension].get(key, 0.0)  # type: ignore[arg-type]


def get_synergy_coefficient(code1: str, code2: str) -> float:
    """
    Compute synergy between two C4 states (0-1).
    Higher = more complementary.
    """
    t1, d1, a1 = decode_code(code1)
    t2, d2, a2 = decode_code(code2)

    # Average affinity across three dimensions
    time_aff = _dimension_distance(t1, t2, "time")
    scale_aff = _dimension_distance(d1, d2, "scale")
    agency_aff = _dimension_distance(a1, a2, "agency")

    # Synergy is highest when agents are different but not opposite
    # Same = 1.0 (strong but redundant), Different = variable
    raw = (time_aff + scale_aff + agency_aff) / 3

    # Boost complementary pairs (different in 1-2 dimensions)
    differences = sum(
        [t1 != t2, d1 != d2, a1 != a2]
    )
    if differences == 1:
        raw += 0.15  # Adjacent — good synergy
    elif differences == 2:
        raw += 0.25  # Complementary — great synergy

    return min(raw, 1.0)


def build_synergy_matrix() -> dict[str, dict[str, float]]:
    """Build full 27x27 synergy matrix."""
    codes = list(ARCHETYPE_MAP.keys())
    matrix: Any = {}
    for c1 in codes:
        matrix[c1] = {}
        for c2 in codes:
            matrix[c1][c2] = get_synergy_coefficient(c1, c2)
    return matrix  # type: ignore[no-any-return]


def get_neighbors(code: str, distance: int = 1) -> list[C4State]:
    """Get archetypes within Hamming distance."""
    from src.c4.engine import C4Space

    space = C4Space()
    state = CanonicalC4State.from_name(code)
    neighbors = [n for _, n in space.neighbors(state)]
    return [ARCHETYPE_MAP[n.code] for n in neighbors if n.code in ARCHETYPE_MAP]


def get_optimal_team(
    task_codes: list[str], team_size: int = 3, diversity_boost: bool = True
) -> list[C4State]:
    """
    Assemble optimal agent team for a task.

    Args:
        task_codes: C4 codes representing the task state(s)
        team_size: Number of agents to select
        diversity_boost: Prefer diverse perspectives

    Returns:
        List of selected archetypes
    """
    all_agents = get_all_archetypes()
    scores = []

    for agent in all_agents:
        # Base score: average synergy with task states
        task_synergy = sum(
            get_synergy_coefficient(agent.code, tc) for tc in task_codes
        ) / len(task_codes)

        # Diversity bonus: prefer agents different from task
        if diversity_boost:
            differences = 0
            for tc in task_codes:
                t1, d1, a1 = decode_code(agent.code)
                t2, d2, a2 = decode_code(tc)
                differences += sum([t1 != t2, d1 != d2, a1 != a2])
            avg_diff = differences / len(task_codes)
            diversity_bonus = avg_diff * 0.1  # Up to 0.3 bonus
        else:
            diversity_bonus = 0

        scores.append((agent, task_synergy + diversity_bonus))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Select top team_size, ensuring diversity
    selected = []
    selected_codes = set()

    for agent, _score in scores:
        if agent.code not in selected_codes and agent.code not in task_codes:
            selected.append(agent)
            selected_codes.add(agent.code)
        if len(selected) >= team_size:
            break

    return selected


def select_agents_for_task(
    problem: str, num_agents: int = 3
) -> list[C4State]:
    """
    Select agents based on problem characteristics.
    Uses keyword matching to infer optimal C4 states.
    """
    problem_lower = problem.lower()

    # Keyword → C4 code mapping
    keyword_map = {
        "history": ["000", "001", "002"],
        "past": ["000", "010", "020"],
        "memory": ["000", "001", "021"],
        "experience": ["000", "100", "200"],
        "current": ["100", "101", "102"],
        "now": ["100", "110", "120"],
        "present": ["100", "101", "111"],
        "today": ["100", "110"],
        "future": ["200", "210", "220"],
        "goal": ["200", "210", "220"],
        "plan": ["200", "201", "211"],
        "vision": ["200", "210", "220"],
        "predict": ["202", "212"],
        "forecast": ["202", "212"],
        "strategy": ["210", "211", "212"],
        "abstract": ["010", "011", "012", "110", "111", "112"],
        "concept": ["010", "110", "210"],
        "theory": ["010", "011", "012"],
        "model": ["110", "111", "112"],
        "system": ["002", "012", "022", "102", "112", "122", "202", "212", "222"],
        "structure": ["012", "112", "212"],
        "design": ["112", "122", "212"],
        "self": ["000", "010", "020", "100", "110", "120", "200", "210", "220"],
        "personal": ["000", "010", "020", "100", "110", "120", "200", "210", "220"],
        "team": ["001", "011", "021", "101", "111", "121", "201", "211", "221"],
        "group": ["001", "011", "021", "101", "111", "121"],
        "collaborate": ["101", "111", "121"],
        "meta": ["020", "021", "022", "120", "121", "122", "220", "221", "222"],
        "learn": ["020", "120", "220"],
        "transform": ["220", "221", "222"],
        "evolve": ["221", "222"],
        "innovation": ["210", "211", "212", "220", "221", "222"],
    }

    # Score each code by keyword matches
    code_scores: dict[str, int] = {code: 0 for code in ARCHETYPE_MAP}

    for keyword, codes in keyword_map.items():
        if keyword in problem_lower:
            for code in codes:
                code_scores[code] += 1

    # Sort by score
    sorted_codes = sorted(code_scores.items(), key=lambda x: x[1], reverse=True)

    # Select top codes with non-zero scores
    top_codes = [code for code, score in sorted_codes[:num_agents] if score > 0]

    # If no matches, select diverse defaults
    if not top_codes:
        top_codes = ["111", "210", "022"]  # Mediator, Strategist, Epistemologist

    return [ARCHETYPE_MAP[code] for code in top_codes[:num_agents]]


def build_agent_prompt(
    code: str, problem: str, language: str = "en"
) -> str:
    """
    Build LLM prompt for a specific C4 archetype agent.

    Args:
        code: C4 state code (e.g., "111")
        problem: Research problem to solve
        language: "en" or "ru"

    Returns:
        System prompt for the archetype
    """
    agent = ARCHETYPE_MAP.get(code)
    if not agent:
        raise ValueError(f"Unknown archetype code: {code}")

    if language == "ru":
        name = agent.name_ru
        role_desc = f"Вы — {name}, агент когнитивной геометрии C4."
        perspective = f"Ваша перспектива: {agent.time} × {agent.scale} × {agent.agency}"
        task = f"Проанализируйте проблему с вашей уникальной точки зрения: {problem}"
        output = (
            "Дайте свой анализ, включая:\n"
            "1. Ключевые наблюдения с вашей перспективы\n"
            "2. Скрытые паттерны, которые видны только вам\n"
            "3. Гипотезу, основанную на ваших сильных сторонах\n"
            "4. Рекомендации по действиям"
        )
    else:
        name = agent.name_en
        role_desc = f"You are {name}, a C4 Cognitive Geometry agent."
        perspective = f"Your perspective: {agent.time} × {agent.scale} × {agent.agency}"
        task = f"Analyze the problem from your unique viewpoint: {problem}"
        output = (
            "Provide your analysis, including:\n"
            "1. Key observations from your perspective\n"
            "2. Hidden patterns only visible to you\n"
            "3. A hypothesis based on your strengths\n"
            "4. Actionable recommendations"
        )

    prompt = f"""{role_desc}

{perspective}
{agent.description}
Metaphor: {agent.metaphor}

Strengths: {', '.join(agent.strengths)}

{task}

{output}

Respond in {language.upper()}.
"""

    return prompt


def build_council_prompt(
    problem: str, agent_codes: list[str], language: str = "en"
) -> str:
    """Build prompt for multi-agent council session."""
    agents = [ARCHETYPE_MAP[code] for code in agent_codes if code in ARCHETYPE_MAP]

    if language == "ru":
        header = f"Совет из {len(agents)} агентов C4 анализирует проблему:\n{problem}\n\n"
        agent_list = "\n".join(
            f"- {a.name_ru} ({a.code}): {a.description}" for a in agents
        )
        instruction = (
            "\n\nКаждый агент даёт свой анализ. Затем Синтезатор объединяет их в единое решение."
        )
    else:
        header = f"Council of {len(agents)} C4 agents analyzing:\n{problem}\n\n"
        agent_list = "\n".join(
            f"- {a.name_en} ({a.code}): {a.description}" for a in agents
        )
        instruction = (
            "\n\nEach agent provides their analysis. Then a Synthesizer combines them into unified solution."
        )

    return header + agent_list + instruction


def build_team_prompt(
    problem: str, team: list[C4State], language: str = "en"
) -> str:
    """Build prompt for a collaborative agent team."""
    if language == "ru":
        intro = f"Команда из {len(team)} агентов работает над проблемой:\n{problem}\n\n"
        roles = "\n".join(
            f"{i+1}. {a.name_ru} ({a.code}) — {a.description}"
            for i, a in enumerate(team)
        )
        task = (
            "\n\nАгенты обсуждают проблему, критикуют идеи друг друга и синтезируют решение."
        )
    else:
        intro = f"Team of {len(team)} agents collaborating on:\n{problem}\n\n"
        roles = "\n".join(
            f"{i+1}. {a.name_en} ({a.code}) — {a.description}"
            for i, a in enumerate(team)
        )
        task = (
            "\n\nAgents discuss the problem, critique each other's ideas, and synthesize a solution."
        )

    return intro + roles + task
