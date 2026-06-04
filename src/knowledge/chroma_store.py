"""ChromaDB Vector Store — RAG backend for C4REQBER knowledge pipeline.

Stores embeddings from LLM calls, knowledge search results, and agent memory.
Provides semantic search (cosine similarity) for retrieval-augmented generation.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from typing import Any


logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Vector store wrapper for ChromaDB.

    Auto-creates collections for: knowledge_cache, agent_memory, paper_embeddings.
    Falls back gracefully if chromadb not installed.
    """

    def __init__(self, persist_dir: str | None = None) -> None:
        if persist_dir is not None:
            # Path traversal guard: ensure persist_dir is within home directory
            abs_dir = os.path.abspath(os.path.expanduser(persist_dir))
            base = os.path.expanduser("~/.c4reqber")
            if not abs_dir.startswith(os.path.abspath(base)):
                raise ValueError(f"persist_dir must be under {base}: {persist_dir}")
            self.persist_dir = abs_dir
        else:
            self.persist_dir = os.path.expanduser("~/.c4reqber/chromadb")
        self._client = None
        self._collections: dict[str, Any] = {}
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        try:
            import chromadb
            return True
        except ImportError:
            return False

    def _get_client(self):
        if not self._client and self.available:
            import chromadb
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

    def _get_collection(self, name: str):
        if name not in self._collections:
            with self._lock:
                if name not in self._collections:
                    client = self._get_client()
                    if client:
                        import chromadb.errors
                        try:
                            self._collections[name] = client.get_or_create_collection(name)
                        except chromadb.errors.ChromaError as e:
                            logger.debug("get_or_create_collection failed: %s", e)
                            # Fallback: try get, then create if not exists
                            try:
                                self._collections[name] = client.get_collection(name)
                            except chromadb.errors.ChromaError:
                                try:
                                    self._collections[name] = client.create_collection(name)
                                except chromadb.errors.ChromaError as e2:
                                    logger.debug("create_collection also failed: %s", e2)
                                    return None
        return self._collections.get(name)

    def add_knowledge(
        self, query: str, results: list[dict], metadata: dict | None = None
    ) -> None:
        """Cache knowledge search results as embeddings."""
        if not self.available:
            return
        try:
            coll = self._get_collection("knowledge_cache")
            if not coll:
                return
            ids = []
            docs = []
            for i, r in enumerate(results[:50]):
                rid = r.get("id", r.get("doi", f"result_{i}"))
                ids.append(f"k_{rid}")
                doc = f"{r.get('title', '')} {r.get('abstract', r.get('snippet', ''))}"
                docs.append(doc[:4000])  # Truncate to avoid ChromaDB overflow
            if ids:
                coll.add(documents=docs, ids=ids, metadatas=[dict(metadata or {}) for _ in ids])
        except Exception as e:
            logger.debug("ChromaDB add_knowledge failed: %s", e)

    def search_knowledge(self, query: str, n_results: int = 5) -> list[dict]:
        """Semantic search cached knowledge."""
        if not self.available:
            return []
        try:
            coll = self._get_collection("knowledge_cache")
            if not coll:
                return []
            results = coll.query(query_texts=[query], n_results=n_results)
            docs = results.get("documents", [[]]) if results else [[]]
            return docs[0] if docs and docs[0] else []
        except Exception as e:
            logger.debug("ChromaDB search failed: %s", e)
            return []

    def store_memory(self, session_id: str, text: str, metadata: dict | None = None) -> None:
        """Store agent memory entry."""
        if not self.available:
            return
        try:
            coll = self._get_collection("agent_memory")
            if not coll:
                return
            import uuid
            coll.add(
                documents=[text],
                ids=[f"mem_{session_id}_{uuid.uuid4().hex[:8]}"],
                metadatas=[metadata or {}],
            )
        except Exception as e:
            logger.debug("ChromaDB store_memory failed: %s", e)

    def recall_memory(self, session_id: str, query: str, n_results: int = 5) -> list[str]:
        """Recall similar memories from agent history."""
        if not self.available:
            return []
        try:
            coll = self._get_collection("agent_memory")
            if not coll:
                return []
            results = coll.query(
                query_texts=[query],
                n_results=n_results,
                where={"session_id": session_id},
            )
            return results.get("documents", [[]])[0] if results else []
        except Exception:
            logger.warning("ChromaDB recall_memory failed", exc_info=True)
            return []

    def _chunk_text(self, text: str, max_sentences: int = 3) -> list[str]:
        """Split text into sentence-based chunks."""
        sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if s.strip()]
        chunks = []
        for i in range(0, len(sentences), max_sentences):
            chunk = " ".join(sentences[i : i + max_sentences])
            if chunk:
                chunks.append(chunk)
        return chunks if chunks else [text]

    def add_paper_embeddings(self, papers: list[dict]) -> None:
        """Index papers with embeddings for discovery pipeline.

        Stores both full abstracts and sentence-level chunks for
        finer-grained semantic retrieval.
        """
        if not self.available:
            return
        try:
            coll = self._get_collection("paper_embeddings")
            if not coll:
                return
            ids, docs, metas = [], [], []
            for p in papers[:100]:
                pid = p.get("doi", p.get("id", ""))
                if not pid:
                    continue
                title = p.get("title", "")
                abstract = p.get("abstract", "")
                # Store full abstract
                ids.append(f"paper_{pid}")
                docs.append(f"{title} {abstract}")
                metas.append({
                    "title": title,
                    "year": str(p.get("year", "")),
                    "source": p.get("source", ""),
                    "chunk_type": "full",
                })
                # Store sentence chunks for finer retrieval
                chunks = self._chunk_text(abstract, max_sentences=3)
                for ci, chunk in enumerate(chunks[:4]):
                    ids.append(f"paper_{pid}_chunk_{ci}")
                    docs.append(f"{title} {chunk}")
                    metas.append({
                        "title": title,
                        "year": str(p.get("year", "")),
                        "source": p.get("source", ""),
                        "chunk_type": "chunk",
                        "chunk_index": ci,
                    })
            if ids:
                coll.add(documents=docs, ids=ids, metadatas=metas)
        except Exception as e:
            logger.debug("ChromaDB paper_embeddings failed: %s", e)

    def search_papers(self, query: str, n_results: int = 10) -> list[dict]:
        """Semantic search across indexed papers.

        Returns a list of dicts containing both metadata and the matched document chunk.
        """
        if not self.available:
            return []
        try:
            coll = self._get_collection("paper_embeddings")
            if not coll:
                return []
            results = coll.query(query_texts=[query], n_results=n_results, include=["documents", "metadatas"])
            if not results:
                return []
            metadatas = results.get("metadatas", [[]])[0]
            documents = results.get("documents", [[]])[0]
            merged = []
            for meta, doc in zip(metadatas, documents, strict=False):
                entry = dict(meta) if meta else {}
                entry["matched_text"] = doc or ""
                merged.append(entry)
            return merged
        except Exception:
            logger.warning("ChromaDB search_papers failed", exc_info=True)
            return []

    async def test_connection(self) -> dict[str, Any]:
        if not self.available:
            return {"healthy": False, "error": "chromadb not installed"}
        try:
            self._get_client()
            return {"healthy": True, "collections": list(self._collections.keys()), "persist_dir": self.persist_dir}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
