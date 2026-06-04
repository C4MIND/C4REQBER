"""
Tests for src/patterns/library/language_evolution.py (Language Evolution Pattern)

Covers:
- LanguageEvolutionConfig dataclass
- LanguageEvolutionPattern initialization
- _initialize_fitness()
- _produce_utterances()
- _learn_grammar()
- _new_generation()
- _calculate_entropy()
- _calculate_divergence()
- run() simulation
- get_metadata()
- Edge cases: few speakers, different learning algorithms
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.language_evolution import (

    LanguageEvolutionPattern,
    LanguageEvolutionConfig,
)


# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestLanguageEvolutionConfig:
    def test_default_init(self):
        cfg = LanguageEvolutionConfig()
        assert cfg.n_speakers == 100
        assert cfg.n_generations == 50
        assert cfg.n_utterances == 10
        assert cfg.learning_algorithm == "frequency"
        assert cfg.fitness_landscape == "neutral"
        assert cfg.mutation_rate == 0.05

    def test_custom_init(self):
        cfg = LanguageEvolutionConfig(
            n_speakers=50,
            n_generations=20,
            learning_algorithm="bayesian",
            fitness_landscape="functional",
        )
        assert cfg.n_speakers == 50
        assert cfg.n_generations == 20
        assert cfg.learning_algorithm == "bayesian"
        assert cfg.fitness_landscape == "functional"


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestLanguageEvolutionPatternInit:
    def test_init_default(self):
        pattern = LanguageEvolutionPattern()
        assert pattern is not None
        assert pattern.config.n_speakers == 100
        assert pattern.population is not None

    def test_init_with_config(self):
        cfg = LanguageEvolutionConfig(n_speakers=50)
        pattern = LanguageEvolutionPattern(cfg)
        assert pattern.config.n_speakers == 50

    def test_class_constants(self):
        assert LanguageEvolutionPattern.PATTERN_ID == "language_evolution"
        assert LanguageEvolutionPattern.PATTERN_VERSION == "6.0.0"

    def test_population_shape(self):
        pattern = LanguageEvolutionPattern(LanguageEvolutionConfig(n_speakers=50, n_utterances=5))
        assert pattern.population.shape == (50, 5)


# ═══════════════════════════════════════════════════════════════════
# Fitness Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestInitializeFitness:
    def test_neutral_fitness(self):
        cfg = LanguageEvolutionConfig(fitness_landscape="neutral", n_utterances=5)
        pattern = LanguageEvolutionPattern(cfg)
        fitness = pattern._initialize_fitness()
        assert np.allclose(fitness, np.ones(5))

    def test_functional_fitness(self):
        cfg = LanguageEvolutionConfig(fitness_landscape="functional", n_utterances=5)
        pattern = LanguageEvolutionPattern(cfg)
        fitness = pattern._initialize_fitness()
        assert fitness[0] == 1.5  # Optimal form
        assert np.all(fitness[1:] >= 0.5)
        assert np.all(fitness[1:] <= 1.0)

    def test_social_fitness(self):
        cfg = LanguageEvolutionConfig(fitness_landscape="social", n_utterances=5)
        pattern = LanguageEvolutionPattern(cfg)
        fitness = pattern._initialize_fitness()
        assert np.allclose(fitness, np.ones(5))


# ═══════════════════════════════════════════════════════════════════
# Utterance Production Tests
# ═══════════════════════════════════════════════════════════════════


class TestProduceUtterances:
    def test_produce_utterances_count(self):
        cfg = LanguageEvolutionConfig(n_speakers=10, n_utterances=5)
        pattern = LanguageEvolutionPattern(cfg)
        utterances = pattern._produce_utterances(0, 20)
        assert len(utterances) == 20
        assert all(0 <= u < 5 for u in utterances)

    def test_produce_utterances_with_mutation(self):
        cfg = LanguageEvolutionConfig(
            n_speakers=10,
            n_utterances=5,
            mutation_rate=1.0,  # Always mutate
        )
        pattern = LanguageEvolutionPattern(cfg)
        utterances = pattern._produce_utterances(0, 10)
        assert len(utterances) == 10


# ═══════════════════════════════════════════════════════════════════
# Learning Algorithm Tests
# ═══════════════════════════════════════════════════════════════════


class TestLearnGrammar:
    def test_frequency_learning(self):
        cfg = LanguageEvolutionConfig(learning_algorithm="frequency", n_utterances=5)
        pattern = LanguageEvolutionPattern(cfg)
        data = [0, 0, 1, 2, 2, 2]
        grammar = pattern._learn_grammar(data)
        assert len(grammar) == 5
        assert np.abs(np.sum(grammar) - 1.0) < 1e-10  # Sums to 1
        assert grammar[2] > grammar[0] > grammar[1]  # Most frequent first

    def test_bayesian_learning(self):
        cfg = LanguageEvolutionConfig(learning_algorithm="bayesian", n_utterances=5)
        pattern = LanguageEvolutionPattern(cfg)
        data = [0, 0, 1, 2, 2, 2]
        grammar = pattern._learn_grammar(data)
        assert len(grammar) == 5
        assert np.abs(np.sum(grammar) - 1.0) < 1e-10

    def test_empty_data(self):
        cfg = LanguageEvolutionConfig(learning_algorithm="frequency", n_utterances=5)
        pattern = LanguageEvolutionPattern(cfg)
        grammar = pattern._learn_grammar([])
        assert len(grammar) == 5
        assert np.allclose(grammar, np.ones(5) / 5)


# ═══════════════════════════════════════════════════════════════════
# Entropy and Divergence Tests
# ═══════════════════════════════════════════════════════════════════


class TestEntropyAndDivergence:
    def test_calculate_entropy_uniform(self):
        cfg = LanguageEvolutionConfig(n_utterances=4)
        pattern = LanguageEvolutionPattern(cfg)
        uniform_dist = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = pattern._calculate_entropy(uniform_dist)
        assert entropy == pytest.approx(np.log(4), rel=1e-5)

    def test_calculate_entropy_zero(self):
        cfg = LanguageEvolutionConfig(n_utterances=4)
        pattern = LanguageEvolutionPattern(cfg)
        deterministic = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = pattern._calculate_entropy(deterministic)
        assert entropy == pytest.approx(0.0, abs=1e-10)

    def test_calculate_divergence(self):
        cfg = LanguageEvolutionConfig(n_speakers=10, n_utterances=4)
        pattern = LanguageEvolutionPattern(cfg)
        divergence = pattern._calculate_divergence()
        assert divergence >= 0  # KL divergence is non-negative


# ═══════════════════════════════════════════════════════════════════
# Run Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_default(self):
        cfg = LanguageEvolutionConfig(n_speakers=20, n_generations=5)
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        assert result is not None
        assert "final_frequencies" in result
        assert "statistics" in result
        assert "dominant_forms" in result

    def test_final_frequencies_sum(self):
        cfg = LanguageEvolutionConfig(n_speakers=20, n_generations=5)
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        freqs = np.array(result["final_frequencies"])
        assert np.abs(np.sum(freqs) - 1.0) < 1e-10

    def test_statistics_structure(self):
        cfg = LanguageEvolutionConfig(n_speakers=20, n_generations=5)
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        stats = result["statistics"]
        assert "entropy" in stats
        assert "normalized_entropy" in stats
        assert "n_fixed_forms" in stats
        assert "max_frequency" in stats

    def test_frequency_history(self):
        cfg = LanguageEvolutionConfig(
            n_speakers=20,
            n_generations=10,
            track_frequency_history=True,
        )
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        assert "frequency_history" in result
        assert len(result["frequency_history"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestMetadata:
    def test_metadata_structure(self):
        meta = LanguageEvolutionPattern.get_metadata()
        assert meta["id"] == "language_evolution"
        assert meta["version"] == "6.0.0"
        assert meta["name"] == "Language Evolution"
        assert "Linguistics" in meta["domain"]

    def test_metadata_parameters(self):
        meta = LanguageEvolutionPattern.get_metadata()
        param_names = [p["name"] for p in meta["parameters"]]
        assert "n_speakers" in param_names
        assert "n_generations" in param_names
        assert "learning_algorithm" in param_names


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_few_speakers(self):
        cfg = LanguageEvolutionConfig(n_speakers=5, n_generations=5)
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        assert "final_frequencies" in result

    def test_single_utterance(self):
        cfg = LanguageEvolutionConfig(n_speakers=10, n_utterances=1, n_generations=5)
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        assert result["final_frequencies"][0] == 1.0

    def test_high_mutation_rate(self):
        cfg = LanguageEvolutionConfig(n_speakers=20, n_generations=5, mutation_rate=0.5)
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        assert "final_frequencies" in result

    def test_high_innovation(self):
        cfg = LanguageEvolutionConfig(
            n_speakers=20,
            n_generations=5,
            innovation_probability=0.5,
        )
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        assert "final_frequencies" in result

    def test_multiple_communities(self):
        cfg = LanguageEvolutionConfig(
            n_speakers=20,
            n_generations=5,
            n_communities=2,
        )
        pattern = LanguageEvolutionPattern(cfg)
        result = pattern.run()
        assert "communities" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
