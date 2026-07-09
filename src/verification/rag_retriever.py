"""RAG (Retrieval-Augmented Generation) for formal proof examples.

Uses TF-IDF + cosine similarity for fast, CPU-based retrieval.
No GPU or external embedding service required.
"""
from __future__ import annotations

import glob
import json
import os
from typing import Any


class ProofExampleRetriever:
    """Retrieve similar formal proof examples via TF-IDF.

    Usage::

        retriever = ProofExampleRetriever()
        examples = retriever.retrieve("For all n, n^2 >= n", language="lean4", k=3)
    """

    def __init__(self, examples_dir: str | None = None) -> None:
        if examples_dir is None:
            examples_dir = os.path.join(os.path.dirname(__file__), "examples")
        self._examples_dir = examples_dir
        self._index: dict[str, Any] | None = None

    def _build_index(self, language: str) -> dict[str, Any]:
        """Build TF-IDF index for a language."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        path = os.path.join(self._examples_dir, f"{language}_examples.json")
        if not os.path.exists(path):
            return {"examples": [], "vectorizer": None, "matrix": None}

        with open(path, encoding="utf-8") as f:
            examples = json.load(f)

        texts = [ex.get("hypothesis", "") for ex in examples]
        if not texts:
            return {"examples": [], "vectorizer": None, "matrix": None}

        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)

        return {
            "examples": examples,
            "vectorizer": vectorizer,
            "matrix": matrix,
        }

    def _get_index(self, language: str) -> dict[str, Any]:
        """Lazy-build index per language."""
        if self._index is None:
            self._index = {}
        if language not in self._index:
            self._index[language] = self._build_index(language)
        return self._index[language]

    def retrieve(self, hypothesis: str, language: str, k: int = 3) -> list[dict[str, str]]:
        """Retrieve top-k similar examples for hypothesis."""
        idx = self._get_index(language)
        examples = idx["examples"]
        vectorizer = idx["vectorizer"]
        matrix = idx["matrix"]

        if not examples or vectorizer is None:
            return []

        from sklearn.metrics.pairwise import cosine_similarity

        query_vec = vectorizer.transform([hypothesis])
        similarities = cosine_similarity(query_vec, matrix).flatten()

        # Get top-k indices
        top_indices = similarities.argsort()[::-1][:k]
        return [examples[i] for i in top_indices if similarities[i] > 0.05]

    def retrieve_all_languages(self, hypothesis: str, k_per_lang: int = 2) -> dict[str, list[dict[str, str]]]:
        """Retrieve examples across all available languages."""
        results: dict[str, list[dict[str, str]]] = {}
        pattern = os.path.join(self._examples_dir, "*_examples.json")
        for path in glob.glob(pattern):
            fname = os.path.basename(path)
            language = fname.replace("_examples.json", "")
            examples = self.retrieve(hypothesis, language, k=k_per_lang)
            if examples:
                results[language] = examples
        return results

    def add_example(self, language: str, hypothesis: str, proof: str) -> None:
        """Add a new example to the library (persists to disk)."""
        path = os.path.join(self._examples_dir, f"{language}_examples.json")
        examples: list[dict[str, str]] = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                examples = json.load(f)

        examples.append({"hypothesis": hypothesis, "proof": proof})

        with open(path, "w", encoding="utf-8") as f:
            json.dump(examples, f, indent=2, ensure_ascii=False)

        # Invalidate cache for this language
        if self._index and language in self._index:
            del self._index[language]
