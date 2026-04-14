from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class RetrievalResult:
    text: str
    source: str  # "user_doc" or "scientific"
    doc_id: Optional[str]
    title: str
    score: float
    metadata: Dict


class HybridRetriever:
    def __init__(self, user_id: str = "default"):
        from .embedder import encode_query
        from .vector_store import UserDocumentStore
        from discovery.sources import SourceDiscoveryService

        self.user_id = user_id
        self.encode_query = encode_query
        self.user_store = UserDocumentStore(user_id)
        self.scientific = SourceDiscoveryService()

    async def query(
        self, query: str, sources: List[str] = None, top_k: int = 10
    ) -> List[RetrievalResult]:
        if sources is None:
            sources = ["user_docs", "scientific"]

        results = []

        if "user_docs" in sources:
            user_results = self._query_user_docs(query, top_k * 2)
            results.extend(user_results)

        if "scientific" in sources:
            sci_results = await self._query_scientific(query, top_k * 2)
            results.extend(sci_results)

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _query_user_docs(self, query: str, n_results: int) -> List[RetrievalResult]:
        embedding = self.encode_query(query)
        raw = self.user_store.query(embedding, n_results=n_results)

        results = []
        if not raw or not raw.get("documents"):
            return results

        docs = raw["documents"][0]
        metas = raw["metadatas"][0]
        distances = raw["distances"][0]

        for text, meta, dist in zip(docs, metas, distances):
            # Convert cosine distance to similarity score
            score = 1.0 - float(dist)
            results.append(
                RetrievalResult(
                    text=text,
                    source="user_doc",
                    doc_id=meta.get("doc_id"),
                    title=meta.get("title", "Unknown"),
                    score=score,
                    metadata=meta,
                )
            )

        return results

    async def _query_scientific(
        self, query: str, n_results: int
    ) -> List[RetrievalResult]:
        try:
            sci_results = await self.scientific.search(query, max_results=n_results)
        except Exception:
            sci_results = []

        results = []
        for i, paper in enumerate(sci_results):
            text = f"{paper.title}\n{getattr(paper, 'abstract', '') or ''}"
            score = getattr(paper, "relevance_score", None) or (1.0 - i * 0.1)
            results.append(
                RetrievalResult(
                    text=text,
                    source="scientific",
                    doc_id=getattr(paper, "id", None),
                    title=paper.title,
                    score=score,
                    metadata={
                        "authors": getattr(paper, "authors", []),
                        "year": getattr(paper, "year", None),
                    },
                )
            )

        return results
