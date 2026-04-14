"""
TURBO-CDI: Test Suite
Comprehensive test coverage
"""

import pytest
import asyncio
from datetime import datetime


# Test C4 Core
class TestC4Core:
    def test_c4_state_creation(self):
        from src.core.c4_state import C4State

        state = C4State(T=1, S=1, A=1)
        assert state.to_coords() == {"T": 1, "S": 1, "A": 1}

    def test_hamming_distance(self):
        from src.core.c4_state import C4State

        s1 = C4State(T=0, S=0, A=0)
        s2 = C4State(T=2, S=2, A=2)
        assert s1.hamming_distance(s2) == 3

    def test_theorem_11(self):
        """Any state reachable in <=6 steps."""
        from src.core.c4_state import C4State, C4Space

        space = C4Space()
        start = C4State(T=0, S=0, A=0)
        end = C4State(T=2, S=2, A=2)

        # Should find path within 6 steps
        path = space.find_path(start, end)
        assert len(path) <= 6


# Test Knowledge Graph
class TestKnowledgeGraph:
    @pytest.fixture
    def kg(self):
        from src.graph.knowledge_graph import KnowledgeGraph

        return KnowledgeGraph()

    def test_add_discovery(self, kg):
        disc_id = kg.add_discovery(
            problem="test problem", hypothesis="test hypothesis", confidence_score=0.8
        )
        assert disc_id.startswith("discovery_")

    def test_get_node(self, kg):
        disc_id = kg.add_discovery(problem="test", hypothesis="test")
        node = kg.get_node(disc_id)
        assert node is not None
        assert node["node_type"] == "discovery"


# Test Validation
class TestValidation:
    def test_bayesian_update(self):
        from src.validation.tracker import BayesianUpdater

        updater = BayesianUpdater()

        # Initial confidence 0.5, update with validated evidence
        new_conf = updater.update(0.5, "validated", strength=0.5)
        assert new_conf > 0.5

        # Update with falsified evidence
        new_conf = updater.update(0.5, "falsified", strength=0.5)
        assert new_conf < 0.5


# Test Analogy Engine
class TestAnalogyEngine:
    def test_find_analogies(self):
        from src.analogy import get_analogy_engine

        engine = get_analogy_engine()

        results = engine.find_analogies(
            "biology", "computer_science", "neuron", top_k=3
        )
        assert len(results) <= 3
        assert all(r.confidence > 0 for r in results)


# Test API
@pytest.mark.asyncio
class TestAPI:
    async def test_health_endpoint(self):
        from src.api.server import app
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] in ["healthy", "degraded"]

    async def test_discover_endpoint(self):
        from src.api.server import app
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/discover", json={"problem": "test problem", "max_hypotheses": 2}
            )
            # Should return 401 without auth
            assert response.status_code == 401


# Test Multi-Agent System
@pytest.mark.asyncio
class TestMultiAgent:
    async def test_analyst_agent(self):
        from src.agents import AnalystAgent

        agent = AnalystAgent()

        result = await agent.process({"problem": "increase battery density"})
        assert result.agent_role == "analyst"
        assert "decomposition" in result.content


# Test Explainability
class TestExplainability:
    def test_explain_path(self):
        from src.explainability import get_explainability_engine

        engine = get_explainability_engine()

        explanation = engine.explain_path(
            problem="test",
            c4_path=["tau+", "sigma", "lambda+"],
            hypothesis="test hypothesis",
        )

        assert len(explanation.steps) == 3
        assert explanation.summary != ""


# Benchmark Tests
class TestBenchmarks:
    def test_hypothesis_generation_speed(self):
        """Benchmark: Generate hypothesis in <5 seconds."""
        import time
        from src.agent import get_agent

        start = time.time()
        agent = get_agent()
        # Mock async run
        result = asyncio.run(agent.discover("test problem", max_hypotheses=3))
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Too slow: {elapsed}s"

    def test_c4_path_finding(self):
        """Benchmark: Find path in <100ms."""
        import time
        from src.core.c4_state import C4State, C4Space

        space = C4Space()
        start = C4State(T=0, S=0, A=0)
        end = C4State(T=2, S=2, A=2)

        t0 = time.time()
        path = space.find_path(start, end)
        elapsed = (time.time() - t0) * 1000

        assert elapsed < 100, f"Too slow: {elapsed}ms"


# Integration Tests
@pytest.mark.asyncio
class TestIntegration:
    async def test_full_discovery_pipeline(self):
        """Test complete discovery cycle."""
        from src.solver.one_shot import get_one_shot_solver

        solver = get_one_shot_solver()
        result = await solver.solve(problem="optimize neural network", max_hypotheses=3)

        assert len(result.hypotheses) > 0
        assert result.duration_seconds > 0
        assert result.estimated_cost_usd >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
