"""
TURBO-CDI: C4-TRIZ Bridge v4.0
Mapping 40 TRIZ principles ↔ 27 C4 operators

TRIZ (Theory of Inventive Problem Solving) - Altshuller
40 Principles + 76 Standard Solutions + ARIZ

C4 (Cognitive Coordinate Cube) - Z₃³ = 27 operators
Time × Scale × Agency dimensions

This bridge enables:
1. Convert TRIZ principles to C4 operator sequences
2. Convert C4 paths to TRIZ principle recommendations
3. Unified contradiction resolution framework
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class TRIZPrinciple(Enum):
    """40 TRIZ Inventive Principles."""

    SEGMENTATION = 1
    EXTRACTION = 2
    LOCAL_QUALITY = 3
    ASYMMETRY = 4
    MERGING = 5
    UNIVERSALITY = 6
    NESTING = 7
    COUNTERWEIGHT = 8
    PRIOR_COUNTERACTION = 9
    PRIOR_ACTION = 10
    CUSHION = 11
    EQUIPOTENTIALITY = 12
    INVERSION = 13
    SPHEROIDAL = 14
    DYNAMICS = 15
    PARTIAL_ACTION = 16
    DIMENSIONAL_CHANGE = 17
    MECHANICAL_VIBRATION = 18
    PERIODIC_ACTION = 19
    CONTINUITY = 20
    RUSHING = 21
    TURN_HARM_INTO_BENEFIT = 22
    FEEDBACK = 23
    MEDIATOR = 24
    SELF_SERVICE = 25
    COPYING = 26
    CHEAP_SHORT_LIVING = 27
    MECHANICS_SUBSTITUTION = 28
    PNEUMATICS_HYDRAULICS = 29
    FLEXIBLE_MEMBRANES = 30
    POROUS_MATERIALS = 31
    COLOR_CHANGE = 32
    HOMOGENEITY = 33
    REJECTING_REGENERATING = 34
    PHASE_TRANSITIONS = 35
    THERMAL_EXPANSION = 36
    STRONG_OXIDANTS = 37
    INERT_ENVIRONMENT = 38
    COMPOSITE_MATERIALS = 39


@dataclass
class TRIZPrincipleInfo:
    """Full information about a TRIZ principle."""

    number: int
    name: str
    description: str
    examples: List[str]
    typical_contradictions: List[str]


# ═══════════════════════════════════════════════════════════════════
# TRIZ PRINCIPLES DATABASE
# ═══════════════════════════════════════════════════════════════════

TRIZ_PRINCIPLES: Dict[int, TRIZPrincipleInfo] = {
    1: TRIZPrincipleInfo(
        1,
        "Segmentation",
        "Divide an object into independent parts; make it modular; increase segmentation",
        ["Multi-blade razor", "Modular furniture", "Distributed computing"],
        ["whole vs parts", "unity vs modularity"],
    ),
    2: TRIZPrincipleInfo(
        2,
        "Extraction",
        "Extract disturbing part; extract essential part",
        [
            "Noise canceling headphones",
            "Active noise reduction",
            "Essential oils extraction",
        ],
        ["presence vs absence", "signal vs noise"],
    ),
    3: TRIZPrincipleInfo(
        3,
        "Local Quality",
        "Different parts should have different functions; each part at optimal conditions",
        [
            "Multi-material objects",
            "Functionally graded materials",
            "Specialized tools",
        ],
        ["uniformity vs specialization", "same vs different"],
    ),
    4: TRIZPrincipleInfo(
        4,
        "Asymmetry",
        "Replace symmetrical with asymmetrical; increase asymmetry",
        ["Asymmetric tires", "Ergonomic handles", "One-way valves"],
        ["symmetry vs asymmetry", "balance vs imbalance"],
    ),
    5: TRIZPrincipleInfo(
        5,
        "Merging",
        "Merge similar objects; merge operations in time",
        ["Multi-function tools", "Swiss army knife", "Just-in-time manufacturing"],
        ["separate vs combined", "sequential vs parallel"],
    ),
    6: TRIZPrincipleInfo(
        6,
        "Universality",
        "Object performs multiple functions; eliminate need for other objects",
        ["Smartphone", "Universal remote", "Multi-tool"],
        ["specialized vs universal", "one vs many"],
    ),
    7: TRIZPrincipleInfo(
        7,
        "Nesting",
        "Place one object inside another; one object passes through cavity of another",
        ["Russian dolls", "Telescoping antenna", "Nested storage"],
        ["external vs internal", "separate vs contained"],
    ),
    8: TRIZPrincipleInfo(
        8,
        "Counterweight",
        "Compensate for weight with aerodynamic/hydrodynamic forces; merge with counterweight",
        ["Wings generate lift", "Counterbalanced crane", "Stabilizers"],
        ["heavy vs light", "weight vs lift"],
    ),
    9: TRIZPrincipleInfo(
        9,
        "Prior Counteraction",
        "Pre-load counter-tension to compensate later stress",
        ["Pre-stressed concrete", "Bowed musical instruments", "Opposing springs"],
        ["before vs after", "passive vs active"],
    ),
    10: TRIZPrincipleInfo(
        10,
        "Prior Action",
        "Pre-complete required changes; pre-arrange objects",
        ["Pre-pasted wallpaper", "Pre-fabricated components", "Pre-heating"],
        ["during vs before", "on-demand vs prepared"],
    ),
    11: TRIZPrincipleInfo(
        11,
        "Cushion",
        "Compensate for low reliability with emergency measures",
        ["Safety margins", "Backup systems", "Airbags"],
        ["reliable vs unreliable", "safe vs dangerous"],
    ),
    12: TRIZPrincipleInfo(
        12,
        "Equipotentiality",
        "Change operating conditions to eliminate need for raise/lower",
        [
            "Hydraulic lifts at loading dock",
            "Assembly at constant height",
            "Rotating workshops",
        ],
        ["high vs low", "up vs down"],
    ),
    13: TRIZPrincipleInfo(
        13,
        "Inversion",
        "Do opposite; make movable fixed and fixed movable; turn upside down",
        [
            "Inverted processing",
            "Moving part stationary, stationary part moving",
            "Vertical gardens",
        ],
        ["active vs passive", "top vs bottom"],
    ),
    14: TRIZPrincipleInfo(
        14,
        "Spheroidality",
        "Replace linear with curved; use rollers, balls, spirals; go to 3D",
        ["Ball bearings", "Curved windshields", "Spiral staircases"],
        ["linear vs curved", "flat vs round"],
    ),
    15: TRIZPrincipleInfo(
        15,
        "Dynamics",
        "Allow characteristics to change; divide into elements that move; increase flexibility",
        ["Adjustable desk", "Flexible manufacturing", "Modular architecture"],
        ["static vs dynamic", "rigid vs flexible"],
    ),
    16: TRIZPrincipleInfo(
        16,
        "Partial/Excessive Action",
        "If exact solution is hard, allow slightly more/less then adjust",
        ["Overspray then mask", "Overfill then level", "Approximation then refinement"],
        ["exact vs approximate", "precise vs loose"],
    ),
    17: TRIZPrincipleInfo(
        17,
        "Dimensional Change",
        "Change 1D to 2D to 3D; use multiple layers; tilt/reorient",
        ["High-rise buildings", "Multi-layer PCBs", "3D printing"],
        ["1D vs 2D vs 3D", "flat vs volumetric"],
    ),
    18: TRIZPrincipleInfo(
        18,
        "Mechanical Vibration",
        "Set in oscillation; increase frequency; use ultrasonic; combine with piezo",
        ["Vibrating conveyor", "Ultrasonic cleaning", "Vibration alerts"],
        ["static vs vibrating", "silent vs noisy"],
    ),
    19: TRIZPrincipleInfo(
        19,
        "Periodic Action",
        "Replace continuous with periodic; change period; use pauses",
        ["Pulsed light", "Intermittent wipers", "PWM control"],
        ["continuous vs intermittent", "always vs sometimes"],
    ),
    20: TRIZPrincipleInfo(
        20,
        "Continuity",
        "Work continuously; eliminate idle moments; make all parts work at full capacity",
        ["Continuous casting", "24/7 operations", "Pipeline processing"],
        ["intermittent vs continuous", "idle vs busy"],
    ),
    21: TRIZPrincipleInfo(
        21,
        "Rushing Through",
        "Perform harmful operation at high speed",
        ["Fast cutting", "Rapid prototyping", "Quick pass heating"],
        ["slow vs fast", "gentle vs aggressive"],
    ),
    22: TRIZPrincipleInfo(
        22,
        "Turn Harm into Benefit",
        "Use harmful factors to achieve positive effect; eliminate by repeating",
        ["Waste heat recovery", "Pressure from explosion", "Recycling waste"],
        ["harmful vs beneficial", "waste vs resource"],
    ),
    23: TRIZPrincipleInfo(
        23,
        "Feedback",
        "Introduce feedback; improve existing feedback; reverse feedback",
        ["Thermostat", "Cruise control", "Self-regulating systems"],
        ["open loop vs closed loop", "uncontrolled vs controlled"],
    ),
    24: TRIZPrincipleInfo(
        24,
        "Mediator",
        "Use intermediate object; temporarily merge then separate",
        ["Catalysts", "Adapters", "Temporary couplings"],
        ["direct vs indirect", "connected vs separated"],
    ),
    25: TRIZPrincipleInfo(
        25,
        "Self-Service",
        "Object serves itself; use waste resources",
        ["Self-healing materials", "Self-cleaning surfaces", "Regenerative braking"],
        ["external vs internal", "passive vs self-sufficient"],
    ),
    26: TRIZPrincipleInfo(
        26,
        "Copying",
        "Use simplified copy; replace with optical copy; IR/UV copies",
        ["Virtual prototyping", "Digital twins", "Simulations"],
        ["real vs virtual", "physical vs digital"],
    ),
    27: TRIZPrincipleInfo(
        27,
        "Cheap Short-Living",
        "Replace expensive with cheap disposable; sacrifice auxiliary",
        ["Disposable filters", "Single-use medical devices", "Consumable tooling"],
        ["durable vs disposable", "expensive vs cheap"],
    ),
    28: TRIZPrincipleInfo(
        28,
        "Mechanics Substitution",
        "Replace mechanical with sensory/optical/thermal/field",
        ["Electronic controls", "Optical sensors", "Magnetic levitation"],
        ["mechanical vs non-mechanical", "physical vs field-based"],
    ),
    29: TRIZPrincipleInfo(
        29,
        "Pneumatics/Hydraulics",
        "Use gas/liquid instead of solid parts; inflatable/fillable",
        ["Air bearings", "Hydraulic actuators", "Inflatable structures"],
        ["solid vs fluid", "rigid vs compliant"],
    ),
    30: TRIZPrincipleInfo(
        30,
        "Flexible Membranes",
        "Replace with flexible membranes; use isolating membranes; pre-stretch",
        ["Membrane filters", "Flexible packaging", "Pre-stressed membranes"],
        ["rigid vs flexible", "thick vs thin"],
    ),
    31: TRIZPrincipleInfo(
        31,
        "Porous Materials",
        "Make porous; add additive; use capillary structures",
        ["Foam materials", "Porous metals", "Wicking structures"],
        ["solid vs porous", "dense vs airy"],
    ),
    32: TRIZPrincipleInfo(
        32,
        "Color Change",
        "Change color; change transparency; add luminescent; use UV/IR",
        ["Photochromic lenses", "Mood lighting", "Heat-sensitive materials"],
        ["opaque vs transparent", "fixed vs changing"],
    ),
    33: TRIZPrincipleInfo(
        33,
        "Homogeneity",
        "Make interacting objects of same material",
        ["Similar material joints", "Welding same metals", "Compatible materials"],
        ["different vs same", "heterogeneous vs homogeneous"],
    ),
    34: TRIZPrincipleInfo(
        34,
        "Rejecting/Regenerating",
        "Object rejects/rebuilds parts; already used portion rejected",
        ["Self-sharpening blades", "Ablative cooling", "Shedding surfaces"],
        ["permanent vs temporary", "conserved vs consumed"],
    ),
    35: TRIZPrincipleInfo(
        35,
        "Phase Transitions",
        "Use phenomena accompanying phase changes; volume change; heat absorption",
        ["Phase change materials", "Heat pipes", "Freeze-thaw cycles"],
        ["solid vs liquid vs gas", "stable vs changing"],
    ),
    36: TRIZPrincipleInfo(
        36,
        "Thermal Expansion",
        "Use thermal expansion/contraction; multiple materials with different rates",
        ["Bimetallic strips", "Thermal actuators", "Expansion joints"],
        ["hot vs cold", "expanded vs contracted"],
    ),
    37: TRIZPrincipleInfo(
        37,
        "Strong Oxidants",
        "Replace normal air with oxygen; ionized radiation; ozone",
        ["Oxygen enrichment", "Plasma processing", "Ozonation"],
        ["normal vs enhanced", "passive vs active"],
    ),
    38: TRIZPrincipleInfo(
        38,
        "Inert Environment",
        "Replace normal with inert; neutral additives; vacuum",
        ["Inert gas welding", "Vacuum processing", "Protective atmospheres"],
        ["reactive vs inert", "present vs absent"],
    ),
    39: TRIZPrincipleInfo(
        39,
        "Composite Materials",
        "Change from single to composite; each for different property",
        ["Fiber-reinforced plastics", "Metal matrix composites", "Hybrid materials"],
        ["simple vs composite", "pure vs alloyed"],
    ),
}


# ═══════════════════════════════════════════════════════════════════
# C4-TRIZ MAPPING
# ═══════════════════════════════════════════════════════════════════

# Mapping: Which C4 operators activate which TRIZ principles
# Format: C4 operator → List of TRIZ principle numbers

C4_TO_TRIZ_MAPPING: Dict[str, List[int]] = {
    # Temporal operators (Time axis)
    "tau+": [10, 19, 20, 21],  # Prior Action, Periodic, Continuity, Rushing
    "tau-": [9, 22, 34],  # Prior Counteraction, Harm→Benefit, Rejecting
    "tau_sigma": [5, 7, 19],  # Merging, Nesting, Periodic
    "tau_delta": [8, 12, 36],  # Counterweight, Equipotentiality, Thermal Expansion
    "tau_rho": [23, 25],  # Feedback, Self-Service
    # Scale operators (Scale axis)
    "sigma": [1, 3, 17, 31],  # Segmentation, Local Quality, Dimensional, Porous
    "sigma_iota": [6, 26, 33],  # Universality, Copying, Homogeneity
    "lambda_sigma": [2, 28, 30],  # Extraction, Mech Substitution, Membranes
    "kappa_sigma": [14, 39],  # Spheroidality, Composites
    "sigma_phi": [4, 15, 32],  # Asymmetry, Dynamics, Color Change
    # Transformation operators
    "delta": [13, 18, 28],  # Inversion, Vibration, Mech Substitution
    "delta_iota": [24, 29],  # Mediator, Pneumatics/Hydraulics
    "delta_phi": [11, 35],  # Cushion, Phase Transitions
    # Perspective operators (Agency axis)
    "rho": [16, 27],  # Partial Action, Cheap Short-Living
    "rho_tau": [21, 37],  # Rushing, Strong Oxidants
    "rho_iota": [25, 26],  # Self-Service, Copying
    "rho_phi": [38],  # Inert Environment
    # Integration operators
    "iota": [5, 6, 24],  # Merging, Universality, Mediator
    "lambda+": [17, 39],  # Dimensional, Composites
    "lambda-": [7],  # Nesting
    "iota_lambda": [3, 33],  # Local Quality, Homogeneity
    "lambda_iota": [29, 30],  # Pneumatics, Membranes
    "kappa+": [8, 12],  # Counterweight, Equipotentiality
    "kappa-": [9],  # Prior Counteraction
    "lambda_kappa": [36],  # Thermal Expansion
    # Composition operators (phi series)
    "kappa_phi": [37, 38],  # Oxidants, Inert
    "mu_phi": [22, 35],  # Harm→Benefit, Phase Transitions
}

# Reverse mapping: TRIZ principle → C4 operators that activate it
TRIZ_TO_C4_MAPPING: Dict[int, List[str]] = {}


def _build_reverse_mapping():
    """Build reverse mapping from C4→TRIZ."""
    global TRIZ_TO_C4_MAPPING
    for operator, principles in C4_TO_TRIZ_MAPPING.items():
        for principle in principles:
            if principle not in TRIZ_TO_C4_MAPPING:
                TRIZ_TO_C4_MAPPING[principle] = []
            TRIZ_TO_C4_MAPPING[principle].append(operator)


_build_reverse_mapping()


# ═══════════════════════════════════════════════════════════════════
# CONTRADICTION MATRIX (SIMPLIFIED)
# ═══════════════════════════════════════════════════════════════════

# Common engineering contradictions and recommended TRIZ principles
CONTRADICTION_MATRIX: Dict[Tuple[str, str], List[int]] = {
    # Format: (worsening_parameter, improving_parameter) → recommended principles
    # Speed-related
    ("speed", "accuracy"): [11, 16, 23, 28],
    ("accuracy", "speed"): [11, 21, 28, 32],
    ("speed", "reliability"): [11, 21, 23, 35],
    ("reliability", "speed"): [21, 23, 28, 35],
    ("speed", "battery_life"): [19, 23, 28, 35],
    ("battery_life", "speed"): [2, 23, 28, 35],
    # Physical properties
    ("strength", "weight"): [1, 8, 15, 29, 40],
    ("weight", "strength"): [1, 8, 15, 29, 40],
    ("power", "size"): [1, 15, 17, 29],
    ("size", "power"): [1, 15, 17, 29],
    ("temperature", "reliability"): [2, 3, 35, 38],
    ("reliability", "temperature"): [35, 36, 38],
    # System complexity
    ("complexity", "ease_of_use"): [1, 6, 26, 32],
    ("ease_of_use", "complexity"): [1, 6, 26, 32],
    ("productivity", "precision"): [16, 19, 23, 35],
    ("precision", "productivity"): [16, 19, 23, 35],
    ("automation", "adaptability"): [15, 23, 25, 35],
    ("adaptability", "automation"): [15, 23, 25, 35],
    # Energy
    ("energy_loss", "speed"): [19, 20, 22, 35],
    ("speed", "energy_loss"): [19, 20, 22, 35],
    ("cost", "performance"): [6, 27, 28, 29],
    ("performance", "cost"): [6, 27, 28, 29],
    # User experience
    ("security", "convenience"): [3, 11, 23, 32],
    ("convenience", "security"): [3, 6, 23, 32],
    ("features", "simplicity"): [1, 3, 6, 26],
    ("simplicity", "features"): [1, 3, 6, 26],
}


# ═══════════════════════════════════════════════════════════════════
# C4-TRIZ BRIDGE CLASS
# ═══════════════════════════════════════════════════════════════════


class C4TrizBridge:
    """
    Bridge between C4 Cognitive Geometry and TRIZ methodology.

    Provides bidirectional translation:
    - C4 path → TRIZ principles
    - TRIZ principles → C4 operators
    - Contradiction → C4+TRIZ solution

    Loads mappings from config/c4_triz_mappings.yaml if available,
    otherwise falls back to hardcoded defaults.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.principles = TRIZ_PRINCIPLES

        # Try to load from YAML config
        yaml_mappings = self._load_yaml_config(config_path)

        if yaml_mappings:
            self.c4_to_triz = yaml_mappings["c4_to_triz"]
            self.triz_to_c4 = yaml_mappings["triz_to_c4"]
            self.contradiction_matrix = yaml_mappings["contradictions"]
            self._config_loaded = True
        else:
            # Fallback to hardcoded defaults
            self.c4_to_triz = C4_TO_TRIZ_MAPPING
            self.triz_to_c4 = TRIZ_TO_C4_MAPPING
            self.contradiction_matrix = CONTRADICTION_MATRIX
            self._config_loaded = False

    def _load_yaml_config(self, config_path: Optional[str]) -> Optional[Dict]:
        """Load C4-TRIZ mappings from YAML config file."""
        try:
            import yaml
        except ImportError:
            print("⚠️  PyYAML not installed. Using hardcoded mappings.")
            return None

        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "c4_triz_mappings.yaml"
            )

        config_path = Path(config_path)

        if not config_path.exists():
            print(f"⚠️  Config not found: {config_path}. Using hardcoded mappings.")
            return None

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            # Parse mappings
            c4_to_triz = {}
            for op_name, mapping in config.get("mappings", {}).items():
                c4_to_triz[op_name] = mapping.get("principles", [])

            # Parse reverse mappings
            triz_to_c4 = {}
            for principle_num, operators in config.get("reverse_mappings", {}).items():
                triz_to_c4[int(principle_num)] = operators

            # Parse contradictions
            contradictions = {}
            for name, contradiction in config.get("contradictions", {}).items():
                key = (contradiction["improve"], contradiction["worsen"])
                contradictions[key] = contradiction.get("principles", [])
                # Add reverse mapping
                reverse_key = (contradiction["worsen"], contradiction["improve"])
                contradictions[reverse_key] = contradiction.get("principles", [])

            print(f"✓ Loaded C4-TRIZ mappings from {config_path}")
            return {
                "c4_to_triz": c4_to_triz,
                "triz_to_c4": triz_to_c4,
                "contradictions": contradictions,
            }

        except Exception as e:
            print(f"⚠️  Failed to load YAML config: {e}. Using hardcoded mappings.")
            return None

    @property
    def using_config(self) -> bool:
        """Check if using external YAML config."""
        return self._config_loaded

    def get_triz_for_c4_path(self, c4_path: List[str]) -> List[int]:
        """
        Get TRIZ principles recommended by a C4 path.

        Example:
            bridge.get_triz_for_c4_path(["tau+", "sigma", "delta"])
            => [10, 19, 20, 21, 1, 3, 17, 31, 13, 18, 28]
        """
        principles = set()
        for operator in c4_path:
            if operator in self.c4_to_triz:
                principles.update(self.c4_to_triz[operator])
        return sorted(list(principles))

    def get_c4_for_triz_principle(self, principle_num: int) -> List[str]:
        """
        Get C4 operators that map to a TRIZ principle.

        Example:
            bridge.get_c4_for_triz_principle(15)  # Dynamics
            => ["sigma_phi"]
        """
        return self.triz_to_c4.get(principle_num, [])

    def get_principle_info(self, principle_num: int) -> Optional[TRIZPrincipleInfo]:
        """Get full info about a TRIZ principle."""
        return self.principles.get(principle_num)

    def recommend_for_contradiction(
        self,
        parameter_to_improve: str,
        parameter_that_worsens: str,
    ) -> Dict[str, any]:
        """
        Get C4+TRIZ recommendations for a contradiction.

        Example:
            bridge.recommend_for_contradiction("speed", "accuracy")
        """
        # Look up in contradiction matrix
        key = (parameter_that_worsens, parameter_to_improve)
        triz_recommendations = self.contradiction_matrix.get(key, [])

        # Map to C4 operators
        c4_recommendations = []
        for principle in triz_recommendations:
            c4_ops = self.get_c4_for_triz_principle(principle)
            c4_recommendations.extend(c4_ops)

        # Remove duplicates while preserving order
        c4_recommendations = list(dict.fromkeys(c4_recommendations))

        return {
            "triz_principles": triz_recommendations,
            "c4_operators": c4_recommendations,
            "principle_details": [
                self.get_principle_info(p) for p in triz_recommendations
            ],
        }

    def explain_bridge(self, c4_operator: str, triz_principle: int) -> str:
        """
        Explain the conceptual bridge between a C4 operator and TRIZ principle.
        """
        triz_info = self.get_principle_info(triz_principle)
        if not triz_info:
            return f"Unknown TRIZ principle: {triz_principle}"

        explanations = {
            (
                "tau+",
                10,
            ): "tau+ (temporal forward) enables Prior Action by moving actions before they're needed",
            (
                "sigma",
                1,
            ): "sigma (abstraction) enables Segmentation by viewing the system as divisible parts",
            (
                "delta",
                13,
            ): "delta (temporal jump) enables Inversion by changing temporal order",
            (
                "iota",
                24,
            ): "iota (perspective integration) enables Mediator by combining viewpoints",
            (
                "lambda+",
                17,
            ): "lambda+ (scale up) enables Dimensional Change by expanding to higher dimensions",
            (
                "rho",
                16,
            ): "rho (other perspective) enables Partial Action through external observation",
        }

        return explanations.get(
            (c4_operator, triz_principle),
            f"{c4_operator} conceptually activates {triz_info.name} through dimensional resonance",
        )

    def generate_c4_triz_path(
        self,
        problem: str,
        contradiction: Tuple[str, str],
    ) -> Dict[str, any]:
        """
        Generate complete solution path using C4+TRIZ.

        Returns a synthesis of both methodologies.
        """
        # Get recommendations
        recs = self.recommend_for_contradiction(contradiction[0], contradiction[1])

        # Build optimal C4 path from recommendations
        c4_operators = recs["c4_operators"][:6]  # Max 6 (Theorem 11)

        # Get full TRIZ principles for this path
        triz_principles = self.get_triz_for_c4_path(c4_operators)

        # Build explanation
        steps = []
        for i, (op, triz) in enumerate(
            zip(c4_operators, triz_principles[: len(c4_operators)])
        ):
            triz_info = self.get_principle_info(triz)
            steps.append(
                {
                    "step": i + 1,
                    "c4_operator": op,
                    "triz_principle": triz,
                    "triz_name": triz_info.name if triz_info else "Unknown",
                    "explanation": self.explain_bridge(op, triz),
                }
            )

        return {
            "problem": problem,
            "contradiction": contradiction,
            "c4_path": c4_operators,
            "triz_principles": triz_principles,
            "steps": steps,
            "estimated_steps": len(steps),
            "within_theorem_11": len(steps) <= 6,
        }

    def get_all_principles(self) -> List[TRIZPrincipleInfo]:
        """Get all 40 TRIZ principles."""
        return list(self.principles.values())

    def search_principles(self, query: str) -> List[TRIZPrincipleInfo]:
        """Search principles by keyword."""
        query = query.lower()
        results = []
        for p in self.principles.values():
            if (
                query in p.name.lower()
                or query in p.description.lower()
                or any(query in ex.lower() for ex in p.examples)
            ):
                results.append(p)
        return results


# ═══════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════

_bridge: Optional[C4TrizBridge] = None


def get_c4_triz_bridge() -> C4TrizBridge:
    """Get singleton C4-TRIZ bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = C4TrizBridge()
    return _bridge
