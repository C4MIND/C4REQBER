"""Tests for src.data.orchestrator — auto-data-retrieval for causal discovery."""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from src.data.orchestrator import DataOrchestrator, DOMAIN_DATA_SOURCES, get_dataframe_for_hypothesis


class TestDomainMapping:
    def test_domain_sources_not_empty(self):
        for domain, sources in DOMAIN_DATA_SOURCES.items():
            assert sources, f"Domain {domain!r} has no mapped sources"
            assert len(set(sources)) == len(sources), f"Domain {domain!r} has duplicate sources"

    def test_resolve_sources_known_domain(self):
        orch = DataOrchestrator()
        sources = orch._resolve_sources("medicine", "drug bioactivity")
        assert "chembl" in sources
        assert "pubchem" in sources
        assert "kaggle" in sources

    def test_resolve_sources_unknown_domain_defaults_to_science(self):
        orch = DataOrchestrator()
        sources = orch._resolve_sources("unknown_domain_xyz", "crystal structure")
        # Should fall back to science defaults
        assert "kaggle" in sources
        assert "uci_ml" in sources

    def test_resolve_sources_keyword_boost(self):
        orch = DataOrchestrator()
        sources = orch._resolve_sources("general", "band gap and fermi energy")
        assert "materials_project" in sources
        # "aflow" is only boosted by its own keywords (aflow, icsd, space group, wyckoff, enthalpy)
        sources_aflow = orch._resolve_sources("general", "perovskite aflow enthalpy")
        assert "aflow" in sources_aflow

    def test_registry_sources_not_primary(self):
        orch = DataOrchestrator()
        sources = orch._resolve_sources("social_science", "survey data")
        # re3data is a registry; it should not appear before real data sources
        if "re3data" in sources:
            assert sources.index("re3data") > 0


class TestDataFrameScoring:
    def test_score_prefers_numeric_columns(self):
        orch = DataOrchestrator()
        df_text = pd.DataFrame({"a": ["x", "y"], "b": ["z", "w"]})
        df_num = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
        assert orch._score_dataframe(df_num, "test") > orch._score_dataframe(df_text, "test")

    def test_score_boosts_keyword_match(self):
        orch = DataOrchestrator()
        df = pd.DataFrame({"temperature": [1.0, 2.0], "pressure": [3.0, 4.0]})
        score = orch._score_dataframe(df, "temperature effect on pressure")
        assert score > 0


class TestFlattenDict:
    def test_flatten_simple(self):
        orch = DataOrchestrator()
        assert orch._flatten_dict({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_flatten_nested(self):
        orch = DataOrchestrator()
        result = orch._flatten_dict({"a": {"b": 1}}, prefix="root")
        assert result == {"root_a_b": 1}

    def test_flatten_skips_lists(self):
        orch = DataOrchestrator()
        result = orch._flatten_dict({"a": [1, 2], "b": 3})
        assert "a" not in result
        assert result["b"] == 3


class TestFindCsvUrl:
    def test_find_csv_in_flat_dict(self):
        orch = DataOrchestrator()
        assert orch._find_csv_url_in_dict({"url": "https://example.com/data.csv"}) == "https://example.com/data.csv"

    def test_find_csv_in_nested_dict(self):
        orch = DataOrchestrator()
        d = {"meta": {"download": "https://example.com/file.csv"}}
        assert orch._find_csv_url_in_dict(d) == "https://example.com/file.csv"

    def test_no_csv_returns_none(self):
        orch = DataOrchestrator()
        assert orch._find_csv_url_in_dict({"url": "https://example.com/page.html"}) is None


class TestExtractBestDataFrame:
    @pytest.mark.anyio(backend="asyncio")
    async def test_no_results_returns_none(self):
        orch = DataOrchestrator()
        df, meta = await orch._extract_best_dataframe(
            [{"source": "kaggle", "items": [], "error": None}], "test"
        )
        assert df is None
        assert meta["attempts"][0]["status"] == "no_results"

    @pytest.mark.anyio(backend="asyncio")
    async def test_structured_source_success(self):
        orch = DataOrchestrator()
        orch.MIN_ROWS = 1  # lower threshold so 1-row test DF is accepted
        # Mock the client method to return properties
        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(return_value={"band_gap": 1.2, "energy": -5.0})
        orch._clients["materials_project"] = mock_client

        items = [{"material_id": "mp-1", "formula": "FeO"}]
        df, meta = await orch._extract_best_dataframe(
            [{"source": "materials_project", "items": items, "error": None}], "band gap"
        )
        assert df is not None
        assert "prop_band_gap" in df.columns or "band_gap" in df.columns
        assert meta["best_source"] == "materials_project"

    @pytest.mark.anyio(backend="asyncio")
    async def test_too_small_dataframe_rejected(self):
        orch = DataOrchestrator()
        # Return a tiny DataFrame via a structured source
        mock_client = MagicMock()
        mock_client.get_properties = AsyncMock(return_value={"x": 1})
        orch._clients["materials_project"] = mock_client

        items = [{"material_id": "mp-1"}]
        df, meta = await orch._extract_best_dataframe(
            [{"source": "materials_project", "items": items, "error": None}], "test"
        )
        assert df is None
        assert any("too_small" in str(a.get("status", "")) for a in meta["attempts"])


class TestDownloadCsv:
    @pytest.mark.anyio(backend="asyncio")
    async def test_download_csv_success(self):
        csv_content = b"a,b\n1,2\n3,4\n"
        orch = DataOrchestrator()

        mock_response = MagicMock()
        mock_response.content = csv_content
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            df = await orch._download_csv("https://example.com/data.csv")
            assert df is not None
            assert list(df.columns) == ["a", "b"]
            assert len(df) == 2

    @pytest.mark.anyio(backend="asyncio")
    async def test_download_csv_failure_returns_none(self):
        orch = DataOrchestrator()
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("network")):
            df = await orch._download_csv("https://example.com/data.csv")
            assert df is None


class TestIntegration:
    @pytest.mark.anyio(backend="asyncio")
    async def test_get_dataframe_for_hypothesis_runs_without_crash(self):
        """End-to-end smoke test with mocked clients."""
        orch = DataOrchestrator()

        # Patch every client init to return a mock that returns empty lists
        def mock_get_client(source: str) -> Any:
            mock = MagicMock()
            mock.search_datasets = AsyncMock(return_value=[])
            mock.search_materials = AsyncMock(return_value=[])
            mock.search_molecule = AsyncMock(return_value=[])
            mock.search_compound = AsyncMock(return_value=[])
            mock.search_gene = AsyncMock(return_value=[])
            mock.search_drugs = AsyncMock(return_value=[])
            mock.search_stations = AsyncMock(return_value=[])
            mock.search_repositories = AsyncMock(return_value=[])
            return mock

        orch._get_client = mock_get_client  # type: ignore[method-assign]

        df, report = await orch.get_dataframe_for_hypothesis("band gap prediction", "materials")
        assert report["sources_searched"]
        assert report["sources_count"] > 0
        # With mocked empty responses, df should be None
        assert df is None
        assert report["dataframe_extracted"] is False

    def test_sync_wrapper_no_event_loop(self):
        """The sync wrapper should work when no loop is running."""
        df, report = get_dataframe_for_hypothesis("test", "general")
        # In a test environment clients may fail to init; we just assert it returns
        assert isinstance(report, dict)
        assert "sources_searched" in report or "note" in report
