# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import hashlib
import logging
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class EmbeddingCache:
    """LRU embedding cache keyed by text SHA256."""

    def __init__(self, max_size: int = 10000) -> None:
        from collections import OrderedDict

        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._max = max_size

    def get(self, text: str) -> np.ndarray | None:
        """Get vector and promote to most-recently used."""
        key = hashlib.sha256(text.encode()).hexdigest()
        vec = self._cache.get(key)
        if vec is not None:
            # Promote to MRU
            self._cache.move_to_end(key)
        return vec

    def set(self, text: str, vec: np.ndarray) -> None:
        """Set vector and promote to most-recently used."""
        key = hashlib.sha256(text.encode()).hexdigest()
        if key in self._cache:
            self._cache.move_to_end(key)
            return
        if len(self._cache) >= self._max:
            # Evict least-recently used (first item)
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = vec

    def _init_ordered_dict(self) -> None:
        """Ensure _cache is an OrderedDict for LRU behavior."""
        from collections import OrderedDict

        if not isinstance(self._cache, OrderedDict):
            # Rebuild in insertion order to preserve existing behavior
            self._cache = OrderedDict(self._cache)  # type: ignore[unreachable]

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore from pickle."""
        self._cache = state.get("_cache", {})
        self._max = state.get("_max", 10000)
        self._init_ordered_dict()


from collections import OrderedDict


_cache = EmbeddingCache()
# Ensure LRU backing on module load
_cache._init_ordered_dict()


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    dot = float(np.dot(a, b))
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    return dot / (na * nb) if na and nb else 0.0


class EmbeddingEngine:
    """Produces embeddings using local sentence-transformers."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._model_name = "all-MiniLM-L6-v2"
        self._batch_size = 32

    def _ensure_model(self) -> bool:
        if self._model is not None:
            return True
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model loaded: %s", self._model_name)
            return True
        except Exception as e:
            raise RuntimeError(f"sentence-transformers unavailable: {e}") from e

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed multiple texts. Returns (n_texts, dim) array."""
        if not texts:
            dim = self._get_dim()
            return np.zeros((0, dim))

        idx_to_vec: dict[int, np.ndarray] = {}
        to_embed: list[str] = []
        to_embed_idx: list[int] = []

        for i, t in enumerate(texts):
            vec = _cache.get(t)
            if vec is not None:
                idx_to_vec[i] = vec
            else:
                to_embed.append(t)
                to_embed_idx.append(i)

        if to_embed:
            new_vecs = self._embed_batch(to_embed)
            for t, v in zip(to_embed, new_vecs, strict=False):
                _cache.set(t, v)
            for orig_idx, vec in zip(to_embed_idx, new_vecs, strict=False):
                idx_to_vec[orig_idx] = vec

        # Assemble result in original text order
        dim = len(next(iter(idx_to_vec.values())))
        result = np.zeros((len(texts), dim))
        for i, vec in idx_to_vec.items():
            result[i] = vec
        return result

    def _get_dim(self) -> int:
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return 384  # fallback for all-MiniLM-L6-v2

    def _embed_batch(self, texts: list[str]) -> list[np.ndarray]:
        if self._ensure_model():
            assert self._model is not None
            embeddings = self._model.encode(
                texts, batch_size=self._batch_size, show_progress_bar=False, convert_to_numpy=True
            )
            return [e for e in embeddings]
        raise RuntimeError("Embedding model unavailable")

    async def aembed(self, texts: list[str]) -> np.ndarray:
        """Async wrapper for embed — delegates to thread pool."""
        import asyncio

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.embed, texts)


_engine = EmbeddingEngine()


def semantic_deduplicate(
    sources: list[dict[str, Any]], threshold: float = 0.85
) -> list[dict[str, Any]]:
    """Remove near-duplicate sources via embedding similarity.

    Falls back to lexical title Jaccard when sentence-transformers is unavailable.
    """
    if len(sources) < 2:
        return sources

    texts = [s.get("title", "") + " " + s.get("snippet", s.get("abstract", "")) for s in sources]
    try:
        vecs = _engine.embed(texts)
    except (RuntimeError, ImportError, ValueError, TypeError) as exc:
        logger.warning(
            "Semantic deduplication unavailable (%s); using lexical title fallback",
            exc,
        )
        return _lexical_deduplicate(sources, threshold=max(0.5, threshold - 0.2))

    # Normalize for cosine similarity via dot product
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized = vecs / norms

    keep: list[int] = [0]
    if len(sources) > 1:
        keep_vecs = normalized[0:1]
        for i in range(1, len(sources)):
            sims = (normalized[i : i + 1] @ keep_vecs.T).flatten()
            if sims.max() < threshold:
                keep.append(i)
                keep_vecs = np.vstack([keep_vecs, normalized[i : i + 1]])

    logger.info(
        "Semantic dedup: %d → %d sources (threshold %.2f)", len(sources), len(keep), threshold
    )
    return [sources[k] for k in keep]


def _lexical_deduplicate(
    sources: list[dict[str, Any]], threshold: float = 0.65
) -> list[dict[str, Any]]:
    """Title-token Jaccard dedup when embeddings are unavailable."""

    def _tokens(title: str) -> set[str]:
        return {t for t in (title or "").lower().split() if len(t) > 2}

    keep: list[dict[str, Any]] = []
    kept_toks: list[set[str]] = []
    for src in sources:
        toks = _tokens(str(src.get("title", "")))
        if not toks:
            keep.append(src)
            kept_toks.append(toks)
            continue
        dup = False
        for prev in kept_toks:
            if not prev:
                continue
            sim = len(toks & prev) / max(len(toks | prev), 1)
            if sim >= threshold:
                dup = True
                break
        if not dup:
            keep.append(src)
            kept_toks.append(toks)
    logger.info(
        "Lexical dedup: %d → %d sources (threshold %.2f)", len(sources), len(keep), threshold
    )
    return keep


def find_best_evidence(
    gap: dict[str, Any], sources: list[dict[str, Any]], top_k: int = 3
) -> list[dict[str, Any]]:
    """Find best source evidence for a gap via embedding similarity.

    Before embedding, verifies that the claimed quote (if any) actually exists
    in the source text. This prevents the self-fulfilling validation loop where
    an LLM hallucinates a quote and the embedding similarity falsely confirms it.
    """
    gap_text = gap.get("area", "") + " " + gap.get("evidence", "")
    if not gap_text.strip() or not sources:
        return []

    # Extract claimed quote from gap evidence
    claimed_quote = gap.get("evidence", "").strip()

    def _quote_exists(source: dict[str, Any], quote: str) -> bool:
        """Check if claimed quote exists in source text (exact or fuzzy substring)."""
        if not quote or len(quote) < 10:
            return True  # Too short to verify meaningfully
        text = f"{source.get('title', '')} {source.get('abstract', source.get('snippet', ''))}"
        text_lower = text.lower()
        quote_lower = quote.lower()
        # Exact substring match
        if quote_lower in text_lower:
            return True
        # Fuzzy match: at least 70% of words in quote appear in source
        quote_words = set(quote_lower.split())
        text_words = set(text_lower.split())
        if not quote_words:
            return True
        overlap = len(quote_words & text_words)
        return overlap / len(quote_words) >= 0.70

    source_texts = []
    valid_sources = []
    for s in sources:
        text = s.get("snippet", s.get("abstract", ""))
        source_texts.append(text)
        valid_sources.append(s)

    gap_vec = _engine.embed([gap_text])[0]
    source_vecs = _engine.embed(source_texts)

    sims = []
    for i in range(len(valid_sources)):
        sim = _cosine(gap_vec, source_vecs[i])
        # If claimed quote does not exist in source, cap score at 0.0
        if claimed_quote and not _quote_exists(valid_sources[i], claimed_quote):
            sim = 0.0
        sims.append((i, sim))

    sims.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, sim in sims[:top_k]:
        s = dict(valid_sources[idx])
        s["_evidence_score"] = round(sim, 3)
        if claimed_quote and not _quote_exists(valid_sources[idx], claimed_quote):
            s["_evidence_verified"] = False
        else:
            s["_evidence_verified"] = True
        results.append(s)
    return results


def cluster_by_topic(
    sources: list[dict[str, Any]], n_clusters: int = 5
) -> dict[int, list[dict[str, Any]]]:
    """Group sources into semantic clusters via embedding K-means."""
    if len(sources) < n_clusters:
        return {0: sources}

    texts = [s.get("title", "") + " " + s.get("snippet", s.get("abstract", "")) for s in sources]
    vecs = _engine.embed(texts)

    from sklearn.cluster import KMeans

    km = KMeans(n_clusters=min(n_clusters, len(sources)), random_state=42, n_init=3)
    labels = km.fit_predict(vecs)

    clusters: dict[int, list[dict[str, Any]]] = {}
    for i, label in enumerate(labels):
        label = int(label)
        clusters.setdefault(label, []).append(sources[i])

    logger.info("Topic clustering: %d sources → %d clusters", len(sources), len(clusters))
    return clusters


def coverage_check(dissertation: str, bibliography: list[dict[str, Any]]) -> dict[str, Any]:
    """Check how well the dissertation covers its bibliography."""
    if not dissertation or not bibliography:
        return {"coverage": 0.0, "covered": 0, "total": len(bibliography), "uncovered": []}

    sections = [s.strip() for s in dissertation.split("\n\n") if len(s.strip()) > 50]
    if not sections:
        return {"coverage": 0.0, "covered": 0, "total": len(bibliography), "uncovered": []}

    section_vecs = _engine.embed(sections)
    bib_texts = [
        b.get("title", "") + " " + b.get("snippet", b.get("abstract", "")) for b in bibliography
    ]
    bib_vecs = _engine.embed(bib_texts)

    covered = 0
    uncovered: list[int] = []
    for i in range(len(bibliography)):
        max_sim = max(_cosine(section_vecs[j], bib_vecs[i]) for j in range(len(sections)))
        if max_sim > 0.4:
            covered += 1
        else:
            uncovered.append(i)

    return {
        "coverage": round(covered / len(bibliography), 2) if bibliography else 1.0,
        "covered": covered,
        "total": len(bibliography),
        "uncovered_indices": uncovered,
    }


# ── Fast-Complete: cheap models for sub-LLM tasks ──


def fast_summarize(text: str, max_sentences: int = 5) -> str:
    """Summarize text using cheapest available model (depth 0). Return key sentences."""
    if not text or len(text.split()) < 30:
        return text
    from src.llm.depth_router import DepthBasedRouter

    model = DepthBasedRouter.route(0, "cheap")  # depth=0 fast-complete
    prompt = f"Extract the {max_sentences} most important factual sentences from this text. Output ONLY the sentences, one per line. No preamble. No commentary.\n\n{text[:3000]}"
    result = _call_llm(model, prompt, max_tokens=300)
    if not result:
        logger.warning("fast_summarize failed: empty response, returning input truncated")
        return text[:500]
    return result


def _extract_json_block(text: str) -> str:
    """Find outermost JSON array/object in text using bracket matching."""
    start = -1
    for i, ch in enumerate(text):
        if ch in "[{":
            start = i
            break
    if start == -1:
        return ""
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return ""


def fast_extract_entities(text: str) -> list[str]:
    """Extract key entities/concepts using cheapest model. Returns list of strings."""
    if not text:
        return []
    from src.llm.depth_router import DepthBasedRouter

    model = DepthBasedRouter.route(0, "balanced")
    prompt = f"Extract 5-10 key scientific entities and concepts from this text. Output ONLY a JSON list of strings. No preamble.\n\n{text[:2000]}"
    result = _call_llm(model, prompt, max_tokens=200)
    if not result or "[" not in result:
        logger.warning("fast_extract_entities failed: empty response, returning empty list")
        return []
    import json

    try:
        block = _extract_json_block(result)
        if not block:
            return []
        return json.loads(block)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("fast_extract_entities JSON parse failed: %s", e)
        return []


def fast_structure(text: str) -> list[tuple[str, str]]:
    """Structure text into (heading, content) sections using cheap model."""
    if not text:
        return []
    from src.llm.depth_router import DepthBasedRouter

    model = DepthBasedRouter.route(0, "cheap")
    prompt = f"""Split this text into logical sections. Output as JSON list of [heading, content] pairs. Content max 200 chars per section.

        {text[:4000]}"""
    result = _call_llm(model, prompt, max_tokens=500)
    if not result or "[" not in result:
        logger.warning("fast_structure failed: empty response, returning empty list")
        return []
    import json

    try:
        block = _extract_json_block(result)
        if not block:
            return []
        decoded = json.loads(block)
        return [(h, c) for h, c in decoded]
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning("fast_structure JSON parse failed: %s", e)
        return []


def _call_llm(model: str, prompt: str, max_tokens: int = 300) -> str:
    """One-shot LLM call via OpenRouter."""
    try:
        import os

        # Audit 2026-06-22 H-8 Tier 1: sync variant of guarded wrapper.
        from src.llm.guarded_call import guarded_chat_completion_sync

        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY required for embeddings")
        data = guarded_chat_completion_sync(
            url="https://openrouter.ai/api/v1/chat/completions",
            api_key=key,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
            timeout=20.0,
        )
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.debug("Fast LLM call failed: %s", e)
        raise RuntimeError("LLM call failed") from e
