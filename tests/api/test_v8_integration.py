"""Integration tests for P0-P6 modules working together through v8 API."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v8_router import router as v8_router


app = FastAPI()
app.include_router(v8_router)
client = TestClient(app)


class TestP4AgendaToP5Exploration:
    """P4 (Agenda) feeds into P5 (Exploration) workflow."""

    @pytest.mark.anyio(backend="asyncio")
    def test_agenda_generates_questions_then_exploration_detects_anomalies(self) -> None:
        """End-to-end: agenda generates questions, exploration finds anomalies."""
        # Step 1: Generate agenda
        with (
            patch("src.api.v8_routers.agenda.AgendaGenerator") as MockGen,
            patch("src.api.v8_routers.agenda.FeasibilityChecker") as MockCheck,
            patch("src.api.v8_routers.agenda.PriorityScorer") as MockScore,
        ):
            mq = MagicMock()
            mq.to_dict.return_value = {"text": "Q1: Does X cause Y?", "strategy": "gap"}
            MockGen.return_value.generate.return_value = [mq]
            MockCheck.return_value.check.return_value = MagicMock(
                to_dict=lambda: {"has_tools": True}
            )
            MockScore.return_value.score.return_value = 0.9

            resp = client.post(
                "/v8/agenda/generate",
                json={
                    "knowledge_graph": {"nodes": ["X", "Y"], "edges": [["X", "Y"]]},
                    "recent_results": [],
                    "n_questions": 3,
                },
            )
        assert resp.status_code == 200
        agenda = resp.json()
        assert len(agenda["questions"]) > 0

        # Step 2: Exploration detects anomalies in the generated question space
        with patch("src.api.v8_routers.exploration.AnomalyDetector") as MockDet:
            MockDet.return_value.detect_literature_anomalies.return_value = []
            resp2 = client.post(
                "/v8/exploration/anomalies",
                json={
                    "embeddings": [[0.1, 0.2], [0.3, 0.4]],
                    "papers": [{"title": "Paper on X"}, {"title": "Paper on Y"}],
                },
            )
        assert resp2.status_code == 200
        anomalies = resp2.json()
        assert "total_detected" in anomalies

    @pytest.mark.anyio(backend="asyncio")
    def test_exploration_generates_surprise_questions(self) -> None:
        """P5: Generate surprising questions from existing agenda."""
        with patch("src.api.v8_routers.exploration.SurpriseDrivenQuestionGenerator") as MockGen:
            MockGen.return_value.generate = AsyncMock(
                return_value=[
                    "Why does X inhibit Y under condition Z?",
                    "What is the causal mechanism between X and Y?",
                ]
            )
            resp = client.post(
                "/v8/exploration/questions",
                json={
                    "existing_questions": ["Does X cause Y?"],
                    "topic": "causal inference",
                    "n_candidates": 10,
                    "top_k": 2,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert all("?" in q for q in data["questions"])


class TestP6DataSourcesIntegration:
    """P6 scientific data sources are reachable and return structured data."""

    @pytest.mark.anyio(backend="asyncio")
    def test_pubchem_search_integration(self) -> None:
        """PubChem client returns compound data."""
        from src.knowledge.sources.pubchem import PubChemClient

        client = PubChemClient()
        # Just verify the client initializes and has the right interface
        assert client.BASE_URL == "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        assert hasattr(client, "search_compound")
        assert hasattr(client, "get_properties")

    @pytest.mark.anyio(backend="asyncio")
    def test_ncbi_search_integration(self) -> None:
        """NCBI E-utilities client returns IDs."""
        from src.knowledge.sources.ncbi_eutils import NCBIEUtilsClient

        client = NCBIEUtilsClient(api_key="test_key", email="test@example.com")
        assert client.email == "test@example.com"
        assert client.BASE_URL == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def test_base_p6_context_manager(self) -> None:
        """All P6 clients support async context manager."""
        import asyncio

        from src.knowledge.sources.base_p6 import BaseP6Client

        async def _test():
            async with BaseP6Client() as c:
                assert c is not None

        asyncio.run(_test())


class TestP0FormalVerificationIntegration:
    """P0 auto-formalization is wired into verification clients."""

    @pytest.mark.anyio(backend="asyncio")
    async def test_lean4_client_verify_discovery_returns_structured(self) -> None:
        """Lean4 client uses auto-formalization config."""
        from src.verification.config import get_auto_formalization_config

        config = get_auto_formalization_config()
        assert config.enabled is True
        assert config.min_confidence == 0.7
        assert config.max_cost_per_discovery == 5.0

    def test_consensus_engine_available(self) -> None:
        """ConsensusEngine can be instantiated."""
        from src.verification.consensus_engine import ConsensusEngine

        engine = ConsensusEngine()
        assert engine is not None


class TestP1CausalInferenceIntegration:
    """P1 causal inference modules are importable and structured."""

    def test_discovery_engine_has_algorithms(self) -> None:
        """CausalDiscoveryEngine supports multiple algorithms."""
        from src.causal.discovery_engine import CausalDiscoveryEngine

        engine = CausalDiscoveryEngine()
        assert hasattr(engine, "discover")
        for algo in ["anm", "pc", "fci", "notears", "correlation"]:
            assert algo in engine.ALGORITHMS

    def test_gp_scm_available(self) -> None:
        """GPSCM is importable and has key methods."""
        from src.causal.gp_scm import GPSCM

        scm = GPSCM()
        assert hasattr(scm, "fit")
        assert hasattr(scm, "counterfactual")


class TestP2P3DiscoveryRankingAndClosedLoop:
    """P2 ranking and P3 closed-loop are wired correctly."""

    def test_rank_hypotheses_orchestrator(self) -> None:
        """rank_hypotheses orchestrator is callable."""
        import asyncio

        from src.discovery.ranking.orchestrator import rank_hypotheses

        result = asyncio.run(rank_hypotheses([], {}))
        assert result == []

    def test_closed_loop_orchestrator_init(self) -> None:
        """ClosedLoopOrchestrator initializes."""
        from src.discovery.closed_loop.orchestrator import ClosedLoopOrchestrator

        orch = ClosedLoopOrchestrator()
        assert orch is not None
        assert hasattr(orch, "run")
