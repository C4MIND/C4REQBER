"""
TURBO-CDI: 27 Functors / Operators
9 Base + 18 Composed (from system-prompts-en.md)
"""

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from .c4_state import C4State


@dataclass(frozen=True)
class C4Operator:
    """
    C4 Operator: transforms C4 state.

    Properties:
    - Period-3: op³ = identity
    - Commutative: op1 ∘ op2 = op2 ∘ op1 (for base operators)
    """

    name: str
    symbol: str
    apply: Callable[[C4State], C4State]
    description: str

    def __call__(self, state: C4State) -> C4State:
        """Apply operator to state."""
        return self.apply(state)


class BaseOperators:
    """
    9 Base Operators (Generators of C4 algebra)
    """

    @staticmethod
    def tau_plus(state: C4State) -> C4State:
        """τ+: Time forward (Past→Present→Future)"""
        return C4State(T=(state.T + 1) % 3, S=state.S, A=state.A)

    @staticmethod
    def tau_minus(state: C4State) -> C4State:
        """τ-: Time backward (Future→Present→Past)"""
        return C4State(T=(state.T - 1) % 3, S=state.S, A=state.A)

    @staticmethod
    def sigma(state: C4State) -> C4State:
        """σ: Connect/Integrate (identity for state, marks operation)"""
        return state  # Context marker, no state change

    @staticmethod
    def delta(state: C4State) -> C4State:
        """δ: Differentiate/Separate (identity for state, marks operation)"""
        return state  # Context marker, no state change

    @staticmethod
    def rho(state: C4State) -> C4State:
        """ρ: Resonance/Pattern (identity for state, marks operation)"""
        return state  # Context marker, no state change

    @staticmethod
    def iota(state: C4State) -> C4State:
        """ι: Invert (0↔2, 1 stays) on all axes"""
        return C4State(T=2 - state.T, S=2 - state.S, A=2 - state.A)

    @staticmethod
    def lambda_plus(state: C4State) -> C4State:
        """λ+: Abstract (Concrete→Abstract→Meta)"""
        return C4State(T=state.T, S=(state.S + 1) % 3, A=state.A)

    @staticmethod
    def lambda_minus(state: C4State) -> C4State:
        """λ-: Concretize (Meta→Abstract→Concrete)"""
        return C4State(T=state.T, S=(state.S - 1) % 3, A=state.A)

    @staticmethod
    def kappa_plus(state: C4State) -> C4State:
        """κ+: Agency expand (Self→Other→System)"""
        return C4State(T=state.T, S=state.S, A=(state.A + 1) % 3)

    @staticmethod
    def kappa_minus(state: C4State) -> C4State:
        """κ-: Agency contract (System→Other→Self)"""
        return C4State(T=state.T, S=state.S, A=(state.A - 1) % 3)


class Operators:
    """
    All 27 Operators: 9 Base + 18 Composed
    """

    def __init__(self):
        self.base = self._create_base()
        self.composed = self._create_composed()
        self.all = {**self.base, **self.composed}

    def _create_base(self) -> Dict[str, C4Operator]:
        """Create 9 base operators."""
        b = BaseOperators()
        return {
            "tau+": C4Operator("tau-forward", "τ+", b.tau_plus, "Past→Present→Future"),
            "tau-": C4Operator(
                "tau-backward", "τ-", b.tau_minus, "Future→Present→Past"
            ),
            "sigma": C4Operator("sigma", "σ", b.sigma, "Connect/Integrate"),
            "delta": C4Operator("delta", "δ", b.delta, "Differentiate/Separate"),
            "rho": C4Operator("rho", "ρ", b.rho, "Resonance/Pattern"),
            "iota": C4Operator("iota", "ι", b.iota, "Invert perspective"),
            "lambda+": C4Operator("lambda-plus", "λ+", b.lambda_plus, "Abstract"),
            "lambda-": C4Operator("lambda-minus", "λ-", b.lambda_minus, "Concretize"),
            "kappa+": C4Operator("kappa-plus", "κ+", b.kappa_plus, "Agency expand"),
            "kappa-": C4Operator("kappa-minus", "κ-", b.kappa_minus, "Agency contract"),
        }

    def _create_composed(self) -> Dict[str, C4Operator]:
        """Create 18 composed operators."""
        b = BaseOperators()
        composed = {}

        # τ ∘ σ: Narrative Connectivity
        composed["tau_sigma"] = C4Operator(
            "narrative-connectivity",
            "τ∘σ",
            lambda s: b.sigma(b.tau_plus(s)),
            "Connect events across time",
        )

        # τ ∘ δ: Chronological Analysis
        composed["tau_delta"] = C4Operator(
            "chronological-analysis",
            "τ∘δ",
            lambda s: b.delta(b.tau_plus(s)),
            "Divide timeline into phases",
        )

        # τ ∘ ρ: Trend Recognition
        composed["tau_rho"] = C4Operator(
            "trend-recognition",
            "τ∘ρ",
            lambda s: b.rho(b.tau_plus(s)),
            "Find temporal patterns",
        )

        # σ ∘ ι: Reconciliation of Opposites
        composed["sigma_iota"] = C4Operator(
            "reconciliation-of-opposites",
            "σ∘ι",
            lambda s: b.iota(b.sigma(s)),
            "Unify contradictions (synthesis)",
        )

        # δ ∘ ι: Perspective Differentiation
        composed["delta_iota"] = C4Operator(
            "perspective-differentiation",
            "δ∘ι",
            lambda s: b.iota(b.delta(s)),
            "Multiple viewpoint analysis",
        )

        # ρ ∘ τ: Resonance Synchronization
        composed["rho_tau"] = C4Operator(
            "resonance-sync",
            "ρ∘τ",
            lambda s: b.tau_plus(b.rho(s)),
            "Match rhythms across time",
        )

        # ρ ∘ ι: Mirror Replication
        composed["rho_iota"] = C4Operator(
            "mirror-replication",
            "ρ∘ι",
            lambda s: b.iota(b.rho(s)),
            "Inverted pattern copies",
        )

        # ι ∘ λ: Inversion of Generalizations
        composed["iota_lambda"] = C4Operator(
            "inversion-of-generalizations",
            "ι∘λ",
            lambda s: b.lambda_plus(b.iota(s)),
            "Critic of principles",
        )

        # λ ∘ σ: Integrated Abstraction
        composed["lambda_sigma"] = C4Operator(
            "integrated-abstraction",
            "λ∘σ",
            lambda s: b.sigma(b.lambda_plus(s)),
            "Build unifying theory",
        )

        # λ ∘ ι: Dialectics
        composed["lambda_iota"] = C4Operator(
            "dialectics",
            "λ∘ι",
            lambda s: b.iota(b.lambda_plus(s)),
            "Elevate contradictions",
        )

        # κ ∘ σ: Detailed Integration
        composed["kappa_sigma"] = C4Operator(
            "detailed-integration",
            "κ∘σ",
            lambda s: b.sigma(b.kappa_plus(s)),
            "Concrete connections",
        )

        # κ ∘ δ: Detailed Decomposition
        composed["kappa_delta"] = C4Operator(
            "detailed-decomposition",
            "κ∘δ",
            lambda s: b.delta(b.kappa_plus(s)),
            "Atomic partition",
        )

        # Additional composed operators for complete set
        composed["lambda_kappa"] = C4Operator(
            "abstraction-cycle",
            "λ∘κ",
            lambda s: b.kappa_plus(b.lambda_plus(s)),
            "Verify meaning preservation",
        )

        composed["sigma_phi"] = C4Operator(
            "contextual-synthesis",
            "σ∘φ",
            lambda s: s,  # Placeholder for phi
            "Integrate with context",
        )

        composed["delta_phi"] = C4Operator(
            "contextual-decomposition",
            "δ∘φ",
            lambda s: s,  # Placeholder
            "Divide by context",
        )

        composed["rho_phi"] = C4Operator(
            "adaptive-replication",
            "ρ∘φ",
            lambda s: s,  # Placeholder
            "Pattern with adaptation",
        )

        composed["kappa_phi"] = C4Operator(
            "concrete-in-context",
            "κ∘φ",
            lambda s: s,  # Placeholder
            "Local applicability",
        )

        composed["mu_phi"] = C4Operator(
            "reflective-adaptation",
            "μ∘φ",
            lambda s: s,  # Placeholder
            "Self-aware reconfiguration",
        )

        return composed

    def get(self, name: str) -> Optional[C4Operator]:
        """Get operator by name."""
        return self.all.get(name)

    def list_all(self) -> List[str]:
        """List all operator names."""
        return list(self.all.keys())

    def apply_sequence(self, state: C4State, sequence: List[str]) -> C4State:
        """Apply sequence of operators to state."""
        current = state
        for op_name in sequence:
            op = self.get(op_name)
            if op:
                current = op(current)
        return current


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

_operators_instance = Operators()


def apply_operator(name: str, state: C4State) -> C4State:
    """
    Apply a single operator to a state.

    Args:
        name: Operator name (e.g., "tau+", "sigma", "delta")
        state: Current C4 state

    Returns:
        Transformed state

    Raises:
        ValueError: If operator name is invalid
    """
    op = _operators_instance.get(name)
    if op is None:
        raise ValueError(f"Unknown operator: {name}")
    return op(state)


def get_operator_transform(name: str) -> Callable[[C4State], C4State]:
    """
    Get the transform function for an operator.

    Args:
        name: Operator name

    Returns:
        Transform function

    Raises:
        ValueError: If operator name is invalid
    """
    op = _operators_instance.get(name)
    if op is None:
        raise ValueError(f"Unknown operator: {name}")
    return op.apply
