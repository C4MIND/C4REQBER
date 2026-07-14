"""C4REQBER L1 Causal Engine — Pearl's do-calculus (3 rules)."""

from __future__ import annotations

import networkx as nx

from .scm import StructuralCausalModel, _nx_is_d_separator


class DoCalculus:
    """
    Implementation of Pearl's do-calculus for causal inference.

    Do-calculus consists of 3 rules for manipulating interventional distributions
    using only observational data and the causal graph structure.
    """

    def __init__(self, scm: StructuralCausalModel) -> None:
        self.scm = scm
        self._dag = scm.dag

    def _mutilated_graph(self, interventions: set[str]) -> nx.DiGraph:
        """
        Create a graph where incoming edges to intervened nodes are removed.
        This represents the do-operator graphically.
        """
        g = self._dag.copy()
        for node in interventions:
            parents = list(g.predecessors(node))
            for parent in parents:
                g.remove_edge(parent, node)
        return g

    def _is_d_separated(self, g: nx.DiGraph, x: set[str], y: set[str], z: set[str]) -> bool:
        """Check d-separation in a given graph."""
        return _nx_is_d_separator(g, x, y, z)

    def rule1_insertion_deletion(
        self,
        y: str,
        z: str,
        x: set[str],
        w: set[str] | None = None,
    ) -> bool:
        """
        Rule 1: Insertion/deletion of observations.

        P(y | do(x), z, w) = P(y | do(x), w) if (Y ⟂ Z | X, W) in G_{do(X)}

        Checks if Z can be inserted/deleted from the conditioning set
        when we have already intervened on X.
        """
        w = w or set()
        g_x = self._mutilated_graph(x)
        return self._is_d_separated(g_x, {y}, {z}, x | w)

    def rule2_action_observation_exchange(
        self,
        y: str,
        z: str,
        x: set[str],
        w: set[str] | None = None,
    ) -> bool:
        """
        Rule 2: Action/observation exchange.

        P(y | do(x), do(z), w) = P(y | do(x), z, w)
        if (Y ⟂ Z | X, W) in G_{do(X), do(Z^)}

        Where Z^ means we remove outgoing edges from Z (not incoming).
        This checks when an intervention on Z can be replaced by observation of Z.
        """
        w = w or set()
        g = self._dag.copy()

        for node in x:
            parents = list(g.predecessors(node))
            for parent in parents:
                g.remove_edge(parent, node)

        for node in {z}:
            children = list(g.successors(node))
            for child in children:
                g.remove_edge(node, child)

        return self._is_d_separated(g, {y}, {z}, x | w)

    def rule3_insertion_deletion_actions(
        self,
        y: str,
        z: str,
        x: set[str],
        w: set[str] | None = None,
    ) -> bool:
        """
        Rule 3: Insertion/deletion of actions.

        P(y | do(x), do(z), w) = P(y | do(x), w)
        if (Y ⟂ Z | X, W) in G_{do(X), do(Z(W))}

        Where Z(W) represents nodes in Z that are not ancestors of W.
        This checks when an intervention on Z can be completely removed.
        """
        w = w or set()
        if z not in self._dag:
            return True

        g = self._dag.copy()

        for node in x:
            parents = list(g.predecessors(node))
            for parent in parents:
                g.remove_edge(parent, node)

        z_ancestors_of_w = set()
        for node in {z}:
            if w:
                for w_node in w:
                    if w_node in g and node in g and nx.has_path(g, node, w_node):
                        z_ancestors_of_w.add(node)

        z_to_remove = {z} - z_ancestors_of_w
        for node in z_to_remove:
            parents = list(g.predecessors(node))
            for parent in parents:
                g.remove_edge(parent, node)

        return self._is_d_separated(g, {y}, {z}, x | w)

    def is_identifiable(self, treatment: str, outcome: str) -> tuple[bool, str | None]:
        """
        Check if the causal effect P(outcome | do(treatment)) is identifiable
        from observational data using the causal graph.

        Uses the backdoor criterion as the primary identifiability check.
        Returns (is_identifiable, adjustment_set_or_reason).
        """
        if treatment == outcome:
            return False, "Treatment and outcome are the same variable"

        if treatment not in self.scm.nodes or outcome not in self.scm.nodes:
            missing = []
            if treatment not in self.scm.nodes:
                missing.append(treatment)
            if outcome not in self.scm.nodes:
                missing.append(outcome)
            return False, f"Missing variables: {missing}"

        backdoor_set = self.scm.get_backdoor_adjustment_set(treatment, outcome)
        if backdoor_set is not None:
            if not backdoor_set:
                return True, "No backdoor paths — effect is directly identifiable"
            return True, f"Adjust for: {backdoor_set}"

        frontdoor_set = self._try_frontdoor(treatment, outcome)
        if frontdoor_set:
            return True, f"Frontdoor criterion satisfied via: {frontdoor_set}"

        if self._try_do_calculus_derivation(treatment, outcome):
            return True, "Identifiable via do-calculus derivation"

        return False, "Causal effect is not identifiable from the given graph"

    def _try_frontdoor(self, treatment: str, outcome: str) -> set[str] | None:
        """
        Check the frontdoor criterion for identifiability.

        A set Z satisfies the frontdoor criterion relative to (X, Y) if:
        1. Z intercepts all directed paths from X to Y
        2. There is no unblocked backdoor path from X to Z
        3. All backdoor paths from Z to Y are blocked by X
        """
        candidates = set(self.scm.nodes) - {treatment, outcome}

        for candidate in candidates:
            if not self._intercepts_all_directed_paths(treatment, outcome, candidate):
                continue

            if self.scm.get_backdoor_adjustment_set(treatment, candidate) is None:
                continue

            backdoor_zy = self.scm.get_backdoor_adjustment_set(candidate, outcome)
            if backdoor_zy is None:
                continue

            if treatment in backdoor_zy or self._can_block_with_x(candidate, outcome, treatment):
                return {candidate}

        return None

    def _intercepts_all_directed_paths(self, x: str, y: str, z: str) -> bool:
        """Check if Z lies on all directed paths from X to Y."""
        if x not in self._dag or y not in self._dag or z not in self._dag:
            return False
        if z == x or z == y:
            return False
        try:
            paths = list(nx.all_simple_paths(self._dag, x, y))
        except nx.NetworkXNoPath:
            return False

        if not paths:
            return False

        for path in paths:
            if z not in path:
                return False
        return True

    def _can_block_with_x(self, z: str, y: str, x: str) -> bool:
        """Check if X blocks all backdoor paths from Z to Y."""
        backdoor_paths = self.scm.get_backdoor_paths(z, y)
        if not backdoor_paths:
            return True

        for path in backdoor_paths:
            if x not in path[1:-1]:
                return False
        return True

    def _try_do_calculus_derivation(self, treatment: str, outcome: str) -> bool:
        """
        Attempt to derive P(Y | do(X)) using do-calculus rules.

        This implements a simplified version that tries to apply rules
        sequentially to reduce the query to an observational expression.
        """
        g_do_x = self._mutilated_graph({treatment})

        if _nx_is_d_separator(g_do_x, {outcome}, {treatment}, set()):
            return True

        for node in set(self.scm.nodes) - {treatment, outcome}:
            if _nx_is_d_separator(g_do_x, {outcome}, {node}, {treatment}):
                return True

        return False

    def get_adjustment_formula(
        self, treatment: str, outcome: str
    ) -> tuple[bool, str | None, set[str] | None]:
        """
        Get the adjustment formula for P(outcome | do(treatment)).

        Returns (identifiable, formula_description, adjustment_set).
        """
        identifiable, reason = self.is_identifiable(treatment, outcome)

        if not identifiable:
            return False, None, None

        backdoor_set = self.scm.get_backdoor_adjustment_set(treatment, outcome)
        if backdoor_set is not None:
            if not backdoor_set:
                formula = f"P({outcome} | do({treatment})) = P({outcome} | {treatment})"
            else:
                z_str = ", ".join(sorted(backdoor_set))
                formula = (
                    f"P({outcome} | do({treatment})) = "
                    f"Σ_{z_str} P({outcome} | {treatment}, {z_str}) P({z_str})"
                )
            return True, formula, backdoor_set

        frontdoor = self._try_frontdoor(treatment, outcome)
        if frontdoor:
            z = list(frontdoor)[0]
            formula = (
                f"P({outcome} | do({treatment})) = "
                f"Σ_{z} P({z} | {treatment}) Σ_{treatment}' P({outcome} | {treatment}', {z}) P({treatment}')"
            )
            return True, formula, frontdoor

        return True, "Derivable via do-calculus", set()

    def estimate_ate_from_data(
        self,
        treatment: str,
        outcome: str,
        data: dict[str, list[float]],
    ) -> float | None:
        """
        Estimate Average Treatment Effect from observational data using
        the backdoor adjustment formula.

        ATE = Σ_z [E[Y | X=1, Z=z] - E[Y | X=0, Z=z]] P(Z=z)
        """
        identifiable, _ = self.is_identifiable(treatment, outcome)
        if not identifiable:
            return None

        backdoor_set = self.scm.get_backdoor_adjustment_set(treatment, outcome)
        if backdoor_set is None:
            return None

        if not backdoor_set:
            treatment_vals = data.get(treatment, [])
            outcome_vals = data.get(outcome, [])
            if not treatment_vals or not outcome_vals:
                return None

            treated_outcomes = [
                o for t, o in zip(treatment_vals, outcome_vals, strict=False) if t >= 0.5
            ]
            control_outcomes = [
                o for t, o in zip(treatment_vals, outcome_vals, strict=False) if t < 0.5
            ]

            if not treated_outcomes or not control_outcomes:
                return None

            return float(
                sum(treated_outcomes) / len(treated_outcomes)
                - sum(control_outcomes) / len(control_outcomes)
            )

        return None

    def list_identifiable_effects(self) -> list[tuple[str, str, str | None]]:
        """List all identifiable causal effects in the model."""
        results = []
        nodes = self.scm.nodes
        for treatment in nodes:
            for outcome in nodes:
                if treatment != outcome:
                    identifiable, reason = self.is_identifiable(treatment, outcome)
                    if identifiable:
                        results.append((treatment, outcome, reason))
        return results
