import chromadb
from pathlib import Path
from typing import List, Dict, Optional


class UserDocumentStore:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.client = chromadb.PersistentClient(
            path=str(Path.home() / ".turbo-cdi" / "vectors")
        )
        self.collection = self.client.get_or_create_collection(
            name=f"user_docs_{user_id}",
            metadata={"hnsw:space": "cosine"}
        )

    def add_document(
        self,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Optional[Dict] = None
    ) -> None:
        """Add document chunks to vector store."""
        metadatas = []
        for i in range(len(chunks)):
            base = {
                "doc_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_type": "user_upload"
            }
            if metadata:
                base.update(metadata)
            metadatas.append(base)

        self.collection.add(
            ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def query(
        self,
        embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict:
        """Query vector store."""
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

    def delete_document(self, doc_id: str) -> None:
        """Delete all chunks for a document."""
        self.collection.delete(where={"doc_id": doc_id})

    def list_documents(self) -> List[str]:
        """List all unique doc_ids in collection."""
        results = self.collection.get(include=["metadatas"])
        if not results or not results.get("metadatas"):
            return []
        return list(set(m["doc_id"] for m in results["metadatas"]))
