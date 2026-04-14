"""
TURBO-CDI v8.0 - Wholeness Validator
Phase 6: Living Structure (Alexander)

Validates "living structure" in transformations using Alexander's 15 properties:
- Levels of scale, Strong centers, Boundaries, Alternating repetition
- Positive space, Good shape, Local symmetries, Deep interlock
- Contrast, Gradients, Roughness, Echoes, The void, Simplicity, Not-separateness
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from datetime import datetime


class LivingProperty(Enum):
    """Alexander's 15 fundamental properties of living structure"""

    LEVELS_OF_SCALE = "levels_of_scale"
    STRONG_CENTERS = "strong_centers"
    BOUNDARIES = "boundaries"
    ALTERNATING_REPETITION = "alternating_repetition"
    POSITIVE_SPACE = "positive_space"
    GOOD_SHAPE = "good_shape"
    LOCAL_SYMMETRIES = "local_symmetries"
    DEEP_INTERLOCK = "deep_interlock"
    CONTRAST = "contrast"
    GRADIENTS = "gradients"
    ROUGHNESS = "roughness"
    ECHOES = "echoes"
    THE_VOID = "the_void"
    SIMPLICITY = "simplicity"
    NOT_SEPARATENESS = "not_separateness"


@dataclass
class PropertyAssessment:
    """Assessment of a single living property"""

    property_type: LivingProperty
    present: bool
    strength: float  # 0-1, how strongly present
    evidence: List[str]  # What indicates this property
    recommendations: List[str]  # How to strengthen


@dataclass
class WholenessReport:
    """Complete wholeness assessment"""

    timestamp: datetime
    overall_score: float  # 0-1, overall living structure score
    properties_present: int  # Count of present properties
    total_properties: int  # Always 15
    property_assessments: List[PropertyAssessment]
    life_score: float  # 0-1, degree of "life" or wholeness
    center_analysis: Dict[str, Any]  # Strong/weak centers
    wholeness_recommendations: List[str]


class WholenessValidator:
    """
    Validates living structure in transformation plans.

    Based on Christopher Alexander's theory of centers and wholeness.
    A transformation has "life" to the degree it manifests the 15 properties.

    Key concepts:
    - Wholeness: The degree of harmony in a structure
    - Centers: Distinct foci of life/energy in the structure
    - Living structure: Configurations that generate life/feeling
    """

    def __init__(self):
        self.properties = list(LivingProperty)
        self._center_detector = CenterDetector()

    def assess_transformation(self, plan: Dict[str, Any]) -> WholenessReport:
        """
        Assess living structure of a transformation plan.

        Args:
            plan: Transformation plan with path, operations, etc.

        Returns:
            WholenessReport with full assessment
        """
        assessments = []

        # Assess each of the 15 properties
        assessments.append(self._assess_levels_of_scale(plan))
        assessments.append(self._assess_strong_centers(plan))
        assessments.append(self._assess_boundaries(plan))
        assessments.append(self._assess_alternating_repetition(plan))
        assessments.append(self._assess_positive_space(plan))
        assessments.append(self._assess_good_shape(plan))
        assessments.append(self._assess_local_symmetries(plan))
        assessments.append(self._assess_deep_interlock(plan))
        assessments.append(self._assess_contrast(plan))
        assessments.append(self._assess_gradients(plan))
        assessments.append(self._assess_roughness(plan))
        assessments.append(self._assess_echoes(plan))
        assessments.append(self._assess_the_void(plan))
        assessments.append(self._assess_simplicity(plan))
        assessments.append(self._assess_not_separateness(plan))

        # Calculate overall score
        present_count = sum(1 for a in assessments if a.present)
        avg_strength = sum(a.strength for a in assessments) / len(assessments)

        # Life score combines presence and strength
        presence_ratio = present_count / len(assessments)
        life_score = (presence_ratio * 0.5) + (avg_strength * 0.5)

        # Analyze centers
        center_analysis = self._center_detector.analyze(plan)

        # Generate recommendations
        recommendations = self._generate_wholeness_recommendations(assessments)

        return WholenessReport(
            timestamp=datetime.now(),
            overall_score=round(avg_strength, 3),
            properties_present=present_count,
            total_properties=len(assessments),
            property_assessments=assessments,
            life_score=round(life_score, 3),
            center_analysis=center_analysis,
            wholeness_recommendations=recommendations,
        )

    # ═════════════════════════════════════════════════════════════════════════════
    # INDIVIDUAL PROPERTY ASSESSMENTS
    # ═════════════════════════════════════════════════════════════════════════════

    def _assess_levels_of_scale(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess levels of scale property.

        Living structures have a hierarchy of scales from large to small.
        """
        path = plan.get("path", [])

        # Check if path has varying scales
        scales = set()
        for step in path:
            if isinstance(step, dict):
                # Extract scale from C4 state
                from_state = step.get("from", "")
                if "0" in from_state:
                    scales.add("concrete")
                if "1" in from_state:
                    scales.add("abstract")
                if "2" in from_state:
                    scales.add("meta")

        n_scales = len(scales)
        present = n_scales >= 2
        strength = n_scales / 3  # Max 3 scales

        evidence = (
            [f"Found {n_scales} distinct scales"] if n_scales > 0 else ["Single scale"]
        )
        recommendations = (
            ["Include transformations across all three scales"] if n_scales < 3 else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.LEVELS_OF_SCALE,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_strong_centers(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess strong centers property.

        Living structures have focal points (centers) that attract attention/energy.
        """
        path = plan.get("path", [])

        # Check for distinct focal points in path
        # A strong transformation has clear beginning, middle, end
        has_beginning = len(path) > 0
        has_middle = len(path) >= 3
        has_end = len(path) > 1

        n_centers = sum([has_beginning, has_middle, has_end])
        present = n_centers >= 2
        strength = n_centers / 3

        evidence = []
        if has_beginning:
            evidence.append("Clear starting point")
        if has_middle:
            evidence.append("Defined middle phase")
        if has_end:
            evidence.append("Clear end state")

        recommendations = ["Add more distinct phases"] if n_centers < 3 else []

        return PropertyAssessment(
            property_type=LivingProperty.STRONG_CENTERS,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_boundaries(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess boundaries property.

        Centers are strengthened by boundaries that separate them.
        """
        path = plan.get("path", [])

        # Check for clear transitions between steps
        boundaries = 0
        for i in range(len(path) - 1):
            step1 = path[i]
            step2 = path[i + 1]
            if isinstance(step1, dict) and isinstance(step2, dict):
                if step1.get("to") != step2.get("from"):
                    boundaries += 1

        present = boundaries > 0 or len(path) > 1
        strength = min(1.0, boundaries / max(1, len(path) - 1)) if len(path) > 1 else 0

        evidence = (
            [f"{boundaries} clear boundaries between steps"]
            if boundaries > 0
            else ["Minimal boundaries"]
        )
        recommendations = (
            ["Clarify transitions between transformation steps"]
            if boundaries == 0
            else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.BOUNDARIES,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_alternating_repetition(
        self, plan: Dict[str, Any]
    ) -> PropertyAssessment:
        """
        Assess alternating repetition property.

        Living structures have rhythms of repetition with variation.
        """
        path = plan.get("path", [])
        operations = [step.get("operation") for step in path if isinstance(step, dict)]

        # Check for patterns like A-B-A-B or A-B-C-A-B-C
        if len(operations) < 3:
            present = False
            strength = 0.0
            evidence = ["Path too short for repetition pattern"]
        else:
            # Look for any repeated operation
            unique_ops = set(operations)
            has_repetition = len(unique_ops) < len(operations)

            present = has_repetition
            strength = (
                (len(operations) - len(unique_ops)) / len(operations)
                if operations
                else 0
            )

            if has_repetition:
                repeated = [op for op in unique_ops if operations.count(op) > 1]
                evidence = [f"Operations repeat with variation: {repeated}"]
            else:
                evidence = ["All operations are unique"]

        recommendations = (
            ["Create rhythmic pattern with alternating operations"]
            if not present
            else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.ALTERNATING_REPETITION,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_positive_space(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess positive space property.

        "Negative" space between centers should also have shape/structure.
        """
        # In transformations, this means intermediate states are meaningful
        path = plan.get("path", [])

        if len(path) < 3:
            present = False
            strength = 0.5
            evidence = ["Short path - limited intermediate space"]
        else:
            # Check if intermediate steps are meaningful
            intermediate = path[1:-1]
            meaningful = sum(
                1
                for step in intermediate
                if isinstance(step, dict) and step.get("operator")
            )

            present = meaningful > 0
            strength = meaningful / len(intermediate) if intermediate else 0
            evidence = [f"{meaningful} meaningful intermediate states"]

        recommendations = (
            ["Ensure each intermediate state has purpose"] if strength < 0.5 else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.POSITIVE_SPACE,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_good_shape(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess good shape property.

        Centers should have coherent, well-structured form.
        """
        # Check for coherent transformation structure
        path = plan.get("path", [])

        # A good shape has consistent step sizing
        if len(path) <= 1:
            strength = 0.5
        else:
            # Check consistency
            strength = 0.8 if len(path) <= 6 else 0.6  # Theorem 11 is good shape

        present = strength >= 0.6
        evidence = [
            f"Path length {len(path)} - {'compact' if len(path) <= 6 else 'extended'}"
        ]
        recommendations = ["Compress path to 6 or fewer steps"] if len(path) > 6 else []

        return PropertyAssessment(
            property_type=LivingProperty.GOOD_SHAPE,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_local_symmetries(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess local symmetries property.

        Centers are made of smaller centers with internal symmetry.
        """
        # Check for symmetrical patterns in operations
        path = plan.get("path", [])
        operations = [step.get("operation") for step in path if isinstance(step, dict)]

        # Palindrome-like symmetry
        symmetric = False
        if len(operations) >= 2:
            symmetric = operations[0] == operations[-1]

        present = symmetric or len(operations) <= 3
        strength = 0.8 if symmetric else 0.5

        evidence = (
            ["Symmetrical operation pattern"] if symmetric else ["Asymmetrical pattern"]
        )
        recommendations = (
            ["Consider symmetrical operation arrangement"] if not symmetric else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.LOCAL_SYMMETRIES,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_deep_interlock(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess deep interlock property.

        Centers interpenetrate, creating connection.
        """
        # Check for operations that build on each other
        path = plan.get("path", [])

        interlocked = False
        for i in range(len(path) - 1):
            step1 = path[i]
            step2 = path[i + 1]
            if isinstance(step1, dict) and isinstance(step2, dict):
                if step1.get("to") == step2.get("from"):
                    interlocked = True
                    break

        present = interlocked
        strength = 0.8 if interlocked else 0.3

        evidence = (
            ["Steps interlock sequentially"]
            if interlocked
            else ["Loosely connected steps"]
        )
        recommendations = (
            ["Ensure each step connects deeply to next"] if not interlocked else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.DEEP_INTERLOCK,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_contrast(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess contrast property.

        Centers are strengthened by contrast with surroundings.
        """
        path = plan.get("path", [])
        operations = [step.get("operation") for step in path if isinstance(step, dict)]

        # Check for contrasting operations
        contrasting_pairs = [("ACTIVATE", "INHIBIT"), ("MODULATE", "DISRUPT")]
        has_contrast = any(
            (op1 in operations and op2 in operations) for op1, op2 in contrasting_pairs
        )

        present = has_contrast
        strength = 0.8 if has_contrast else 0.4

        evidence = (
            ["Contrasting operations present"] if has_contrast else ["Limited contrast"]
        )
        recommendations = (
            ["Add contrasting operations for emphasis"] if not has_contrast else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.CONTRAST,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_gradients(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess gradients property.

        Change happens gradually through graduated transitions.
        """
        path = plan.get("path", [])

        # Check for gradual change in C4 states
        if len(path) < 2:
            present = False
            strength = 0.0
            evidence = ["Single step - no gradient possible"]
        else:
            # Gradual transformation is good
            present = True
            strength = min(1.0, len(path) / 6)  # Up to 6 steps is graduated
            evidence = [f"{len(path)} steps create gradual transition"]

        recommendations = []  # Gradients usually present

        return PropertyAssessment(
            property_type=LivingProperty.GRADIENTS,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_roughness(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess roughness property.

        Living structure is slightly imperfect, not mechanically precise.
        """
        # In transformations, this means adaptability and variation
        path = plan.get("path", [])

        # Some variation in operations indicates roughness
        operations = [step.get("operation") for step in path if isinstance(step, dict)]
        unique = len(set(operations))
        total = len(operations)

        variety_ratio = unique / total if total > 0 else 0

        present = variety_ratio > 0.3  # Some variety
        strength = min(1.0, variety_ratio + 0.3)  # Moderate roughness

        evidence = [
            f"{unique} unique operations in {total} steps - {'varied' if present else 'uniform'}"
        ]
        recommendations = ["Add operation variety"] if variety_ratio < 0.3 else []

        return PropertyAssessment(
            property_type=LivingProperty.ROUGHNESS,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_echoes(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess echoes property.

        Similar angles, shapes, forms repeat at different scales.
        """
        path = plan.get("path", [])

        # Echoes in transformation = similar patterns repeating
        # Check for repeated operation at different path positions
        operations = [step.get("operation") for step in path if isinstance(step, dict)]

        has_echoes = False
        for i, op in enumerate(operations):
            for j in range(i + 2, len(operations)):  # Not adjacent
                if operations[j] == op:
                    has_echoes = True
                    break

        present = has_echoes
        strength = 0.7 if has_echoes else 0.3

        evidence = (
            ["Similar operations echo at different positions"]
            if has_echoes
            else ["No echoes detected"]
        )
        recommendations = (
            ["Repeat key operations with variation"] if not has_echoes else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.ECHOES,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_the_void(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess "the void" property.

        Large centers intensify by surrounding with smaller centers.
        """
        path = plan.get("path", [])

        # The void in transformation = clear climax or focal point
        if len(path) >= 3:
            has_void = True  # Middle step is surrounded
            strength = 0.8
            evidence = ["Middle steps surrounded by beginning and end"]
        else:
            has_void = False
            strength = 0.4
            evidence = ["Short path - limited void structure"]

        recommendations = (
            ["Extend path to create surrounding structure"] if len(path) < 3 else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.THE_VOID,
            present=has_void,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_simplicity(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess simplicity property.

        Inner calm despite complexity; removal of unnecessary.
        """
        path = plan.get("path", [])

        # Simplicity = minimal necessary steps
        # Theorem 11 (≤6 steps) embodies simplicity
        n_steps = len(path)

        if n_steps <= 3:
            strength = 1.0
            evidence = ["Minimal essential path"]
        elif n_steps <= 6:
            strength = 0.8
            evidence = ["Compact path within Theorem 11 bound"]
        else:
            strength = 0.5
            evidence = ["Extended path - could be simplified"]

        recommendations = ["Compress path to essential steps"] if n_steps > 6 else []

        return PropertyAssessment(
            property_type=LivingProperty.SIMPLICITY,
            present=strength >= 0.6,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _assess_not_separateness(self, plan: Dict[str, Any]) -> PropertyAssessment:
        """
        Assess not-separateness property.

        Centers merge with surroundings; no harsh boundaries.
        """
        path = plan.get("path", [])
        domain = plan.get("domain", "")

        # Check for domain continuity
        # If transformation respects domain nature = not separate
        present = True  # Assume good integration

        # Deduction for mismatched operations
        if domain in ["psychology", "art"] and any(
            step.get("operation") == "DISRUPT" for step in path
        ):
            strength = 0.6  # Slightly separate
            evidence = ["Some operations may be harsh for domain"]
        else:
            strength = 0.9
            evidence = ["Transformation well-integrated with domain"]

        recommendations = (
            ["Ensure operations fit domain character"] if strength < 0.8 else []
        )

        return PropertyAssessment(
            property_type=LivingProperty.NOT_SEPARATENESS,
            present=present,
            strength=strength,
            evidence=evidence,
            recommendations=recommendations,
        )

    def _generate_wholeness_recommendations(
        self, assessments: List[PropertyAssessment]
    ) -> List[str]:
        """Generate recommendations for improving wholeness"""
        weak_properties = [a for a in assessments if a.strength < 0.5]

        recommendations = []

        if len(weak_properties) > 5:
            recommendations.append(
                f"{len(weak_properties)} properties weak - major restructuring needed"
            )

        for prop in weak_properties[:3]:
            if prop.recommendations:
                recommendations.append(
                    f"{prop.property_type.value}: {prop.recommendations[0]}"
                )

        return recommendations

    def generate_report_markdown(self, report: WholenessReport) -> str:
        """Generate markdown report for documentation"""
        lines = [
            "# Wholeness Assessment Report",
            f"**Date:** {report.timestamp.isoformat()}",
            f"**Overall Score:** {report.overall_score:.1%}",
            f"**Life Score:** {report.life_score:.1%}",
            f"**Properties Present:** {report.properties_present}/{report.total_properties}",
            "",
            "## Center Analysis",
            f"**Strong Centers:** {report.center_analysis.get('strong_centers', 'N/A')}",
            f"**Weak Centers:** {report.center_analysis.get('weak_centers', 'N/A')}",
            "",
            "## Property Assessments",
            "",
        ]

        for assessment in report.property_assessments:
            icon = "✅" if assessment.present else "⚠️"
            lines.append(
                f"### {icon} {assessment.property_type.value.replace('_', ' ').title()}"
            )
            lines.append(f"**Strength:** {assessment.strength:.1%}")
            lines.append(f"**Evidence:** {', '.join(assessment.evidence)}")
            if assessment.recommendations:
                lines.append(f"**Recommend:** {assessment.recommendations[0]}")
            lines.append("")

        if report.wholeness_recommendations:
            lines.extend(["## Wholeness Recommendations", ""])
            for rec in report.wholeness_recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class CenterDetector:
    """Helper class for detecting centers in structures"""

    def analyze(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze centers in a transformation plan"""
        path = plan.get("path", [])

        if not path:
            return {"strong_centers": 0, "weak_centers": 0}

        # First and last are always centers
        strong = 2 if len(path) > 1 else 1

        # Middle steps may be centers if well-formed
        weak = max(0, len(path) - 2)

        return {
            "strong_centers": strong,
            "weak_centers": weak,
            "total": len(path),
            "center_ratio": strong / len(path) if path else 0,
        }
