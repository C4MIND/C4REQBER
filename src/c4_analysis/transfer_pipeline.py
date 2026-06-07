"""
C44TCDI: Cross-Domain Innovation Transfer Pipeline
Wires the isomorphism engine into an end-to-end transfer pipeline.
Adds graph-based structural isomorphism, dimensional consistency,
and conservation law preservation checks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import numpy as np

from src.c4.engine import C4Space
from src.c4.transformer import (
    DomainFingerprint,
    DomainTransformer,
    IsomorphismResult,
    IsomorphismType,
)
from src.memory.isomorphism_seed import ISOMORPHISM_SEED


# Domain keywords for cross-domain detection
_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "biology": {
        "cell", "organism", "gene", "protein", "dna", "rna", "enzyme", "metabolism",
        "evolution", "species", "ecosystem", "tissue", "organ", "immune", "neuron",
        "synapse", "membrane", "receptor", "hormone", "virus", "bacteria", "drug",
        "delivery", "pharmaceutical", "biological", "life", "living", "growth",
        "antibody", "pathogen", "circulation", "diffusion",
    },
    "fluid_dynamics": {
        "fluid", "flow", "turbulence", "vortex", "viscosity", "reynolds", "navier",
        "stokes", "aerodynamic", "hydrodynamic", "pressure", "velocity", "stream",
        "boundary", "layer", "drag", "lift", "current", "liquid", "gas", "plasma",
        "convection", "diffusion", "porous", "pipe", "channel", "jet", "wake",
        "laminar", "turbulent", "shear", "strain",
    },
    "neural_networks": {
        "neural", "network", "deep", "learning", "gradient", "backpropagation",
        "activation", "weight", "layer", "neuron", "perceptron", "cnn", "rnn",
        "transformer", "attention", "embedding", "training", "inference", "model",
        "dropout", "batch", "epoch", "overfitting",
    },
    "thermodynamics": {
        "entropy", "energy", "heat", "temperature", "thermal", "equilibrium",
        "free energy", "enthalpy", "carnot", "refrigeration", "cycle", "engine",
        "work", "transfer", "conduction", "radiation", "exergy", "boltzmann",
    },
    "quantum_mechanics": {
        "quantum", "wavefunction", "superposition", "entanglement", "tunneling",
        "particle", "photon", "electron", "spin", "qubit", "interference",
        "observable", "hamiltonian", "eigenstate", "coherence", "decoherence",
    },
    "optimization": {
        "optimize", "gradient", "descent", "sgd", "adam", "momentum", "minimum",
        "maximum", "convex", "constraint", "objective", "loss", "cost", "function",
        "search", "heuristic", "genetic", "algorithm", "solver", "scheduler",
    },
    "machine_learning": {
        "machine learning", "ml", "supervised", "unsupervised", "reinforcement",
        "classification", "regression", "clustering", "feature", "dataset",
        "overfitting", "underfitting", "generalization", "validation", "latent",
    },
    "control_theory": {
        "control", "feedback", "pid", "stability", "system", "dynamics",
        "input", "output", "state space", "transfer function", "controller",
        "actuator", "sensor", "loop", "regulator", "servo", "setpoint",
    },
    "materials_science": {
        "material", "crystal", "lattice", "alloy", "polymer", "ceramic",
        "composite", "microstructure", "phase", "diffusion", "dislocation",
        "stress", "strain", "elastic", "plastic", "fracture", "fatigue",
        "annealing", "quenching", "hardening",
    },
    "economics": {
        "market", "price", "supply", "demand", "equilibrium", "gdp", "inflation",
        "trade", "investment", "capital", "risk", "portfolio", "game theory",
        "auction", "behavioral", "macro", "micro", "crash", "bubble",
    },
    "network_science": {
        "graph", "network", "node", "edge", "centrality", "clustering",
        "path", "connectivity", "topology", "small world", "scale free",
        "community", "degree", "adjacency", "bipartite", "modularity",
    },
    "physics": {
        "force", "field", "potential", "wave", "oscillation", "resonance",
        "electromagnetic", "gravity", "relativity", "mechanics", "optics",
        "acoustics", "kinematics", "momentum", "energy", "mass", "phase",
    },
    "ecology": {
        "ecosystem", "species", "population", "predator", "prey", "biodiversity",
        "niche", "habitat", "competition", "symbiosis", "food web", "invasive",
        "conservation", "sustainability", "carbon", "climate", "extinction",
    },
    "information_theory": {
        "information", "entropy", "channel", "capacity", "coding", "compression",
        "noise", "shannon", "bitrate", "mutual information", "kullback",
        "divergence", "source", "transmission", "decode",
    },
    "continual_learning": {
        "continual", "lifelong", "catastrophic forgetting", "task", "replay",
        "elastic", "consolidation", "ewc", "knowledge retention", "transfer",
    },
}


# Dimensional analysis registry: entity -> base dimensions [L, M, T, I, Θ, N, J]
# L=length, M=mass, T=time, I=current, Θ=temperature, N=amount, J=luminous intensity
_DIMENSIONAL_REGISTRY: dict[str, list[float]] = {
    # Mechanics
    "velocity": [1, 0, -1, 0, 0, 0, 0],
    "speed": [1, 0, -1, 0, 0, 0, 0],
    "acceleration": [1, 0, -2, 0, 0, 0, 0],
    "force": [1, 1, -2, 0, 0, 0, 0],
    "energy": [2, 1, -2, 0, 0, 0, 0],
    "power": [2, 1, -3, 0, 0, 0, 0],
    "pressure": [-1, 1, -2, 0, 0, 0, 0],
    "stress": [-1, 1, -2, 0, 0, 0, 0],
    "strain": [0, 0, 0, 0, 0, 0, 0],
    "mass": [0, 1, 0, 0, 0, 0, 0],
    "density": [-3, 1, 0, 0, 0, 0, 0],
    "momentum": [1, 1, -1, 0, 0, 0, 0],
    "angular_momentum": [2, 1, -1, 0, 0, 0, 0],
    "frequency": [0, 0, -1, 0, 0, 0, 0],
    "diffusion_coefficient": [2, 0, -1, 0, 0, 0, 0],
    "viscosity": [-1, 1, -1, 0, 0, 0, 0],
    # Electromagnetism
    "voltage": [2, 1, -3, -1, 0, 0, 0],
    "current": [0, 0, 0, 1, 0, 0, 0],
    "resistance": [2, 1, -3, -2, 0, 0, 0],
    "capacitance": [-2, -1, 4, 2, 0, 0, 0],
    "inductance": [2, 1, -2, -2, 0, 0, 0],
    "electric_field": [1, 1, -3, -1, 0, 0, 0],
    "magnetic_field": [0, 1, -2, -1, 0, 0, 0],
    # Thermodynamics
    "temperature": [0, 0, 0, 0, 1, 0, 0],
    "entropy": [2, 1, -2, 0, -1, 0, 0],
    "heat_capacity": [2, 1, -2, 0, -1, 0, 0],
    "thermal_conductivity": [1, 1, -3, 0, -1, 0, 0],
}


# Conservation laws by domain
_CONSERVATION_LAWS: dict[str, list[str]] = {
    "physics": ["energy", "momentum", "angular_momentum", "charge"],
    "fluid_dynamics": ["mass", "momentum", "energy"],
    "thermodynamics": ["energy", "entropy"],
    "electromagnetics": ["charge", "energy"],
    "mechanics": ["energy", "momentum"],
    "control_theory": ["stability", "controllability"],
    "neural_networks": ["information", "gradient_flow"],
    "machine_learning": ["information", "generalization"],
}


@dataclass
class StructuralIsomorphismResult:
    """Result of graph-based structural isomorphism check."""

    mapping: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    structural_preserved: bool = False
    dimensional_consistent: bool = False
    conservation_preserved: bool = False
    node_match_ratio: float = 0.0
    edge_match_ratio: float = 0.0
    dimensional_violations: list[str] = field(default_factory=list)
    missing_conservation_laws: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mapping": self.mapping,
            "confidence": self.confidence,
            "structural_preserved": self.structural_preserved,
            "dimensional_consistent": self.dimensional_consistent,
            "conservation_preserved": self.conservation_preserved,
            "node_match_ratio": self.node_match_ratio,
            "edge_match_ratio": self.edge_match_ratio,
            "dimensional_violations": self.dimensional_violations,
            "missing_conservation_laws": self.missing_conservation_laws,
        }


@dataclass
class TransferResult:
    """Result of a cross-domain innovation transfer."""

    problem: str
    source_domain: str
    target_domain: str
    mappings: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    triggered_auto: bool = False
    description: str = ""
    adaptation_rules: list[str] = field(default_factory=list)
    triz_principles: list[int] = field(default_factory=list)
    isomorphism_type: str = "failed"
    structural_result: StructuralIsomorphismResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "source_domain": self.source_domain,
            "target_domain": self.target_domain,
            "mappings": self.mappings,
            "confidence": self.confidence,
            "triggered_auto": self.triggered_auto,
            "description": self.description,
            "adaptation_rules": self.adaptation_rules,
            "triz_principles": self.triz_principles,
            "isomorphism_type": self.isomorphism_type,
            "structural_result": self.structural_result.to_dict()
            if self.structural_result
            else None,
        }


def detect_cross_domain(problem: str) -> list[str]:
    """
    Detect which domains are present in a problem statement.
    Returns list of domain names with >=2 keywords matched.
    """
    p_lower = problem.lower()
    found_domains: list[str] = []
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in p_lower)
        if matches >= 2:
            found_domains.append(domain)
    return found_domains


def should_auto_trigger(problem: str) -> bool:
    """Check if c4_fingerprint should auto-trigger cross-domain transfer."""
    return len(detect_cross_domain(problem)) >= 2


def _seed_to_fingerprint(seed: dict[str, Any]) -> DomainFingerprint:
    """Convert an isomorphism seed to a DomainFingerprint."""
    mapping = seed.get("mapping", "")
    entities: list[str] = []
    relations: list[tuple[str, str, str]] = []
    if "↔" in mapping:
        parts = [p.strip() for p in mapping.split("↔")]
        entities.extend(parts)
        if len(parts) == 2:
            relations.append((parts[0], "isomorphic_to", parts[1]))
    else:
        # Fallback: extract nouns from mapping text
        words = re.findall(r"\b\w{4,}\b", mapping.lower())
        entities = list(dict.fromkeys(words))[:4]
    constraints: list[str] = []
    if seed.get("triz"):
        constraints.append(f"triz:{','.join(str(t) for t in seed['triz'])}")
    return DomainFingerprint(
        domain=seed.get("source", "unknown"),
        entities=entities,
        relations=relations,
        constraints=constraints,
    )


def _seeds_to_candidates(seeds: list[dict[str, Any]]) -> list[DomainFingerprint]:
    """Convert isomorphism seeds to fingerprint candidates (both source and target)."""
    candidates: list[DomainFingerprint] = []
    for seed in seeds:
        # Source-domain fingerprint
        fp_src = _seed_to_fingerprint(seed)
        candidates.append(fp_src)
        # Target-domain fingerprint (swap source/target for reverse lookup)
        mapping = seed.get("mapping", "")
        entities: list[str] = []
        relations: list[tuple[str, str, str]] = []
        if "↔" in mapping:
            parts = [p.strip() for p in mapping.split("↔")]
            entities.extend(parts)
            if len(parts) == 2:
                relations.append((parts[1], "isomorphic_to", parts[0]))
        else:
            words = re.findall(r"\b\w{4,}\b", mapping.lower())
            entities = list(dict.fromkeys(words))[:4]
        constraints: list[str] = []
        if seed.get("triz"):
            constraints.append(f"triz:{','.join(str(t) for t in seed['triz'])}")
        fp_tgt = DomainFingerprint(
            domain=seed.get("target", "unknown"),
            entities=entities,
            relations=relations,
            constraints=constraints,
        )
        candidates.append(fp_tgt)
    return candidates


def extract_ontology_graph(problem: str) -> nx.DiGraph:
    """
    Extract an ontology graph from problem text.
    Entities become nodes, detected relations become edges.
    """
    G = nx.DiGraph()
    cleaned = re.sub(r"[^\w\s-]", " ", problem.lower())
    words = cleaned.split()

    # Extract candidate entities (nouns / meaningful terms)
    entities: list[str] = []
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "and", "but", "or", "yet", "so", "if",
        "because", "although", "though", "while", "where", "when", "that",
        "which", "who", "whom", "whose", "what", "this", "these", "those",
        "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
        "us", "them", "my", "your", "his", "its", "our", "their", "how",
        "why", "there", "here", "then", "than", "only", "also",
        "just", "even", "not", "no", "nor", "all", "any", "both", "each",
        "few", "more", "most", "other", "some", "such", "one", "two",
    }
    for word in words:
        w = word.strip("-").lower()
        if not w or len(w) < 3 or w.isdigit() or w in stopwords:
            continue
        entities.append(w)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_entities: list[str] = []
    for e in entities:
        if e not in seen:
            seen.add(e)
            unique_entities.append(e)

    # Add nodes
    for ent in unique_entities[:30]:
        G.add_node(ent)

    # Detect relations using simple patterns
    relation_patterns: list[tuple[list[str], str]] = [
        (["causes", "causing", "leads", "produces", "generates"], "causes"),
        (["depends", "requires", "needs", "relies"], "depends_on"),
        (["inhibits", "prevents", "blocks", "suppresses"], "inhibits"),
        (["converts", "transforms", "changes"], "converts_to"),
        (["is", "are", "was", "were"], "is_a"),
        (["has", "have", "had", "contains", "includes"], "has_property"),
        (["increases", "decreases", "reduces", "enhances", "modulates"], "modulates"),
        (["flows", "moves", "transfers", "propagates", "diffuses"], "flows_to"),
        (["represents", "models", "simulates", "maps"], "represents"),
        (["feedback", "coupling", "linkage", "connection"], "coupled_to"),
    ]

    text_lower = problem.lower()
    for ent_a in unique_entities[:20]:
        for ent_b in unique_entities[:20]:
            if ent_a == ent_b:
                continue
            # Check if both appear near each other
            idx_a = text_lower.find(ent_a)
            idx_b = text_lower.find(ent_b)
            if idx_a == -1 or idx_b == -1:
                continue
            window = text_lower[
                max(0, min(idx_a, idx_b) - 30) : min(len(text_lower), max(idx_a, idx_b) + 30)
            ]
            for keywords, rel_type in relation_patterns:
                if any(kw in window for kw in keywords):
                    G.add_edge(ent_a, ent_b, relation=rel_type)
                    break

    return G


def _dimensional_signature(entity: str) -> list[float] | None:
    """Look up dimensional signature for an entity."""
    ent_lower = entity.lower().replace("_", " ").replace("-", " ")
    for key, dims in _DIMENSIONAL_REGISTRY.items():
        key_lower = key.lower().replace("_", " ").replace("-", " ")
        if key_lower in ent_lower or ent_lower in key_lower:
            return dims
    return None


def check_dimensional_consistency(
    source_graph: nx.DiGraph,
    target_graph: nx.DiGraph,
    mapping: dict[str, str],
) -> tuple[bool, list[str]]:
    """
    Check that mapped entities have compatible dimensional signatures.
    Returns (consistent, list_of_violations).
    """
    violations: list[str] = []
    if not mapping:
        return False, ["No mapping provided for dimensional check"]

    for src_ent, tgt_ent in mapping.items():
        src_dims = _dimensional_signature(src_ent)
        tgt_dims = _dimensional_signature(tgt_ent)
        if src_dims is None or tgt_dims is None:
            continue
        src_arr = np.array(src_dims, dtype=float)
        tgt_arr = np.array(tgt_dims, dtype=float)
        # Exact match required for full consistency
        if not np.allclose(src_arr, tgt_arr):
            violations.append(
                f"Dimensional mismatch: {src_ent} {src_dims} -> {tgt_ent} {tgt_dims}"
            )

    return len(violations) == 0, violations


def check_conservation_laws(
    domain: str,
    graph: nx.DiGraph,
) -> tuple[bool, list[str]]:
    """
    Check whether known conservation laws for a domain are represented in the graph.
    Returns (preserved, list_of_missing_laws).
    """
    domain_lower = domain.lower().replace(" ", "_").replace("-", "_")
    laws = []
    for d, l in _CONSERVATION_LAWS.items():
        if d in domain_lower or domain_lower in d:
            laws.extend(l)
    if not laws:
        # Default physics laws for generic domains
        laws = ["energy", "momentum"]

    nodes_lower = {n.lower() for n in graph.nodes()}
    missing: list[str] = []
    for law in laws:
        # Check if any node contains the law concept
        found = any(law in node for node in nodes_lower)
        if not found:
            missing.append(law)

    return len(missing) == 0, missing


def graph_isomorphism_match(
    source_graph: nx.DiGraph,
    target_graph: nx.DiGraph,
) -> StructuralIsomorphismResult:
    """
    Use networkx GraphMatcher (VF2) to find structural isomorphism.
    Returns detailed structural match result.
    """
    result = StructuralIsomorphismResult()

    if len(source_graph.nodes()) == 0 or len(target_graph.nodes()) == 0:
        result.dimensional_violations.append("Empty source or target graph")
        return result

    # Use VF2 algorithm via networkx (DiGraphMatcher for directed graphs)
    matcher = nx.isomorphism.DiGraphMatcher(
        source_graph,
        target_graph,
        node_match=lambda n1, n2: True,  # Generic node match
        edge_match=lambda e1, e2: True,  # Generic edge match
    )

    is_isomorphic = matcher.is_isomorphic()
    result.structural_preserved = is_isomorphic

    if is_isomorphic:
        result.mapping = dict(matcher.mapping)
        result.confidence = 1.0
        result.node_match_ratio = 1.0
        result.edge_match_ratio = 1.0
    else:
        # Find largest common subgraph approximation
        # Use subgraph isomorphism only for small graphs (VF2 is exponential)
        best_mapping: dict[str, str] = {}
        best_size = 0
        max_nodes_for_vf2 = 12
        if (
            len(source_graph.nodes()) <= max_nodes_for_vf2
            and len(target_graph.nodes()) <= max_nodes_for_vf2
        ):
            try:
                for mapping in matcher.subgraph_isomorphisms_iter():
                    if len(mapping) > best_size:
                        best_size = len(mapping)
                        best_mapping = dict(mapping)
            except (ValueError, TypeError):
                pass  # Fallback to greedy approximation
        else:
            # Greedy approximation: match nodes by degree similarity
            src_degrees = dict(source_graph.degree())
            tgt_degrees = dict(target_graph.degree())
            sorted_src = sorted(src_degrees, key=lambda k: src_degrees[k], reverse=True)
            sorted_tgt = sorted(tgt_degrees, key=lambda k: tgt_degrees[k], reverse=True)
            for src_node, tgt_node in zip(sorted_src, sorted_tgt, strict=False):
                best_mapping[src_node] = tgt_node
                best_size += 1

        result.mapping = best_mapping
        result.node_match_ratio = (
            best_size / max(len(source_graph.nodes()), len(target_graph.nodes()))
            if source_graph.nodes() or target_graph.nodes()
            else 0.0
        )
        result.edge_match_ratio = (
            best_size / max(len(source_graph.edges()), len(target_graph.edges()))
            if source_graph.edges() or target_graph.edges()
            else 0.0
        )
        result.confidence = round(
            0.5 * result.node_match_ratio + 0.5 * result.edge_match_ratio, 4
        )

    return result


class TransferPipeline:
    """
    Cross-Domain Innovation Transfer Pipeline.
    Uses DomainTransformer + pre-computed isomorphism seeds + graph isomorphism.
    """

    def __init__(self, c4_space: C4Space | None = None) -> None:
        self.c4_space = c4_space or C4Space()
        self.transformer = DomainTransformer(self.c4_space)
        self._seeds: list[dict[str, Any]] = ISOMORPHISM_SEED
        self._candidates = _seeds_to_candidates(self._seeds)

    def transfer(
        self,
        problem: str,
        source_domain: str,
        target_domain: str,
        auto_triggered: bool = False,
    ) -> TransferResult:
        """
        Execute cross-domain transfer from source to target domain.
        """
        source_norm = source_domain.lower().replace(" ", "_").replace("-", "_")
        target_norm = target_domain.lower().replace(" ", "_").replace("-", "_")

        entities = self._extract_entities(problem)
        source_fp = self.transformer.fingerprint(
            domain=source_norm,
            entities=entities,
            relations=[],
            constraints=[],
        )

        # Extract ontology graphs from problem text
        source_graph = extract_ontology_graph(problem)
        target_graph = extract_ontology_graph(
            f"Transfer from {source_domain} to {target_domain}: {problem}"
        )

        # Graph-based structural isomorphism check
        structural_result = graph_isomorphism_match(source_graph, target_graph)

        # Dimensional consistency check
        dim_consistent, dim_violations = check_dimensional_consistency(
            source_graph, target_graph, structural_result.mapping
        )
        structural_result.dimensional_consistent = dim_consistent
        structural_result.dimensional_violations = dim_violations

        # Conservation law check
        cons_preserved, missing_cons = check_conservation_laws(
            source_norm, source_graph
        )
        structural_result.conservation_preserved = cons_preserved
        structural_result.missing_conservation_laws = missing_cons

        # First: look for exact seed matches by domain pair
        exact_seeds = [
            s
            for s in self._seeds
            if s.get("source") == source_norm and s.get("target") == target_norm
        ]

        if exact_seeds:
            # Use best exact seed match
            seed = max(exact_seeds, key=lambda s: s.get("confidence", 0))
            transfer_result = TransferResult(
                problem=problem,
                source_domain=source_domain,
                target_domain=target_domain,
                confidence=seed.get("confidence", 0.0),
                triggered_auto=auto_triggered,
                description=f"Exact seed match: {seed.get('mapping', '')}",
                isomorphism_type="verified",
                structural_result=structural_result,
            )
            transfer_result.mappings.append({
                "mapping": seed.get("mapping", ""),
                "confidence": seed.get("confidence", 0),
                "applications": seed.get("applications", ""),
            })
            transfer_result.triz_principles = seed.get("triz", [])
            # Build a synthetic isomorphism result for adaptation
            iso_result = IsomorphismResult(
                source_domain=source_norm,
                target_domain=target_norm,
                source_state=None,
                target_state=None,
                confidence=seed.get("confidence", 0.0),
                isomorphism_type=IsomorphismType.VERIFIED,
                description=seed.get("mapping", ""),
            )
            adaptation = self.transformer.fra_adapt(source_fp, iso_result)
            transfer_result.adaptation_rules = adaptation.get(
                "adaptation_rules", []
            )
            return transfer_result

        # Fallback: use structural isomorphism search
        result = self.transformer.find_isomorphism(
            source=source_fp,
            target_domain=target_norm,
            candidates=self._candidates,
        )

        transfer_result = TransferResult(
            problem=problem,
            source_domain=source_domain,
            target_domain=target_domain,
            confidence=result.confidence,
            triggered_auto=auto_triggered,
            description=result.description,
            isomorphism_type=result.isomorphism_type.value,
            structural_result=structural_result,
        )

        if result.isomorphism_type != IsomorphismType.FAILED:
            matching_seeds = [
                s
                for s in self._seeds
                if s.get("source") == source_norm and s.get("target") == target_norm
            ]
            if matching_seeds:
                seed = max(matching_seeds, key=lambda s: s.get("confidence", 0))
                transfer_result.mappings.append({
                    "mapping": seed.get("mapping", ""),
                    "confidence": seed.get("confidence", 0),
                    "applications": seed.get("applications", ""),
                })
                transfer_result.triz_principles = seed.get("triz", [])

            adaptation = self.transformer.fra_adapt(source_fp, result)
            transfer_result.adaptation_rules = adaptation.get(
                "adaptation_rules", []
            )

        return transfer_result

    def _extract_entities(self, problem: str) -> list[str]:
        """Extract candidate entities from problem text."""
        cleaned = re.sub(r"[^\w\s-]", " ", problem)
        words = cleaned.split()
        entities: list[str] = []
        for word in words:
            w = word.strip("-").lower()
            if not w or len(w) < 3 or w.isdigit():
                continue
            entities.append(w)
        seen: set[str] = set()
        result: list[str] = []
        for e in entities:
            if e not in seen:
                seen.add(e)
                result.append(e)
        return result[:15]


def c4_transfer(
    problem: str,
    source_domain: str,
    target_domain: str,
) -> TransferResult:
    """
    Public API: Execute cross-domain innovation transfer.
    """
    pipeline = TransferPipeline()
    return pipeline.transfer(problem, source_domain, target_domain)


def cross_domain_transfer(
    problem: str,
    source_domain: str | None = None,
    target_domain: str | None = None,
) -> TransferResult:
    """
    Pipeline integration step: auto-detect domains if not provided.
    """
    if source_domain and target_domain:
        return c4_transfer(problem, source_domain, target_domain)

    detected = detect_cross_domain(problem)
    if len(detected) >= 2:
        src = source_domain or detected[0]
        tgt = target_domain or detected[1]
        result = c4_transfer(problem, src, tgt)
        result.triggered_auto = True
        return result

    return c4_transfer(
        problem,
        source_domain or "general",
        target_domain or "machine_learning",
    )
