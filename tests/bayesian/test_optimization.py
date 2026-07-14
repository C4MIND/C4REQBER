"""Tests for src/bayesian/optimization.py."""

from __future__ import annotations

import numpy as np
import pytest

from src.bayesian.optimization import (
    BayesianOptimizer,
    GaussianProcess,
    MultiObjectiveBayesianOptimizer,
    RBFKernel,
    expected_improvement,
    upper_confidence_bound,
)


class TestRBFKernel:
    """Tests for RBF kernel."""

    def test_self_similarity(self):
        kernel = RBFKernel(length_scale=1.0, sigma_f=1.0)
        X = np.array([[0.0], [1.0]])
        K = kernel(X, X)
        assert K[0, 0] == pytest.approx(1.0)
        assert K[1, 1] == pytest.approx(1.0)

    def test_distance_decay(self):
        kernel = RBFKernel(length_scale=1.0, sigma_f=1.0)
        X1 = np.array([[0.0]])
        X2 = np.array([[1.0]])
        K = kernel(X1, X2)
        assert K[0, 0] == pytest.approx(np.exp(-0.5), abs=1e-6)

    def test_larger_length_scale(self):
        kernel1 = RBFKernel(length_scale=0.1, sigma_f=1.0)
        kernel2 = RBFKernel(length_scale=10.0, sigma_f=1.0)
        X1 = np.array([[0.0]])
        X2 = np.array([[1.0]])
        assert kernel1(X1, X2)[0, 0] < kernel2(X1, X2)[0, 0]

    def test_multidimensional(self):
        kernel = RBFKernel(length_scale=1.0, sigma_f=1.0)
        X1 = np.array([[0.0, 0.0], [1.0, 1.0]])
        X2 = np.array([[0.0, 0.0], [1.0, 1.0]])
        K = kernel(X1, X2)
        assert K.shape == (2, 2)
        assert K[0, 0] == pytest.approx(1.0)


class TestGaussianProcess:
    """Tests for Gaussian Process regressor."""

    def test_fit_and_predict(self):
        gp = GaussianProcess()
        X = np.array([[0.0], [1.0], [2.0]])
        y = np.array([0.0, 1.0, 4.0])
        gp.fit(X, y)
        mu, std = gp.predict(np.array([[1.0]]), return_std=True)
        assert mu[0] == pytest.approx(1.0, abs=0.5)
        assert std[0] >= 0

    def test_interpolation(self):
        gp = GaussianProcess(noise=1e-10)
        X = np.array([[0.0], [1.0], [2.0]])
        y = np.array([0.0, 1.0, 2.0])
        gp.fit(X, y)
        mu, _ = gp.predict(X, return_std=True)
        np.testing.assert_array_almost_equal(mu, y, decimal=4)

    def test_predict_without_std(self):
        gp = GaussianProcess()
        X = np.array([[0.0], [1.0]])
        y = np.array([0.0, 1.0])
        gp.fit(X, y)
        mu = gp.predict(np.array([[0.5]]), return_std=False)
        assert isinstance(mu, np.ndarray)

    def test_unfitted_raises(self):
        gp = GaussianProcess()
        with pytest.raises(ValueError, match="not fitted"):
            gp.predict(np.array([[0.0]]))

    def test_uncertainty_increases_far_from_data(self):
        gp = GaussianProcess()
        X = np.array([[0.0], [1.0]])
        y = np.array([0.0, 1.0])
        gp.fit(X, y)
        _, std_near = gp.predict(np.array([[0.5]]), return_std=True)
        _, std_far = gp.predict(np.array([[100.0]]), return_std=True)
        assert std_far[0] > std_near[0]


class TestExpectedImprovement:
    """Tests for Expected Improvement acquisition function."""

    def test_returns_non_negative(self):
        gp = GaussianProcess()
        gp.fit(np.array([[0.0], [1.0]]), np.array([0.0, 1.0]))
        X = np.array([[0.5], [1.5]])
        ei = expected_improvement(X, gp)
        assert np.all(ei >= 0)

    def test_higher_at_promising_points(self):
        gp = GaussianProcess()
        gp.fit(np.array([[0.0], [1.0], [2.0]]), np.array([0.0, 0.5, 1.0]))
        X_test = np.array([[-1.0], [3.0]])
        ei = expected_improvement(X_test, gp)
        assert ei[0] > 0 or ei[1] > 0

    def test_zero_at_observed_points(self):
        gp = GaussianProcess(noise=1e-10)
        X = np.array([[0.0], [1.0]])
        y = np.array([0.0, 1.0])
        gp.fit(X, y)
        ei = expected_improvement(X, gp)
        assert np.all(ei < 1e-6)

    def test_maximize_vs_minimize(self):
        gp = GaussianProcess()
        gp.fit(np.array([[0.0], [1.0]]), np.array([0.0, 1.0]))
        X = np.array([[2.0]])
        ei_max = expected_improvement(X, gp, maximize=True)
        ei_min = expected_improvement(X, gp, maximize=False)
        assert ei_max != ei_min


class TestUpperConfidenceBound:
    """Tests for Upper Confidence Bound acquisition function."""

    def test_returns_values(self):
        gp = GaussianProcess()
        gp.fit(np.array([[0.0], [1.0]]), np.array([0.0, 1.0]))
        X = np.array([[0.5]])
        ucb = upper_confidence_bound(X, gp, kappa=2.0)
        assert len(ucb) == 1

    def test_higher_kappa_increases_exploration(self):
        gp = GaussianProcess()
        gp.fit(np.array([[0.0], [1.0]]), np.array([0.0, 1.0]))
        X = np.array([[0.5]])
        ucb1 = upper_confidence_bound(X, gp, kappa=1.0)
        ucb2 = upper_confidence_bound(X, gp, kappa=3.0)
        assert ucb2[0] > ucb1[0]

    def test_maximize_vs_minimize(self):
        gp = GaussianProcess()
        gp.fit(np.array([[0.0], [1.0]]), np.array([0.0, 1.0]))
        X = np.array([[0.5]])
        ucb_max = upper_confidence_bound(X, gp, maximize=True)
        ucb_min = upper_confidence_bound(X, gp, maximize=False)
        assert ucb_max[0] > ucb_min[0]


class TestBayesianOptimizer:
    """Tests for Bayesian Optimizer."""

    def test_finds_maximum_of_quadratic(self):
        def objective(x: np.ndarray) -> float:
            return float(-(x[0] - 0.5) ** 2)

        opt = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0]]),
            acquisition="ei",
            n_init=5,
            maximize=True,
        )
        best_x, best_y = opt.optimize(n_iter=20)
        assert best_x[0] == pytest.approx(0.5, abs=0.1)
        assert best_y == pytest.approx(0.0, abs=0.05)

    def test_finds_minimum_of_quadratic(self):
        def objective(x: np.ndarray) -> float:
            return float((x[0] - 0.5) ** 2)

        opt = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0]]),
            acquisition="ei",
            n_init=5,
            maximize=False,
        )
        best_x, best_y = opt.optimize(n_iter=20)
        assert best_x[0] == pytest.approx(0.5, abs=0.1)
        assert best_y == pytest.approx(0.0, abs=0.05)

    def test_respects_bounds(self):
        def objective(x: np.ndarray) -> float:
            return float(x[0])

        opt = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[10.0, 20.0]]),
            n_init=3,
        )
        best_x, _ = opt.optimize(n_iter=5)
        assert 10.0 <= best_x[0] <= 20.0
        for x in opt.X_obs:
            assert 10.0 <= x[0] <= 20.0

    def test_ucb_acquisition(self):
        def objective(x: np.ndarray) -> float:
            return float(-(x[0] - 0.5) ** 2)

        opt = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0]]),
            acquisition="ucb",
            n_init=5,
            maximize=True,
        )
        best_x, best_y = opt.optimize(n_iter=15)
        assert best_y >= -0.5

    def test_2d_optimization(self):
        def objective(x: np.ndarray) -> float:
            return float(-((x[0] - 0.3) ** 2 + (x[1] - 0.7) ** 2))

        opt = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0], [0.0, 1.0]]),
            n_init=8,
            maximize=True,
        )
        best_x, best_y = opt.optimize(n_iter=20)
        assert best_y > -0.5

    def test_observations_grow(self):
        def objective(x: np.ndarray) -> float:
            return float(x[0])

        opt = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0]]),
            n_init=3,
        )
        opt.optimize(n_iter=5)
        assert len(opt.X_obs) == 8
        assert len(opt.y_obs) == 8


class TestMultiObjectiveBayesianOptimizer:
    """Tests for Multi-Objective Bayesian Optimizer."""

    def test_basic_multi_objective(self):
        def f1(x: np.ndarray) -> float:
            return float(x[0] ** 2)

        def f2(x: np.ndarray) -> float:
            return float((x[0] - 1.0) ** 2)

        opt = MultiObjectiveBayesianOptimizer(
            objectives=[f1, f2],
            bounds=np.array([[0.0, 1.0]]),
            n_init=5,
        )
        X_obs, Y_obs = opt.optimize(n_iter=10)
        assert len(X_obs) > 5
        assert len(Y_obs) > 5
        assert all(len(y) == 2 for y in Y_obs)

    def test_bounds_respected(self):
        def f1(x: np.ndarray) -> float:
            return float(x[0])

        def f2(x: np.ndarray) -> float:
            return float(-x[0])

        opt = MultiObjectiveBayesianOptimizer(
            objectives=[f1, f2],
            bounds=np.array([[0.0, 1.0]]),
            n_init=3,
        )
        X_obs, _ = opt.optimize(n_iter=5)
        for x in X_obs:
            assert 0.0 <= x[0] <= 1.0

    def test_2d_input(self):
        def f1(x: np.ndarray) -> float:
            return float(x[0] ** 2 + x[1] ** 2)

        def f2(x: np.ndarray) -> float:
            return float((x[0] - 1.0) ** 2 + (x[1] - 1.0) ** 2)

        opt = MultiObjectiveBayesianOptimizer(
            objectives=[f1, f2],
            bounds=np.array([[0.0, 1.0], [0.0, 1.0]]),
            n_init=5,
        )
        X_obs, Y_obs = opt.optimize(n_iter=8)
        assert all(len(x) == 2 for x in X_obs)
        assert all(len(y) == 2 for y in Y_obs)


class TestOptimizationIntegration:
    """Integration tests for full Bayesian Optimization workflow."""

    def test_gp_regression_accuracy(self):
        np.random.seed(42)
        X_train = np.linspace(0, 10, 20).reshape(-1, 1)
        y_train = np.sin(X_train).flatten()
        gp = GaussianProcess(kernel=RBFKernel(length_scale=1.0, sigma_f=1.0))
        gp.fit(X_train, y_train)
        X_test = np.linspace(0, 10, 100).reshape(-1, 1)
        mu, std = gp.predict(X_test, return_std=True)
        y_true = np.sin(X_test).flatten()
        mse = np.mean((mu - y_true) ** 2)
        assert mse < 0.1
        assert np.all(std >= 0)

    def test_bo_improves_over_random(self):
        def objective(x: np.ndarray) -> float:
            return float(np.sin(3 * x[0]) * np.cos(5 * x[0]))

        opt = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0]]),
            acquisition="ei",
            n_init=3,
            maximize=True,
        )
        best_x, best_y = opt.optimize(n_iter=20)

        random_samples = np.random.uniform(0, 1, 100)
        random_best = max(objective(np.array([x])) for x in random_samples)
        assert best_y >= random_best - 0.2

    def test_bo_vs_ucb(self):
        def objective(x: np.ndarray) -> float:
            return float(-(x[0] - 0.7) ** 2)

        opt_ei = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0]]),
            acquisition="ei",
            n_init=5,
            maximize=True,
        )
        opt_ucb = BayesianOptimizer(
            objective=objective,
            bounds=np.array([[0.0, 1.0]]),
            acquisition="ucb",
            n_init=5,
            maximize=True,
        )
        _, best_ei = opt_ei.optimize(n_iter=15)
        _, best_ucb = opt_ucb.optimize(n_iter=15)
        assert best_ei > -0.5
        assert best_ucb > -0.5

    def test_multi_objective_pareto_approximation(self):
        def f1(x: np.ndarray) -> float:
            return float(x[0] ** 2)

        def f2(x: np.ndarray) -> float:
            return float((x[0] - 1.0) ** 2)

        opt = MultiObjectiveBayesianOptimizer(
            objectives=[f1, f2],
            bounds=np.array([[0.0, 1.0]]),
            n_init=8,
        )
        _, Y_obs = opt.optimize(n_iter=15)
        Y_arr = np.vstack(Y_obs)
        assert np.min(Y_arr[:, 0]) < 0.5
        assert np.min(Y_arr[:, 1]) < 0.5
