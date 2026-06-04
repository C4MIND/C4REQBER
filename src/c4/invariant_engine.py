# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
import math
from typing import Any


logger = logging.getLogger(__name__)

# Try optional ML dependencies
_HAS_SBERT = False
_HAS_SCIPY = False
_HAS_NETWORKX = False
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

try:
    from scipy.sparse import csr_matrix
    from scipy.spatial.distance import cosine as cosine_distance
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

try:
    import networkx as nx
    _HAS_NETWORKX = True
except ImportError:
    _HAS_NETWORKX = False


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Embedder — SciBERT / sentence-transformers
# ═══════════════════════════════════════════════════════════════════════════════

class DomainEmbedder:
    """Embed domain descriptions into a shared vector space.

    Tries sentence-transformers. Falls back to TF-IDF bag-of-words.
    Loads lazily — first embed() call triggers model download.
    """

    def __init__(self) -> None:
        self._model: Any = None
        self._loaded = False
        self._tfidf_vocab: dict[str, int] = {}
        self._tfidf_df: dict[str, float] = {}

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            logger.debug("sentence-transformers unavailable — using TF-IDF fallback")

    def embed(self, text: str) -> list[float]:
        """Embed."""
        self._ensure_loaded()
        if self._model is not None:
            try:
                vec = self._model.encode(text, convert_to_numpy=True)
                return [float(v) for v in vec]
            except Exception:
                logger.warning("Sentence-BERT embed failed, falling back to TF-IDF")
        return self._tfidf_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        self._ensure_loaded()
        if self._model is not None:
            try:
                vecs = self._model.encode(texts, convert_to_numpy=True)
                return [[float(v) for v in vec] for vec in vecs]
            except Exception:
                logger.warning("Sentence-BERT batch embed failed, falling back to TF-IDF")
        return [self._tfidf_embed(t) for t in texts]

    def _tfidf_embed(self, text: str) -> list[float]:
        tokens = text.lower().split()
        fixed_dim = 256
        vec = [0.0] * fixed_dim
        for t in tokens:
            h = hash(t) % fixed_dim
            freq = self._tfidf_df.get(t, 0) + 1
            self._tfidf_df[t] = freq
            vec[h] += math.log(1 + freq)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def cosine(a: list[float], b: list[float]) -> float:
        """Cosine."""
        if _HAS_SCIPY and _HAS_NUMPY:
            return float(1 - cosine_distance(np.array(a), np.array(b)))
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)


# ═══════════════════════════════════════════════════════════════════════════════
# Structure Extractor — parse domain structure from text
# ═══════════════════════════════════════════════════════════════════════════════

class StructureExtractor:
    """Extract structural graph from domain text.

    Builds entity-relation-entity triples from equations, dependencies, dimensions.
    """

    DIMENSION_REGISTRY = {
        "mass": "M", "length": "L", "time": "T", "temperature": "Θ",
        "current": "I", "amount": "N", "luminous": "J",
        "energy": "ML²T⁻²", "force": "MLT⁻²", "pressure": "ML⁻¹T⁻²",
        "velocity": "LT⁻¹", "acceleration": "LT⁻²", "frequency": "T⁻¹",
        "power": "ML²T⁻³", "entropy": "ML²T⁻²Θ⁻¹", "voltage": "ML²T⁻³I⁻¹",
    }

    RELATION_INDICATORS = {
        "causes": "→", "leads_to": "→", "results_in": "→", "produces": "→",
        "depends_on": "←", "requires": "←", "governed_by": "←",
        "inhibits": "⊣", "suppresses": "⊣", "blocks": "⊣",
        "interacts_with": "↔", "coupled_with": "↔", "correlates": "↔",
        "is_a": "⊂", "instance_of": "⊂", "belongs_to": "⊂",
    }

    def extract(self, text: str) -> dict[str, Any]:
        """Extract."""
        text_lower = text.lower()

        entities: list[str] = []
        seen: set[str] = set()
        for word in text_lower.replace(",", " ").replace(".", " ").split():
            w = word.strip("()[]{}:;\"'")
            if len(w) > 3 and w not in seen:
                entities.append(w)
                seen.add(w)

        relations: list[dict[str, str]] = []
        for phrase, rel_type in self.RELATION_INDICATORS.items():
            if phrase in text_lower:
                # Find entities around the phrase
                idx = text_lower.find(phrase)
                bef = text_lower[:idx].split()[-3:]
                aft = text_lower[idx + len(phrase):].split()[:3]
                for s in bef:
                    for t in aft:
                        if s in seen and t in seen and s != t:
                            relations.append({"source": s, "target": t, "type": rel_type})

        dimensions: dict[str, str] = {}
        for entity in entities[:30]:
            for dim_name, dim_formula in self.DIMENSION_REGISTRY.items():
                if dim_name in entity.lower():
                    dimensions[entity] = dim_formula
                    break

        return {
            "entities": entities[:30],
            "relations": relations[:50],
            "dimensions": dimensions,
            "entity_count": len(entities),
            "relation_count": len(relations),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Weisfeiler-Lehman Kernel — fuzzy graph matching
# ═══════════════════════════════════════════════════════════════════════════════

class WeisfeilerLehmanKernel:
    """WL subtree kernel for graph structure similarity.

    Compares two domain graphs via k-iteration label refinement.
    O(n·m·k) — practical for graphs up to ~1000 nodes.
    """

    def __init__(self, iterations: int = 3) -> None:
        self.iterations = iterations

    def similarity(
        self,
        g1: dict[str, list[str]],
        g2: dict[str, list[str]],
    ) -> float:
        """Compute WL kernel similarity between two graphs."""
        labels1 = {n: hash(n) & 0xFFFFFFFF for n in g1}
        labels2 = {n: hash(n) & 0xFFFFFFFF for n in g2}

        vec1: dict[int, int] = {}
        vec2: dict[int, int] = {}

        for _ in range(self.iterations):
            vec1 = {}
            for n in g1:
                label = labels1[n]
                vec1[label] = vec1.get(label, 0) + 1

            vec2 = {}
            for n in g2:
                label = labels2[n]
                vec2[label] = vec2.get(label, 0) + 1

            # Refine labels
            labels1 = self._refine(g1, labels1)
            labels2 = self._refine(g2, labels2)

        return self._cosine_vec(vec1, vec2)

    def _refine(self, graph: dict[str, list[str]], labels: dict[str, int]) -> dict[str, int]:
        new_labels: dict[str, int] = {}
        for node, neighbors in graph.items():
            neighbor_labels = tuple(sorted(labels.get(n, 0) for n in neighbors))
            combined = (labels[node], neighbor_labels)
            new_labels[node] = hash(combined) & 0xFFFFFFFF
        return new_labels

    @staticmethod
    def _cosine_vec(a: dict[int, int], b: dict[int, int]) -> float:
        keys = set(a) | set(b)
        dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)


# ═══════════════════════════════════════════════════════════════════════════════
# Transfer Engine — latent space alignment + confidence
# ═══════════════════════════════════════════════════════════════════════════════

class TransferEngine:
    """Cross-domain transfer via embedding alignment + structural matching.

    Pipeline:
    1. Embed source & target domain descriptions
    2. Extract structural graphs
    3. WL kernel similarity
    4. Combined confidence score
    5. Generate transfer hypothesis (structural invariant)
    """

    def __init__(self) -> None:
        self.embedder = DomainEmbedder()
        self.extractor = StructureExtractor()
        self.wl_kernel = WeisfeilerLehmanKernel(iterations=3)

    def compute_transfer(
        self,
        source_text: str,
        target_text: str,
        source_name: str = "source",
        target_name: str = "target",
    ) -> dict[str, Any]:
        """Compute cross-domain transfer between source and target domains.

        Returns:
            dict with transfer_confidence, structural_similarity,
            embedding_similarity, shared_invariants, transfer_hypothesis.
        """
        # 1. Embeddings
        try:
            src_emb = self.embedder.embed(source_text[:2000])
            tgt_emb = self.embedder.embed(target_text[:2000])
            emb_sim = DomainEmbedder.cosine(src_emb, tgt_emb)
        except Exception:
            emb_sim = 0.3  # fallback

        # 2. Structure extraction
        src_struct = self.extractor.extract(source_text[:2000])
        tgt_struct = self.extractor.extract(target_text[:2000])

        # 3. Build adjacency graphs
        src_graph: dict[str, list[str]] = {}
        for r in src_struct["relations"]:
            s, t = r["source"], r["target"]
            src_graph.setdefault(s, []).append(t)
        tgt_graph: dict[str, list[str]] = {}
        for r in tgt_struct["relations"]:
            s, t = r["source"], r["target"]
            tgt_graph.setdefault(s, []).append(t)

        # 4. WL kernel similarity
        struct_sim = self.wl_kernel.similarity(src_graph, tgt_graph) if src_graph and tgt_graph else 0.0

        # 5. Dimensional matching
        dim_overlap = self._dimension_overlap(src_struct.get("dimensions", {}), tgt_struct.get("dimensions", {}))

        # 6. Combined confidence
        confidence = (
            0.35 * emb_sim +
            0.35 * struct_sim +
            0.20 * dim_overlap +
            0.10 * min(len(src_struct["relations"]), len(tgt_struct["relations"])) / max(1, max(len(src_struct["relations"]), len(tgt_struct["relations"])))
        )

        # 7. Generate transfer hypothesis
        shared_entities = set(src_struct["entities"][:10]) & set(tgt_struct["entities"][:10])
        hypothesis = self._generate_transfer_hypothesis(
            source_name, target_name, emb_sim, struct_sim, list(shared_entities),
            src_struct.get("dimensions", {}), tgt_struct.get("dimensions", {}),
        )

        quality = "strong" if confidence >= 0.7 else "moderate" if confidence >= 0.4 else "weak"

        return {
            "transfer_confidence": round(confidence, 4),
            "structural_similarity": round(struct_sim, 4),
            "embedding_similarity": round(emb_sim, 4),
            "dimensional_overlap": round(dim_overlap, 4),
            "shared_entities": list(shared_entities)[:10],
            "source_relations": len(src_struct["relations"]),
            "target_relations": len(tgt_struct["relations"]),
            "transfer_quality": quality,
            "transfer_hypothesis": hypothesis,
            "source": source_name,
            "target": target_name,
        }

    def _dimension_overlap(self, dims1: dict[str, str], dims2: dict[str, str]) -> float:
        vals1 = set(dims1.values())
        vals2 = set(dims2.values())
        union = len(vals1 | vals2)
        if union == 0:
            return 0.0
        return len(vals1 & vals2) / union

    def _generate_transfer_hypothesis(
        self,
        source: str, target: str,
        emb_sim: float, struct_sim: float,
        shared: list[str],
        dims1: dict[str, str], dims2: dict[str, str],
    ) -> str:
        if emb_sim > 0.6 and struct_sim > 0.5:
            return (
                f"Strong structural parallel: {source} and {target} share domain invariants "
                f"(embedding={emb_sim:.2f}, structure={struct_sim:.2f}). "
                + (f"Shared elements: {', '.join(shared[:5])}. " if shared else "")
                + f"Transfer recommended — apply {source} methodology to {target}."
            )
        elif emb_sim > 0.3 or struct_sim > 0.3:
            return (
                f"Moderate parallel detected ({source} ↔ {target}): "
                f"embedding={emb_sim:.2f}, structure={struct_sim:.2f}. "
                + (f"Partial overlap: {', '.join(shared[:3])}. " if shared else "")
                + "Experimental transfer warranted with self-validation."
            )
        else:
            return f"Weak structural parallel ({source} ↔ {target}). Consider broader analogical search."


__all__ = ["DomainEmbedder", "StructureExtractor", "WeisfeilerLehmanKernel", "TransferEngine"]
