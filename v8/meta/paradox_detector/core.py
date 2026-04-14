"""
TURBO-CDI v8.0 - Paradox Detector
Agent 4: Meta Systems

Detects and resolves logical paradoxes and conflicts in transformation plans.
Prevents self-defeating strategies and circular dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from datetime import datetime
from enum import Enum


class ParadoxType(Enum):
    """Types of paradoxes that can be detected"""

    CIRCULARITY = "circularity"  # A leads to B leads to A
    CONTRADICTION = "contradiction"  # Opposing operations on same target
    SELF_DEFEAT = "self_defeat"  # Goal undermines itself
    INFINITE_REGRESS = "infinite_regress"  # Infinite chain without base
    FALSE_PREMISE = "false_premise"  # Based on falsified assumptions
    MORAL_HAZARD = "moral_hazard"  # Incentives create bad outcomes
    COMPOSITION = "composition"  # Whole ≠ sum of parts


@dataclass
class Paradox:
    """Detected paradox"""

    paradox_type: ParadoxType
    description: str
    severity: str  # "low", "medium", "high", "critical"
    involved_steps: List[int]  # Step indices involved
    resolution_suggestions: List[str]
    auto_resolvable: bool


@dataclass
class Conflict:
    """Detected conflict between components"""

    conflict_type: str
    description: str
    component_a: str
    component_b: str
    resolution_priority: str  # "low", "medium", "high"


class ParadoxDetector:
    """
    Detects logical paradoxes and conflicts in transformation systems.

    Paradox types detected:
    - Circularity: Transformation chains that loop back
    - Contradiction: Opposing operations on same target
    - Self-defeat: Goals that undermine themselves
    - Infinite regress: Unending chains
    - False premise: Based on falsified hypotheses
    - Moral hazard: Perverse incentives

    Based on logical analysis and Bateson's work on double binds.
    """

    def __init__(self):
        self.detected_paradoxes: List[Paradox] = []
        self.resolved_paradoxes: List[Paradox] = []

    def analyze_plan(self, plan: Dict[str, Any]) -> List[Paradox]:
        """
        Analyze transformation plan for paradoxes.

        Args:
            plan: Transformation plan with path, operations, etc.

        Returns:
            List of detected paradoxes
        """
        paradoxes = []

        # Check for various paradox types
        paradoxes.extend(self._check_circularity(plan))
        paradoxes.extend(self._check_contradiction(plan))
        paradoxes.extend(self._check_self_defeat(plan))
        paradoxes.extend(self._check_infinite_regress(plan))
        paradoxes.extend(self._check_false_premise(plan))
        paradoxes.extend(self._check_moral_hazard(plan))

        self.detected_paradoxes.extend(paradoxes)
        return paradoxes

    def _check_circularity(self, plan: Dict[str, Any]) -> List[Paradox]:
        """Check for circular transformation chains"""
        path = plan.get("path", [])
        paradoxes = []

        if len(path) < 3:
            return paradoxes

        # Extract state signatures
        states = []
        for step in path:
            if isinstance(step, dict):
                state_sig = step.get("from", "") + "->" + step.get("to", "")
                states.append(state_sig)

        # Check for repeated patterns (indicates potential cycle)
        seen = set()
        for i, state in enumerate(states):
            if state in seen:
                # Found potential cycle
                paradoxes.append(
                    Paradox(
                        paradox_type=ParadoxType.CIRCULARITY,
                        description=f"Potential circularity detected: state pattern '{state}' repeats",
                        severity="high",
                        involved_steps=[i],
                        resolution_suggestions=[
                            "Break the cycle by introducing a new intermediate state",
                            "Change operation at step {} to alter path".format(i),
                            "Use DISRUPT operation to exit the loop",
                        ],
                        auto_resolvable=False,
                    )
                )
            seen.add(state)

        return paradoxes

    def _check_contradiction(self, plan: Dict[str, Any]) -> List[Paradox]:
        """Check for contradictory operations on same target"""
        path = plan.get("path", [])
        operations = []

        # Extract operations
        for i, step in enumerate(path):
            if isinstance(step, dict):
                op = step.get("operation", "")
                target = step.get("target", "")
                operations.append((i, op, target))

        paradoxes = []

        # Check for contradictions
        opposing_pairs = [
            ("ACTIVATE", "INHIBIT"),
            ("MODULATE", "DISRUPT"),
        ]

        for i, (idx1, op1, target1) in enumerate(operations):
            for idx2, op2, target2 in operations[i + 1 :]:
                if target1 == target2:  # Same target
                    if (op1, op2) in opposing_pairs or (op2, op1) in opposing_pairs:
                        paradoxes.append(
                            Paradox(
                                paradox_type=ParadoxType.CONTRADICTION,
                                description=f"Contradictory operations '{op1}' and '{op2}' on '{target1}'",
                                severity="high",
                                involved_steps=[idx1, idx2],
                                resolution_suggestions=[
                                    f"Choose one operation: either {op1} or {op2}",
                                    "Apply operations sequentially, not simultaneously",
                                    "Use REGULATE to balance the opposing forces",
                                ],
                                auto_resolvable=False,
                            )
                        )

        return paradoxes

    def _check_self_defeat(self, plan: Dict[str, Any]) -> List[Paradox]:
        """Check for self-defeating goals"""
        goal = plan.get("goal", "")
        domain = plan.get("domain", "")

        paradoxes = []

        # Common self-defeating patterns
        self_defeating_patterns = [
            ("perfect", "optimization"),  # Perfect is enemy of good
            ("complete", "control"),  # Total control loses adaptability
            ("maximum", "efficiency"),  # Over-optimization brittleness
            ("absolute", "certainty"),  # Certainty prevents learning
        ]

        goal_lower = goal.lower() if goal else ""

        for word1, word2 in self_defeating_patterns:
            if word1 in goal_lower and word2 in goal_lower:
                paradoxes.append(
                    Paradox(
                        paradox_type=ParadoxType.SELF_DEFEAT,
                        description=f"Goal '{goal}' contains self-defeating pattern: '{word1} {word2}'",
                        severity="medium",
                        involved_steps=[],
                        resolution_suggestions=[
                            f"Replace '{word1}' with 'sufficient' or 'appropriate'",
                            "Add constraint: 'while maintaining flexibility'",
                            "Consider trade-offs explicitly",
                        ],
                        auto_resolvable=False,
                    )
                )

        # Domain-specific self-defeat patterns
        if domain == "psychology" and "control" in goal_lower:
            paradoxes.append(
                Paradox(
                    paradox_type=ParadoxType.SELF_DEFEAT,
                    description="Attempting to control psychological processes often backfires",
                    severity="medium",
                    involved_steps=[],
                    resolution_suggestions=[
                        "Use MODULATE instead of CONTROL",
                        "Focus on influence rather than control",
                        "Allow for emergence",
                    ],
                    auto_resolvable=True,
                )
            )

        return paradoxes

    def _check_infinite_regress(self, plan: Dict[str, Any]) -> List[Paradox]:
        """Check for infinite regress patterns"""
        path = plan.get("path", [])

        if len(path) < 6:  # Theorem 11 bound
            return []

        # If path is at the limit, check for patterns that suggest more steps needed
        paradoxes = []

        # Check for "and then..." patterns in descriptions
        for i, step in enumerate(path):
            if isinstance(step, dict):
                desc = step.get("description", "")
                if "further" in desc.lower() or "more steps" in desc.lower():
                    paradoxes.append(
                        Paradox(
                            paradox_type=ParadoxType.INFINITE_REGRESS,
                            description=f"Step {i} suggests need for indefinite continuation",
                            severity="medium",
                            involved_steps=[i],
                            resolution_suggestions=[
                                "Define clear termination condition",
                                "Break into smaller bounded sub-tasks",
                                "Use recursion with base case",
                            ],
                            auto_resolvable=True,
                        )
                    )

        return paradoxes

    def _check_false_premise(self, plan: Dict[str, Any]) -> List[Paradox]:
        """Check for plans based on falsified hypotheses"""
        # This would integrate with falsification engine
        # For now, check for known problematic assumptions

        paradoxes = []
        domain = plan.get("domain", "")

        # Known falsified assumptions by domain
        falsified_assumptions = {
            "physics": ["perpetual motion", "faster than light communication"],
            "psychology": ["perfect rationality", "unlimited willpower"],
            "economics": ["perfect information", "perpetual growth"],
        }

        plan_str = str(plan).lower()

        for dom, assumptions in falsified_assumptions.items():
            if dom in domain.lower():
                for assumption in assumptions:
                    if assumption in plan_str:
                        paradoxes.append(
                            Paradox(
                                paradox_type=ParadoxType.FALSE_PREMISE,
                                description=f"Plan assumes '{assumption}' which has been falsified",
                                severity="critical",
                                involved_steps=[],
                                resolution_suggestions=[
                                    f"Remove assumption of '{assumption}'",
                                    f"Find alternative to '{assumption}'",
                                    "Consult domain expert",
                                ],
                                auto_resolvable=False,
                            )
                        )

        return paradoxes

    def _check_moral_hazard(self, plan: Dict[str, Any]) -> List[Paradox]:
        """Check for moral hazard / perverse incentives"""
        paradoxes = []

        # Check for measurement-focused plans that might cause gaming
        operations = plan.get("operations", [])

        # If plan focuses heavily on measurement without safeguards
        if "measure" in str(plan).lower() and "verify" not in str(plan).lower():
            paradoxes.append(
                Paradox(
                    paradox_type=ParadoxType.MORAL_HAZARD,
                    description="Plan emphasizes measurement without verification - risk of gaming metrics",
                    severity="medium",
                    involved_steps=[],
                    resolution_suggestions=[
                        "Add verification steps independent of measurement",
                        "Use multiple metrics to prevent gaming",
                        "Include qualitative assessment",
                    ],
                    auto_resolvable=True,
                )
            )

        return paradoxes

    def detect_conflicts(
        self, plan_a: Dict[str, Any], plan_b: Dict[str, Any]
    ) -> List[Conflict]:
        """
        Detect conflicts between two plans.

        Args:
            plan_a: First plan
            plan_b: Second plan

        Returns:
            List of conflicts
        """
        conflicts = []

        # Check for resource conflicts
        resources_a = set(plan_a.get("resources", []))
        resources_b = set(plan_b.get("resources", []))
        shared_resources = resources_a & resources_b

        if shared_resources:
            conflicts.append(
                Conflict(
                    conflict_type="resource",
                    description=f"Plans share resources: {shared_resources}",
                    component_a=plan_a.get("id", "A"),
                    component_b=plan_b.get("id", "B"),
                    resolution_priority="medium",
                )
            )

        # Check for goal conflicts
        goal_a = plan_a.get("goal", "").lower()
        goal_b = plan_b.get("goal", "").lower()

        opposing_goals = [
            ("increase", "decrease"),
            ("expand", "contract"),
            ("activate", "inhibit"),
        ]

        for inc, dec in opposing_goals:
            if inc in goal_a and dec in goal_b:
                conflicts.append(
                    Conflict(
                        conflict_type="goal_opposition",
                        description=f"Opposing goals: '{goal_a}' vs '{goal_b}'",
                        component_a=plan_a.get("id", "A"),
                        component_b=plan_b.get("id", "B"),
                        resolution_priority="high",
                    )
                )

        return conflicts

    def attempt_resolution(self, paradox: Paradox) -> Optional[Dict[str, Any]]:
        """
        Attempt automatic paradox resolution.

        Args:
            paradox: Paradox to resolve

        Returns:
            Resolution action if auto-resolvable, None otherwise
        """
        if not paradox.auto_resolvable:
            return None

        if paradox.paradox_type == ParadoxType.SELF_DEFEAT:
            return {
                "action": "replace_operation",
                "from": "CONTROL",
                "to": "MODULATE",
                "reason": paradox.resolution_suggestions[0],
            }

        if paradox.paradox_type == ParadoxType.INFINITE_REGRESS:
            return {
                "action": "add_termination",
                "max_steps": 6,  # Theorem 11 bound
                "reason": paradox.resolution_suggestions[0],
            }

        if paradox.paradox_type == ParadoxType.MORAL_HAZARD:
            return {
                "action": "add_verification",
                "verification_type": "independent",
                "reason": paradox.resolution_suggestions[0],
            }

        return None

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive paradox analysis report"""
        active = [
            p for p in self.detected_paradoxes if p not in self.resolved_paradoxes
        ]

        by_type = {}
        for p in self.detected_paradoxes:
            pt = p.paradox_type.value
            by_type[pt] = by_type.get(pt, 0) + 1

        by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for p in self.detected_paradoxes:
            by_severity[p.severity] = by_severity.get(p.severity, 0) + 1

        return {
            "total_detected": len(self.detected_paradoxes),
            "active_paradoxes": len(active),
            "resolved": len(self.resolved_paradoxes),
            "by_type": by_type,
            "by_severity": by_severity,
            "auto_resolvable": sum(1 for p in active if p.auto_resolvable),
            "requires_manual": sum(1 for p in active if not p.auto_resolvable),
        }
