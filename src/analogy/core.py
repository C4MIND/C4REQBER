"""
C4REQBER: Analogy Engine Core
Main AnalogyEngine class and core analogy discovery logic.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from src.analogy.operations import ConceptNetBridge, SemanticEmbedder, Word2VecAnalogySolver
from src.analogy.utils import AnalogyResult
from src.graph.knowledge_graph import get_knowledge_graph


class AnalogyEngine:
    """
    Main analogy discovery engine combining multiple methods.

    Methods:
    - Semantic: Sentence-BERT cosine similarity
    - Structural: Word2Vec vector arithmetic
    - Knowledge-based: ConceptNet/conceptual metaphors
    - Graph-based: NetworkX structure matching
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        word2vec_path: str | None = None,
        similarity_threshold: float = 0.6,
    ) -> None:
        from src.analogy.utils import HAS_GENSIM, HAS_SENTENCE_TRANSFORMERS

        self.embedder = SemanticEmbedder(embedding_model)
        self.word2vec = Word2VecAnalogySolver(word2vec_path)
        self.conceptnet = ConceptNetBridge()
        self.knowledge_graph = get_knowledge_graph()
        self.similarity_threshold = similarity_threshold

        print("✓ AnalogyEngine initialized")
        print(
            f"  - Semantic: {'Sentence-BERT' if HAS_SENTENCE_TRANSFORMERS else 'TF-IDF fallback'}"
        )
        print(f"  - Word2Vec: {'Available' if HAS_GENSIM else 'Unavailable'}")

    def find_analogies(
        self,
        source_domain: str,
        target_domain: str,
        source_concept: str,
        top_k: int = 5,
    ) -> list[AnalogyResult]:
        """Find analogies for a concept across domains."""
        results: list[AnalogyResult] = []

        # Method 1: Check known conceptual metaphors
        metaphors = self.conceptnet.find_conceptual_metaphors(
            source_domain, target_domain
        )
        for sc, tc in metaphors:
            if sc.lower() == source_concept.lower():
                results.append(
                    AnalogyResult(
                        source_concept=source_concept,
                        target_concept=tc,
                        source_domain=source_domain,
                        target_domain=target_domain,
                        mapping_type="semantic",
                        confidence=0.85,
                        reasoning="Known conceptual metaphor",
                    )
                )

        # Method 2: Semantic similarity to target domain concepts
        target_concepts = self.conceptnet.get_domain_concepts(target_domain)
        if target_concepts:
            source_embedding = self.embedder.embed(
                f"{source_concept} in {source_domain}"
            )
            target_embeddings = self.embedder.batch_embed(
                [f"{tc} in {target_domain}" for tc in target_concepts]
            )

            similarities = np.dot(target_embeddings, source_embedding)
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            for idx in top_indices:
                if similarities[idx] >= self.similarity_threshold:
                    results.append(
                        AnalogyResult(
                            source_concept=source_concept,
                            target_concept=target_concepts[idx],
                            source_domain=source_domain,
                            target_domain=target_domain,
                            mapping_type="semantic",
                            confidence=float(similarities[idx]),
                            semantic_similarity=float(similarities[idx]),
                            reasoning=f"Semantic similarity: {similarities[idx]:.3f}",
                        )
                    )

        # Method 3: Word2Vec analogies if available
        if self.word2vec.model is not None:
            w2v_results = self._word2vec_domain_analogy(
                source_domain, target_domain, source_concept
            )
            results.extend(w2v_results)

        # Method 4: Graph-based analogy discovery
        graph_results = self._graph_analogy_search(
            source_domain, target_domain, source_concept
        )
        results.extend(graph_results)

        # Deduplicate and sort by confidence
        seen = set()
        unique_results = []
        for r in results:
            key = (r.source_concept.lower(), r.target_concept.lower())
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        unique_results.sort(key=lambda x: x.confidence, reverse=True)
        return unique_results[:top_k]

    def _word2vec_domain_analogy(
        self,
        source_domain: str,
        target_domain: str,
        source_concept: str,
    ) -> list[AnalogyResult]:
        """Use Word2Vec to find domain analogies."""
        results = []
        anchors = self.conceptnet.find_conceptual_metaphors(
            source_domain, target_domain
        )

        for A, B in anchors[:3]:
            solutions = self.word2vec.solve(A, B, source_concept, topn=3)
            for target_concept, score in solutions:
                if score >= 0.5:
                    results.append(
                        AnalogyResult(
                            source_concept=source_concept,
                            target_concept=target_concept,
                            source_domain=source_domain,
                            target_domain=target_domain,
                            mapping_type="structural",
                            confidence=score,
                            structural_similarity=score,
                            reasoning=f"Word2Vec analogy {A}:{B}::{source_concept}:{target_concept}",
                        )
                    )

        return results

    def _graph_analogy_search(
        self,
        source_domain: str,
        target_domain: str,
        source_concept: str,
    ) -> list[AnalogyResult]:
        """Find analogies using knowledge graph structure."""
        results = []
        analogies = self.knowledge_graph.get_nodes_by_type("analogy")

        for analogy in analogies:
            meta = analogy.get("metadata", {})
            if (
                meta.get("source_domain") == source_domain
                and meta.get("target_domain") == target_domain
            ):
                if meta.get("verified", False):
                    results.append(
                        AnalogyResult(
                            source_concept=source_concept,
                            target_concept=meta.get("target_concept", "unknown"),
                            source_domain=source_domain,
                            target_domain=target_domain,
                            mapping_type="graph_based",
                            confidence=meta.get("confidence", 0.5) * 0.9,
                            reasoning="Verified analogy from knowledge graph",
                        )
                    )

        return results

    def discover_cross_domain_analogies(
        self,
        domain1: str,
        domain2: str,
        max_analogies: int = 10,
    ) -> list[AnalogyResult]:
        """Systematically discover analogies between two domains."""
        results: Any = []
        concepts1 = self.conceptnet.get_domain_concepts(domain1)
        concepts2 = self.conceptnet.get_domain_concepts(domain2)

        if not concepts1 or not concepts2:
            print(f"⚠️  No predefined concepts for {domain1} or {domain2}")
            return results  # type: ignore[no-any-return]

        embeddings1 = self.embedder.batch_embed(
            [f"{c} in {domain1}" for c in concepts1]
        )
        embeddings2 = self.embedder.batch_embed(
            [f"{c} in {domain2}" for c in concepts2]
        )

        similarity_matrix = np.dot(embeddings1, embeddings2.T)

        pairs = []
        for i, c1 in enumerate(concepts1):
            for j, c2 in enumerate(concepts2):
                pairs.append((similarity_matrix[i, j], c1, c2))

        pairs.sort(reverse=True)

        for score, c1, c2 in pairs[:max_analogies]:
            if score >= self.similarity_threshold:
                results.append(
                    AnalogyResult(
                        source_concept=c1,
                        target_concept=c2,
                        source_domain=domain1,
                        target_domain=domain2,
                        mapping_type="semantic",
                        confidence=float(score),
                        semantic_similarity=float(score),
                        reasoning=f"Cross-domain semantic match: {score:.3f}",
                    )
                )

        return results  # type: ignore[no-any-return]

    def solve_proportional_analogy(
        self,
        A: str,
        B: str,
        C: str,
    ) -> AnalogyResult | None:
        """Solve A:B::C:? using Word2Vec."""
        if self.word2vec.model is None:
            return None

        solutions = self.word2vec.solve(A, B, C, topn=1)
        if solutions:
            D, score = solutions[0]
            return AnalogyResult(
                source_concept=f"{A}:{B}",
                target_concept=f"{C}:{D}",
                source_domain="proportional",
                target_domain="proportional",
                mapping_type="structural",
                confidence=score,
                structural_similarity=score,
                reasoning=f"Word2Vec: {A}:{B}::{C}:{D}",
            )
        return None

    def store_analogy(self, result: AnalogyResult) -> str:
        """Store analogy in knowledge graph."""
        analogy_id = self.knowledge_graph.add_analogy(
            source_domain=result.source_domain,
            target_domain=result.target_domain,
            source_concept=result.source_concept,
            target_concept=result.target_concept,
            mapping_type=result.mapping_type,
            confidence=result.confidence,
            semantic_similarity=result.semantic_similarity,
            structural_similarity=result.structural_similarity,
            evidence=result.evidence or [],
        )
        self.knowledge_graph.save()
        return analogy_id

    def get_analogy_chain(
        self,
        source_domain: str,
        target_domain: str,
        max_length: int = 3,
    ) -> list[list[str]]:
        """Find chains of analogies connecting domains."""
        return self.knowledge_graph.find_analogy_chains(
            source_domain, target_domain, max_length
        )


def get_analogy_engine() -> AnalogyEngine:
    """Get singleton analogy engine instance (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("analogy_engine", AnalogyEngine)
