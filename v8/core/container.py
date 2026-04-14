from typing import Optional
from core.settings import Settings
from rag.retriever import HybridRetriever
from rag.ingestion import DocumentIngester
from discovery.lab import DiscoveryLab


class Container:
    """Dependency Injection Container for TURBO-CDI v8.3"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._retriever: Optional[HybridRetriever] = None
        self._ingester: Optional[DocumentIngester] = None
        self._discovery_lab: Optional[DiscoveryLab] = None

    @property
    def retriever(self) -> HybridRetriever:
        """Lazy-loaded HybridRetriever"""
        if self._retriever is None:
            self._retriever = HybridRetriever()
        return self._retriever

    @property
    def document_ingester(self) -> DocumentIngester:
        """Lazy-loaded DocumentIngester"""
        if self._ingester is None:
            self._ingester = DocumentIngester()
        return self._ingester

    @property
    def discovery_lab(self) -> DiscoveryLab:
        """Lazy-loaded DiscoveryLab"""
        if self._discovery_lab is None:
            self._discovery_lab = DiscoveryLab()
        return self._discovery_lab
