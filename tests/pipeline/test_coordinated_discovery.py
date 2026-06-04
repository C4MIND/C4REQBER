from __future__ import annotations

from src.pipeline.coordinated_discovery import (
    CoordinatedDiscovery,
    CrossValidation,
    PipelineAgent,
)


class TestPipelineAgent:
    def test_elapsed_returns_zero_when_not_started(self) -> None:
        agent = PipelineAgent(id="test", scientist_path="einstein", triz_principle="segmentation", mode="turbo")
        assert agent.elapsed == 0.0

    def test_elapsed_positive_after_start(self) -> None:
        agent = PipelineAgent(id="test", scientist_path="einstein", triz_principle="segmentation", mode="turbo")
        agent.started_at = 1000.0
        assert agent.elapsed > 0.0

    def test_elapsed_uses_finished_at_when_set(self) -> None:
        agent = PipelineAgent(id="test", scientist_path="darwin", triz_principle="extraction", mode="solve")
        agent.started_at = 1000.0
        agent.finished_at = 1500.0
        assert agent.elapsed == 500.0


class TestCoordinatedDiscoveryPlan:
    def test_plan_generates_n_agents(self) -> None:
        cd = CoordinatedDiscovery(num_agents=3, mode="turbo")
        agents = cd.plan("quantum gravity")
        assert len(agents) == 3

    def test_plan_agents_have_unique_ids(self) -> None:
        cd = CoordinatedDiscovery(num_agents=5, mode="turbo")
        agents = cd.plan("protein folding")
        ids = {a.id for a in agents}
        assert len(ids) == 5

    def test_plan_agents_have_assigned_path_and_triz(self) -> None:
        cd = CoordinatedDiscovery(num_agents=3, mode="turbo")
        agents = cd.plan("climate modeling")
        for agent in agents:
            assert agent.scientist_path in CoordinatedDiscovery.SCIENTIST_PATHS
            assert agent.triz_principle in CoordinatedDiscovery.TRIZ_PRINCIPLES
            assert agent.mode == "turbo"
            assert agent.id.startswith("agent_")

    def test_plan_is_deterministic_same_topic(self) -> None:
        cd1 = CoordinatedDiscovery(num_agents=4, mode="solve")
        cd2 = CoordinatedDiscovery(num_agents=4, mode="solve")
        agents1 = cd1.plan("dark matter")
        agents2 = cd2.plan("dark matter")
        assert [a.id for a in agents1] == [a.id for a in agents2]
        assert [a.scientist_path for a in agents1] == [a.scientist_path for a in agents2]

    def test_plan_num_agents_capped_by_scientist_paths(self) -> None:
        cd = CoordinatedDiscovery(num_agents=50, mode="turbo")
        agents = cd.plan("anything")
        assert len(agents) == len(CoordinatedDiscovery.SCIENTIST_PATHS)


class TestCrossValidateGaps:
    def test_cross_validate_gaps_empty_when_no_gaps(self) -> None:
        cd = CoordinatedDiscovery(num_agents=3, mode="turbo")
        cd.plan("test topic")
        result = cd.cross_validate_gaps()
        assert result == []

    def test_cross_validate_gaps_returns_validations_with_gaps(self) -> None:
        cd = CoordinatedDiscovery(num_agents=3, mode="turbo")
        cd.plan("test topic")
        cd._agents[0].gaps = [{"area": "quantum error correction", "desc": "gap1"}]
        cd._agents[0].hypotheses = [{"title": "surface codes are optimal", "conclusion": "promising"}]
        cd._agents[1].gaps = [{"area": "quantum error correction", "desc": "gap1"}]
        cd._agents[1].hypotheses = [{"title": "surface codes are optimal", "conclusion": "promising"}]
        cd._agents[2].gaps = [{"area": "topological qubits"}]
        cd._agents[2].hypotheses = [{"title": "anyon braiding", "conclusion": "unverified"}]
        result = cd.cross_validate_gaps()
        assert len(result) > 0
        assert all(isinstance(cv, CrossValidation) for cv in result)

    def test_cross_validate_gaps_finds_overlap(self) -> None:
        cd = CoordinatedDiscovery(num_agents=2, mode="turbo")
        cd.plan("test")
        cd._agents[0].gaps = [{"area": "cold fusion"}]
        cd._agents[0].hypotheses = [{"title": "muon catalysis"}]
        cd._agents[1].gaps = [{"area": "cold fusion"}]
        cd._agents[1].hypotheses = [{"title": "muon catalysis"}]
        result = cd.cross_validate_gaps()
        assert len(result) == 1
        assert result[0].gap_overlap == 1.0
        assert result[0].hypothesis_agreement == 1.0

    def test_cross_validate_detects_contradiction(self) -> None:
        cd = CoordinatedDiscovery(num_agents=2, mode="turbo")
        cd.plan("test")
        cd._agents[0].gaps = [{"area": "dark energy"}]
        cd._agents[0].hypotheses = [{"title": "modified gravity", "conclusion": "viable"}]
        cd._agents[1].gaps = [{"area": "dark energy"}]
        cd._agents[1].hypotheses = [{"title": "cosmological constant", "conclusion": "refuted"}]
        result = cd.cross_validate_gaps()
        assert result[0].contradictory is True


class TestCrossValidationReport:
    def test_report_returns_string(self) -> None:
        cd = CoordinatedDiscovery(num_agents=2, mode="turbo")
        cd.plan("test")
        cd._agents[0].gaps = [{"area": "quantum gravity"}]
        cd._agents[0].hypotheses = [{"title": "loop quantum gravity"}]
        cd._agents[1].gaps = [{"area": "quantum gravity"}]
        cd._agents[1].hypotheses = [{"title": "string theory"}]
        cd.cross_validate_gaps()
        report = cd.cross_validation_report()
        assert isinstance(report, str)
        assert "Cross-Validation Report" in report
        assert "Agreement Score" in report


class TestMergeConsensus:
    def test_merge_consensus_returns_result(self) -> None:
        cd = CoordinatedDiscovery(num_agents=2, mode="turbo")
        cd.plan("test topic")
        cd._agents[0].gaps = [{"area": "protein folding"}]
        cd._agents[0].hypotheses = [{"title": "alphafold-like approach"}]
        cd._agents[1].gaps = [{"area": "protein folding"}]
        cd._agents[1].hypotheses = [{"title": "physics-based approach"}]
        cd.cross_validate_gaps()
        result = cd.merge_consensus()
        assert len(result.agents) == 2
        assert len(result.consensus_gaps) > 0
        assert result.agreement_score >= 0.0
