from __future__ import annotations

import hashlib
import json
import logging


logger = logging.getLogger(__name__)
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.pipeline.result import PipelineResult


_STOP_WORDS: set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "over",
    "this", "that", "these", "those", "it", "its", "they", "them",
    "their", "we", "our", "you", "your", "he", "she", "him", "her",
    "and", "but", "or", "nor", "not", "so", "if", "then", "than",
    "too", "very", "just", "about", "also", "only", "other", "some",
    "such", "each", "all", "both", "few", "more", "most", "any",
    "no", "now", "new", "up", "out", "when", "where", "how", "which",
    "who", "whom", "what", "why", "because", "while", "although",
    "however", "therefore", "thus", "yet", "still", "already",
}


@dataclass
class DiscoveryFingerprint:
    """DiscoveryFingerprint."""
    hypothesis_hash: str
    keywords: list[str]
    domain: str
    c4_state: str
    timestamp: float
    pipeline_version: str

    def to_dict(self) -> dict:
        return {
            "hypothesis_hash": self.hypothesis_hash,
            "keywords": self.keywords,
            "domain": self.domain,
            "c4_state": self.c4_state,
            "timestamp": self.timestamp,
            "pipeline_version": self.pipeline_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DiscoveryFingerprint:
        return cls(
            hypothesis_hash=data["hypothesis_hash"],
            keywords=data["keywords"],
            domain=data["domain"],
            c4_state=data["c4_state"],
            timestamp=data["timestamp"],
            pipeline_version=data["pipeline_version"],
        )


class DiscoveryMemory:
    """DiscoveryMemory."""
    def __init__(self, store_path: str = "discovery/memory/") -> None:
        self._store_dir = Path(store_path)
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._store_dir / "fingerprints.json"
        self._fingerprints: list[DiscoveryFingerprint] = self._load()

    def _load(self) -> list[DiscoveryFingerprint]:
        if not self._index_path.exists():
            return []
        try:
            raw = json.loads(self._index_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return [DiscoveryFingerprint.from_dict(item) for item in raw]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        return []

    def _save(self) -> None:
        try:
            data = [fp.to_dict() for fp in self._fingerprints]
            tmp_path = self._index_path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_path.replace(self._index_path)
        except (OSError, TypeError) as e:
            logger.warning("Failed to save discovery memory: %s", e)

    @staticmethod
    def _extract_keywords(text: str, n: int = 10) -> list[str]:
        words = re.findall(r"[a-zA-Z]{3,}", text.lower())
        filtered = [w for w in words if w not in _STOP_WORDS]
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(n)]

    @staticmethod
    def _jaccard_similarity(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        intersection = a & b
        union = a | b
        return len(intersection) / len(union)

    def _extract_hypothesis_text(self, result: PipelineResult) -> str:
        if result.hypotheses and result.hypotheses[0]:
            h = result.hypotheses[0]
            if isinstance(h, dict):
                text = h.get("text", h.get("final_solution", h.get("hypothesis", "")))
                if text is not None:
                    return str(text)
                return ""
            return str(h)  # type: ignore[unreachable]
        return ""

    def _extract_domain(self, result: PipelineResult) -> str:
        det = result.detection_results or {}
        return det.get("domain", det.get("c4_domain", "unknown"))

    def _extract_c4_state(self, result: PipelineResult) -> str:
        det = result.detection_results or {}
        state = det.get("c4_state", "")
        if state:
            return str(state)
        fingerprint = det.get("c4_fingerprint", det.get("fingerprint", ""))
        if fingerprint:
            return str(fingerprint)
        return "unknown"

    async def record(self, result: PipelineResult) -> DiscoveryFingerprint | None:
        """Record."""
        hypothesis_text = self._extract_hypothesis_text(result)
        if not hypothesis_text:
            return None
        hypothesis_hash = hashlib.sha256(hypothesis_text.encode()).hexdigest()
        keywords = self._extract_keywords(hypothesis_text)
        domain = self._extract_domain(result)
        c4_state = self._extract_c4_state(result)

        fp = DiscoveryFingerprint(
            hypothesis_hash=hypothesis_hash,
            keywords=keywords,
            domain=domain,
            c4_state=c4_state,
            timestamp=time.time(),
            pipeline_version=result.pipeline_version,
        )

        existing = any(f.hypothesis_hash == hypothesis_hash for f in self._fingerprints)
        if not existing:
            self._fingerprints.append(fp)
            self._save()

        return fp

    async def check_novelty(
        self, hypothesis: str, domain: str
    ) -> tuple[bool, DiscoveryFingerprint | None]:
        """Check novelty."""
        hypothesis_hash = hashlib.sha256(hypothesis.encode()).hexdigest()
        keywords = set(self._extract_keywords(hypothesis))

        best_match: DiscoveryFingerprint | None = None
        best_sim = 0.0

        for fp in self._fingerprints:
            fp_keywords = set(fp.keywords)
            sim = self._jaccard_similarity(keywords, fp_keywords)
            if sim > best_sim:
                best_sim = sim
                best_match = fp
            if hypothesis_hash == fp.hypothesis_hash:
                return False, fp

        if best_sim > 0.7 and best_match is not None:
            return False, best_match

        return True, None

    async def deduplicate(self, results: list[PipelineResult]) -> list[PipelineResult]:
        """Deduplicate."""
        if len(results) <= 1:
            return list(results)

        seen: list[set[str]] = []
        kept: list[PipelineResult] = []

        for r in results:
            kw = set(self._extract_keywords(self._extract_hypothesis_text(r)))
            duplicate = False
            for existing_kw in seen:
                if self._jaccard_similarity(kw, existing_kw) > 0.7:
                    duplicate = True
                    break
            if not duplicate:
                seen.append(kw)
                kept.append(r)

        return kept

    async def search_memory(
        self, query: str, k: int = 5
    ) -> list[DiscoveryFingerprint]:
        """Search memory."""
        query_keywords = set(self._extract_keywords(query))
        if not self._fingerprints or not query_keywords:
            return []

        scored = [
            (
                self._jaccard_similarity(query_keywords, set(fp.keywords)),
                fp,
            )
            for fp in self._fingerprints
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [fp for sim, fp in scored[:k] if sim > 0.0]
