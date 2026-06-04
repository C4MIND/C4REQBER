"""
C4REQBER v6.0 - Adaptive Filter Pattern
Signal processing using LMS (Least Mean Squares) and RLS (Recursive Least Squares) algorithms.

Pattern Structure (Christopher Alexander):
- Context: Noise cancellation, system identification, channel equalization
- Forces: Convergence speed vs. stability, tracking vs. steady-state error
- Solution: Adaptive algorithms with configurable learning rates
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class AdaptiveAlgorithm(Enum):
    """Available adaptive filtering algorithms"""

    LMS = "lms"  # Least Mean Squares
    NLMS = "nlms"  # Normalized LMS
    RLS = "rls"  # Recursive Least Squares
    RLS_FORGETTING = "rls_forgetting"  # RLS with forgetting factor


@dataclass
class AdaptiveFilterConfig:
    """Configuration for adaptive filter"""

    # Filter parameters
    filter_order: int = 32  # Number of filter taps
    algorithm: AdaptiveAlgorithm = AdaptiveAlgorithm.LMS

    # LMS parameters
    mu: float = 0.01  # Step size (learning rate)
    mu_min: float = 0.001  # Minimum step size for variable mu
    mu_max: float = 0.1  # Maximum step size for variable mu

    # RLS parameters
    delta: float = 1.0  # Initialization parameter (P(0) = delta * I)
    lambda_factor: float = 0.99  # Forgetting factor (0.95 - 1.0)

    # Simulation parameters
    n_samples: int = 10000  # Number of input samples
    snr_db: float = 20.0  # Signal-to-noise ratio in dB

    # System identification mode
    sys_id_mode: bool = True  # If True, identify unknown system
    unknown_system: np.ndarray | None = None  # Unknown system coefficients

    # Output
    output_interval: int = 100


class AdaptiveFilterPattern:
    """
    Adaptive filter implementation with LMS and RLS algorithms.

    Supports:
    - System identification
    - Noise cancellation
    - Channel equalization
    """

    PATTERN_ID = "adaptive_filter"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: AdaptiveFilterConfig | None = None) -> None:
        self.config = config or AdaptiveFilterConfig()
        self.weights: np.ndarray | None = None
        self.error_history: list[float] = []
        self.weight_history: list[np.ndarray] = []
        self.mse_history: list[float] = []

        # RLS-specific variables
        self.P: np.ndarray | None = None  # Inverse correlation matrix

        self._initialize_filter()

    def _initialize_filter(self) -> None:
        """Initialize filter weights and RLS variables"""
        cfg = self.config

        # Initialize filter weights to zero
        self.weights = np.zeros(cfg.filter_order)

        # Initialize unknown system if in system identification mode
        if cfg.sys_id_mode and cfg.unknown_system is None:
            # Create a random unknown system (low-pass characteristic)
            self.unknown_system = np.exp(-np.linspace(0, 3, cfg.filter_order))
            self.unknown_system /= np.linalg.norm(self.unknown_system)
        elif cfg.sys_id_mode:
            self.unknown_system = cfg.unknown_system
        else:
            self.unknown_system = None

        # Initialize RLS inverse correlation matrix
        if cfg.algorithm in [AdaptiveAlgorithm.RLS, AdaptiveAlgorithm.RLS_FORGETTING]:
            self.P = np.eye(cfg.filter_order) / cfg.delta

    def _generate_input_signal(self) -> np.ndarray:
        """Generate colored input signal (AR process)"""
        cfg = self.config

        # Generate white noise
        white_noise = np.random.randn(cfg.n_samples + cfg.filter_order)

        # Create colored noise using simple AR(1) filter
        x = np.zeros_like(white_noise)
        x[0] = white_noise[0]
        for i in range(1, len(white_noise)):
            x[i] = 0.8 * x[i - 1] + white_noise[i]

        return x

    def _generate_desired_signal(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Generate desired signal by filtering input through unknown system"""
        cfg = self.config

        if cfg.sys_id_mode and self.unknown_system is not None:
            # Convolve input with unknown system
            d_clean = np.convolve(x, self.unknown_system, mode="same")
        else:
            # Generate a simple reference signal
            d_clean = np.sin(2 * np.pi * 0.05 * np.arange(len(x)))

        # Add noise based on SNR
        signal_power = np.mean(d_clean**2)
        noise_power = signal_power / (10 ** (cfg.snr_db / 10))
        noise = np.sqrt(noise_power) * np.random.randn(len(d_clean))

        return d_clean + noise, d_clean

    def _lms_update(self, x_vec: np.ndarray, e: float) -> np.ndarray:
        """Standard LMS weight update"""
        return self.config.mu * e * x_vec

    def _nlms_update(self, x_vec: np.ndarray, e: float) -> np.ndarray:
        """Normalized LMS weight update"""
        norm_x = (
            np.dot(x_vec, x_vec) + 1e-10
        )  # Small constant to avoid division by zero
        return (self.config.mu / norm_x) * e * x_vec  # type: ignore[no-any-return]

    def _rls_update(self, x_vec: np.ndarray, e: float) -> np.ndarray:
        """RLS weight update with forgetting factor"""
        cfg = self.config

        # Gain vector
        Px = self.P @ x_vec
        if cfg.algorithm == AdaptiveAlgorithm.RLS_FORGETTING:
            denom = cfg.lambda_factor + x_vec @ Px
        else:
            denom = 1.0 + x_vec @ Px
        k = Px / denom

        # Weight update
        weight_update = e * k

        # Update inverse correlation matrix
        if cfg.algorithm == AdaptiveAlgorithm.RLS_FORGETTING:
            self.P = (self.P - np.outer(k, Px)) / cfg.lambda_factor
        else:
            self.P = self.P - np.outer(k, Px)

        return weight_update  # type: ignore[no-any-return]

    def _update_weights(self, x_vec: np.ndarray, e: float) -> np.ndarray:
        """Update filter weights based on selected algorithm"""
        cfg = self.config

        if cfg.algorithm == AdaptiveAlgorithm.LMS:
            return self._lms_update(x_vec, e)
        elif cfg.algorithm == AdaptiveAlgorithm.NLMS:
            return self._nlms_update(x_vec, e)
        elif cfg.algorithm in [AdaptiveAlgorithm.RLS, AdaptiveAlgorithm.RLS_FORGETTING]:
            return self._rls_update(x_vec, e)
        else:
            return np.zeros_like(self.weights)

    def _compute_learning_curve(self, window_size: int = 100) -> list[float]:
        """Compute smoothed learning curve (MSE over time)"""
        if len(self.error_history) < window_size:
            return [np.mean(np.array(self.error_history) ** 2)]

        mse = []
        for i in range(window_size, len(self.error_history)):
            window = self.error_history[i - window_size : i]
            mse.append(np.mean(np.array(window) ** 2))
        return mse

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run adaptive filter simulation"""
        cfg = self.config

        logger.info(
            f"Starting adaptive filter: {cfg.algorithm.value}, order={cfg.filter_order}"
        )

        # Generate signals
        x = self._generate_input_signal()
        d, d_clean = self._generate_desired_signal(x)

        # Adaptive filtering loop
        y_output = np.zeros(cfg.n_samples)

        for n in range(cfg.filter_order, cfg.filter_order + cfg.n_samples):
            # Extract input vector
            x_vec = x[n - cfg.filter_order : n][::-1]  # Reverse for causal filtering

            # Filter output
            y = np.dot(self.weights, x_vec)  # type: ignore[arg-type]
            y_output[n - cfg.filter_order] = y

            # Error signal
            e = d[n] - y
            self.error_history.append(e)

            # Weight update
            weight_update = self._update_weights(x_vec, e)
            self.weights += weight_update

            # Store weight history periodically
            if n % cfg.output_interval == 0:
                self.weight_history.append(self.weights.copy())

            # Compute running MSE
            if len(self.error_history) % 100 == 0:
                mse = np.mean(np.array(self.error_history[-100:]) ** 2)
                self.mse_history.append(mse)

        return self._format_output(x, d, d_clean, y_output)

    def _format_output(
        self, x: np.ndarray, d: np.ndarray, d_clean: np.ndarray, y: np.ndarray
    ) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Calculate final MSE and performance metrics
        final_errors = np.array(self.error_history[-1000:])
        final_mse = np.mean(final_errors**2)

        # Calculate misadjustment (excess MSE / minimum MSE)
        noise_power = np.mean((d - d_clean) ** 2)
        misadjustment = (
            (final_mse - noise_power) / noise_power if noise_power > 0 else 0
        )

        # System identification: compare estimated weights with unknown system
        weight_error = None
        if cfg.sys_id_mode and self.unknown_system is not None:
            weight_error = np.linalg.norm(self.weights - self.unknown_system)
            weight_error_normalized = weight_error / np.linalg.norm(self.unknown_system)
        else:
            weight_error_normalized = None

        # Compute convergence time (samples to reach within 10% of final MSE)
        convergence_sample = None
        target_mse = final_mse * 1.1
        for i, mse in enumerate(self.mse_history):
            if mse <= target_mse:
                convergence_sample = i * 100  # Account for sampling interval
                break

        return {
            "algorithm": cfg.algorithm.value,
            "filter_order": cfg.filter_order,
            "final_weights": self.weights.tolist(),  # type: ignore[union-attr]
            "final_mse": float(final_mse),
            "noise_power": float(noise_power),
            "misadjustment": float(misadjustment),
            "weight_error": float(weight_error) if weight_error is not None else None,
            "weight_error_normalized": float(weight_error_normalized)
            if weight_error_normalized is not None
            else None,
            "convergence_samples": convergence_sample,
            "error_history": self.error_history[::10],  # Subsample for output
            "mse_history": self.mse_history,
            "learning_curve": self._compute_learning_curve(),
            "mean_output": float(np.mean(y)),
            "output_variance": float(np.var(y)),
            "unknown_system": self.unknown_system.tolist()
            if self.unknown_system is not None
            else None,
            "config": {
                "mu": cfg.mu,
                "lambda_factor": cfg.lambda_factor
                if cfg.algorithm
                in [AdaptiveAlgorithm.RLS, AdaptiveAlgorithm.RLS_FORGETTING]
                else None,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Adaptive Filter",
            "category": "EXTENDED",
            "domain": ["Signal Processing", "Communications", "Control Systems"],
            "description": "Adaptive filtering using LMS and RLS algorithms",
            "computational_complexity": "O(N) per sample for LMS, O(N²) for RLS",
            "typical_runtime": "seconds",
            "accuracy": "High (converges to Wiener solution)",
            "assumptions": [
                "Stationary or slowly varying system",
                "Sufficient excitation (persistent input)",
                "Step size within stability bounds for LMS",
            ],
            "parameters": [
                {
                    "name": "filter_order",
                    "type": "int",
                    "default": 32,
                    "description": "Number of filter taps",
                },
                {
                    "name": "algorithm",
                    "type": "enum",
                    "options": ["lms", "nlms", "rls", "rls_forgetting"],
                    "default": "lms",
                },
                {
                    "name": "mu",
                    "type": "float",
                    "default": 0.01,
                    "description": "LMS step size",
                },
                {
                    "name": "lambda_factor",
                    "type": "float",
                    "default": 0.99,
                    "description": "RLS forgetting factor",
                },
                {
                    "name": "n_samples",
                    "type": "int",
                    "default": 10000,
                    "description": "Number of input samples",
                },
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================


def test_lms_convergence() -> None:
    """Test that LMS algorithm converges"""
    config = AdaptiveFilterConfig(
        algorithm=AdaptiveAlgorithm.LMS,
        filter_order=16,
        n_samples=5000,
        mu=0.01,
        snr_db=30,
    )

    filter_obj = AdaptiveFilterPattern(config)
    result = filter_obj.run()

    # Check convergence
    assert result["final_mse"] < 0.1, f"LMS did not converge: MSE={result['final_mse']}"
    assert result["weight_error_normalized"] < 0.5, "Weight error too high"
    print("✓ LMS convergence test passed")


def test_rls_faster_convergence() -> None:
    """Test that RLS converges faster than LMS"""
    np.random.seed(42)

    # LMS run
    config_lms = AdaptiveFilterConfig(
        algorithm=AdaptiveAlgorithm.LMS, filter_order=16, n_samples=3000, mu=0.01
    )
    filter_lms = AdaptiveFilterPattern(config_lms)
    result_lms = filter_lms.run()

    # RLS run
    np.random.seed(42)
    config_rls = AdaptiveFilterConfig(
        algorithm=AdaptiveAlgorithm.RLS, filter_order=16, n_samples=3000
    )
    filter_rls = AdaptiveFilterPattern(config_rls)
    result_rls = filter_rls.run()

    # RLS should have lower final weight error
    assert (
        result_rls["weight_error_normalized"] < result_lms["weight_error_normalized"]
    ), "RLS should achieve lower weight error than LMS"
    print("✓ RLS faster convergence test passed")


def test_nlms_stability() -> None:
    """Test NLMS stability with high input power"""
    config = AdaptiveFilterConfig(
        algorithm=AdaptiveAlgorithm.NLMS,
        filter_order=16,
        n_samples=2000,
        mu=1.0,  # High step size that would make LMS unstable
        snr_db=10,
    )

    filter_obj = AdaptiveFilterPattern(config)
    result = filter_obj.run()

    # NLMS should remain stable
    assert np.isfinite(result["final_mse"]), "NLMS became unstable"
    assert result["final_mse"] < 1.0, f"NLMS MSE too high: {result['final_mse']}"
    print("✓ NLMS stability test passed")


def test_system_identification() -> None:
    """Test system identification mode"""
    # Define a known system
    unknown_system = np.array([0.5, -0.3, 0.2, -0.1, 0.05])

    config = AdaptiveFilterConfig(
        algorithm=AdaptiveAlgorithm.RLS,
        filter_order=5,
        n_samples=3000,
        unknown_system=unknown_system,
        sys_id_mode=True,
        snr_db=40,
    )

    filter_obj = AdaptiveFilterPattern(config)
    result = filter_obj.run()

    # Should identify the system accurately
    assert result["weight_error_normalized"] < 0.1, (
        f"System identification failed: error={result['weight_error_normalized']}"
    )
    print("✓ System identification test passed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run tests
    test_lms_convergence()
    test_rls_faster_convergence()
    test_nlms_stability()
    test_system_identification()

    # Demo run
    print("\n--- Demo Run ---")
    config = AdaptiveFilterConfig(
        algorithm=AdaptiveAlgorithm.LMS, filter_order=16, n_samples=5000, mu=0.01
    )

    filter_obj = AdaptiveFilterPattern(config)
    result = filter_obj.run()

    print(f"Algorithm: {result['algorithm']}")
    print(f"Final MSE: {result['final_mse']:.6f}")
    print(f"Weight Error: {result['weight_error_normalized']:.4f}")
    print(f"Convergence: {result['convergence_samples']} samples")
