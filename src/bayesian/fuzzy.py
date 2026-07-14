"""Fuzzy Logic: fuzzy sets, Mamdani inference, and Fuzzy Cognitive Maps."""

from __future__ import annotations

from typing import Callable, Literal

import numpy as np
from numpy.typing import NDArray


class FuzzySet:
    """Fuzzy set defined by a membership function."""

    def __init__(self, name: str, membership: Callable[[NDArray[np.float64]], NDArray[np.float64]]) -> None:
        self.name = name
        self.membership = membership

    def __call__(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.clip(self.membership(np.asarray(x, dtype=np.float64)), 0, 1)

    def __and__(self, other: FuzzySet) -> FuzzySet:
        return FuzzySet(f"{self.name}_AND_{other.name}", lambda x: np.minimum(self(x), other(x)))

    def __or__(self, other: FuzzySet) -> FuzzySet:
        return FuzzySet(f"{self.name}_OR_{other.name}", lambda x: np.maximum(self(x), other(x)))

    def __invert__(self) -> FuzzySet:
        return FuzzySet(f"NOT_{self.name}", lambda x: 1 - self(x))


def triangular(a: float, b: float, c: float) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Triangular membership function."""
    def _mf(x: NDArray[np.float64]) -> NDArray[np.float64]:
        x = np.asarray(x, dtype=np.float64)
        left = np.maximum(0, (x - a) / (b - a + 1e-12))
        right = np.maximum(0, (c - x) / (c - b + 1e-12))
        return np.where(x <= b, left, right)
    return _mf


def trapezoidal(a: float, b: float, c: float, d: float) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Trapezoidal membership function."""
    def _mf(x: NDArray[np.float64]) -> NDArray[np.float64]:
        x = np.asarray(x, dtype=np.float64)
        left = np.maximum(0, (x - a) / (b - a + 1e-12))
        right = np.maximum(0, (d - x) / (d - c + 1e-12))
        return np.minimum(np.where(x <= b, left, right), 1.0)
    return _mf


def gaussian(center: float, sigma: float) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Gaussian membership function."""
    def _mf(x: NDArray[np.float64]) -> NDArray[np.float64]:
        result: NDArray[np.float64] = np.exp(-0.5 * ((np.asarray(x, dtype=np.float64) - center) / sigma) ** 2)
        return result
    return _mf


class FuzzyVariable:
    """Linguistic variable with fuzzy terms."""

    def __init__(self, name: str, universe: NDArray[np.float64]) -> None:
        self.name = name
        self.universe = np.asarray(universe, dtype=np.float64)
        self.terms: dict[str, FuzzySet] = {}

    def add_term(self, name: str, mf: Callable[[NDArray[np.float64]], NDArray[np.float64]]) -> FuzzyVariable:
        """Add term."""
        self.terms[name] = FuzzySet(name, mf)
        return self

    def fuzzify(self, crisp_value: float) -> dict[str, float]:
        """Convert crisp value to membership degrees."""
        val = np.array([crisp_value])
        return {name: float(term(val)[0]) for name, term in self.terms.items()}


class FuzzyRule:
    """Mamdani fuzzy rule: IF antecedent THEN consequent."""

    def __init__(
        self,
        antecedent: FuzzySet,
        consequent: FuzzySet,
        consequent_universe: NDArray[np.float64],
    ) -> None:
        self.antecedent = antecedent
        self.consequent = consequent
        self.consequent_universe = np.asarray(consequent_universe, dtype=np.float64)

    def evaluate(self, firing_strength: float) -> NDArray[np.float64]:
        """Clip consequent membership at firing strength."""
        mf_vals = self.consequent(self.consequent_universe)
        return np.minimum(mf_vals, firing_strength)


class MamdaniInference:
    """Mamdani fuzzy inference engine."""

    def __init__(self) -> None:
        self.rules: list[FuzzyRule] = []

    def add_rule(self, rule: FuzzyRule) -> MamdaniInference:
        """Add rule."""
        self.rules.append(rule)
        return self

    def infer(
        self,
        firing_strengths: list[float],
        defuzzify: Literal["centroid", "bisector"] = "centroid",
    ) -> float:
        """Aggregate rules and defuzzify."""
        if len(firing_strengths) != len(self.rules):
            raise ValueError("Firing strengths must match number of rules")
        aggregated = np.zeros_like(self.rules[0].consequent_universe)
        for strength, rule in zip(firing_strengths, self.rules, strict=False):
            aggregated = np.maximum(aggregated, rule.evaluate(strength))
        if defuzzify == "centroid":
            return self._centroid(self.rules[0].consequent_universe, aggregated)
        return self._bisector(self.rules[0].consequent_universe, aggregated)

    @staticmethod
    def _centroid(x: NDArray[np.float64], mf: NDArray[np.float64]) -> float:
        num = np.trapezoid(x * mf, x)
        den = np.trapezoid(mf, x)
        return float(num / (den + 1e-12))

    @staticmethod
    def _bisector(x: NDArray[np.float64], mf: NDArray[np.float64]) -> float:
        total = np.trapezoid(mf, x)
        cum = np.cumsum((mf[:-1] + mf[1:]) / 2 * np.diff(x))
        idx = int(np.searchsorted(cum, total / 2))
        return float(x[min(idx, len(x) - 1)])


class FuzzyCognitiveMap:
    """Fuzzy Cognitive Map for modeling causal relationships."""

    def __init__(self, concepts: list[str]) -> None:
        self.concepts = concepts
        self.n = len(concepts)
        self.W = np.zeros((self.n, self.n), dtype=np.float64)
        self.state = np.zeros(self.n, dtype=np.float64)
        self._index = {c: i for i, c in enumerate(concepts)}

    def set_weight(self, from_concept: str, to_concept: str, weight: float) -> FuzzyCognitiveMap:
        """Set causal weight between concepts."""
        self.W[self._index[from_concept], self._index[to_concept]] = weight
        return self

    def set_state(self, concept: str, value: float) -> FuzzyCognitiveMap:
        """Set initial activation of a concept."""
        self.state[self._index[concept]] = np.clip(value, -1, 1)
        return self

    def get_state(self, concept: str) -> float:
        return float(self.state[self._index[concept]])

    def update(
        self,
        iterations: int = 10,
        activation: Literal["sigmoid", "tanh"] = "sigmoid",
        lambda_param: float = 1.0,
    ) -> NDArray[np.float64]:
        """Iterate FCM to convergence."""
        for _ in range(iterations):
            new_state = self.W.T @ self.state
            if activation == "sigmoid":
                self.state = 1 / (1 + np.exp(-lambda_param * new_state))
            else:
                self.state = np.tanh(lambda_param * new_state)
        return self.state.copy()

    def steady_state(
        self,
        tol: float = 1e-6,
        max_iter: int = 1000,
        activation: Literal["sigmoid", "tanh"] = "sigmoid",
        lambda_param: float = 1.0,
    ) -> NDArray[np.float64]:
        """Run until convergence."""
        for _ in range(max_iter):
            old = self.state.copy()
            new_state = self.W.T @ self.state
            if activation == "sigmoid":
                self.state = 1 / (1 + np.exp(-lambda_param * new_state))
            else:
                self.state = np.tanh(lambda_param * new_state)
            if np.linalg.norm(self.state - old) < tol:
                break
        return self.state.copy()

    def scenario_analysis(
        self,
        clamped: dict[str, float],
        iterations: int = 20,
    ) -> dict[str, float]:
        """Run with clamped concepts fixed."""
        original = self.state.copy()
        for concept, value in clamped.items():
            self.state[self._index[concept]] = value
        for _ in range(iterations):
            new_state = self.W.T @ self.state
            self.state = np.tanh(new_state)
            for concept, value in clamped.items():
                self.state[self._index[concept]] = value
        result = {c: float(self.state[i]) for c, i in self._index.items()}
        self.state = original
        return result
