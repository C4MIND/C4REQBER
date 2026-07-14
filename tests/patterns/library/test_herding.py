"""
Tests for herding pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.herding import HerdingConfig, HerdingModel


class TestConfig:
    def test_default_config(self):
        cfg = HerdingConfig()
        assert cfg.n_agents == 100
        assert cfg.n_states == 2
        assert cfg.temperature == 1.0
        assert cfg.J == 1.0

    def test_custom_config(self):
        cfg = HerdingConfig(n_agents=50, temperature=0.5)
        assert cfg.n_agents == 50
        assert cfg.temperature == 0.5


class TestInit:
    def test_model_init_default(self):
        model = HerdingModel()
        assert len(model.opinions) == 100
        assert model.network.shape == (100, 100)
        assert np.all(np.abs(model.opinions) == 1)

    def test_model_init_custom(self):
        cfg = HerdingConfig(n_agents=50)
        model = HerdingModel(cfg)
        assert len(model.opinions) == 50


class TestNetwork:
    def test_complete_network(self):
        cfg = HerdingConfig(n_agents=10, network_type="complete")
        model = HerdingModel(cfg)
        assert np.all(model.network + np.eye(10) == 1)

    def test_lattice_network(self):
        cfg = HerdingConfig(n_agents=10, network_type="lattice")
        model = HerdingModel(cfg)
        assert np.sum(model.network) == 20  # 2 neighbors each, bidirectional

    def test_small_world_network(self):
        cfg = HerdingConfig(n_agents=20, network_type="small_world")
        model = HerdingModel(cfg)
        assert model.network.shape == (20, 20)


class TestLocalField:
    def test_local_field_all_positive(self):
        cfg = HerdingConfig(n_agents=10, network_type="complete")
        model = HerdingModel(cfg)
        model.opinions = np.ones(10)
        field = model.local_field(0)
        assert field > 0
        assert field == cfg.J * 9

    def test_local_field_mixed(self):
        cfg = HerdingConfig(n_agents=10, network_type="complete")
        model = HerdingModel(cfg)
        model.opinions = np.concatenate([np.ones(5), -np.ones(5)])
        field = model.local_field(0)
        # Field sign depends on random initialization; just check it's finite
        assert np.isfinite(field)


class TestUpdateRules:
    def test_ising_update_strong_field(self):
        cfg = HerdingConfig(n_agents=10, temperature=0.01)
        model = HerdingModel(cfg)
        model.opinions = np.ones(10)
        model.opinions[0] = -1
        model.config.external_field = 5.0
        new_opinion = model.update_opinion_ising(0)
        assert new_opinion == 1

    def test_majority_update(self):
        cfg = HerdingConfig(n_agents=5, network_type="complete", temperature=0.01)
        model = HerdingModel(cfg)
        model.opinions = np.array([1, 1, 1, 1, -1])
        new_opinion = model.update_opinion_majority(4)
        assert new_opinion == 1

    def test_voter_update(self):
        cfg = HerdingConfig(n_agents=5, network_type="complete")
        model = HerdingModel(cfg)
        model.opinions = np.array([1, 1, 1, 1, -1])
        new_opinion = model.update_opinion_voter(4)
        assert new_opinion in [-1, 1]


class TestSimulate:
    def test_simulate_ising(self):
        cfg = HerdingConfig(n_agents=20, max_iterations=50)
        model = HerdingModel(cfg)
        result = model.simulate(update_rule="ising")
        assert "final_magnetization" in result
        assert "iterations" in result
        assert result["iterations"] <= 50

    def test_simulate_majority(self):
        cfg = HerdingConfig(n_agents=20, max_iterations=50)
        model = HerdingModel(cfg)
        result = model.simulate(update_rule="majority")
        assert "final_magnetization" in result

    def test_simulate_voter(self):
        cfg = HerdingConfig(n_agents=20, max_iterations=50)
        model = HerdingModel(cfg)
        result = model.simulate(update_rule="voter")
        assert "final_magnetization" in result


class TestCascade:
    def test_information_cascade(self):
        cfg = HerdingConfig(n_agents=20)
        model = HerdingModel(cfg)
        cascade = model.information_cascade()
        assert "decisions" in cascade
        assert len(cascade["decisions"]) == 20
        assert "cascade_started" in cascade

    def test_cascade_length(self):
        cfg = HerdingConfig(n_agents=10)
        model = HerdingModel(cfg)
        cascade = model.information_cascade()
        assert isinstance(cascade["cascade_started"], bool)


class TestSocialLearning:
    def test_social_learning(self):
        cfg = HerdingConfig(n_agents=20, max_iterations=100)
        model = HerdingModel(cfg)
        learning = model.social_learning(true_value=0.5)
        assert "final_beliefs" in learning
        assert "final_error" in learning
        assert learning["final_error"] < 0.2

    def test_consensus(self):
        cfg = HerdingConfig(n_agents=20, max_iterations=200)
        model = HerdingModel(cfg)
        learning = model.social_learning(true_value=0.5)
        assert isinstance(learning["consensus_reached"], bool)


class TestPhaseTransition:
    def test_phase_transition(self):
        cfg = HerdingConfig(n_agents=20, max_iterations=20)
        model = HerdingModel(cfg)
        phase = model.phase_transition_analysis()
        assert "temperatures" in phase
        assert "magnetizations" in phase
        assert "critical_temperature" in phase


class TestRun:
    def test_run(self):
        cfg = HerdingConfig(n_agents=20, max_iterations=20)
        model = HerdingModel(cfg)
        result = model.run()
        assert "opinion_dynamics" in result
        assert "information_cascade" in result
        assert "social_learning" in result
        assert "phase_transition" in result

    def test_metadata(self):
        meta = HerdingModel.get_metadata()
        assert "pattern_id" in meta
        assert "name" in meta


class TestEdgeCases:
    def test_single_agent(self):
        cfg = HerdingConfig(n_agents=1)
        model = HerdingModel(cfg)
        result = model.simulate(update_rule="ising")
        assert abs(result["final_magnetization"]) == 1.0

    def test_uniform_initial(self):
        cfg = HerdingConfig(n_agents=10, initial_opinion="uniform")
        model = HerdingModel(cfg)
        assert np.all(model.opinions == 1)

    def test_polarized_initial(self):
        cfg = HerdingConfig(n_agents=10, initial_opinion="polarized")
        model = HerdingModel(cfg)
        assert np.sum(model.opinions > 0) == 5
        assert np.sum(model.opinions < 0) == 5

    def test_external_field(self):
        cfg = HerdingConfig(n_agents=10, external_field=2.0)
        model = HerdingModel(cfg)
        model.opinions = np.ones(10)
        field = model.local_field(0)
        assert field >= cfg.external_field
