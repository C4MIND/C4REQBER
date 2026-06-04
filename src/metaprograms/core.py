"""Core Metaprograms for C4REQBER v7.

Implements ~70 core Metaprograms (MPs) organized by 7 categories,
each with C4 coordinates F⟨T,S,A⟩ (Temporal, Scale, Agency).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class TemporalAxis(Enum):
    """T axis: temporal orientation."""

    PAST = 0
    PRESENT = 1
    FUTURE = 2


class ScaleAxis(Enum):
    """S axis: abstraction level."""

    CONCRETE = 0
    ABSTRACT = 1
    META = 2


class AgencyAxis(Enum):
    """A axis: agency focus."""

    SELF = 0
    OTHER = 1
    SYSTEM = 2


@dataclass(frozen=True)
class C4Coord:
    """C4 coordinate F⟨T,S,A⟩."""

    temporal: TemporalAxis
    scale: ScaleAxis
    agency: AgencyAxis

    def __repr__(self) -> str:
        return (
            f"F⟨{self.temporal.name},{self.scale.name},{self.agency.name}⟩"
        )

    def to_tuple(self) -> tuple[int, int, int]:
        """Return numeric tuple for distance calculations."""
        t_map = {TemporalAxis.PAST: 0, TemporalAxis.PRESENT: 1, TemporalAxis.FUTURE: 2}
        s_map = {ScaleAxis.CONCRETE: 0, ScaleAxis.ABSTRACT: 1, ScaleAxis.META: 2}
        a_map = {AgencyAxis.SELF: 0, AgencyAxis.OTHER: 1, AgencyAxis.SYSTEM: 2}
        return (t_map[self.temporal], s_map[self.scale], a_map[self.agency])


@dataclass(frozen=True)
class Metaprogram:
    """A single Metaprogram definition."""

    code: str
    name: str
    category: str
    c4: C4Coord
    description: str
    keywords: tuple[str, ...]
    opposite: str | None = None


# ═══════════════════════════════════════════════════════════════════════════
# 70 CORE METAPROGRAMS
# ═══════════════════════════════════════════════════════════════════════════

# ─── TEMPORAL (12 MPs) ────────────────────────────────────────────────────
TEMPORAL_METAPROGRAMS: Final[list[Metaprogram]] = [
    Metaprogram(
        "T01", "Past Orientation", "Temporal",
        C4Coord(TemporalAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Focus on historical events, prior experiences, and what has already occurred.",
        ("before", "used to", "previously", "back then", "history", "earlier",
         "once", "formerly", "in the past", "remember when", " nostalgic"),
        "T02",
    ),
    Metaprogram(
        "T02", "Present Orientation", "Temporal",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Focus on immediate now, current state, and what is happening right now.",
        ("now", "currently", "at the moment", "right now", "today", "presently",
         "immediately", "here and now", "as we speak", "in this moment"),
        "T01",
    ),
    Metaprogram(
        "T03", "Future Orientation", "Temporal",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Focus on upcoming events, plans, goals, and what will happen.",
        ("will", "going to", "plan", "future", "next", "upcoming", "soon",
         "tomorrow", "eventually", "ahead", "prospect", "vision"),
        "T01",
    ),
    Metaprogram(
        "T04", "Past-Reflective", "Temporal",
        C4Coord(TemporalAxis.PAST, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Analytical reflection on past events to extract meaning and lessons.",
        ("looking back", "in retrospect", "hindsight", "lessons learned",
         "what I learned", "reflecting on", "reconsidering", "revisited"),
    ),
    Metaprogram(
        "T05", "Present-Flow", "Temporal",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Being fully immersed in the current activity without distraction.",
        ("in the zone", "flow state", "immersed", "absorbed", "engrossed",
         "losing track of time", "effortlessly", "naturally"),
    ),
    Metaprogram(
        "T06", "Future-Visionary", "Temporal",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.META, AgencyAxis.SELF),
        "Creating grand long-term visions and transformative scenarios.",
        ("imagine", "someday", "transform", "revolutionize", "paradigm shift",
         "breakthrough", "game changer", "disrupt", "moonshot"),
    ),
    Metaprogram(
        "T07", "Historical-Cyclical", "Temporal",
        C4Coord(TemporalAxis.PAST, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Viewing events through repeating patterns and historical cycles.",
        ("cycle", "recurring", "pattern repeats", "history repeats", "seasonal",
         "boom and bust", "rhythm", "ebb and flow", "periodic"),
    ),
    Metaprogram(
        "T08", "Immediate-Urgency", "Temporal",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Sense of pressing need to act right now.",
        ("urgent", "asap", "deadline", "critical", "pressing", "emergency",
         "time-sensitive", "rush", "hurry", "cannot wait"),
    ),
    Metaprogram(
        "T09", "Long-Term-Strategic", "Temporal",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM),
        "Planning with extended time horizons and systemic foresight.",
        ("long-term", "strategic", "five-year", "decade", "legacy",
         "sustainable", "enduring", "lasting", "over time", "roadmap"),
    ),
    Metaprogram(
        "T10", "Nostalgic", "Temporal",
        C4Coord(TemporalAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Sentimental longing for past experiences or states.",
        ("nostalgic", "good old days", "miss those times", "wish we could",
         "those were the days", "fond memories", "longing for"),
    ),
    Metaprogram(
        "T11", "Speculative", "Temporal",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Exploring hypothetical future scenarios and possibilities.",
        ("what if", "suppose", "imagine if", "could be", "might happen",
         "hypothetically", "scenario", "contingency", "possibility"),
    ),
    Metaprogram(
        "T12", "Time-Fluid", "Temporal",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Experiencing time as non-linear, malleable, or context-dependent.",
        ("timeless", "elastic", "subjective time", "time flies", "time drags",
         "in another era", "parallel timeline", "time warp"),
    ),
]

# ─── SCALE (15 MPs) ───────────────────────────────────────────────────────
SCALE_METAPROGRAMS: Final[list[Metaprogram]] = [
    Metaprogram(
        "S01", "Concrete-Detail", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Focus on specific, tangible, observable details.",
        ("specifically", "exactly", "precisely", "the fact is", "for instance",
         "such as", "in particular", "namely", "concretely"),
        "S02",
    ),
    Metaprogram(
        "S02", "Abstract-General", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Focus on general principles, patterns, and concepts.",
        ("in general", "overall", "broadly", "conceptually", "theoretically",
         "essentially", "fundamentally", "at a high level", "in principle"),
        "S01",
    ),
    Metaprogram(
        "S03", "Meta-Systemic", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Operating at the level of systems-of-systems and meta-patterns.",
        ("meta", "system of systems", "framework", "paradigm", "epistemic",
         "ontological", "second-order", "higher-order", "recursive"),
    ),
    Metaprogram(
        "S04", "Reductionist", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SYSTEM),
        "Breaking problems into smallest constituent parts.",
        ("break down", "decompose", "atomize", "granular", "component",
         "element", "constituent", "piece by piece", "step by step"),
        "S05",
    ),
    Metaprogram(
        "S05", "Holistic", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM),
        "Viewing problems as integrated wholes rather than parts.",
        ("whole picture", "big picture", "integrated", "interconnected",
         "gestalt", "synergy", "unity", "ecosystem", "holistic"),
        "S04",
    ),
    Metaprogram(
        "S06", "Micro-Focus", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Intense focus on minute details and fine distinctions.",
        ("nuance", "subtle", "fine detail", "granular", "pixel-level",
         "nitty-gritty", "minutiae", "fine print", "detail-oriented"),
    ),
    Metaprogram(
        "S07", "Macro-Focus", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM),
        "Broad view encompassing large-scale patterns and trends.",
        ("macro", "landscape", "overview", "bird's eye", "panoramic",
         "sweeping", "global view", "market-wide", "industry-level"),
    ),
    Metaprogram(
        "S08", "Ladder-Up", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SELF),
        "Moving from concrete to abstract levels (chunking up).",
        ("what's the bigger", "higher purpose", "what does this mean",
         "so what", "ultimately", "at the highest level", "transcend"),
    ),
    Metaprogram(
        "S09", "Ladder-Down", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Moving from abstract to concrete levels (chunking down).",
        ("for example", "specifically how", "what exactly", "give me an instance",
         "concretely", "practically speaking", "in practice", "how so"),
    ),
    Metaprogram(
        "S10", "Analogical", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Understanding through cross-domain mappings and metaphors.",
        ("like", "similar to", "analogy", "metaphor", "just as", "comparable",
         "akin to", "parallel", "isomorphic", "as if"),
    ),
    Metaprogram(
        "S11", "Prototypical", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Thinking in terms of representative examples and exemplars.",
        ("typical", "classic example", "paradigm case", "archetypal",
         "quintessential", "stereotypical", "representative", "model"),
    ),
    Metaprogram(
        "S12", "Dimensional", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Analyzing across multiple independent dimensions simultaneously.",
        ("dimension", "axis", "parameter", "variable", "factor", "aspect",
         "multivariate", "multidimensional", "degrees of freedom"),
    ),
    Metaprogram(
        "S13", "Scalar-Quantitative", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SYSTEM),
        "Measuring and comparing on numerical scales.",
        ("metric", "quantify", "measure", "score", "rating", "percentage",
         "numerical", "scale of", "degrees", "points", "KPI"),
    ),
    Metaprogram(
        "S14", "Categorical-Qualitative", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM),
        "Classifying into distinct qualitative categories.",
        ("category", "type", "kind", "class", "qualitative", "taxonomy",
         "sort", "bucket", "bin", "cluster", "archetype"),
    ),
    Metaprogram(
        "S15", "Recursive-Self-Referential", "Scale",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SELF),
        "Applying patterns to themselves; self-referential thinking.",
        ("self-referential", "recursive", "fractal", "nested", "self-similar",
         "turtles all the way", "infinite regress", "feedback loop on itself"),
    ),
]

# ─── AGENCY (10 MPs) ──────────────────────────────────────────────────────
AGENCY_METAPROGRAMS: Final[list[Metaprogram]] = [
    Metaprogram(
        "A01", "Self-Agency", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Belief in personal control and ability to cause effects.",
        ("I can", "I will", "my choice", "I decide", "under my control",
         "I am responsible", "I caused", "my power", "I choose"),
        "A02",
    ),
    Metaprogram(
        "A02", "External-Agency", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.OTHER),
        "Attributing causation to external people, forces, or circumstances.",
        ("they made me", "circumstances", "forced to", "had no choice",
         "external pressure", "society", "the system", "fate", "destiny"),
        "A01",
    ),
    Metaprogram(
        "A03", "System-Agency", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM),
        "Attributing causation to emergent systemic properties.",
        ("emergent", "systemic", "structural", "institutional", "network effect",
         "complex adaptive", "self-organizing", "collective behavior"),
    ),
    Metaprogram(
        "A04", "Internal-Locus", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Control perceived as originating from within the individual.",
        ("internal", "intrinsic motivation", "self-driven", "from within",
         "my values", "personal standards", "inner compass", "authentic self"),
        "A05",
    ),
    Metaprogram(
        "A05", "External-Locus", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.OTHER),
        "Control perceived as originating from outside the individual.",
        ("external validation", "approval", "expectations", "social pressure",
         "what others think", "reputation", "status", "recognition"),
        "A04",
    ),
    Metaprogram(
        "A06", "Collaborative-Agency", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.OTHER),
        "Joint action and shared responsibility with others.",
        ("together", "we can", "collaborative", "teamwork", "partnership",
         "co-create", "joint effort", "mutual", "collective action"),
    ),
    Metaprogram(
        "A07", "Distributed-Agency", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Agency spread across networks, tools, and environments.",
        ("distributed", "delegated", "outsourced", "crowdsourced", "swarm",
         "multi-agent", "hybrid intelligence", "human-AI team"),
    ),
    Metaprogram(
        "A08", "Reactive", "Agency",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Responding to stimuli and events as they occur.",
        ("react", "respond", "firefight", "put out fires", "ad hoc",
         "improvise", "wing it", "play it by ear", "on the fly"),
        "A09",
    ),
    Metaprogram(
        "A09", "Proactive", "Agency",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Anticipating and initiating action before events occur.",
        ("proactive", "initiate", "anticipate", "preemptive", "get ahead",
         "take charge", "seize initiative", "pioneer", "forge ahead"),
        "A08",
    ),
    Metaprogram(
        "A10", "Stewardship", "Agency",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Acting as caretaker for systems and future generations.",
        ("steward", "guardian", "custodian", "trustee", "responsible for",
         "legacy", "sustain", "preserve", "intergenerational", "fiduciary"),
    ),
]

# ─── PROCESS (8 MPs) ──────────────────────────────────────────────────────
PROCESS_METAPROGRAMS: Final[list[Metaprogram]] = [
    Metaprogram(
        "P01", "Action-Oriented", "Process",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Preference for doing, executing, and taking immediate steps.",
        ("do it", "act now", "execute", "implement", "get it done",
         "move fast", "just start", "ship it", "deploy", "launch"),
        "P02",
    ),
    Metaprogram(
        "P02", "Reflection-Oriented", "Process",
        C4Coord(TemporalAxis.PAST, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Preference for thinking, analyzing, and considering before acting.",
        ("think about", "consider", "reflect", "analyze", "ponder",
         "deliberate", "contemplate", "meditate on", "mull over"),
        "P01",
    ),
    Metaprogram(
        "P03", "Iterative", "Process",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SYSTEM),
        "Progressing through repeated cycles of improvement.",
        ("iterate", "cycle", "refine", "pivot", "agile", "sprint",
         "feedback loop", "continuous improvement", "Kaizen"),
    ),
    Metaprogram(
        "P04", "Linear-Sequential", "Process",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Following step-by-step progression toward completion.",
        ("step by step", "sequential", "phase", "milestone", "waterfall",
         "stages", "in order", "first then", "roadmap", "timeline"),
        "P03",
    ),
    Metaprogram(
        "P05", "Experimental", "Process",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Testing hypotheses through controlled trials and exploration.",
        ("experiment", "test", "hypothesis", "trial", "pilot", "prototype",
         "A/B test", "validate", "exploratory", "empirical"),
    ),
    Metaprogram(
        "P06", "Intuitive", "Process",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Relying on gut feeling, pattern recognition, and tacit knowledge.",
        ("intuition", "gut feeling", "instinct", "sixth sense", "hunch",
         "felt sense", "inner knowing", "tacit", "implicit", "visceral"),
        "P05",
    ),
    Metaprogram(
        "P07", "Disciplined-Methodical", "Process",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Following rigorous, structured, and repeatable procedures.",
        ("rigorous", "methodical", "systematic", "disciplined", "protocol",
         "procedure", "by the book", "checklist", "standardized", "SOP"),
    ),
    Metaprogram(
        "P08", "Opportunistic", "Process",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Seizing unexpected opportunities and adapting to openings.",
        ("opportunity", "serendipity", "lucky break", "window opened",
         "strike while", "capitalize", "exploit", "leverage", "ride the wave"),
    ),
]

# ─── RESULT (8 MPs) ───────────────────────────────────────────────────────
RESULT_METAPROGRAMS: Final[list[Metaprogram]] = [
    Metaprogram(
        "R01", "Goal-Focused", "Result",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Oriented toward achieving specific, defined outcomes.",
        ("goal", "objective", "target", "aim", "destination", "end state",
         "milestone", "deliverable", "outcome", "result"),
        "R02",
    ),
    Metaprogram(
        "R02", "Journey-Focused", "Result",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Valuing the process and experience over the destination.",
        ("journey", "process", "experience", "growth", "learning",
         "enjoy the ride", "path", "way of life", "practice"),
        "R01",
    ),
    Metaprogram(
        "R03", "Perfectionist", "Result",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Striving for flawless, error-free outcomes.",
        ("perfect", "flawless", "impeccable", "zero defects", "exactly right",
         "precisely", "without error", "spotless", "immaculate"),
        "R04",
    ),
    Metaprogram(
        "R04", "Satisficing", "Result",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Accepting good-enough solutions to conserve resources.",
        ("good enough", "satisfice", "adequate", "sufficient", "reasonable",
         "workable", "pragmatic", "feasible", "close enough", "80/20"),
        "R03",
    ),
    Metaprogram(
        "R05", "Optimization", "Result",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM),
        "Seeking the mathematically best possible solution.",
        ("optimal", "maximize", "minimize", "best possible", "peak",
         "ideal", "perfect balance", "Pareto", "efficient frontier"),
    ),
    Metaprogram(
        "R06", "Risk-Averse", "Result",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Prioritizing safety and avoiding negative outcomes.",
        ("safe", "avoid risk", "conservative", "cautious", "hedge",
         "protect", "downside", "worst case", "insurance", "buffer"),
        "R07",
    ),
    Metaprogram(
        "R07", "Risk-Seeking", "Result",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Willing to accept uncertainty for potentially greater rewards.",
        ("risk", "bold", "daring", "all in", "high stakes", "venture",
         "speculate", "gamble", "moonshot", "no risk no reward"),
        "R06",
    ),
    Metaprogram(
        "R08", "Legacy-Oriented", "Result",
        C4Coord(TemporalAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Focused on long-term impact and what endures beyond oneself.",
        ("legacy", "impact", "lasting change", "future generations",
         "footprint", "mark on the world", "enduring", "timeless contribution"),
    ),
]

# ─── COMMUNICATION (12 MPs) ───────────────────────────────────────────────
COMMUNICATION_METAPROGRAMS: Final[list[Metaprogram]] = [
    Metaprogram(
        "C01", "Internal-Reference", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Judging based on internal standards and personal experience.",
        ("I know", "in my experience", "to me", "personally", "I feel",
         "my sense", "internally", "subjectively", "for me"),
        "C02",
    ),
    Metaprogram(
        "C02", "External-Reference", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.OTHER),
        "Judging based on external data, feedback, and others' opinions.",
        ("they say", "research shows", "data indicates", "experts agree",
         "according to", "survey", "study", "benchmark", "external"),
        "C01",
    ),
    Metaprogram(
        "C03", "Visual", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Processing and expressing information through visual imagery.",
        ("see", "look", "picture", "imagine", "visualize", "perspective",
         "view", "scene", "appearance", "bright", "color", "shape"),
    ),
    Metaprogram(
        "C04", "Auditory", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Processing and expressing information through sound and language.",
        ("hear", "sound", "listen", "tell", "say", "word", "tone",
         "resonate", "harmony", "loud", "quiet", "ring"),
    ),
    Metaprogram(
        "C05", "Kinesthetic", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Processing and expressing information through body sensation and movement.",
        ("feel", "touch", "grasp", "handle", "concrete", "solid",
         "heavy", "light", "pressure", "movement", "flow", "texture"),
    ),
    Metaprogram(
        "C06", "Digital", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM),
        "Processing information through structured logic and discrete categories.",
        ("true/false", "binary", "logic", "precise", "exact", "digital",
         "on/off", "yes/no", "either/or", "categorical", "discrete"),
    ),
    Metaprogram(
        "C07", "Analog", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Processing information through continuous gradients and degrees.",
        ("more or less", "gradually", "spectrum", "continuum", "shade",
         "degree", "relative", "approximately", "fuzzy", "analog"),
        "C06",
    ),
    Metaprogram(
        "C08", "Explicit", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.OTHER),
        "Stating information directly and unambiguously.",
        ("clearly", "explicitly", "directly", "plainly", "frankly",
         "outright", "verbatim", "spell out", "in plain English"),
        "C09",
    ),
    Metaprogram(
        "C09", "Implicit", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.OTHER),
        "Conveying meaning indirectly through context and suggestion.",
        ("hint", "imply", "suggest", "between the lines", "subtext",
         "nuance", "read the room", "unsaid", "tacit", "undercurrent"),
        "C08",
    ),
    Metaprogram(
        "C10", "Assertive", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Expressing needs and opinions directly while respecting others.",
        ("I need", "I want", "my position", "I state", "I assert",
         "direct", "clear boundary", "stand my ground", "firm"),
    ),
    Metaprogram(
        "C11", "Empathetic", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.OTHER),
        "Attuning to and reflecting others' emotional states.",
        ("I understand", "you feel", "that must be", "I hear you",
         "validate", "acknowledge", "resonate", "compassion", "attune"),
    ),
    Metaprogram(
        "C12", "Systemic-Communication", "Communication",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Communicating about patterns of communication themselves (meta-communication).",
        ("meta-communication", "how we talk", "communication pattern",
         "framing", "discourse", "dialogue structure", "interaction pattern"),
    ),
]

# ─── META-COGNITIVE (5 MPs) ───────────────────────────────────────────────
METACOGNITIVE_METAPROGRAMS: Final[list[Metaprogram]] = [
    Metaprogram(
        "M01", "Observer-O0", "Meta-cognitive",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "First-order experience: being immersed in thought without awareness of thinking.",
        ("I think", "I believe", "my thought", "in my mind", "naturally",
         "obviously", "of course", "I assume"),
    ),
    Metaprogram(
        "M02", "Observer-O1", "Meta-cognitive",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF),
        "Second-order awareness: noticing that one is thinking.",
        ("I notice I think", "I am aware that", "I observe myself",
         "I realize", "I recognize", "catching myself", "stepping back"),
    ),
    Metaprogram(
        "M03", "Observer-O2", "Meta-cognitive",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SYSTEM),
        "Third-order awareness: observing the pattern of one's observation habits.",
        ("I notice I notice", "pattern in my awareness", "how I observe",
         "meta-awareness", "recursive self", "observer of the observer"),
    ),
    Metaprogram(
        "M04", "Cognitive-Flexibility", "Meta-cognitive",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.META, AgencyAxis.SELF),
        "Ability to shift between different MPs and cognitive frames.",
        ("on the other hand", "alternatively", "from another angle",
         "reframe", "shift perspective", "consider the opposite", "flip it"),
    ),
    Metaprogram(
        "M05", "Cognitive-Stubbornness", "Meta-cognitive",
        C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
        "Resistance to changing one's dominant cognitive patterns.",
        ("always", "never", "that's just how I am", "can't change",
         "fixed", "rigid", "set in my ways", "unchangeable"),
        "M04",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
# REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

ALL_METAPROGRAMS: Final[list[Metaprogram]] = (
    TEMPORAL_METAPROGRAMS
    + SCALE_METAPROGRAMS
    + AGENCY_METAPROGRAMS
    + PROCESS_METAPROGRAMS
    + RESULT_METAPROGRAMS
    + COMMUNICATION_METAPROGRAMS
    + METACOGNITIVE_METAPROGRAMS
)

METAPROGRAM_BY_CODE: Final[dict[str, Metaprogram]] = {
    mp.code: mp for mp in ALL_METAPROGRAMS
}

CATEGORY_MAP: Final[dict[str, list[Metaprogram]]] = {
    "Temporal": TEMPORAL_METAPROGRAMS,
    "Scale": SCALE_METAPROGRAMS,
    "Agency": AGENCY_METAPROGRAMS,
    "Process": PROCESS_METAPROGRAMS,
    "Result": RESULT_METAPROGRAMS,
    "Communication": COMMUNICATION_METAPROGRAMS,
    "Meta-cognitive": METACOGNITIVE_METAPROGRAMS,
}


def get_metaprogram(code: str) -> Metaprogram | None:
    """Lookup a metaprogram by its code."""
    return METAPROGRAM_BY_CODE.get(code)


def get_by_category(category: str) -> list[Metaprogram]:
    """Get all metaprograms in a category."""
    return CATEGORY_MAP.get(category, [])


def count_metaprograms() -> dict[str, int]:
    """Return counts per category and total."""
    counts = {cat: len(mps) for cat, mps in CATEGORY_MAP.items()}
    counts["Total"] = sum(counts.values())
    return counts


def hamming_distance(c1: C4Coord, c2: C4Coord) -> int:
    """Hamming distance between two C4 coordinates."""
    t1, s1, a1 = c1.to_tuple()
    t2, s2, a2 = c2.to_tuple()
    return int(t1 != t2) + int(s1 != s2) + int(a1 != a2)
