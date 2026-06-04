"""
C4REQBER: Analogy Engine Utilities
Shared helpers and data structures.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


# Optional imports with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("⚠️  sentence-transformers not installed. Using TF-IDF fallback.")

try:
    import gensim
    from gensim.models import KeyedVectors, Word2Vec
    HAS_GENSIM = True
except ImportError:
    HAS_GENSIM = False
    print("⚠️  gensim not installed. Word2Vec analogies unavailable.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️  scikit-learn not installed. Using numpy for similarity.")

from src.models.pydantic_models import AnalogyMappingModel


@dataclass
class AnalogyResult:
    """Result of analogy discovery."""

    source_concept: str
    target_concept: str
    source_domain: str
    target_domain: str
    mapping_type: str
    confidence: float
    semantic_similarity: float | None = None
    structural_similarity: float | None = None
    reasoning: str = ""
    evidence: list[str] = field(default_factory=list)

    def to_model(self) -> AnalogyMappingModel:
        """Convert to pydantic model for storage."""
        return AnalogyMappingModel(
            source_domain=self.source_domain,
            target_domain=self.target_domain,
            mapping_type=self.mapping_type,  # type: ignore[arg-type]
            source_concept=self.source_concept,
            target_concept=self.target_concept,
            confidence=self.confidence,
            semantic_similarity=self.semantic_similarity,
            structural_similarity=self.structural_similarity,
        )


def simple_hash_embedding(text: str, dim: int = 128) -> NDArray[np.float64]:
    """Simple hash-based embedding as last resort."""
    words = text.lower().split()
    vec = np.zeros(dim)
    for word in words:
        for i, char in enumerate(word):
            vec[i % dim] += ord(char)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def normalize_embedding(embedding: NDArray[np.float64]) -> NDArray[np.float64]:
    """L2-normalize an embedding vector."""
    norm = np.linalg.norm(embedding)
    return embedding / norm if norm > 0 else embedding


def extract_concepts_from_text(text: str, min_length: int = 4) -> set[str]:
    """Extract potential concepts from text using simple heuristics."""
    patterns = [
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
        r"\b[a-z]+(?:\s+[a-z]+){1,2}\b",
    ]

    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
        "her", "was", "one", "our", "out", "day", "get", "has", "him", "his",
        "how", "man", "new", "now", "old", "see", "two", "way", "who", "boy",
        "did", "its", "let", "put", "say", "she", "too", "use", "this", "that",
        "with", "from",
    }

    extracted: set[str] = set()
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            if len(match) >= min_length and match not in stop_words:
                extracted.add(match)

    return extracted
