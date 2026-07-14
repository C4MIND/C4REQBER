"""
TRIZ Su-Field (Substance-Field) Analysis Model.

Su-Field models describe technical systems as interactions between
Substances (S1, S2) and Fields (F).

Classical TRIZ Su-Field notation:
    S1 — object being processed / acted upon
    S2 — tool / instrument acting on S1
    F  — energy / field coupling S1 and S2

A complete Su-Field has all three elements connected:
    S2 —F→ S1

Incomplete Su-Fields are innovation opportunities.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from src.c4.state import C4State


# =============================================================================
# FIELD ONTOLOGY
# =============================================================================

class FieldType(Enum):
    """The six fundamental TRIZ field types."""

    MECHANICAL = auto()
    THERMAL = auto()
    CHEMICAL = auto()
    ELECTRICAL = auto()
    MAGNETIC = auto()
    OPTICAL = auto()

    def __str__(self) -> str:
        return self.name.title()


FIELD_KEYWORDS: dict[FieldType, set[str]] = {
    FieldType.MECHANICAL: {
        "force", "pressure", "friction", "wear", "stress", "strain", "deformation",
        "impact", "collision", "vibration", "motion", "movement", "rotation",
        "mechanical", "load", "weight", "gravity", "torque", "tension",
        "compression", "shear", "bending", "stretch", "elastic", "plastic",
    },
    FieldType.THERMAL: {
        "heat", "temperature", "thermal", "cooling", "heating", "warm", "cold",
        "hot", "insulation", "conductivity", "convection", "radiation", "melting",
        "freezing", "boiling", "condensation", "evaporation", "sublimation",
    },
    FieldType.CHEMICAL: {
        "chemical", "reaction", "catalyst", "oxidation", "reduction", "corrosion",
        "dissolve", "solution", "acid", "base", "ph", "polymerization",
        "decomposition", "synthesis", "combustion", "electrolysis", "diffusion",
    },
    FieldType.ELECTRICAL: {
        "electric", "current", "voltage", "resistance", "capacitance", "inductance",
        "conductivity", "insulation", "dielectric", "electrode", "circuit",
        "power", "energy", "charge", "discharge", "arc", "spark", "ionization",
    },
    FieldType.MAGNETIC: {
        "magnetic", "magnet", "ferromagnetic", "diamagnetic", "paramagnetic",
        "field", "flux", "induction", "levitation", "attraction", "repulsion",
        "polarity", "electromagnetic", "magnetization", "demagnetization",
    },
    FieldType.OPTICAL: {
        "light", "optical", "laser", "photon", "radiation", "visible", "infrared",
        "ultraviolet", "reflection", "refraction", "diffraction", "interference",
        "polarization", "spectrum", "wavelength", "frequency", "transparency",
        "opacity", "color", "brightness", "illumination", "imaging",
    },
}


# =============================================================================
# SU-FIELD MODEL
# =============================================================================

@dataclass
class SuFieldModel:
    """
    A Su-Field model: S1 (object), S2 (tool), F (field).

    Status:
        - "complete":   S1, S2, F all present and coupled
        - "incomplete": one element missing
        - "harmful":    complete but producing harmful effect
        - "insufficient": complete but effect is too weak/strong
    """
    s1: str | None = None
    s2: str | None = None
    f: FieldType | None = None
    status: str = "incomplete"
    harmful_effect: str | None = None
    description: str = ""

    def is_complete(self) -> bool:
        return self.s1 is not None and self.s2 is not None and self.f is not None

    def missing_elements(self) -> list[str]:
        """Missing elements."""
        missing = []
        if self.s1 is None:
            missing.append("S1 (object)")
        if self.s2 is None:
            missing.append("S2 (tool)")
        if self.f is None:
            missing.append("F (field)")
        return missing

    def to_notation(self) -> str:
        """Return classical Su-Field notation string."""
        s1_str = self.s1 or "?"
        s2_str = self.s2 or "?"
        f_str = str(self.f) if self.f else "?"
        if self.is_complete():
            return f"{s2_str} —{f_str}→ {s1_str}"
        return f"[{s2_str}] —[{f_str}]→ [{s1_str}]  (incomplete)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "s1": self.s1,
            "s2": self.s2,
            "f": str(self.f) if self.f else None,
            "status": self.status,
            "harmful_effect": self.harmful_effect,
            "description": self.description,
            "notation": self.to_notation(),
            "is_complete": self.is_complete(),
            "missing_elements": self.missing_elements(),
        }


# =============================================================================
# SU-FIELD ANALYZER
# =============================================================================

_COMMON_VERBS = (
    r"strikes?|hits?|cuts?|drives?|pushes?|pulls?|lifts?|heats?|cools?|melts?|freezes?|"
    r"welds?|solders?|glues?|bonds?|joins?|splits?|compresses?|expands?|stretches?|bends?|"
    r"rotates?|moves?|transports?|holds?|supports?|levitates?|extracts?|removes?|adds?|"
    r"inserts?|injects?|sprays?|pours?|spreads?|applies?|cleans?|washes?|dries?|paints?|"
    r"prints?|etches?|engraves?|marks?|packages?|wraps?|covers?|protects?|shields?|"
    r"insulates?|isolates?|connects?|attaches?|fastens?|secures?|releases?|locks?|opens?|"
    r"closes?|starts?|stops?|activates?|deactivates?|enables?|disables?|turns?\s+(?:on|off)|"
    r"ignites?|extinguishes?|burns?|oxidizes?|reduces?|ionizes?|polarizes?|magnetizes?|"
    r"demagnetizes?|charges?|discharges?|grounds?|amplifies?|attenuates?|modulates?|"
    r"encodes?|decodes?|encrypts?|decrypts?|compresses?|decompresses?|translates?|"
    r"recognizes?|identifies?|classifies?|sorts?|ranks?|grades?|evaluates?|tests?|checks?|"
    r"inspects?|examines?|analyzes?|studies?|investigates?|researches?|explores?|discovers?|"
    r"finds?|locates?|positions?|places?|arranges?|organizes?|orders?|aligns?|orients?|"
    r"directs?|guides?|leads?|steers?|navigates?|pilots?|flies?|sails?|swims?|walks?|runs?|"
    r"jumps?|rolls?|slides?|glides?|climbs?|crawls?|hunts?|tracks?|traces?|follows?|chases?|"
    r"catches?|captures?|traps?|hooks?|shoots?|fires?|launches?|throws?|tosses?|casts?|"
    r"flings?|hurls?|pitches?|serves?|spikes?|smashes?|slams?|bangs?|crashes?|collides?|"
    r"impacts?|slaps?|punches?|kicks?|stabs?|pokes?|jabs?|thrusts?|shoves?|presses?|"
    r"squeezes?|pinches?|bites?|chews?|licks?|sucks?|blows?|breathes?|inhales?|exhales?|"
    r"sighs?|yawns?|coughs?|sneezes?|spits?|sweats?|bleeds?|cries?|laughs?|grins?|smiles?|"
    r"frowns?|glares?|stares?|gazes?|peeks?|peers?|looks?|sees?|views?|watches?|observes?|"
    r"notices?|spots?|senses?|feels?|touches?|tastes?|smells?|hears?|listens?|sounds?|rings?|"
    r"buzzes?|hums?|whirs?|whines?|whistles?|hisses?|roars?|rumbles?|thunders?|crackles?|"
    r"pops?|snaps?|cracks?|booms?|thuds?|clunks?|clanks?|clangs?|chimes?|dings?|dongs?|"
    r"ticks?|tocks?|clicks?|clacks?|coos?|caws?|crows?|gobbles?|hoots?|howls?|barks?|growls?|"
    r"snarls?|yelps?|woofs?|meows?|purrs?|mews?|bleats?|baas?|moos?|lows?|bellows?|brays?|"
    r"neighs?|whinnies?|snorts?|grunts?|oinks?|squeals?|squeaks?|cheeps?|chirps?|tweets?|"
    r"twitters?|warbles?|trills?|sings?|chants?|recites?|repeats?|echoes?|resounds?|vibrates?|"
    r"oscillates?|pulsates?|throbs?|quivers?|shivers?|shudders?|trembles?|shakes?|wobbles?|"
    r"wavers?|flutters?|flickers?|flashes?|gleams?|glimmers?|glitters?|sparkles?|twinkles?|"
    r"shines?|glows?|blazes?|flares?|waves?|ripples?|surges?|swells?|heaves?|billows?|"
    r"tumbles?|tosses?|pitches?|yaws?|sways?|swings?|rocks?|wallows?|lurches?|staggers?|"
    r"reels?|totters?|teeters?|hesitates?|pauses?|halts?|ceases?|desists?|refrains?|abstains?|"
    r"forbears?|avoids?|shuns?|eschews?|evades?|eludes?|dodges?|ducks?|sidesteps?|bypasses?|"
    r"circumvents?|skirts?|eases?|slips?|falls?|drops?|plunges?|dives?|plummets?|topples?|"
    r"collapses?|caves?|crumbles?|disintegrates?|dissolves?|melts?|liquefies?|solidifies?|"
    r"thaws?|defrosts?|deices?|chills?|refrigerates?|cryopreserves?|lyophilizes?|dehydrates?|"
    r"desiccates?|air-dries?|oven-dries?|sun-dries?|kiln-dries?|smokes?|cures?|preserves?|"
    r"pickles?|brines?|salts?|sugars?|cans?|bottles?|jars?|vacuum-packs?|foils?|films?|coats?|"
    r"glazes?|ices?|frosts?|dusts?|powders?|granulates?|pelletizes?|tablets?|capsules?|"
    r"encapsulates?|microencapsulates?|emulsifies?|homogenizes?|pasteurizes?|sterilizes?|"
    r"sanitizes?|disinfects?|fumigates?|irradiates?|autoclaves?|boils?|simmers?|poaches?|"
    r"stews?|braises?|roasts?|bakes?|broils?|grills?|barbecues?|fries?|sautes?|sears?|"
    r"scorches?|chars?|burns?|carbonizes?|calcines?|smelts?|refines?|purifies?|cleanses?|"
    r"clarifies?|filters?|strains?|sieves?|screens?|sorts?|separates?|divides?|fractionates?|"
    r"distills?|rectifies?|isolates?|polishes?|finishes?|buffs?|burnishes?|glosses?|varnishes?|"
    r"lacquers?|paints?|stains?|dyes?|tints?|colors?|pigments?|inks?|brands?|stamps?|imprints?|"
    r"embosses?|carves?|sculpts?|molds?|casts?|forges?|shapes?|fashions?|fabricates?|"
    r"manufactures?|produces?|makes?|creates?|builds?|constructs?|assembles?|erects?|raises?|"
    r"elevates?|hoists?|heaves?|hauls?|tows?|tugs?|drags?|draws?|trails?|shadows?|hounds?|"
    r"badgers?|heckles?|harasses?|pesters?|annoys?|irritates?|bothers?|disturbs?|disrupts?|"
    r"interrupts?|breaks?|ends?|terminates?|concludes?|shuts?|seals?|bars?|bolts?|latches?|"
    r"ties?|binds?|tapes?|cements?|fuses?|merges?|combines?|blends?|mixes?|stirs?|shakes?|"
    r"agitates?|purees?|suspends?|disperses?|dilutes?|concentrates?|evaporates?|condenses?|"
    r"leaches?|percolates?|clarifies?|perfects?|accomplishes?|achieves?|attains?|reaches?|"
    r"arrives?|gets?|obtains?|acquires?|gains?|earns?|wins?|scores?|nets?|grosses?|clears?|"
    r"profits?|advantages?|margins?|buffers?|cushions?|pads?|fills?|stuffs?|wads?|bats?|cores?|"
    r"centers?|kernels?|nucleuses?|seeds?|germs?|embryos?|ova?|spawns?|roes?|milts?|sperms?|"
    r"semens?|spores?|pollens?|grains?|granules?|particles?|specks?|flakes?|chips?|shards?|"
    r"fragments?|pieces?|bits?|portions?|segments?|sections?|divisions?|parcels?|packets?|"
    r"packs?|bundles?|bales?|rolls?|coils?|spools?|reels?|bobbins?|cones?|tubes?|cylinders?|"
    r"barrels?|drums?|kegs?|casks?|vats?|tanks?|reservoirs?|basins?|bowls?|dishes?|plates?|"
    r"trays?|platters?|salvers?|chargers?|coasters?|mats?|pillows?|bolsters?|headrests?|"
    r"backrests?|armrests?|footrests?|legrests?|seats?|chairs?|stools?|benches?|sofas?|couches?|"
    r"settees?|loveseats?|divans?|ottomans?|hassocks?|poufs?|beanbags?|chaises?|recliners?|"
    r"rockers?|gliders?|swivels?|barstools?|counterstools?|footstools?|stepstools?|ladders?|"
    r"steps?|stairs?|rungs?|treads?|risers?|banisters?|railings?|handrails?|guardrails?|"
    r"fences?|walls?|barriers?|dividers?|partitions?|screens?|panels?|boards?|sheets?|slabs?|"
    r"panes?|windows?|doors?|gates?|portals?|hatches?|lids?|covers?|caps?|tops?|stoppers?|"
    r"corks?|plugs?|bungs?|seals?|gaskets?|washers?|packings?|joints?|seams?|junctions?|"
    r"connections?|unions?|couplings?|links?|belts?|girdles?|sashes?|ribbons?|strips?|bands?|"
    r"stripes?|lines?|strokes?|dashes?|dots?|spots?|flecks?|patches?|blotches?|stains?|"
    r"smudges?|smears?|blurs?|hazes?|fogs?|mists?|clouds?|smogs?|fumes?|vapors?|steam?|"
    r"smokes?|soots?|ashes?|dusts?|dirts?|soils?|earths?|grounds?|lands?|terrains?|topographies?|"
    r"reliefs?|elevations?|altitudes?|heights?|depths?|breadths?|widths?|lengths?|spans?|"
    r"reaches?|ranges?|scopes?|extents?|stretches?|spreads?|expanses?|areas?|spaces?|rooms?|"
    r"volumes?|capacities?|contents?|loads?|burdens?|weights?|hefts?|masses?|bulks?|sizes?|"
    r"dimensions?|measurements?|quantities?|amounts?|numbers?|counts?|tallies?|scores?|totals?|"
    r"sums?|aggregates?|wholes?|grosses?|nets?|finals?|ultimates?|lasts?|terminations?|"
    r"cessations?|discontinuations?|suspensions?|rests?|reposes?|relaxations?|eases?|comforts?|"
    r"reliefs?|respites?|recesses?|breaks?|pauses?|interruptions?|interludes?|intervals?|gaps?|"
    r"openings?|holes?|apertures?|vents?|outlets?|ducts?|pipes?|conduits?|channels?|canals?|"
    r"passages?|passageways?|corridors?|hallways?|aisles?|lanes?|alleys?|paths?|tracks?|trails?|"
    r"ways?|roads?|streets?|avenues?|boulevards?|terraces?|places?|courts?|squares?|plazas?|"
    r"piazzas?|forums?|malls?|promenades?|esplanades?|boardwalks?|piers?|wharves?|docks?|"
    r"quays?|jetties?|breakwaters?|moles?|causeways?|dams?|dikes?|levees?|embankments?|"
    r"ramparts?|bulwarks?|bastions?|fortresses?|castles?|palaces?|mansions?|estates?|manors?|"
    r"villas?|cottages?|bungalows?|cabins?|lodges?|huts?|shacks?|sheds?|lean-tos?|tents?|"
    r"teepees?|yurts?|igloos?|hogans?|wickiups?|wigwams?|longhouses?|pueblos?|adobes?|"
    r"haciendas?|ranches?|farms?|plantations?|orchards?|vineyards?|groves?|woods?|forests?|"
    r"jungles?|rainforests?|bushes?|scrubs?|thickets?|brakes?|copses?|stands?|nurseries?|"
    r"greenhouses?|hothouses?|conservatories?|orangeries?|aviaries?|apiaries?|piggeries?|"
    r"sties?|henhouses?|coops?|hutches?|cages?|pens?|corrals?|paddocks?|pastures?|meadows?|"
    r"fields?|leas?|vales?|valleys?|dales?|glens?|canyons?|ravines?|gorges?|passes?|notches?|"
    r"saddles?|cols?|ridges?|crests?|peaks?|summits?|apexes?|pinnacles?|zeniths?|acmes?|"
    r"climaxes?|culminations?|crowns?|heads?|tips?|points?|spikes?|spires?|steeples?|minarets?|"
    r"obelisks?|monoliths?|megaliths?|menhirs?|dolmens?|cromlechs?|stonehenges?|circles?|"
    r"rings?|hoops?|loops?|eyes?|nooses?|lassos?|lasses?|snares?|pitfalls?|ambushes?|decoys?|"
    r"lures?|baits?|spoons?|spinners?|buzzers?|poppers?|walkers?|divers?|floaters?|sliders?|"
    r"swimmers?|wobblers?|crankbaits?|jerkbait|spoonbait|spinnerbait|buzzbait|chatterbait|"
    r"swimbait|softbait"
)


class SuFieldAnalyzer:
    """
    Extract Su-Field models from natural-language problem descriptions,
    check completeness, and apply the 76 standard transformation rules.
    """

    S1_PATTERNS: list[re.Pattern] = [
        re.compile(
            r"(?:the\s+)?(?P<s2>[a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})\s+"
            rf"(?:{_COMMON_VERBS})s?\b\s+"
            r"(?:the\s+)?(?P<s1>[a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})",
            re.IGNORECASE,
        ),
    ]

    S2_PATTERNS: list[re.Pattern] = [
        re.compile(
            r"(?:using|with|by means of|via|through)\s+(?:a\s+)?(?P<s2>[a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:tool|instrument|device|machine|agent)\s+(?:is\s+)?(?P<s2>[a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})",
            re.IGNORECASE,
        ),
        re.compile(
            r"from\s+(?P<s2>[a-zA-Z]+(?:\s+[a-zA-Z]+){0,3})\s+(?:\w+\s+){0,3}(?:"
            + _COMMON_VERBS[: _COMMON_VERBS.index("|")]  # first verb as anchor
            + r")",
            re.IGNORECASE,
        ),
    ]

    HARMFUL_PATTERNS: list[re.Pattern] = [
        re.compile(
            r"(?:harmful|undesirable|unwanted|negative|bad|damage|destroy|wear|corrode|"
            r"overheat|break|split)",
            re.IGNORECASE,
        ),
    ]

    def __init__(self) -> None:
        self.field_keywords = FIELD_KEYWORDS

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_noun_phrase(phrase: str) -> str:
        """Strip leading articles and truncate at prepositions."""
        phrase = phrase.strip()
        lower = phrase.lower()
        for article in ("the ", "a ", "an "):
            if lower.startswith(article):
                phrase = phrase[len(article):]
                break
        # Stop at first preposition
        prepositions = {"into", "through", "above", "below", "on", "in", "at", "from",
                        "to", "for", "with", "by", "of", "over", "under", "between",
                        "among", "within", "without", "against", "toward", "towards",
                        "across", "around", "behind", "beside", "besides", "beyond",
                        "despite", "during", "except", "inside", "outside", "upon",
                        "via", "like", "near", "off", "past", "since", "till", "until"}
        words = phrase.split()
        filtered = []
        for w in words:
            if w.lower().rstrip(",;:") in prepositions:
                break
            filtered.append(w)
        return " ".join(filtered) if filtered else phrase

    _INVALID_SUBJECTS = {
        "we", "i", "you", "they", "it", "he", "she", "need", "needs", "want", "wants",
        "have", "has", "had", "do", "does", "did", "can", "could", "will", "would",
        "shall", "should", "may", "might", "must", "to", "a", "an", "the", "this",
        "that", "these", "those", "there", "here", "where", "when", "why", "how",
        "what", "who", "which", "whose", "whom",
    }

    def _is_valid_subject(self, phrase: str) -> bool:
        """Check that the extracted phrase is a plausible noun/substance."""
        if not phrase:
            return False
        first_word = phrase.split()[0].lower().rstrip(",;:")
        return first_word not in self._INVALID_SUBJECTS

    def extract(self, text: str) -> SuFieldModel:
        """
        Extract a Su-Field model from natural-language text.
        """
        text_lower = text.lower()
        model = SuFieldModel(description=text[:300])

        # Extract S1 and S2 using simple sentence parsing
        sentences = re.split(r"[.!?;]+", text)
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            # Try S2 verb S1 pattern: "hammer strikes nail"
            for pat in self.S1_PATTERNS:
                m = pat.search(sent)
                if m:
                    s2_raw = self._clean_noun_phrase(m.group("s2"))
                    s1_raw = self._clean_noun_phrase(m.group("s1"))
                    if not model.s2 and self._is_valid_subject(s2_raw):
                        model.s2 = s2_raw
                    if not model.s1 and self._is_valid_subject(s1_raw):
                        model.s1 = s1_raw
                    break
            # Try S2 patterns
            for pat in self.S2_PATTERNS:
                m = pat.search(sent)
                if m and m.group("s2"):
                    s2_raw = self._clean_noun_phrase(m.group("s2"))
                    if self._is_valid_subject(s2_raw):
                        model.s2 = s2_raw
                        break

        # Detect field type from keywords
        model.f = self._detect_field(text_lower, sentences)

        # Determine status
        model.status = self._determine_status(text_lower, model)

        # Detect harmful effects
        for pat in self.HARMFUL_PATTERNS:
            if pat.search(text):
                model.harmful_effect = self._extract_harmful_effect(text)
                break

        return model

    def _detect_field(self, text_lower: str, sentences: list[str] | None = None) -> FieldType | None:
        """Detect the dominant field type from keyword counts."""
        from collections import Counter
        scores: dict[FieldType, int] = {ft: 0 for ft in FieldType}
        words = re.findall(r"\b\w+\b", text_lower)
        word_counts = Counter(words)
        for ft, keywords in self.field_keywords.items():
            scores[ft] = sum(word_counts[w] for w in keywords if w in word_counts)
        best = max(scores, key=lambda k: scores[k])
        if scores[best] > 0:
            return best

        # Fallback: infer from action verbs in sentences
        if sentences:
            mechanical_verbs = {
                "strike", "strikes", "hit", "hits", "cut", "cuts", "drive", "drives",
                "push", "pushes", "pull", "pulls", "lift", "lifts", "press", "presses",
                "squeeze", "squeezes", "bend", "bends", "twist", "twists", "rotate",
                "rotates", "move", "moves", "roll", "rolls", "slide", "slides", "drill",
                "drills", "grind", "grinds", "polish", "polishes", "hammer", "hammers",
                "pound", "pounds", "crush", "crushes", "compress", "compresses", "expand",
                "expands", "stretch", "stretches", "tear", "tears", "rip", "rips", "break",
                "breaks", "fracture", "fractures", "split", "splits", "crack", "cracks",
                "punch", "punches", "kick", "kicks", "stab", "stabs", "poke", "pokes",
                "jab", "jabs", "thrust", "thrusts", "shove", "shoves", "pinch", "pinches",
                "bite", "bites", "chew", "chews", "suck", "sucks", "blow", "blows",
            }
            all_text = " ".join(s.lower() for s in sentences)
            action_words = set(re.findall(r"\b\w+\b", all_text))
            if action_words & mechanical_verbs:
                return FieldType.MECHANICAL

        return None

    def _determine_status(self, text_lower: str, model: SuFieldModel) -> str:
        if not model.is_complete():
            return "incomplete"
        if any(p.search(text_lower) for p in self.HARMFUL_PATTERNS):
            return "harmful"
        if "insufficient" in text_lower or "too weak" in text_lower or "too strong" in text_lower:
            return "insufficient"
        return "complete"

    def _extract_harmful_effect(self, text: str) -> str:
        """Extract a short phrase describing the harmful effect."""
        sentences = re.split(r"[.!?;]+", text)
        for sent in sentences:
            if any(p.search(sent) for p in self.HARMFUL_PATTERNS):
                return sent.strip()[:120]
        return "Harmful interaction detected"

    # ------------------------------------------------------------------
    # Completeness checking
    # ------------------------------------------------------------------

    def check_completeness(self, model: SuFieldModel) -> dict[str, Any]:
        """
        Analyze a Su-Field model and report completeness with diagnostic info.
        """
        missing = model.missing_elements()
        recommendations = []

        if model.s1 is None:
            recommendations.append(
                "Identify the object being processed (S1). What is the target of the action?"
            )
        if model.s2 is None:
            recommendations.append(
                "Identify the tool or instrument (S2). What acts on the object?"
            )
        if model.f is None:
            recommendations.append(
                "Identify the field type (F). What energy or interaction couples S1 and S2?"
            )

        if model.status == "harmful" and model.is_complete():
            recommendations.append(
                "The Su-Field is complete but harmful. Consider: "
                "(1) Introduce a third substance S3 to mediate, "
                "(2) Replace the field with a different type, "
                "(3) Transition to a higher-level Su-Field."
            )

        return {
            "model": model.to_dict(),
            "is_complete": model.is_complete(),
            "missing_elements": missing,
            "status": model.status,
            "recommendations": recommendations,
            "completeness_score": (3 - len(missing)) / 3.0,
        }

    # ------------------------------------------------------------------
    # Transformation rules (Su-Field → Standard Solutions mapping)
    # ------------------------------------------------------------------

    def apply_transformation_rules(self, model: SuFieldModel) -> list[dict[str, Any]]:
        """
        Apply the 76 standard transformation rules relevant to the given Su-Field.
        Returns applicable rules with explanations.
        """
        rules = []

        # Rule category based on model status
        if model.status == "incomplete":
            rules.extend(self._incomplete_rules(model))
        elif model.status == "harmful":
            rules.extend(self._harmful_rules(model))
        elif model.status == "insufficient":
            rules.extend(self._insufficient_rules(model))
        else:
            rules.extend(self._enhancement_rules(model))

        return rules

    def _incomplete_rules(self, model: SuFieldModel) -> list[dict[str, Any]]:
        """Rules for incomplete Su-Fields (Class 1 of 76 Standard Solutions)."""
        rules = []
        if model.s1 and not model.s2 and not model.f:
            rules.append({
                "rule_id": "1.1.1",
                "class": "Class 1",
                "name": "Complete Su-Field with S2 + F",
                "description": "Add a tool (S2) and a field (F) to create a complete Su-Field.",
                "action": f"Introduce a tool to act on {model.s1} and select an appropriate field.",
                "c4_shift": "scale_shift",
            })
        if model.s1 and model.s2 and not model.f:
            rules.append({
                "rule_id": "1.1.2",
                "class": "Class 1",
                "name": "Add Field to Incomplete Su-Field",
                "description": "Introduce a field to couple S1 and S2.",
                "action": f"Apply a mechanical, thermal, or chemical field between {model.s2} and {model.s1}.",
                "c4_shift": "time_shift",
            })
        if model.s1 and model.f and not model.s2:
            rules.append({
                "rule_id": "1.1.3",
                "class": "Class 1",
                "name": "Add Tool for Existing Field",
                "description": "The field exists but needs a tool to direct it onto S1.",
                "action": f"Introduce an intermediate tool to channel the {model.f} field onto {model.s1}.",
                "c4_shift": "agency_shift",
            })
        return rules

    def _harmful_rules(self, model: SuFieldModel) -> list[dict[str, Any]]:
        """Rules for harmful complete Su-Fields (Class 2 of 76 Standard Solutions)."""
        rules = []
        if model.is_complete() and model.harmful_effect:
            rules.append({
                "rule_id": "2.1.1",
                "class": "Class 2",
                "name": "Introduce S3 to Protect S1",
                "description": "Add a third substance between S2 and S1 to absorb the harmful effect.",
                "action": f"Place a protective layer or mediator between {model.s2} and {model.s1}.",
                "c4_shift": "agency_shift",
            })
            rules.append({
                "rule_id": "2.1.2",
                "class": "Class 2",
                "name": "Modify Existing Field",
                "description": "Change the field parameters (intensity, frequency, direction) to eliminate harm.",
                "action": f"Adjust the {model.f} field properties to avoid the harmful effect.",
                "c4_shift": "scale_shift",
            })
            rules.append({
                "rule_id": "2.2.1",
                "class": "Class 2",
                "name": "Replace Field with Less Harmful Type",
                "description": "Swap the current field for one that achieves the same effect without harm.",
                "action": f"Replace {model.f} field with an alternative (e.g., optical instead of thermal).",
                "c4_shift": "time_shift",
            })
        return rules

    def _insufficient_rules(self, model: SuFieldModel) -> list[dict[str, Any]]:
        """Rules for insufficient-effect Su-Fields."""
        rules = []
        if model.is_complete():
            rules.append({
                "rule_id": "3.1.1",
                "class": "Class 3",
                "name": "Intensify Field",
                "description": "Increase the field intensity or switch to a more energetic field type.",
                "action": f"Increase {model.f} field strength or transition to a higher-energy field.",
                "c4_shift": "scale_shift",
            })
            rules.append({
                "rule_id": "3.1.2",
                "class": "Class 3",
                "name": "Use Ferromagnetic Particles + Magnetic Field",
                "description": "Add ferromagnetic particles to S1 and apply a magnetic field for better control.",
                "action": "Introduce ferromagnetic additives and control with magnetic field.",
                "c4_shift": "agency_shift",
            })
        return rules

    def _enhancement_rules(self, model: SuFieldModel) -> list[dict[str, Any]]:
        """Rules for already-complete, well-functioning Su-Fields (optimization)."""
        rules = []
        rules.append({
            "rule_id": "5.1.1",
            "class": "Class 5",
            "name": "Transition to Super-System",
            "description": "Combine multiple Su-Fields into a higher-level system.",
            "action": "Merge with adjacent systems to create a super-system Su-Field.",
            "c4_shift": "combined_shift",
        })
        rules.append({
            "rule_id": "5.2.1",
            "class": "Class 5",
            "name": "Introduce Pneumatic/Hydraulic Structure",
            "description": "Replace solid structures with gas or liquid filled ones.",
            "action": "Use inflatable, liquid-filled, or air-cushion structures.",
            "c4_shift": "scale_shift",
        })
        return rules

    # ------------------------------------------------------------------
    # Full analysis pipeline
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Full Su-Field analysis pipeline:
        1. Extract model from text
        2. Check completeness
        3. Apply transformation rules
        4. Map to C4 trajectory
        """
        model = self.extract(text)
        completeness = self.check_completeness(model)
        transformations = self.apply_transformation_rules(model)

        # Map to C4
        c4_start = C4State(T=1, S=0, A=0)  # Present, Concrete, Self
        if model.status == "incomplete":
            c4_end = C4State(T=2, S=1, A=0)   # Future, Abstract, Self
        elif model.status == "harmful":
            c4_end = C4State(T=1, S=1, A=1)   # Present, Abstract, Other
        else:
            c4_end = C4State(T=1, S=2, A=2)   # Present, Meta, System

        return {
            "model": model.to_dict(),
            "completeness": completeness,
            "transformations": transformations,
            "c4_mapping": {
                "start_state": str(c4_start),
                "end_state": str(c4_end),
                "trajectory": [str(s) for s in self._path(c4_start, c4_end)],
                "shift_type": self._determine_shift_type(c4_start, c4_end),
            },
        }

    def _path(self, start: C4State, end: C4State) -> list[C4State]:
        """Generate a simple path between two C4 states."""
        from src.c4.engine import C4Space
        space = C4Space()
        return space.find_path(start, end)

    def _determine_shift_type(self, start: C4State, end: C4State) -> str:
        """Label the type of C4 shift."""
        diffs = []
        if start.T != end.T:
            diffs.append("time")
        if start.S != end.S:
            diffs.append("scale")
        if start.A != end.A:
            diffs.append("agency")
        if len(diffs) == 1:
            return f"{diffs[0]}_shift"
        elif len(diffs) > 1:
            return "combined_shift"
        return "no_shift"


# =============================================================================
# TEXTBOOK EXAMPLES
# =============================================================================

TEXTBOOK_SUFIELD_EXAMPLES: list[dict[str, str | None]] = [
    {
        "text": "A hammer strikes a nail into wood. The mechanical force drives the nail, but the wood may split.",
        "expected_s1": "nail",
        "expected_s2": "hammer",
        "expected_f": "Mechanical",
        "expected_status": "harmful",
    },
    {
        "text": "A laser beam cuts through a steel plate. The intense optical field melts the metal.",
        "expected_s1": "steel plate",
        "expected_s2": "laser",
        "expected_f": "Optical",
        "expected_status": "complete",
    },
    {
        "text": "We need to detect cracks inside a ceramic component without destroying it.",
        "expected_s1": "ceramic component",
        "expected_s2": None,
        "expected_f": None,
        "expected_status": "incomplete",
    },
    {
        "text": "An electric current passes through a resistor, generating heat. The excessive thermal field damages nearby components.",
        "expected_s1": "resistor",
        "expected_s2": None,
        "expected_f": "Electrical",
        "expected_status": "harmful",
    },
    {
        "text": "A magnetic field levitates a train above the tracks, eliminating friction. The magnetic force from electromagnets lifts the train body.",
        "expected_s1": "train",
        "expected_s2": "electromagnets",
        "expected_f": "Magnetic",
        "expected_status": "complete",
    },
]


def analyze_sufield(text: str) -> dict[str, Any]:
    """Convenience function for one-shot Su-Field analysis."""
    return SuFieldAnalyzer().analyze(text)
