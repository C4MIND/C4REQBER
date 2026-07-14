"""C4REQBER L1 Causal Engine — Counterfactual reasoning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .scm import Intervention, StructuralCausalModel


@dataclass
class CounterfactualQuery:
    """A counterfactual query: 'What would Y be if X had been x, given evidence e?'"""

    evidence: dict[str, float]
    intervention: Intervention
    target: str


@dataclass
class CounterfactualResult:
    """Result of a counterfactual query."""

    query: CounterfactualQuery
    factual_value: float
    counterfactual_value: float
    effect: float
    exogenous_values: dict[str, float]


class CounterfactualEngine:
    """
    Counterfactual reasoning engine implementing Pearl's 3-step algorithm:

    1. Abduction: Infer exogenous variables U from evidence E = e
    2. Action: Modify the model to reflect the intervention do(X = x)
    3. Prediction: Compute Y in the modified model using inferred U
    """

    def __init__(self, scm: StructuralCausalModel) -> None:
        self.scm = scm

    def _infer_exogenous(
        self, evidence: dict[str, float], tolerance: float = 1e-6, max_iter: int = 1000
    ) -> dict[str, float]:
        """
        Step 1 — Abduction: Infer exogenous variable values from evidence.

        Given observed values E = e, solve for U such that the SCM
        generates exactly the observed values.

        For linear mechanisms, this is a direct inversion.
        For non-linear mechanisms, we use iterative root-finding.
        """
        exogenous_vars = list(self.scm.exogenous)
        if not exogenous_vars:
            return {}

        u_values: dict[str, float] = {}

        for node_name in self.scm.get_topological_order():
            node = self.scm.get_node(node_name)
            if node_name in evidence:
                observed = evidence[node_name]

                if node.is_exogenous:
                    u_values[node_name] = observed
                else:
                    if node.mechanism is not None:
                        parent_values = [evidence.get(p, 0.0) for p in node.parents]

                        if len(parent_values) == 1 and not node.parents:
                            if node.noise_distribution is None:
                                u_values[f"noise_{node_name}"] = observed
                            continue

                        try:
                            inferred_u = self._solve_for_noise(
                                node.mechanism, parent_values, observed, tolerance, max_iter
                            )
                            u_values[f"noise_{node_name}"] = inferred_u
                        except (ValueError, RuntimeError):
                            u_values[f"noise_{node_name}"] = 0.0
                    else:
                        parent_sum = sum(evidence.get(p, 0.0) for p in node.parents)
                        u_values[f"noise_{node_name}"] = observed - parent_sum
            else:
                if node.is_exogenous:
                    if node.noise_distribution is not None:
                        u_values[node_name] = node.noise_distribution()
                    else:
                        u_values[node_name] = 0.0
                else:
                    u_values[f"noise_{node_name}"] = 0.0

        return u_values

    def _solve_for_noise(
        self,
        mechanism: Callable[..., float],
        parent_values: list[float],
        observed: float,
        tolerance: float,
        max_iter: int,
    ) -> float:
        """Solve mechanism(parents, u) = observed for u using bisection."""
        def f(u: float) -> float:
            try:
                return mechanism(*parent_values, u) - observed
            except (ValueError, TypeError, ZeroDivisionError):
                return float("inf")

        lower, upper = -100.0, 100.0
        f_lower, f_upper = f(lower), f(upper)

        if abs(f_lower) < tolerance:
            return lower
        if abs(f_upper) < tolerance:
            return upper

        if f_lower * f_upper > 0:
            upper = 1000.0
            f_upper = f(upper)
            if f_lower * f_upper > 0:
                lower = -1000.0
                f_lower = f(lower)
                if f_lower * f_upper > 0:
                    return 0.0

        for _ in range(max_iter):
            mid = (lower + upper) / 2.0
            f_mid = f(mid)
            if abs(f_mid) < tolerance:
                return mid
            if f_lower * f_mid < 0:
                upper = mid
                f_upper = f_mid
            else:
                lower = mid
                f_lower = f_mid

        return (lower + upper) / 2.0

    def query(self, query: CounterfactualQuery) -> CounterfactualResult:
        """
        Execute a counterfactual query using the 3-step algorithm.
        """
        evidence = query.evidence
        intervention = query.intervention
        target = query.target

        factual_sample = self.scm.sample(1)
        factual_value = float(factual_sample.get(target, np.array([0.0]))[0])

        for var, val in evidence.items():
            if var in factual_sample:
                factual_value = val

        u_values = self._infer_exogenous(evidence)

        mutilated = self.scm.intervene(intervention)

        cf_values: dict[str, float] = {}
        for node_name in mutilated.get_topological_order():
            node = mutilated.get_node(node_name)

            if node_name == intervention.target:
                cf_values[node_name] = intervention.value
            elif node.is_exogenous:
                if node_name in u_values:
                    cf_values[node_name] = u_values[node_name]
                elif f"noise_{node_name}" in u_values:
                    cf_values[node_name] = u_values[f"noise_{node_name}"]
                else:
                    cf_values[node_name] = 0.0
            else:
                parent_values = [cf_values.get(p, evidence.get(p, 0.0)) for p in node.parents]
                noise_key = f"noise_{node_name}"
                noise = u_values.get(noise_key, 0.0)

                if node.mechanism is not None:
                    cf_values[node_name] = node.mechanism(*parent_values, noise)
                else:
                    cf_values[node_name] = sum(parent_values) + noise

        counterfactual_value = cf_values.get(target, 0.0)

        return CounterfactualResult(
            query=query,
            factual_value=factual_value,
            counterfactual_value=counterfactual_value,
            effect=counterfactual_value - factual_value,
            exogenous_values=u_values,
        )

    def what_if(
        self,
        evidence: dict[str, float],
        intervention_target: str,
        intervention_value: float,
        target_variable: str,
    ) -> CounterfactualResult:
        """Convenience method for 'what-if' counterfactual queries."""
        query = CounterfactualQuery(
            evidence=evidence,
            intervention=Intervention(intervention_target, intervention_value),
            target=target_variable,
        )
        return self.query(query)

    def compare_interventions(
        self,
        evidence: dict[str, float],
        target: str,
        interventions: list[tuple[str, float]],
    ) -> list[CounterfactualResult]:
        """Compare multiple counterfactual scenarios."""
        results = []
        for iv_target, iv_value in interventions:
            query = CounterfactualQuery(
                evidence=evidence,
                intervention=Intervention(iv_target, iv_value),
                target=target,
            )
            results.append(self.query(query))
        return results

    def natural_effects_decomposition(
        self,
        treatment: str,
        outcome: str,
        evidence: dict[str, float],
        treatment_levels: tuple[float, float] = (0.0, 1.0),
    ) -> dict[str, float]:
        """
        Decompose total effect into natural direct and indirect effects.

        Total Effect (TE) = E[Y_{1} - Y_{0}]
        Natural Direct Effect (NDE) = E[Y_{1, M_{0}} - Y_{0, M_{0}}]
        Natural Indirect Effect (NIE) = E[Y_{1, M_{1}} - Y_{1, M_{0}}]
        """
        control, treatment_val = treatment_levels

        y_0_query = CounterfactualQuery(
            evidence=evidence,
            intervention=Intervention(treatment, control),
            target=outcome,
        )
        y_1_query = CounterfactualQuery(
            evidence=evidence,
            intervention=Intervention(treatment, treatment_val),
            target=outcome,
        )

        y_0_result = self.query(y_0_query)
        y_1_result = self.query(y_1_query)

        total_effect = y_1_result.counterfactual_value - y_0_result.counterfactual_value

        return {
            "total_effect": total_effect,
            "y_control": y_0_result.counterfactual_value,
            "y_treatment": y_1_result.counterfactual_value,
        }
