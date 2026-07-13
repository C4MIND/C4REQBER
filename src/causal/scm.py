"""C4REQBER L1 Causal Engine — Structural Causal Models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import networkx as nx
import numpy as np


def _nx_is_d_separator(
    graph: nx.DiGraph,
    x: set[str],
    y: set[str],
    z: set[str],
) -> bool:
    """Call the d-separation API across supported NetworkX releases."""
    modern_api = getattr(nx, "is_d_separator", None)
    if modern_api is not None:
        return bool(modern_api(graph, x, y, z))
    return bool(nx.d_separated(graph, x, y, z))


@dataclass
class CausalNode:
    """A node in a Structural Causal Model representing an endogenous or exogenous variable."""

    name: str
    parents: list[str] = field(default_factory=list)
    mechanism: Callable[..., float] | None = None
    noise_distribution: Callable[[], float] | None = None
    is_exogenous: bool = False
    domain: tuple[float, float] | None = None

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CausalNode):
            return NotImplemented
        return self.name == other.name


@dataclass
class Intervention:
    """Represents a do-intervention: do(X = x)."""

    target: str
    value: float


class StructuralCausalModel:
    """
    Structural Causal Model (SCM) based on Pearl's framework.

    An SCM is a tuple M = <V, U, F, P(U)> where:
    - V: endogenous variables
    - U: exogenous variables
    - F: structural functions (mechanisms)
    - P(U): distribution over exogenous variables
    """

    def __init__(self) -> None:
        self._nodes: dict[str, CausalNode] = {}
        self._dag = nx.DiGraph()
        self._exogenous: set[str] = set()
        self._endogenous: set[str] = set()

    def add_node(
        self,
        name: str,
        parents: list[str] | None = None,
        mechanism: Callable[..., float] | None = None,
        noise: Callable[[], float] | None = None,
        is_exogenous: bool = False,
        domain: tuple[float, float] | None = None,
    ) -> CausalNode:
        """Add a variable to the SCM."""
        if name in self._nodes:
            raise ValueError(f"Node '{name}' already exists")

        parents = parents or []
        node = CausalNode(
            name=name,
            parents=parents,
            mechanism=mechanism,
            noise_distribution=noise,
            is_exogenous=is_exogenous,
            domain=domain,
        )
        self._nodes[name] = node
        self._dag.add_node(name)

        if is_exogenous:
            self._exogenous.add(name)
        else:
            self._endogenous.add(name)

        for parent in parents:
            if parent not in self._nodes:
                raise ValueError(f"Parent node '{parent}' does not exist")
            self._dag.add_edge(parent, name)

        if not nx.is_directed_acyclic_graph(self._dag):
            self._dag.remove_node(name)
            del self._nodes[name]
            if is_exogenous:
                self._exogenous.discard(name)
            else:
                self._endogenous.discard(name)
            raise ValueError(f"Adding node '{name}' creates a cycle")

        return node

    def get_node(self, name: str) -> CausalNode:
        """Retrieve a node by name."""
        if name not in self._nodes:
            raise KeyError(f"Node '{name}' not found")
        return self._nodes[name]

    @property
    def nodes(self) -> list[str]:
        """All variable names in the SCM."""
        return list(self._nodes.keys())

    @property
    def endogenous(self) -> set[str]:
        """Endogenous (observed) variables."""
        return set(self._endogenous)

    @property
    def exogenous(self) -> set[str]:
        """Exogenous (unobserved/noise) variables."""
        return set(self._exogenous)

    @property
    def dag(self) -> nx.DiGraph:
        """The causal DAG."""
        return self._dag.copy()

    def parents(self, node: str) -> list[str]:
        """Direct causes of a node."""
        return list(self._dag.predecessors(node))

    def children(self, node: str) -> list[str]:
        """Direct effects of a node."""
        return list(self._dag.successors(node))

    def ancestors(self, node: str) -> set[str]:
        """All ancestors of a node (transitive closure of parents)."""
        return set(nx.ancestors(self._dag, node))

    def descendants(self, node: str) -> set[str]:
        """All descendants of a node (transitive closure of children)."""
        return set(nx.descendants(self._dag, node))

    def is_d_separated(self, x: str, y: str, conditioning_set: set[str] | None = None) -> bool:
        """
        Check if X and Y are d-separated given a conditioning set Z.

        D-separation is the graphical criterion for conditional independence
        in Bayesian networks and causal DAGs.
        """
        z = conditioning_set or set()
        return _nx_is_d_separator(self._dag, {x}, {y}, z)

    def get_topological_order(self) -> list[str]:
        """Return variables in topological order (causal ordering)."""
        return list(nx.topological_sort(self._dag))

    def sample(
        self, n_samples: int = 1, interventions: list[Intervention] | None = None
    ) -> dict[str, np.ndarray]:
        """
        Generate samples from the SCM, optionally under interventions.

        For interventions, we replace the structural equation of the target
        variable with a constant function returning the intervention value.
        """
        interventions = interventions or []
        intervention_map = {iv.target: iv.value for iv in interventions}

        order = self.get_topological_order()
        samples: dict[str, list[float]] = {name: [] for name in order}

        rng = np.random.default_rng()
        for _ in range(n_samples):
            values: dict[str, float] = {}
            for name in order:
                node = self._nodes[name]
                if name in intervention_map:
                    values[name] = intervention_map[name]
                elif node.is_exogenous:
                    if node.mechanism is not None:
                        values[name] = float(node.mechanism())
                    elif node.noise_distribution is not None:
                        values[name] = float(node.noise_distribution())
                    else:
                        values[name] = float(rng.normal(0, 1))
                else:
                    parent_values = [values[p] for p in node.parents]
                    if node.mechanism is not None:
                        if node.noise_distribution is not None:
                            noise = float(node.noise_distribution())
                        else:
                            noise = float(rng.normal(0, 1))
                        values[name] = float(node.mechanism(*parent_values, noise))
                    else:
                        values[name] = sum(parent_values) if parent_values else 0.0
                samples[name].append(values[name])

        return {name: np.array(vals) for name, vals in samples.items()}

    def intervene(self, intervention: Intervention) -> StructuralCausalModel:
        """
        Create a modified SCM under intervention do(X = x).

        Returns a new SCM where the target variable's mechanism is replaced
        by a constant function. This is the mutilated model M_x.
        """
        new_scm = StructuralCausalModel()

        for name, node in self._nodes.items():
            if name == intervention.target:
                new_scm.add_node(
                    name=name,
                    parents=[],
                    mechanism=_make_constant(intervention.value),
                    is_exogenous=True,
                    domain=node.domain,
                )
            else:
                new_scm.add_node(
                    name=name,
                    parents=node.parents.copy(),
                    mechanism=node.mechanism,
                    noise=node.noise_distribution,
                    is_exogenous=node.is_exogenous,
                    domain=node.domain,
                )

        return new_scm

    def get_interventional_distribution(
        self, target: str, intervention: Intervention, n_samples: int = 10000
    ) -> np.ndarray:
        """
        Estimate P(Y | do(X = x)) via Monte Carlo sampling from the mutilated model.
        """
        mutilated = self.intervene(intervention)
        samples = mutilated.sample(n_samples)
        return samples[target]

    def get_causal_effect(
        self, treatment: str, outcome: str, treatment_value: float = 1.0, control_value: float = 0.0
    ) -> float:
        """
        Compute Average Causal Effect (ACE):
        ACE = E[Y | do(X = 1)] - E[Y | do(X = 0)]
        """
        do_1 = self.get_interventional_distribution(
            outcome, Intervention(treatment, treatment_value), n_samples=200000
        )
        do_0 = self.get_interventional_distribution(
            outcome, Intervention(treatment, control_value), n_samples=200000
        )
        return float(np.mean(do_1) - np.mean(do_0))

    def get_backdoor_paths(self, treatment: str, outcome: str) -> list[list[str]]:
        """
        Find all backdoor paths from treatment to outcome.

        A backdoor path is a path between treatment and outcome with an arrow
        pointing into treatment (i.e., not a directed path from treatment to outcome).
        """
        undirected = self._dag.to_undirected()
        all_paths = list(nx.all_simple_paths(undirected, treatment, outcome))

        backdoor_paths = []
        for path in all_paths:
            if len(path) < 2:
                continue
            if self._dag.has_edge(path[1], treatment):
                backdoor_paths.append(path)

        return backdoor_paths

    def get_backdoor_adjustment_set(self, treatment: str, outcome: str) -> set[str] | None:
        """
        Find a valid backdoor adjustment set using the graphical criterion.

        A set Z satisfies the backdoor criterion relative to (X, Y) if:
        1. Z blocks every backdoor path from X to Y
        2. No node in Z is a descendant of X
        """
        backdoor_paths = self.get_backdoor_paths(treatment, outcome)
        if not backdoor_paths:
            return set()

        candidates = set(self._nodes.keys()) - {treatment, outcome} - self.descendants(treatment)

        for z in candidates:
            blocks_all = True
            for path in backdoor_paths:
                if not self._blocks_path(path, {z}):
                    blocks_all = False
                    break
            if blocks_all:
                return {z}

        for r in range(2, len(candidates) + 1):
            from itertools import combinations

            for combo in combinations(candidates, r):
                blocks_all = True
                for path in backdoor_paths:
                    if not self._blocks_path(path, set(combo)):
                        blocks_all = False
                        break
                if blocks_all:
                    return set(combo)

        return None

    def _blocks_path(self, path: list[str], z: set[str]) -> bool:
        """Check if conditioning set Z blocks a given path."""
        for i in range(1, len(path) - 1):
            node = path[i]
            prev_node = path[i - 1]
            next_node = path[i + 1]

            prev_to_node = self._dag.has_edge(prev_node, node)
            node_to_prev = self._dag.has_edge(node, prev_node)
            node_to_next = self._dag.has_edge(node, next_node)
            next_to_node = self._dag.has_edge(next_node, node)

            is_collider = (prev_to_node or next_to_node) and (node_to_prev or node_to_next)

            if is_collider:
                if node not in z and not any(desc in z for desc in self.descendants(node)):
                    continue
                else:
                    return False
            else:
                if node in z:
                    return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize SCM to dictionary."""
        return {
            "nodes": [
                {
                    "name": n.name,
                    "parents": n.parents,
                    "is_exogenous": n.is_exogenous,
                    "domain": n.domain,
                }
                for n in self._nodes.values()
            ],
            "edges": list(self._dag.edges()),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StructuralCausalModel:
        """Deserialize SCM from dictionary."""
        scm = cls()
        for node_data in data["nodes"]:
            scm.add_node(
                name=node_data["name"],
                parents=node_data.get("parents", []),
                is_exogenous=node_data.get("is_exogenous", False),
                domain=node_data.get("domain"),
            )
        return scm

    def __repr__(self) -> str:
        return f"SCM(nodes={len(self._nodes)}, edges={self._dag.number_of_edges()})"


def _make_constant(value: float) -> Callable[..., float]:
    """Create a constant function for interventions."""

    def _const(*args: Any) -> float:
        return value

    return _const
