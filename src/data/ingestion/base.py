"""
c4reqber: Unified Data Ingestion Layer

Plugin pattern for ingesting scientific data from multiple sources:
CSV, JSON, APIs (OpenAlex, PubChem, NCBI), synthetic generators.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import pandas as pd


@dataclass
class UnifiedDataFrame:
    """Standardized data container with metadata."""

    data: pd.DataFrame
    source: str
    query: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, int]:
        return self.data.shape

    @property
    def columns(self) -> list[str]:
        return list(self.data.columns)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "shape": self.shape,
            "columns": self.columns,
            "metadata": self.metadata,
        }


class DataSource(Protocol):
    """Protocol for all data ingestion sources."""

    name: str

    async def load(self, query: dict[str, Any]) -> UnifiedDataFrame | None:
        """Load data from source. Returns None if unavailable."""
        ...

    def supports_causal_discovery(self) -> bool:
        """Whether this source provides structured tabular data suitable for causal discovery."""
        ...

    def supports_tabular(self) -> bool:
        """Whether this source provides tabular data."""
        ...


class CSVAdapter:
    """Adapter for local CSV files."""

    name = "csv"

    async def load(self, query: dict[str, Any]) -> UnifiedDataFrame | None:
        path = query.get("path")
        if not path:
            return None
        try:
            df = pd.read_csv(path)
            return UnifiedDataFrame(
                data=df,
                source="csv",
                query=query,
                metadata={"path": path, "rows": len(df)},
            )
        except Exception:
            return None

    def supports_causal_discovery(self) -> bool:
        return True

    def supports_tabular(self) -> bool:
        return True


class SyntheticSCMAdapter:
    """Generate synthetic data from a Structural Causal Model for testing."""

    name = "synthetic_scm"

    async def load(self, query: dict[str, Any]) -> UnifiedDataFrame | None:
        n_samples = query.get("n_samples", 1000)
        n_nodes = query.get("n_nodes", 5)
        seed = query.get("seed", 42)

        import numpy as np

        rng = np.random.default_rng(seed)

        # Generate random DAG
        nodes = [f"X{i}" for i in range(n_nodes)]
        data: dict[str, Any] = {}

        for i, node in enumerate(nodes):
            parents = nodes[:i]  # chain structure for simplicity
            if not parents:
                data[node] = rng.normal(0, 1, n_samples)
            else:
                parent_sum = sum(data[p] for p in parents)
                noise = rng.normal(0, 0.5, n_samples)
                # Nonlinear: sigmoid + linear
                data[node] = 1 / (1 + np.exp(-parent_sum * 0.5)) + parent_sum * 0.3 + noise

        df = pd.DataFrame(data)
        return UnifiedDataFrame(
            data=df,
            source="synthetic_scm",
            query=query,
            metadata={
                "n_samples": n_samples,
                "n_nodes": n_nodes,
                "seed": seed,
                "structure": "chain",
            },
        )

    def supports_causal_discovery(self) -> bool:
        return True

    def supports_tabular(self) -> bool:
        return True


class DataSourceRegistry:
    """Registry of all available data sources."""

    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}
        self.register(CSVAdapter())
        self.register(SyntheticSCMAdapter())

    def register(self, source: DataSource) -> None:
        self._sources[source.name] = source

    def get(self, name: str) -> DataSource | None:
        return self._sources.get(name)

    def list_sources(self) -> list[str]:
        return list(self._sources.keys())

    async def load(self, source_name: str, query: dict[str, Any]) -> UnifiedDataFrame | None:
        source = self._sources.get(source_name)
        if not source:
            return None
        return await source.load(query)


# Global registry
_registry: DataSourceRegistry | None = None


def get_data_source_registry() -> DataSourceRegistry:
    """Get the global data source registry."""
    global _registry
    if _registry is None:
        _registry = DataSourceRegistry()
    return _registry
