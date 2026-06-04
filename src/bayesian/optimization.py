"""Bayesian Optimization with Gaussian Process surrogate and acquisition functions."""

from __future__ import annotations

from typing import Callable, Literal

import numpy as np
from numpy.typing import NDArray


class RBFKernel:
    """Radial Basis Function (Gaussian) kernel."""

    def __init__(self, length_scale: float = 1.0, sigma_f: float = 1.0) -> None:
        self.length_scale = length_scale
        self.sigma_f = sigma_f

    def __call__(self, X1: NDArray[np.float64], X2: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute kernel matrix between X1 and X2."""
        sqdist = (
            np.sum(X1**2, axis=1).reshape(-1, 1)
            + np.sum(X2**2, axis=1)
            - 2 * np.dot(X1, X2.T)
        )
        return self.sigma_f**2 * np.exp(-0.5 * sqdist / self.length_scale**2)  # type: ignore[no-any-return]


class GaussianProcess:
    """Gaussian Process regressor with RBF kernel."""

    def __init__(
        self,
        kernel: RBFKernel | None = None,
        noise: float = 1e-5,
    ) -> None:
        self.kernel = kernel or RBFKernel()
        self.noise = noise
        self.X_train: NDArray[np.float64] | None = None
        self.y_train: NDArray[np.float64] | None = None
        self.K_inv: NDArray[np.float64] | None = None

    def fit(self, X: NDArray[np.float64], y: NDArray[np.float64]) -> GaussianProcess:
        """Fit the GP to training data."""
        self.X_train = np.asarray(X, dtype=np.float64)
        self.y_train = np.asarray(y, dtype=np.float64).reshape(-1, 1)
        K = self.kernel(self.X_train, self.X_train)
        K += self.noise * np.eye(len(K))
        self.K_inv = np.linalg.inv(K).astype(np.float64)
        return self

    def predict(
        self, X: NDArray[np.float64], return_std: bool = True
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]] | NDArray[np.float64]:
        """Predict mean and optionally standard deviation at X."""
        if self.X_train is None or self.K_inv is None or self.y_train is None:
            raise ValueError("GP not fitted")
        X = np.asarray(X, dtype=np.float64)
        K_s = self.kernel(self.X_train, X)
        K_ss = self.kernel(X, X)
        mu = K_s.T @ self.K_inv @ self.y_train
        if not return_std:
            return mu.ravel()
        var = np.diag(K_ss) - np.sum(K_s.T @ self.K_inv * K_s.T, axis=1)
        std = np.sqrt(np.maximum(var, 0))
        return mu.ravel(), std


def expected_improvement(
    X: NDArray[np.float64],
    gp: GaussianProcess,
    xi: float = 0.01,
    maximize: bool = True,
) -> NDArray[np.float64]:
    """Expected Improvement acquisition function."""
    mu, sigma = gp.predict(X, return_std=True)
    if gp.y_train is None:
        raise ValueError("GP not fitted")
    y_best = np.max(gp.y_train) if maximize else np.min(gp.y_train)
    sigma = np.maximum(sigma, 1e-9)
    if maximize:
        imp = mu - y_best - xi
    else:
        imp = y_best - mu - xi
    z = imp / sigma
    ei = imp * 0.5 * (1 + np.sign(z))  # approximation using scipy would be exact
    # Manual standard normal CDF/ PDF
    ei = imp * _norm_cdf(z) + sigma * _norm_pdf(z)
    return ei


def upper_confidence_bound(
    X: NDArray[np.float64],
    gp: GaussianProcess,
    kappa: float = 2.576,
    maximize: bool = True,
) -> NDArray[np.float64]:
    """Upper Confidence Bound acquisition function."""
    mu, sigma = gp.predict(X, return_std=True)
    if maximize:
        return mu + kappa * sigma
    return -(mu - kappa * sigma)


def _norm_pdf(x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Standard normal PDF."""
    return np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)  # type: ignore[no-any-return]


def _norm_cdf(x: NDArray[np.float64]) -> NDArray[np.float64]:
    """Standard normal CDF (Abramowitz & Stegun approximation)."""
    return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 / np.pi * x**2)))  # type: ignore[no-any-return]


class BayesianOptimizer:
    """Bayesian Optimization with GP surrogate."""

    def __init__(
        self,
        objective: Callable[[NDArray[np.float64]], float],
        bounds: NDArray[np.float64],
        acquisition: Literal["ei", "ucb"] = "ei",
        n_init: int = 5,
        kernel: RBFKernel | None = None,
        maximize: bool = True,
    ) -> None:
        self.objective = objective
        self.bounds = np.asarray(bounds, dtype=np.float64)
        self.acquisition_name = acquisition
        self.n_init = n_init
        self.gp = GaussianProcess(kernel=kernel)
        self.maximize = maximize
        self.X_obs: list[NDArray[np.float64]] = []
        self.y_obs: list[float] = []

    def _acquisition_fn(
        self, X: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        if self.acquisition_name == "ei":
            return expected_improvement(X, self.gp, maximize=self.maximize)
        return upper_confidence_bound(X, self.gp, maximize=self.maximize)

    def _optimize_acquisition(self, n_samples: int = 1000) -> NDArray[np.float64]:
        """Optimize acquisition via random sampling."""
        dims = self.bounds.shape[0]
        samples = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1], size=(n_samples, dims)
        )
        vals = self._acquisition_fn(samples)
        return samples[np.argmax(vals)]  # type: ignore[no-any-return]

    def optimize(self, n_iter: int = 10) -> tuple[NDArray[np.float64], float]:
        """Run Bayesian Optimization."""
        dims = self.bounds.shape[0]
        # Initial random samples
        for _ in range(self.n_init):
            x = np.random.uniform(self.bounds[:, 0], self.bounds[:, 1], size=dims)
            y = self.objective(x)
            self.X_obs.append(x)
            self.y_obs.append(y)

        for _ in range(n_iter):
            X_arr = np.vstack(self.X_obs)
            y_arr = np.array(self.y_obs, dtype=np.float64)
            self.gp.fit(X_arr, y_arr)
            x_next = self._optimize_acquisition()
            y_next = self.objective(x_next)
            self.X_obs.append(x_next)
            self.y_obs.append(y_next)

        best_idx = int(np.argmax(self.y_obs) if self.maximize else np.argmin(self.y_obs))
        return self.X_obs[best_idx], self.y_obs[best_idx]


class MultiObjectiveBayesianOptimizer:
    """Multi-objective BO via random scalarization."""

    def __init__(
        self,
        objectives: list[Callable[[NDArray[np.float64]], float]],
        bounds: NDArray[np.float64],
        n_init: int = 5,
    ) -> None:
        self.objectives = objectives
        self.bounds = np.asarray(bounds, dtype=np.float64)
        self.n_init = n_init
        self.gps = [GaussianProcess() for _ in objectives]
        self.X_obs: list[NDArray[np.float64]] = []
        self.Y_obs: list[NDArray[np.float64]] = []

    def _scalarize(self, Y: NDArray[np.float64], weights: NDArray[np.float64]) -> NDArray[np.float64]:
        """Weighted Chebyshev scalarization."""
        return np.max(Y * weights, axis=1)  # type: ignore[no-any-return]

    def optimize(self, n_iter: int = 10) -> tuple[list[NDArray[np.float64]], list[NDArray[np.float64]]]:
        """Run multi-objective optimization."""
        dims = self.bounds.shape[0]
        n_obj = len(self.objectives)
        for _ in range(self.n_init):
            x = np.random.uniform(self.bounds[:, 0], self.bounds[:, 1], size=dims)
            y = np.array([f(x) for f in self.objectives], dtype=np.float64)
            self.X_obs.append(x)
            self.Y_obs.append(y)

        for _ in range(n_iter):
            weights = np.random.dirichlet(np.ones(n_obj))
            Y_arr = np.vstack(self.Y_obs)
            s = self._scalarize(Y_arr, weights)
            self.gps[0].fit(np.vstack(self.X_obs), s)
            # Use first GP for acquisition (simplified)
            x_next = BayesianOptimizer._optimize_acquisition(
                type("B", (), {
                    "bounds": self.bounds,
                    "gp": self.gps[0],
                    "acquisition_name": "ei",
                    "maximize": True,
                    "_acquisition_fn": lambda self, X: expected_improvement(X, self.gp),
                })()
            )
            # Inline acquisition optimization
            samples = np.random.uniform(
                self.bounds[:, 0], self.bounds[:, 1], size=(1000, dims)
            )
            vals = expected_improvement(samples, self.gps[0])
            x_next = samples[np.argmax(vals)]
            y_next = np.array([f(x_next) for f in self.objectives], dtype=np.float64)
            self.X_obs.append(x_next)
            self.Y_obs.append(y_next)

        return self.X_obs, self.Y_obs
