import threading
from sentence_transformers import SentenceTransformer
from typing import List

_embedder = None
_lock = threading.Lock()


def get_embedder() -> SentenceTransformer:
    """Thread-safe singleton SentenceTransformer to avoid memory bloat."""
    global _embedder
    if _embedder is None:
        with _lock:
            if _embedder is None:
                _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def encode(texts: List[str]) -> List[List[float]]:
    """Encode texts to embeddings."""
    model = get_embedder()
    return model.encode(texts).tolist()


def encode_query(text: str) -> List[float]:
    """Encode a single query."""
    model = get_embedder()
    return model.encode([text])[0].tolist()
