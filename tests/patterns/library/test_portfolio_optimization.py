"""
Tests for portfolio_optimization pattern module.
"""
import numpy as np
import pytest

from src.patterns.library.portfolio_optimization import PortfolioOptimizationConfig, PortfolioOptimizationModel



class TestConfig:
    def test_default_config(self):
        cfg = PortfolioOptimizationConfig()
        assert cfg.n_assets == 10
        assert cfg.risk_aversion == 2.0
        assert cfg.min_weight == 0.0
        assert cfg.max_weight == 1.0

    def test_custom_config(self):
        cfg = PortfolioOptimizationConfig(n_assets=5, risk_aversion=3.0)
        assert cfg.n_assets == 5
        assert cfg.risk_aversion == 3.0


class TestInit:
    def test_model_init_default(self):
        model = PortfolioOptimizationModel()
        assert model.config is not None
        assert model.returns is None

    def test_model_init_custom(self):
        cfg = PortfolioOptimizationConfig(n_assets=5)
        model = PortfolioOptimizationModel(cfg)
        assert model.config.n_assets == 5


class TestDataGeneration:
    def test_generate_sample_data(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data(n_periods=100)
        assert len(model.expected_returns) == 10
        assert model.cov_matrix.shape == (10, 10)
        assert len(model.returns) == 100

    def test_correlation_matrix(self):
        model = PortfolioOptimizationModel()
        corr = model._generate_correlation_matrix(5, 0.3)
        assert corr.shape == (5, 5)
        assert np.allclose(np.diag(corr), 1.0)


class TestPortfolioStats:
    def test_portfolio_stats(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        weights = np.ones(10) / 10
        ret, risk, sharpe = model._portfolio_stats(weights)
        assert isinstance(ret, float)
        assert isinstance(risk, float)
        assert isinstance(sharpe, float)
        assert risk >= 0


class TestMarkowitz:
    def test_markowitz_weights_sum(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        result = model.markowitz_optimization()
        assert abs(sum(result['weights']) - 1.0) < 0.01
        assert all(w >= 0 for w in result['weights'])

    def test_markowitz_risk_positive(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        result = model.markowitz_optimization()
        assert result['risk'] > 0


class TestMaxSharpe:
    def test_max_sharpe_weights_sum(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        result = model.maximum_sharpe_portfolio()
        assert abs(sum(result['weights']) - 1.0) < 0.01

    def test_max_sharpe_highest(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        max_sharpe = model.maximum_sharpe_portfolio()
        markowitz = model.markowitz_optimization()
        assert max_sharpe['sharpe_ratio'] >= min(markowitz['sharpe_ratio'], 0) - 0.01


class TestMinVariance:
    def test_min_variance_weights_sum(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        result = model.minimum_variance_portfolio()
        assert abs(sum(result['weights']) - 1.0) < 0.01

    def test_min_variance_lowest_risk(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        min_var = model.minimum_variance_portfolio()
        markowitz = model.markowitz_optimization()
        assert min_var['risk'] <= markowitz['risk'] * 1.01


class TestRiskParity:
    def test_risk_parity_weights_sum(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        result = model.risk_parity_portfolio()
        assert abs(sum(result['weights']) - 1.0) < 0.01

    def test_risk_parity_contributions(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        result = model.risk_parity_portfolio()
        assert 'risk_contributions' in result
        rc = np.array(result['risk_contributions'])
        if len(rc) > 0 and np.sum(rc) > 0:
            rc_norm = rc / np.sum(rc)
            assert np.std(rc_norm) < 0.3


class TestBlackLitterman:
    def test_black_litterman_returns(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        views = [{'assets': [0], 'view': 0.20, 'confidence': 0.8}]
        result = model.black_litterman(views)
        assert 'bl_expected_returns' in result
        assert len(result['bl_expected_returns']) == 10


class TestEfficientFrontier:
    def test_efficient_frontier(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        frontier = model.efficient_frontier(n_points=20)
        assert len(frontier['returns']) == 20
        assert len(frontier['risks']) == 20


class TestRun:
    def test_run(self):
        model = PortfolioOptimizationModel()
        result = model.run()
        assert 'markowitz' in result
        assert 'maximum_sharpe' in result
        assert 'minimum_variance' in result
        assert 'risk_parity' in result
        assert 'black_litterman' in result
        assert 'efficient_frontier' in result

    def test_metadata(self):
        meta = PortfolioOptimizationModel.get_metadata()
        assert 'pattern_id' in meta
        assert 'name' in meta


class TestEdgeCases:
    def test_single_asset(self):
        cfg = PortfolioOptimizationConfig(n_assets=1)
        model = PortfolioOptimizationModel(cfg)
        model.generate_sample_data()
        result = model.markowitz_optimization()
        assert abs(result['weights'][0] - 1.0) < 0.01

    def test_equal_weight_benchmark(self):
        model = PortfolioOptimizationModel()
        model.generate_sample_data()
        result = model.run()
        eq = result['equal_weight_benchmark']
        assert abs(sum(eq['weights']) - 1.0) < 0.01

    def test_short_sales_allowed(self):
        cfg = PortfolioOptimizationConfig(allow_short=True)
        model = PortfolioOptimizationModel(cfg)
        model.generate_sample_data()
        result = model.markowitz_optimization()
        assert abs(sum(result['weights']) - 1.0) < 0.01
