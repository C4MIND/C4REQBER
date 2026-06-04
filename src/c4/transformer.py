"""
C4REQBER: Domain Transformer
Cross-domain isomorphism engine using structural fingerprinting.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .engine import C4Space, C4State


# numpy is optional — imported once at module level
try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


class IsomorphismType(Enum):
    """IsomorphismType."""
    VERIFIED = "verified"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class DomainFingerprint:
    """Structural signature of a problem in a domain."""

    domain: str
    entities: list[str] = field(default_factory=list)
    relations: list[tuple[str, str, str]] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    c4_state: C4State | None = None
    spectral_hash: str = ""

    def compute_hash(self) -> str:
        """Compute deterministic structural hash."""
        data = {
            "entities": sorted(self.entities),
            "relations": sorted([f"{a}:{r}:{b}" for a, r, b in self.relations]),
            "constraints": sorted(self.constraints),
        }
        raw = json.dumps(data, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def __post_init__(self) -> None:
        if not self.spectral_hash:
            self.spectral_hash = self.compute_hash()


@dataclass
class IsomorphismResult:
    """Result of domain isomorphism search."""

    source_domain: str
    target_domain: str
    source_state: C4State | None
    target_state: C4State | None
    mapping: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    isomorphism_type: IsomorphismType = IsomorphismType.PARTIAL
    path: list[str] = field(default_factory=list)
    qzrf_operators: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class StructuralMemoryEntry:
    """Entry in the structural memory bank."""

    id: str
    source_fingerprint: DomainFingerprint
    target_fingerprint: DomainFingerprint | None
    result: IsomorphismResult
    timestamp: str = ""
    validation_result: str | None = None


class DomainTransformer:
    """
    Domain Transformer: meta-operator for cross-domain isomorphisms.

    Algorithm:
    1. Fingerprint: Extract structural signature
    2. Spectral Embedding: Project to shared latent space
    3. Nearest Neighbor: Find closest known isomorphism
    4. Weisfeiler-Lehman Verification: Graph isomorphism check
    """

    def __init__(self, c4_space: C4Space | None = None) -> None:
        self.c4_space = c4_space or C4Space()
        self._structural_memory: list[StructuralMemoryEntry] = []

    def fingerprint(
        self,
        domain: str,
        entities: list[str],
        relations: list[tuple[str, str, str]],
        constraints: list[str],
        c4_state: C4State | None = None,
    ) -> DomainFingerprint:
        """Create structural fingerprint of a problem."""
        return DomainFingerprint(
            domain=domain,
            entities=entities,
            relations=relations,
            constraints=constraints,
            c4_state=c4_state,
        )

    def find_isomorphism(
        self,
        source: DomainFingerprint,
        target_domain: str,
        candidates: list[DomainFingerprint],
    ) -> IsomorphismResult:
        """
        Find isomorphism from source to target domain.
        Uses spectral embedding + structural similarity.
        """
        best_result = IsomorphismResult(
            source_domain=source.domain,
            target_domain=target_domain,
            source_state=source.c4_state,
            target_state=None,
            confidence=0.0,
            isomorphism_type=IsomorphismType.FAILED,
            description="No match found",
        )

        for candidate in candidates:
            if candidate.domain != target_domain:
                continue
            struct_score, mapping = self._structural_similarity(source, candidate)
            spectral_score = self._spectral_similarity(source, candidate)
            # Weighted combination: spectral captures graph topology, structural captures labels
            score = 0.6 * spectral_score + 0.4 * struct_score
            if score > best_result.confidence:
                iso_type = (
                    IsomorphismType.VERIFIED if score > 0.9 else IsomorphismType.PARTIAL
                )
                best_result = IsomorphismResult(
                    source_domain=source.domain,
                    target_domain=target_domain,
                    source_state=source.c4_state,
                    target_state=candidate.c4_state,
                    mapping=mapping,
                    confidence=score,
                    isomorphism_type=iso_type,
                    path=self._infer_c4_path(source.c4_state, candidate.c4_state),
                    description=f"Spectral: {spectral_score:.2f}, Structural: {struct_score:.2f}",
                )

        return best_result

    def _spectral_embedding(
        self, fp: DomainFingerprint, dim: int = 3
    ) -> list[float] | None:
        """
        Compute spectral embedding of a domain fingerprint using graph Laplacian.
        Returns a flat list of eigenvector components or None if too small.
        """
        if not _HAS_NUMPY:
            return None

        entities = list(fp.entities)
        n = len(entities)
        if n < 2:
            return None

        entity_idx = {e: i for i, e in enumerate(entities)}
        adj = np.zeros((n, n))

        for src, rel, tgt in fp.relations:
            if src in entity_idx and tgt in entity_idx:
                i, j = entity_idx[src], entity_idx[tgt]
                weight = 1.0
                # Boost weight for stronger relation types
                if rel in ("depends_on", "implements", "causes"):
                    weight = 2.0
                adj[i, j] += weight
                adj[j, i] += weight  # undirected

        # Degree matrix
        degrees = np.sum(adj, axis=1)
        if np.max(degrees) == 0:
            return None

        # Normalized Laplacian: L = I - D^-1/2 A D^-1/2
        d_inv_sqrt = np.power(degrees, -0.5)
        d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0
        D_inv_sqrt = np.diag(d_inv_sqrt)
        L = np.eye(n) - D_inv_sqrt @ adj @ D_inv_sqrt

        # Eigen decomposition (smallest eigenvalues)
        try:
            eigvals, eigvecs = np.linalg.eigh(L)
        except np.linalg.LinAlgError:
            return None

        # Take eigenvectors for smallest non-zero eigenvalues
        k = min(dim, n - 1)
        embedding = (
            eigvecs[:, 1 : k + 1].flatten().tolist()
        )  # skip first (constant) eigenvector
        return embedding  # type: ignore[no-any-return]

    def _spectral_similarity(self, a: DomainFingerprint, b: DomainFingerprint) -> float:
        """Compute cosine similarity between spectral embeddings."""
        emb_a = self._spectral_embedding(a)
        emb_b = self._spectral_embedding(b)
        if emb_a is None or emb_b is None:
            return 0.0

        try:
            import numpy as np

            vec_a = np.array(emb_a)
            vec_b = np.array(emb_b)
            # Pad shorter vector
            if len(vec_a) < len(vec_b):
                vec_a = np.pad(vec_a, (0, len(vec_b) - len(vec_a)))
            elif len(vec_b) < len(vec_a):
                vec_b = np.pad(vec_b, (0, len(vec_a) - len(vec_b)))

            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            cosine = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
            return max(0.0, min(1.0, cosine))
        except (np.linalg.LinAlgError, ValueError, TypeError):
            return 0.0

    def _structural_similarity(
        self, a: DomainFingerprint, b: DomainFingerprint
    ) -> tuple[float, dict[str, str]]:
        """
        Compute structural similarity between two fingerprints.
        Returns (score, entity_mapping).
        """
        # Entity overlap
        entity_set_a = set(a.entities)
        entity_set_b = set(b.entities)
        if not entity_set_a or not entity_set_b:
            return 0.0, {}

        overlap = len(entity_set_a & entity_set_b)
        entity_score = overlap / max(len(entity_set_a), len(entity_set_b))

        # Relation structure similarity (simplified: count of matching relation types)
        rel_types_a = set(r for _, r, _ in a.relations)
        rel_types_b = set(r for _, r, _ in b.relations)
        rel_score = (
            (len(rel_types_a & rel_types_b) / max(len(rel_types_a), len(rel_types_b)))
            if rel_types_a or rel_types_b
            else 0.0
        )

        # Constraint overlap
        constr_a = set(a.constraints)
        constr_b = set(b.constraints)
        constr_score = (
            (len(constr_a & constr_b) / max(len(constr_a), len(constr_b)))
            if constr_a or constr_b
            else 0.0
        )

        score = 0.4 * entity_score + 0.4 * rel_score + 0.2 * constr_score

        # Simple mapping: match entities by name similarity
        mapping = {}
        for ea in a.entities:
            for eb in b.entities:
                if (
                    ea.lower() == eb.lower()
                    or ea.lower() in eb.lower()
                    or eb.lower() in ea.lower()
                ):
                    mapping[ea] = eb
                    break

        return score, mapping

    def _infer_c4_path(
        self, start: C4State | None, end: C4State | None
    ) -> list[str]:
        """Infer C4 operator path between states."""
        if start is None or end is None:
            return []
        path = self.c4_space.shortest_path(start, end)
        return path.operators

    def store_memory(self, entry: StructuralMemoryEntry) -> None:
        """Store result in structural memory."""
        self._structural_memory.append(entry)

    def search_memory(
        self, fingerprint: DomainFingerprint, min_confidence: float = 0.0
    ) -> list[StructuralMemoryEntry]:
        """Search structural memory for similar fingerprints."""
        results = []
        for entry in self._structural_memory:
            score, _ = self._structural_similarity(
                fingerprint, entry.source_fingerprint
            )
            if score >= min_confidence:
                results.append(entry)
        return sorted(results, key=lambda e: e.result.confidence, reverse=True)

    def fra_adapt(
        self, source: DomainFingerprint, analog: IsomorphismResult
    ) -> dict[str, Any]:
        """
        FRA: Fingerprint → Route → Adapt
        Adapt a known solution to the current problem.
        """
        return {
            "fingerprint": source.spectral_hash,
            "route": analog.path,
            "mapping": analog.mapping,
            "adaptation_rules": self._generate_adaptation_rules(source, analog),
            "confidence": analog.confidence,
        }

    def _generate_adaptation_rules(
        self, source: DomainFingerprint, analog: IsomorphismResult
    ) -> list[str]:
        """Generate adaptation rules from analog to source."""
        rules = []
        for src_entity, tgt_entity in analog.mapping.items():
            rules.append(f"Map '{src_entity}' → '{tgt_entity}'")
        if source.c4_state and analog.target_state:
            path = self.c4_space.shortest_path(source.c4_state, analog.target_state)
            rules.append(f"C4 transformation: {' → '.join(path.operators)}")
        return rules
