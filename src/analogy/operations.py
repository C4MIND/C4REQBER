"""
C4REQBER: Analogy Operations
Semantic, structural, and knowledge-based analogy solvers.
"""
from __future__ import annotations

import numpy as np
from cachetools import LRUCache  # type: ignore[import-untyped]
from numpy.typing import NDArray

from src.analogy.data import CONCEPTUAL_METAPHORS, DOMAIN_CONCEPTS
from src.analogy.utils import (
    HAS_GENSIM,
    HAS_SENTENCE_TRANSFORMERS,
    HAS_SKLEARN,
    normalize_embedding,
    simple_hash_embedding,
)
from src.graph.knowledge_graph import get_knowledge_graph


if HAS_SENTENCE_TRANSFORMERS:
    from sentence_transformers import SentenceTransformer
if HAS_SKLEARN:
    from sklearn.feature_extraction.text import TfidfVectorizer
if HAS_GENSIM:
    from gensim.models import KeyedVectors


class SemanticEmbedder:
    """Semantic embedding using Sentence-BERT or TF-IDF fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self.model = None
        self.fallback_vectorizer = None
        self._embedding_cache: LRUCache = LRUCache(maxsize=1000)

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"✓ Loaded Sentence-BERT model: {model_name}")
            except Exception as e:
                print(f"⚠️  Failed to load Sentence-BERT: {e}")
                self.model = None

        if self.model is None and HAS_SKLEARN:
            self.fallback_vectorizer = TfidfVectorizer(
                max_features=1000, stop_words="english", ngram_range=(1, 2)
            )

    def embed(self, text: str) -> NDArray[np.float64]:
        """Get embedding vector for text."""
        if text in self._embedding_cache:
            return self._embedding_cache[text]  # type: ignore[no-any-return]

        if self.model is not None:
            embedding = self.model.encode(text, convert_to_numpy=True)
        elif HAS_SKLEARN:
            if not hasattr(self.fallback_vectorizer, "vocabulary_"):
                self.fallback_vectorizer.fit([text])  # type: ignore[union-attr]
            embedding = self.fallback_vectorizer.transform([text]).toarray()[0]  # type: ignore[union-attr]
        else:
            embedding = simple_hash_embedding(text)

        embedding = normalize_embedding(embedding)
        self._embedding_cache[text] = embedding
        return embedding

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        emb1 = self.embed(text1)
        emb2 = self.embed(text2)
        return float(np.dot(emb1, emb2))

    def batch_embed(self, texts: list[str]) -> NDArray[np.float64]:
        """Embed multiple texts efficiently."""
        if self.model is not None:
            return self.model.encode(texts, convert_to_numpy=True)
        return np.array([self.embed(t) for t in texts])


class Word2VecAnalogySolver:
    """Solve analogies using Word2Vec vector arithmetic: A:B::C:D => D = C + (B - A)."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model = None
        self.model_path = model_path

        if HAS_GENSIM and model_path:
            try:
                self.model = KeyedVectors.load_word2vec_format(model_path, binary=True)
                print(f"✓ Loaded Word2Vec model: {model_path}")
            except Exception as e:
                print(f"⚠️  Failed to load Word2Vec: {e}")

    def solve(self, A: str, B: str, C: str, topn: int = 5) -> list[tuple[str, float]]:
        """Solve A:B::C:? analogy. Returns list of (word, similarity) tuples."""
        if self.model is None:
            return []

        try:
            A = A.lower().replace(" ", "_")
            B = B.lower().replace(" ", "_")
            C = C.lower().replace(" ", "_")
            result = self.model.most_similar(positive=[B, C], negative=[A], topn=topn)
            return [(word.replace("_", " "), float(score)) for word, score in result]
        except (KeyError, ValueError, AttributeError, RuntimeError):
            return []

    def doesnt_match(self, words: list[str]) -> str | None:
        """Find the word that doesn't match the others."""
        if self.model is None:
            return None
        try:
            normalized = [w.lower().replace(" ", "_") for w in words]
            return self.model.doesnt_match(normalized).replace("_", " ")  # type: ignore[no-any-return]
        except (KeyError, ValueError, AttributeError):
            return None

    def similarity(self, word1: str, word2: str) -> float:
        """Get similarity between two words."""
        if self.model is None:
            return 0.0
        try:
            w1 = word1.lower().replace(" ", "_")
            w2 = word2.lower().replace(" ", "_")
            return float(self.model.similarity(w1, w2))
        except (KeyError, ValueError, AttributeError):
            return 0.0


class ConceptNetBridge:
    """Knowledge-based analogies using ConceptNet relations and conceptual metaphors."""

    DOMAIN_CONCEPTS = DOMAIN_CONCEPTS
    CONCEPTUAL_METAPHORS = CONCEPTUAL_METAPHORS

    def __init__(self) -> None:
        self.knowledge_graph = get_knowledge_graph()
        self._load_conceptual_metaphors()

    def _load_conceptual_metaphors(self) -> None:
        """Load conceptual metaphors into knowledge graph."""
        for sd, sc, td, tc in self.CONCEPTUAL_METAPHORS:
            existing = self.knowledge_graph.get_nodes_by_type("analogy")
            exists = any(
                a.get("metadata", {}).get("source_concept") == sc
                and a.get("metadata", {}).get("target_concept") == tc
                for a in existing
            )
            if not exists:
                self.knowledge_graph.add_analogy(
                    source_domain=sd,
                    target_domain=td,
                    source_concept=sc,
                    target_concept=tc,
                    mapping_type="semantic",
                    confidence=0.8,
                    evidence=["conceptual_metaphor"],
                )

    def get_domain_concepts(self, domain: str) -> list[str]:
        """Get characteristic concepts for a domain."""
        return self.DOMAIN_CONCEPTS.get(domain, [])

    def find_conceptual_metaphors(
        self, source_domain: str, target_domain: str
    ) -> list[tuple[str, str]]:
        """Find known conceptual metaphors between domains."""
        results = []
        for sd, sc, td, tc in self.CONCEPTUAL_METAPHORS:
            if sd == source_domain and td == target_domain:
                results.append((sc, tc))
            elif sd == target_domain and td == source_domain:
                results.append((tc, sc))
        return results

    def add_concept(self, domain: str, concept: str, auto_save: bool = True) -> bool:
        """Add a new concept to a domain. Returns True if added, False if already exists."""
        if domain not in self.DOMAIN_CONCEPTS:
            self.DOMAIN_CONCEPTS[domain] = []
            print(f"✓ Created new domain: {domain}")

        if concept.lower() in [c.lower() for c in self.DOMAIN_CONCEPTS[domain]]:
            return False

        self.DOMAIN_CONCEPTS[domain].append(concept)
        if auto_save:
            self._save_concept_to_graph(domain, concept)
        return True

    def _metaphor_exists(
        self, sd: str, sc: str, td: str, tc: str
    ) -> bool:
        """Check if a conceptual metaphor already exists."""
        for esd, esc, etd, etc in self.CONCEPTUAL_METAPHORS:
            if esd == sd and esc == sc and etd == td and etc == tc:
                return True
        return False

    def add_conceptual_metaphor(
        self,
        source_domain: str,
        source_concept: str,
        target_domain: str,
        target_concept: str,
        confidence: float = 0.8,
        auto_save: bool = True,
    ) -> bool:
        """Add a new conceptual metaphor. Returns True if added, False if already exists."""
        self.add_concept(source_domain, source_concept, auto_save=False)
        self.add_concept(target_domain, target_concept, auto_save=False)

        if self._metaphor_exists(source_domain, source_concept, target_domain, target_concept):
            return False

        self.CONCEPTUAL_METAPHORS.append(
            (source_domain, source_concept, target_domain, target_concept)
        )

        if auto_save:
            self.knowledge_graph.add_analogy(
                source_domain=source_domain,
                target_domain=target_domain,
                source_concept=source_concept,
                target_concept=target_concept,
                mapping_type="semantic",
                confidence=confidence,
                evidence=["user_added"],
            )
            self.knowledge_graph.save()
        return True

    def extract_concepts_from_text(
        self, text: str, domain: str, min_length: int = 4
    ) -> list[str]:
        """Auto-extract potential concepts from text and add to domain."""
        from src.analogy.utils import extract_concepts_from_text as _extract

        extracted = _extract(text, min_length)
        added = []
        for concept in extracted:
            if self.add_concept(domain, concept, auto_save=False):
                added.append(concept)

        if added:
            self.knowledge_graph.save()
        return added

    def auto_extract_from_hypothesis(
        self, hypothesis: str, domain: str
    ) -> dict[str, list]:  # type: ignore[type-arg]
        """Auto-extract concepts and potential analogies from a hypothesis."""
        concepts = self.extract_concepts_from_text(hypothesis, domain)
        potential_analogies = []

        for concept in concepts:
            for other_domain, other_concepts in self.DOMAIN_CONCEPTS.items():
                if other_domain == domain:
                    continue
                for other_concept in other_concepts:
                    if (
                        concept.lower() in other_concept.lower()
                        or other_concept.lower() in concept.lower()
                    ):
                        potential_analogies.append({
                            "source": (domain, concept),
                            "target": (other_domain, other_concept),
                            "match_type": "substring",
                        })

        return {"concepts": concepts, "potential_analogies": potential_analogies}

    def _save_concept_to_graph(self, domain: str, concept: str) -> None:
        """Save concept node to knowledge graph."""
        from datetime import datetime

        node_id = f"concept_{domain}_{concept.replace(' ', '_')}"
        if not self.knowledge_graph.has_node(node_id):
            self.knowledge_graph.graph.add_node(
                node_id,
                node_type="concept",
                domain=domain,
                concept=concept,
                created_at=datetime.now().isoformat(),
            )
            domain_id = f"domain_{domain}"
            if not self.knowledge_graph.has_node(domain_id):
                self.knowledge_graph.graph.add_node(
                    domain_id, node_type="domain", name=domain
                )
            self.knowledge_graph.add_edge(node_id, domain_id, edge_type="belongs_to")
            self.knowledge_graph.save()

    def list_domains(self) -> list[str]:
        """List all available domains."""
        return list(self.DOMAIN_CONCEPTS.keys())

    def get_concept_stats(self) -> dict[str, int]:
        """Get concept counts by domain."""
        return {domain: len(concepts) for domain, concepts in self.DOMAIN_CONCEPTS.items()}
