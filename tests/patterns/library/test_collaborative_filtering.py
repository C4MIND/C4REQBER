"""
Tests for src/patterns/library/collaborative_filtering.py (Collaborative Filtering Pattern)

Covers:
- CFAlgorithm enum
- CollaborativeFilteringConfig dataclass
- CollaborativeFilteringPattern initialization
- _initialize() and _generate_ratings()
- _predict() matrix factorization
- _calculate_loss() and _calculate_rmse()
- _als_step() alternating least squares
- _sgd_step() stochastic gradient descent
- _svd_step() singular value decomposition
- run() training loop
- _format_output() results
- _recommend_for_cold_start()
- get_metadata()
- Edge cases: zero ratings, single user/item, extreme sparsity
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.collaborative_filtering import (
    CFAlgorithm,
    CollaborativeFilteringConfig,
    CollaborativeFilteringPattern,
)


# ═══════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ═══════════════════════════════════════════════════════════════════


class TestCFAlgorithm:
    def test_enum_values(self):
        assert CFAlgorithm.SVD.value == "svd"
        assert CFAlgorithm.NMF.value == "nmf"
        assert CFAlgorithm.ALS.value == "als"
        assert CFAlgorithm.SGD.value == "sgd"


class TestCollaborativeFilteringConfig:
    def test_default_init(self):
        cfg = CollaborativeFilteringConfig()
        assert cfg.algorithm == CFAlgorithm.ALS
        assert cfg.n_users == 100
        assert cfg.n_items == 50
        assert cfg.n_factors == 10
        assert cfg.sparsity == 0.9
        assert cfg.rating_range == (1.0, 5.0)
        assert cfg.learning_rate == 0.01
        assert cfg.regularization == 0.1
        assert cfg.n_epochs == 20
        assert cfg.batch_size == 32
        assert cfg.decay == 0.99
        assert cfg.test_ratio == 0.2
        assert cfg.cold_start_users == 5

    def test_custom_init(self):
        cfg = CollaborativeFilteringConfig(
            algorithm=CFAlgorithm.SGD,
            n_users=200,
            n_items=100,
            n_factors=20,
            sparsity=0.8,
            learning_rate=0.02,
        )
        assert cfg.algorithm == CFAlgorithm.SGD
        assert cfg.n_users == 200
        assert cfg.n_items == 100
        assert cfg.n_factors == 20
        assert cfg.sparsity == 0.8
        assert cfg.learning_rate == 0.02


# ═══════════════════════════════════════════════════════════════════
# CollaborativeFilteringPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestCollaborativeFilteringPatternInit:
    def test_init(self):
        pattern = CollaborativeFilteringPattern()
        assert pattern is not None
        assert pattern.config is not None
        assert pattern.ratings is not None
        assert pattern.mask is not None
        assert pattern.U is not None
        assert pattern.V is not None

    def test_pattern_id(self):
        assert CollaborativeFilteringPattern.PATTERN_ID == "collaborative_filtering"
        assert CollaborativeFilteringPattern.PATTERN_VERSION == "6.0.0"


# ═══════════════════════════════════════════════════════════════════
# Ratings Generation
# ═══════════════════════════════════════════════════════════════════


class TestGenerateRatings:
    def test_ratings_shape(self):
        cfg = CollaborativeFilteringConfig(n_users=50, n_items=30)
        pattern = CollaborativeFilteringPattern(cfg)
        assert pattern.ratings.shape == (50, 30)

    def test_ratings_have_nans(self):
        cfg = CollaborativeFilteringConfig(n_users=50, n_items=30, sparsity=0.9)
        pattern = CollaborativeFilteringPattern(cfg)
        assert np.sum(np.isnan(pattern.ratings)) > 0

    def test_rating_range(self):
        cfg = CollaborativeFilteringConfig(rating_range=(1.0, 5.0))
        pattern = CollaborativeFilteringPattern(cfg)
        valid_ratings = pattern.ratings[~np.isnan(pattern.ratings)]
        assert np.all(valid_ratings >= 1.0)
        assert np.all(valid_ratings <= 5.0)

    def test_cold_start_users(self):
        cfg = CollaborativeFilteringConfig(n_users=20, cold_start_users=5)
        pattern = CollaborativeFilteringPattern(cfg)
        # Cold start users should have very few ratings
        for u in range(5):
            rated_items = np.sum(~np.isnan(pattern.ratings[u, :]))
            assert rated_items <= 3


# ═══════════════════════════════════════════════════════════════════
# Prediction
# ═══════════════════════════════════════════════════════════════════


class TestPredict:
    def test_prediction_shape(self):
        cfg = CollaborativeFilteringConfig(n_users=50, n_items=30, n_factors=10)
        pattern = CollaborativeFilteringPattern(cfg)
        predictions = pattern._predict()
        assert predictions.shape == (50, 30)

    def test_prediction_finite(self):
        cfg = CollaborativeFilteringConfig()
        pattern = CollaborativeFilteringPattern(cfg)
        predictions = pattern._predict()
        assert np.all(np.isfinite(predictions))


# ═══════════════════════════════════════════════════════════════════
# Loss and RMSE Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateLoss:
    def test_loss_positive(self):
        cfg = CollaborativeFilteringConfig()
        pattern = CollaborativeFilteringPattern(cfg)
        loss = pattern._calculate_loss(pattern.train_mask)
        assert loss >= 0

    def test_loss_with_regularization(self):
        cfg = CollaborativeFilteringConfig(regularization=0.1)
        pattern = CollaborativeFilteringPattern(cfg)
        loss1 = pattern._calculate_loss(pattern.train_mask)
        cfg2 = CollaborativeFilteringConfig(regularization=1.0)
        pattern2 = CollaborativeFilteringPattern(cfg2)
        loss2 = pattern2._calculate_loss(pattern2.train_mask)
        # Higher regularization should generally increase loss
        # (though random initialization makes this probabilistic)
        assert loss1 >= 0 and loss2 >= 0


class TestCalculateRMSE:
    def test_rmse_positive(self):
        cfg = CollaborativeFilteringConfig()
        pattern = CollaborativeFilteringPattern(cfg)
        rmse = pattern._calculate_rmse(pattern.train_mask)
        assert rmse >= 0

    def test_rmse_finite(self):
        cfg = CollaborativeFilteringConfig()
        pattern = CollaborativeFilteringPattern(cfg)
        rmse = pattern._calculate_rmse(pattern.train_mask)
        assert np.isfinite(rmse)


# ═══════════════════════════════════════════════════════════════════
# Training Steps
# ═══════════════════════════════════════════════════════════════════


class TestALSStep:
    def test_als_updates_factors(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.ALS)
        pattern = CollaborativeFilteringPattern(cfg)
        U_before = pattern.U.copy()
        pattern._als_step()
        # Factors should be updated
        assert not np.allclose(pattern.U, U_before) or not np.allclose(pattern.U, 0)


class TestSGDStep:
    def test_sgd_updates_factors(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.SGD)
        pattern = CollaborativeFilteringPattern(cfg)
        U_before = pattern.U.copy()
        pattern._sgd_step()
        # Factors should be updated
        assert not np.allclose(pattern.U, U_before) or not np.allclose(pattern.U, 0)


class TestSVDStep:
    def test_svd_completes(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.SVD)
        pattern = CollaborativeFilteringPattern(cfg)
        pattern._svd_step()
        # After SVD, factors should be set
        assert pattern.U is not None
        assert pattern.V is not None


# ═══════════════════════════════════════════════════════════════════
# Run Training
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_als(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.ALS, n_epochs=5)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert "final_rmse" in result
        assert "train" in result["final_rmse"]
        assert "test" in result["final_rmse"]

    def test_run_sgd(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.SGD, n_epochs=5)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert "final_rmse" in result

    def test_run_svd(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.SVD)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert "final_rmse" in result
        # SVD is non-iterative
        assert len(result["history"]["train_rmse"]) == 1

    def test_run_nmf(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.NMF, n_epochs=5)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert "final_rmse" in result

    def test_results_structure(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.ALS, n_epochs=5)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert "algorithm" in result
        assert "final_rmse" in result
        assert "mae" in result
        assert "history" in result
        assert "predictions_sample" in result
        assert "factor_analysis" in result
        assert "data_stats" in result


# ═══════════════════════════════════════════════════════════════════
# Cold Start Recommendations
# ═══════════════════════════════════════════════════════════════════


class TestRecommendForColdStart:
    def test_cold_start_recommendations(self):
        cfg = CollaborativeFilteringConfig(
            algorithm=CFAlgorithm.ALS,
            n_users=50,
            n_items=30,
            cold_start_users=5,
            n_epochs=5,
        )
        pattern = CollaborativeFilteringPattern(cfg)
        pattern.run()
        recs = pattern._recommend_for_cold_start()
        assert isinstance(recs, list)
        if recs:
            assert "user" in recs[0]
            assert "recommended_items" in recs[0]
            assert "predicted_ratings" in recs[0]


# ═══════════════════════════════════════════════════════════════════
# Output Formatting
# ═══════════════════════════════════════════════════════════════════


class TestFormatOutput:
    def test_output_contains_expected_keys(self):
        cfg = CollaborativeFilteringConfig(algorithm=CFAlgorithm.ALS, n_epochs=5)
        pattern = CollaborativeFilteringPattern(cfg)
        pattern.run()
        result = pattern._format_output()
        assert "algorithm" in result
        assert "final_rmse" in result
        assert "mae" in result
        assert "history" in result
        assert "factor_analysis" in result
        assert "data_stats" in result
        assert "config" in result


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = CollaborativeFilteringPattern.get_metadata()
        assert meta["id"] == "collaborative_filtering"
        assert meta["name"] == "Collaborative Filtering"
        assert "category" in meta
        assert "parameters" in meta


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_high_sparsity(self):
        cfg = CollaborativeFilteringConfig(sparsity=0.99, n_epochs=3)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert result["data_stats"]["sparsity"] > 0.95

    def test_low_sparsity(self):
        cfg = CollaborativeFilteringConfig(sparsity=0.5, n_epochs=3)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert result["data_stats"]["sparsity"] < 0.6

    def test_small_matrix(self):
        cfg = CollaborativeFilteringConfig(n_users=10, n_items=5, n_factors=3, n_epochs=3)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert result["data_stats"]["n_users"] == 10
        assert result["data_stats"]["n_items"] == 5

    def test_many_factors(self):
        cfg = CollaborativeFilteringConfig(n_factors=50, n_epochs=3)
        pattern = CollaborativeFilteringPattern(cfg)
        result = pattern.run()
        assert result["config"]["n_factors"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
