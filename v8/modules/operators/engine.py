"""
TURBO-CDI v8.0 - Operators Module
L3: QZRF 14 Operators

Standalone module for phase operators with resonance³ effectiveness.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any
from enum import Enum
from modules import PentadOperation, SeptetObject


class OperatorPhase(Enum):
    """Phase categories for operators"""

    ALPHA = "alpha"  # Initiation
    BETA = "beta"  # Development
    GAMMA = "gamma"  # Culmination
    OMEGA = "omega"  # Integration


@dataclass
class QZRFOperator:
    """
    Quantum-Zeno-Resonance-Field Operator

    14 phase operators that mediate between Pentad and Septet.
    """

    id: str
    name: str
    phase: OperatorPhase
    operation: PentadOperation
    resonance_base: float  # 0.0 - 1.0
    description: str

    def calculate_resonance(
        self, domain: str, domain_profile: Optional[dict] = None
    ) -> float:
        """
        Calculate resonance³ effectiveness for this operator.

        Formula: resonance = base × domain_adjustment × phase_alignment
        """
        base = self.resonance_base

        # Domain adjustment
        if domain_profile and "resonance_factors" in domain_profile:
            domain_factor = domain_profile["resonance_factors"].get(self.id, 1.0)
        else:
            domain_factor = 1.0

        # Phase alignment (simplified)
        phase_alignment = 0.9 if domain in ["physics", "mathematics"] else 0.85

        # Resonance³: effectiveness scales with cube of resonance
        resonance = base * domain_factor * phase_alignment
        return resonance**3


class OperatorsEngine:
    """
    L3: QZRF Operators Engine

    Manages 14 phase operators across 4 phases.
    """

    def __init__(self):
        self._operators: dict[str, QZRFOperator] = {}
        self._build_operators()

    def _build_operators(self):
        """Build all 14 QZRF operators"""
        operators_data = [
            # Alpha phase (initiation)
            (
                "op_alpha_1",
                "Phase Lock",
                OperatorPhase.ALPHA,
                PentadOperation.ACTIVATE,
                0.85,
                "Lock initial state",
            ),
            (
                "op_alpha_2",
                "Coherence Init",
                OperatorPhase.ALPHA,
                PentadOperation.REGULATE,
                0.80,
                "Initialize coherence",
            ),
            (
                "op_alpha_3",
                "Wave Seed",
                OperatorPhase.ALPHA,
                PentadOperation.MODULATE,
                0.75,
                "Seed wave pattern",
            ),
            # Beta phase (development)
            (
                "op_beta_1",
                "Amplitude Boost",
                OperatorPhase.BETA,
                PentadOperation.ACTIVATE,
                0.82,
                "Amplify signal",
            ),
            (
                "op_beta_2",
                "Frequency Shift",
                OperatorPhase.BETA,
                PentadOperation.DISRUPT,
                0.78,
                "Shift frequency domain",
            ),
            (
                "op_beta_3",
                "Phase Modulation",
                OperatorPhase.BETA,
                PentadOperation.MODULATE,
                0.88,
                "Modulate phase",
            ),
            (
                "op_beta_4",
                "Harmonic Couple",
                OperatorPhase.BETA,
                PentadOperation.REGULATE,
                0.85,
                "Couple harmonics",
            ),
            # Gamma phase (culmination)
            (
                "op_gamma_1",
                "Resonance Peak",
                OperatorPhase.GAMMA,
                PentadOperation.ACTIVATE,
                0.90,
                "Achieve resonance",
            ),
            (
                "op_gamma_2",
                "Damping Control",
                OperatorPhase.GAMMA,
                PentadOperation.INHIBIT,
                0.80,
                "Control damping",
            ),
            (
                "op_gamma_3",
                "Transition Gate",
                OperatorPhase.GAMMA,
                PentadOperation.DISRUPT,
                0.85,
                "Gate transition",
            ),
            # Omega phase (integration)
            (
                "op_omega_1",
                "Field Collapse",
                OperatorPhase.OMEGA,
                PentadOperation.DISRUPT,
                0.75,
                "Collapse field",
            ),
            (
                "op_omega_2",
                "Memory Encode",
                OperatorPhase.OMEGA,
                PentadOperation.REGULATE,
                0.88,
                "Encode to memory",
            ),
            (
                "op_omega_3",
                "State Recurse",
                OperatorPhase.OMEGA,
                PentadOperation.MODULATE,
                0.82,
                "Recursive state",
            ),
            (
                "op_omega_4",
                "Quantum Echo",
                OperatorPhase.OMEGA,
                PentadOperation.INHIBIT,
                0.80,
                "Quantum feedback",
            ),
        ]

        for op_id, name, phase, operation, resonance, desc in operators_data:
            self._operators[op_id] = QZRFOperator(
                id=op_id,
                name=name,
                phase=phase,
                operation=operation,
                resonance_base=resonance,
                description=desc,
            )

    def get_operator(self, operator_id: str) -> Optional[QZRFOperator]:
        """Get operator by ID"""
        return self._operators.get(operator_id)

    def get_by_phase(self, phase: OperatorPhase) -> list[QZRFOperator]:
        """Get all operators in a phase"""
        return [op for op in self._operators.values() if op.phase == phase]

    def get_by_operation(self, operation: PentadOperation) -> list[QZRFOperator]:
        """Get all operators for an operation type"""
        return [op for op in self._operators.values() if op.operation == operation]

    def apply_operator(self, operator_id: str, context: dict) -> dict:
        """
        Apply an operator in a given context.

        Returns result with resonance³ effectiveness.
        """
        operator = self.get_operator(operator_id)
        if not operator:
            raise ValueError(f"Unknown operator: {operator_id}")

        domain = context.get("domain", "general")
        domain_profile = context.get("domain_profile")

        resonance = operator.calculate_resonance(domain, domain_profile)

        return {
            "operator": operator,
            "resonance": resonance,
            "effectiveness": resonance**3,
            "phase": operator.phase.value,
            "applied": True,
        }

    def get_all_operators(self) -> list[QZRFOperator]:
        """Get all 14 operators"""
        return list(self._operators.values())
