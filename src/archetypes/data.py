"""
C4 Archetypes Data — 27 states of the Z₃³ hypercube
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class C4Archetype:
    """Single C4 cognitive state."""

    code: str
    time: str  # Past / Present / Future
    scale: str  # Concrete / Abstract / Meta
    agency: str  # Self / Other / System
    name_en: str
    name_ru: str
    description: str
    metaphor: str
    strengths: list[str]
    color: str  # Hex color for visualization


# The 27 C4 archetypes
ARCHETYPE_MAP: dict[str, C4Archetype] = {
    "000": C4Archetype(
        code="000",
        time="Past",
        scale="Concrete",
        agency="Self",
        name_en="Historian",
        name_ru="Историк",
        description="Personal experience analyst. Extracts patterns from individual past events.",
        metaphor="An archaeologist brushing dust from a personal artifact",
        strengths=["pattern recognition", "historical analysis", "learning from experience", "detail orientation"],
        color="#3B82F6",
    ),
    "001": C4Archetype(
        code="001",
        time="Past",
        scale="Concrete",
        agency="Other",
        name_en="Recorder",
        name_ru="Летописец",
        description="Collective memory keeper. Documents shared experiences and group history.",
        metaphor="A scribe chronicling the journey of a caravan",
        strengths=["documentation", "collective memory", "storytelling", "continuity"],
        color="#60A5FA",
    ),
    "002": C4Archetype(
        code="002",
        time="Past",
        scale="Concrete",
        agency="System",
        name_en="Archivist",
        name_ru="Архивист",
        description="System history researcher. Uncovers concrete patterns in organizational past.",
        metaphor="A librarian organizing the scrolls of civilization",
        strengths=["systematic record-keeping", "data retrieval", "organizational memory", "taxonomy"],
        color="#93C5FD",
    ),
    "010": C4Archetype(
        code="010",
        time="Past",
        scale="Abstract",
        agency="Self",
        name_en="Theorist",
        name_ru="Теоретик",
        description="Abstract pattern thinker. Derives principles from personal historical reflection.",
        metaphor="A cartographer mapping the terrain of memory",
        strengths=["abstraction", "principle derivation", "conceptual modeling", "reflection"],
        color="#8B5CF6",
    ),
    "011": C4Archetype(
        code="011",
        time="Past",
        scale="Abstract",
        agency="Other",
        name_en="Analyst",
        name_ru="Аналитик",
        description="Collective theory builder. Synthesizes abstract lessons from group experiences.",
        metaphor="A chemist distilling essence from collective wisdom",
        strengths=["synthesis", "comparative analysis", "trend identification", "framework building"],
        color="#A78BFA",
    ),
    "012": C4Archetype(
        code="012",
        time="Past",
        scale="Abstract",
        agency="System",
        name_en="Systematizer",
        name_ru="Систематизатор",
        description="Organizational evolution analyst. Studies abstract patterns in systemic development.",
        metaphor="An engineer reverse-engineering the blueprint of history",
        strengths=["systems thinking", "evolutionary analysis", "structural modeling", "pattern generalization"],
        color="#C4B5FD",
    ),
    "020": C4Archetype(
        code="020",
        time="Past",
        scale="Meta",
        agency="Self",
        name_en="Philosopher",
        name_ru="Философ",
        description="Meta-wisdom keeper. Reflects on personal learning methodologies.",
        metaphor="A mirror reflecting on the nature of mirrors",
        strengths=["meta-cognition", "epistemological inquiry", "self-reflection", "wisdom synthesis"],
        color="#EC4899",
    ),
    "021": C4Archetype(
        code="021",
        time="Past",
        scale="Meta",
        agency="Other",
        name_en="Hermeneutist",
        name_ru="Герменевтик",
        description="Collective wisdom guardian. Holds meta-knowledge about group learning.",
        metaphor="A translator deciphering the language of shared meaning",
        strengths=["interpretation", "meaning-making", "cultural analysis", "narrative understanding"],
        color="#F472B6",
    ),
    "022": C4Archetype(
        code="022",
        time="Past",
        scale="Meta",
        agency="System",
        name_en="Epistemologist",
        name_ru="Эпистемолог",
        description="Systemic meta-historian. Understands how systems learn and evolve.",
        metaphor="A historian writing the history of history itself",
        strengths=["knowledge systems", "learning theory", "epistemic frameworks", "institutional memory"],
        color="#FBCFE8",
    ),
    "100": C4Archetype(
        code="100",
        time="Present",
        scale="Concrete",
        agency="Self",
        name_en="Experiencer",
        name_ru="Переживающий",
        description="Personal reality scanner. Notices concrete details in current personal experience.",
        metaphor="A sensor feeling the texture of the present moment",
        strengths=["sensory awareness", "embodied cognition", "immediate perception", "reactivity"],
        color="#10B981",
    ),
    "101": C4Archetype(
        code="101",
        time="Present",
        scale="Concrete",
        agency="Other",
        name_en="Collaborator",
        name_ru="Соратник",
        description="Team dynamics navigator. Coordinates concrete actions within groups.",
        metaphor="A dancer synchronizing movements with partners",
        strengths=["coordination", "teamwork", "communication", "mutual adaptation"],
        color="#34D399",
    ),
    "102": C4Archetype(
        code="102",
        time="Present",
        scale="Concrete",
        agency="System",
        name_en="Observer",
        name_ru="Наблюдатель",
        description="System executor. Manages concrete operational processes.",
        metaphor="A pilot monitoring the instruments of a complex machine",
        strengths=["process management", "operational oversight", "quality control", "execution"],
        color="#6EE7B7",
    ),
    "110": C4Archetype(
        code="110",
        time="Present",
        scale="Abstract",
        agency="Self",
        name_en="Abstractionist",
        name_ru="Абстракционист",
        description="Abstract pattern recognizer. Identifies conceptual structures in current situations.",
        metaphor="A geologist reading the strata of the present",
        strengths=["pattern recognition", "conceptual abstraction", "insight generation", "modeling"],
        color="#F59E0B",
    ),
    "111": C4Archetype(
        code="111",
        time="Present",
        scale="Abstract",
        agency="Other",
        name_en="Mediator",
        name_ru="Посредник",
        description="Integration mediator. Synthesizes abstract perspectives in group discussions.",
        metaphor="A conductor hearing the harmony between instruments",
        strengths=["perspective integration", "conflict resolution", "consensus building", "facilitation"],
        color="#FBBF24",
    ),
    "112": C4Archetype(
        code="112",
        time="Present",
        scale="Abstract",
        agency="System",
        name_en="Architect",
        name_ru="Архитектор",
        description="System designer. Creates abstract models for organizational challenges.",
        metaphor="An architect drafting blueprints for invisible structures",
        strengths=["system design", "structural thinking", "framework creation", "pattern instantiation"],
        color="#FCD34D",
    ),
    "120": C4Archetype(
        code="120",
        time="Present",
        scale="Meta",
        agency="Self",
        name_en="Metacognitivist",
        name_ru="Метакогнитивист",
        description="Self-awareness monitor. Observes own cognitive processes and meta-patterns.",
        metaphor="A mind watching itself think",
        strengths=["self-monitoring", "cognitive regulation", "awareness", "reflective practice"],
        color="#EF4444",
    ),
    "121": C4Archetype(
        code="121",
        time="Present",
        scale="Meta",
        agency="Other",
        name_en="Facilitator",
        name_ru="Фасилитатор",
        description="Group process analyst. Examines how groups think and make decisions.",
        metaphor="A gardener tending to the ecosystem of group dynamics",
        strengths=["process facilitation", "group dynamics", "decision analysis", "collaborative optimization"],
        color="#F87171",
    ),
    "122": C4Archetype(
        code="122",
        time="Present",
        scale="Meta",
        agency="System",
        name_en="Orchestrator",
        name_ru="Оркестратор",
        description="System-of-systems designer. Creates frameworks for organizational meta-cognition.",
        metaphor="A composer writing the score for an entire ecosystem",
        strengths=["ecosystem design", "meta-systems", "orchestration", "framework architecture"],
        color="#FCA5A5",
    ),
    "200": C4Archetype(
        code="200",
        time="Future",
        scale="Concrete",
        agency="Self",
        name_en="Visionary",
        name_ru="Визионер",
        description="Personal goal setter. Creates concrete action plans for individual future.",
        metaphor="A navigator plotting a course through uncharted waters",
        strengths=["goal setting", "vision crafting", "strategic planning", "future modeling"],
        color="#06B6D4",
    ),
    "201": C4Archetype(
        code="201",
        time="Future",
        scale="Concrete",
        agency="Other",
        name_en="Planner",
        name_ru="Планировщик",
        description="Team planner. Orchestrates concrete future actions across group members.",
        metaphor="A choreographer planning movements for the entire ensemble",
        strengths=["project planning", "resource allocation", "timeline management", "coordination"],
        color="#22D3EE",
    ),
    "202": C4Archetype(
        code="202",
        time="Future",
        scale="Concrete",
        agency="System",
        name_en="Prophet",
        name_ru="Пророк",
        description="System forecaster. Predicts concrete future system states.",
        metaphor="A meteorologist reading the signs of coming storms",
        strengths=["forecasting", "prediction", "trend extrapolation", "scenario planning"],
        color="#67E8F9",
    ),
    "210": C4Archetype(
        code="210",
        time="Future",
        scale="Abstract",
        agency="Self",
        name_en="Strategist",
        name_ru="Стратег",
        description="Personal vision holder. Develops abstract strategies for individual growth.",
        metaphor="A chess grandmaster seeing ten moves ahead",
        strengths=["strategic thinking", "long-term planning", "abstract visioning", "path optimization"],
        color="#8B5CF6",
    ),
    "211": C4Archetype(
        code="211",
        time="Future",
        scale="Abstract",
        agency="Other",
        name_en="Integrator",
        name_ru="Интегратор",
        description="Collective dream weaver. Shapes abstract visions for group futures.",
        metaphor="A weaver combining threads into a shared tapestry of tomorrow",
        strengths=["vision integration", "collective future shaping", "narrative construction", "shared meaning"],
        color="#A78BFA",
    ),
    "212": C4Archetype(
        code="212",
        time="Future",
        scale="Abstract",
        agency="System",
        name_en="Futurist",
        name_ru="Футурист",
        description="System trend forecaster. Predicts abstract patterns in systemic evolution.",
        metaphor="A cartographer mapping the topology of possible futures",
        strengths=["trend analysis", "future studies", "systems forecasting", "evolutionary prediction"],
        color="#C4B5FD",
    ),
    "220": C4Archetype(
        code="220",
        time="Future",
        scale="Meta",
        agency="Self",
        name_en="Transcendent",
        name_ru="Трансцендент",
        description="Personal transcendence guide. Envisions meta-level personal transformation.",
        metaphor="A phoenix envisioning its own rebirth",
        strengths=["transformational vision", "meta-level growth", "self-actualization", "paradigm shifting"],
        color="#F43F5E",
    ),
    "221": C4Archetype(
        code="221",
        time="Future",
        scale="Meta",
        agency="Other",
        name_en="Evolutionist",
        name_ru="Эволюционист",
        description="Collective evolution catalyst. Facilitates meta-level group transformation.",
        metaphor="A catalyst triggering chain reactions of collective growth",
        strengths=["transformational facilitation", "evolutionary design", "collective growth", "paradigm engineering"],
        color="#FB7185",
    ),
    "222": C4Archetype(
        code="222",
        time="Future",
        scale="Meta",
        agency="System",
        name_en="Cosmic",
        name_ru="Космический",
        description="Ultimate meta-agent. Operates at the highest level of systemic future meta-cognition.",
        metaphor="A singularity contemplating the birth of universes",
        strengths=["universal perspective", "meta-evolution", "cosmic cognition", "ultimate synthesis"],
        color="#FDA4AF",
    ),
}


# Time/Scale/Agency coordinate mapping
TIME_MAP = {"0": "Past", "1": "Present", "2": "Future"}
SCALE_MAP = {"0": "Concrete", "1": "Abstract", "2": "Meta"}
AGENCY_MAP = {"0": "Self", "1": "Other", "2": "System"}


def get_archetype(code: str) -> C4Archetype | None:
    """Get archetype by C4 code."""
    return ARCHETYPE_MAP.get(code)


def get_all_archetypes() -> list[C4Archetype]:
    """Get all 27 archetypes ordered by code."""
    return [ARCHETYPE_MAP[f"{t}{d}{a}"] for t in "012" for d in "012" for a in "012"]


def decode_code(code: str) -> tuple[str, str, str]:
    """Decode C4 code into (time, scale, agency)."""
    if len(code) != 3:
        raise ValueError(f"Invalid C4 code: {code}")
    return TIME_MAP[code[0]], SCALE_MAP[code[1]], AGENCY_MAP[code[2]]


def encode_code(time: str, scale: str, agency: str) -> str:
    """Encode (time, scale, agency) into C4 code."""
    t = {v: k for k, v in TIME_MAP.items()}[time]
    d = {v: k for k, v in SCALE_MAP.items()}[scale]
    a = {v: k for k, v in AGENCY_MAP.items()}[agency]
    return f"{t}{d}{a}"
