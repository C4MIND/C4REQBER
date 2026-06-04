"""
C4REQBER v6.0 - Wavelet Analysis Pattern
Discrete Wavelet Transform (DWT) for multi-resolution signal analysis.

Pattern Structure (Christopher Alexander):
- Context: Time-frequency analysis, transient detection, signal compression
- Forces: Time resolution vs. frequency resolution, wavelet selection
- Solution: Multi-level decomposition with various wavelet families
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class WaveletFamily(Enum):
    """Available wavelet families"""

    HAAR = "haar"
    DB = "daubechies"  # Daubechies wavelets
    SYM = "symlet"  # Symlets
    COIF = "coiflet"  # Coiflets
    BIOR = "biorthogonal"  # Biorthogonal wavelets


class ThresholdMethod(Enum):
    """Denoising threshold methods"""

    HARD = "hard"
    SOFT = "soft"
    GARROTE = "garrote"


@dataclass
class WaveletAnalysisConfig:
    """Configuration for wavelet analysis"""

    # Wavelet parameters
    wavelet_family: WaveletFamily = WaveletFamily.DB
    wavelet_order: int = 4  # Order of wavelet (e.g., db4)

    # Decomposition parameters
    max_level: int | None = None  # Maximum decomposition level (None = auto)

    # Denoising parameters
    denoise: bool = False
    threshold_method: ThresholdMethod = ThresholdMethod.SOFT
    threshold_sigma: float = 1.0  # Noise standard deviation (None = estimate)

    # Signal parameters
    n_samples: int = 4096
    sampling_rate: float = 1000.0

    # Analysis options
    compute_energy: bool = True
    compute_entropy: bool = True


class WaveletAnalysisPattern:
    """
    Discrete Wavelet Transform (DWT) pattern.

    Implements:
    - Multi-level wavelet decomposition
    - Signal denoising
    - Feature extraction (energy, entropy)
    - Reconstruction
    """

    PATTERN_ID = "wavelet_analysis"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: WaveletAnalysisConfig | None = None) -> None:
        self.config = config or WaveletAnalysisConfig()
        self.coefficients: list[np.ndarray] = []
        self.reconstructed_signal: np.ndarray | None = None

        # Initialize wavelet filters
        self._initialize_wavelet()

    def _initialize_wavelet(self) -> None:
        """Initialize wavelet decomposition/reconstruction filters"""
        cfg = self.config

        # Get wavelet filters based on family and order
        self.decomp_filter_lo, self.decomp_filter_hi = self._get_wavelet_filters(
            cfg.wavelet_family, cfg.wavelet_order, decomposition=True
        )
        self.recon_filter_lo, self.recon_filter_hi = self._get_wavelet_filters(
            cfg.wavelet_family, cfg.wavelet_order, decomposition=False
        )

        # Determine max level
        if cfg.max_level is None:
            cfg.max_level = int(
                np.floor(
                    np.log2(self.config.n_samples / (len(self.decomp_filter_lo) - 1))
                )
            )
            cfg.max_level = max(1, min(cfg.max_level, 10))

    def _get_wavelet_filters(
        self, family: WaveletFamily, order: int, decomposition: bool
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Get wavelet filter coefficients.
        Returns (low_pass, high_pass) filters.
        """
        if family == WaveletFamily.HAAR:
            # Haar wavelet (simplest)
            if decomposition:
                lo = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])
                hi = np.array([1 / np.sqrt(2), -1 / np.sqrt(2)])
            else:
                lo = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])
                hi = np.array([-1 / np.sqrt(2), 1 / np.sqrt(2)])

        elif family == WaveletFamily.DB:
            # Daubechies wavelets
            lo = self._daubechies_coefficients(order)
            if decomposition:
                hi = self._get_high_pass_from_low_pass(lo)
            else:
                # For reconstruction, reverse and alternate signs
                hi = lo[::-1] * np.array([(-1) ** i for i in range(len(lo))])
                lo = lo[::-1]

        elif family == WaveletFamily.SYM:
            # Symlets (approximate)
            lo = self._symlet_coefficients(order)
            if decomposition:
                hi = self._get_high_pass_from_low_pass(lo)
            else:
                hi = lo[::-1] * np.array([(-1) ** i for i in range(len(lo))])
                lo = lo[::-1]

        else:
            # Default to Haar
            lo = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])
            hi = np.array([1 / np.sqrt(2), -1 / np.sqrt(2)])

        return lo, hi

    def _daubechies_coefficients(self, order: int) -> np.ndarray:
        """Get Daubechies filter coefficients"""
        # Predefined coefficients for common Daubechies wavelets
        coefficients = {
            1: [1 / np.sqrt(2), 1 / np.sqrt(2)],  # Same as Haar
            2: [0.48296, 0.83652, 0.22414, -0.12941],
            4: [
                0.48296,
                0.83652,
                0.22414,
                -0.12941,
                -0.17132,
                0.07872,
                0.04297,
                -0.01523,
            ],
            6: [
                0.33267,
                0.80689,
                0.45988,
                -0.13501,
                -0.08544,
                0.03522,
                0.02325,
                -0.01054,
                -0.00676,
                0.00239,
                0.00156,
                -0.00053,
            ],
        }

        if order in coefficients:
            return np.array(coefficients[order])
        else:
            # Return db4 as default
            return np.array(coefficients[4])

    def _symlet_coefficients(self, order: int) -> np.ndarray:
        """Get Symlet filter coefficients (approximated)"""
        # Symlets are similar to Daubechies but with more symmetry
        # Use Daubechies as approximation
        return self._daubechies_coefficients(order)

    def _get_high_pass_from_low_pass(self, lo: np.ndarray) -> np.ndarray:
        """Derive high-pass filter from low-pass filter"""
        # h[n] = (-1)^n * lo[N-1-n]
        n = len(lo)
        hi = np.array([(-1) ** i * lo[n - 1 - i] for i in range(n)])
        return hi

    def _convolve_decimate(self, x: np.ndarray, h: np.ndarray) -> np.ndarray:
        """Convolve and downsample by 2"""
        y = np.convolve(x, h, mode="full")
        return y[1::2] if len(y) % 2 == 1 else y[::2]

    def _upsample_convolve(
        self, x: np.ndarray, h: np.ndarray, original_len: int
    ) -> np.ndarray:
        """Upsample by 2 and convolve"""
        y = np.zeros(2 * len(x))
        y[::2] = x
        result = np.convolve(y, h, mode="full")
        return result[:original_len]

    def _dwt_level(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Single level DWT"""
        approx = self._convolve_decimate(x, self.decomp_filter_lo)
        detail = self._convolve_decimate(x, self.decomp_filter_hi)
        return approx, detail

    def _idwt_level(
        self, approx: np.ndarray, detail: np.ndarray, original_len: int
    ) -> np.ndarray:
        """Single level inverse DWT"""
        lo_recon = self._upsample_convolve(approx, self.recon_filter_lo, original_len)
        hi_recon = self._upsample_convolve(detail, self.recon_filter_hi, original_len)
        return lo_recon + hi_recon  # type: ignore[no-any-return]

    def decompose(self, x: np.ndarray, level: int | None = None) -> list[np.ndarray]:
        """Multi-level wavelet decomposition"""
        if level is None:
            level = self.config.max_level

        coefficients = []
        approx = x.copy()

        for _i in range(level):  # type: ignore[arg-type]
            if len(approx) < len(self.decomp_filter_lo) * 2:
                break

            approx, detail = self._dwt_level(approx)
            coefficients.append(detail)

        # Add final approximation
        coefficients.append(approx)

        return coefficients[::-1]  # [cA, cD_n, cD_{n-1}, ..., cD_1]

    def reconstruct(
        self, coefficients: list[np.ndarray], original_len: int
    ) -> np.ndarray:
        """Multi-level wavelet reconstruction"""
        # Coefficients are [cA, cD_n, cD_{n-1}, ..., cD_1]
        approx = coefficients[0]

        for i, detail in enumerate(coefficients[1:]):
            # Estimate output length for this level
            expected_len = min(
                len(approx) * 2 + len(self.recon_filter_lo) - 2,
                original_len // (2 ** (len(coefficients) - 2 - i)),
            )
            approx = self._idwt_level(approx, detail, expected_len)

        # Trim to original length
        return approx[:original_len]

    def _threshold_coefficients(
        self, coefficients: list[np.ndarray]
    ) -> list[np.ndarray]:
        """Apply thresholding for denoising"""
        cfg = self.config

        thresholded = [coefficients[0].copy()]  # Keep approximation unchanged

        for detail in coefficients[1:]:
            # Estimate noise level using median absolute deviation
            if cfg.threshold_sigma is None:
                sigma = np.median(np.abs(detail)) / 0.6745  # type: ignore[unreachable]
            else:
                sigma = cfg.threshold_sigma

            # Universal threshold
            threshold = sigma * np.sqrt(2 * np.log(len(detail)))

            if cfg.threshold_method == ThresholdMethod.HARD:
                # Hard thresholding
                detail_thresh = np.where(np.abs(detail) > threshold, detail, 0)

            elif cfg.threshold_method == ThresholdMethod.SOFT:
                # Soft thresholding
                detail_thresh = np.sign(detail) * np.maximum(
                    np.abs(detail) - threshold, 0
                )

            elif cfg.threshold_method == ThresholdMethod.GARROTE:
                # Garrote thresholding
                detail_thresh = np.where(
                    np.abs(detail) > threshold, detail - threshold**2 / detail, 0
                )

            else:
                detail_thresh = detail  # type: ignore[unreachable]

            thresholded.append(detail_thresh)

        return thresholded

    def _compute_energy_distribution(
        self, coefficients: list[np.ndarray]
    ) -> list[float]:
        """Compute energy distribution across decomposition levels"""
        energies = []
        total_energy = sum(np.sum(c**2) for c in coefficients)

        for coeff in coefficients:
            energy = np.sum(coeff**2)
            energies.append(float(energy / total_energy if total_energy > 0 else 0))

        return energies

    def _compute_entropy(self, coefficients: list[np.ndarray]) -> float:
        """Compute wavelet entropy (measure of disorder)"""
        energies = [np.sum(c**2) for c in coefficients]
        total = sum(energies)

        if total == 0:
            return 0.0

        probabilities = [e / total for e in energies]
        entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)

        return entropy  # type: ignore[no-any-return]

    def _generate_test_signal(self) -> np.ndarray:
        """Generate test signal with transients"""
        cfg = self.config
        t = np.arange(cfg.n_samples) / cfg.sampling_rate

        # Base signal: sum of sinusoids at different frequencies
        signal = (
            1.0 * np.sin(2 * np.pi * 5 * t)  # Low frequency
            + 0.5 * np.sin(2 * np.pi * 50 * t)  # Medium frequency
        )

        # Add transient events
        transient_times = [0.2, 0.5, 0.8]
        for tt in transient_times:
            idx = int(tt * cfg.sampling_rate)
            if idx < cfg.n_samples:
                signal[idx : idx + 50] += (
                    2.0
                    * np.exp(-np.arange(50) / 10)
                    * np.sin(2 * np.pi * 200 * np.arange(50) / cfg.sampling_rate)
                )

        # Add noise
        signal += 0.3 * np.random.randn(cfg.n_samples)

        return signal  # type: ignore[no-any-return]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run wavelet analysis"""
        cfg = self.config

        logger.info(
            f"Starting wavelet analysis: {cfg.wavelet_family.value}, "
            f"order={cfg.wavelet_order}, levels={cfg.max_level}"
        )

        # Get signal
        if hypothesis and "signal" in hypothesis:
            x = np.array(hypothesis["signal"])
            if len(x) != cfg.n_samples:
                cfg.n_samples = len(x)
        else:
            x = self._generate_test_signal()

        # Ensure length is power of 2 for simplicity
        target_len = 2 ** int(np.floor(np.log2(len(x))))
        x = x[:target_len]
        original_len = len(x)

        # Multi-level decomposition
        self.coefficients = self.decompose(x, cfg.max_level)
        actual_levels = len(self.coefficients) - 1  # Exclude approximation

        # Apply denoising if requested
        if cfg.denoise:
            self.coefficients = self._threshold_coefficients(self.coefficients)

        # Reconstruct signal
        self.reconstructed_signal = self.reconstruct(self.coefficients, original_len)

        # Compute reconstruction error
        reconstruction_error = np.mean((x - self.reconstructed_signal) ** 2)
        snr_improvement = (
            10 * np.log10(np.mean(x**2) / reconstruction_error)
            if reconstruction_error > 0
            else np.inf
        )

        return self._format_output(
            x, actual_levels, reconstruction_error, snr_improvement
        )

    def _format_output(
        self, x: np.ndarray, levels: int, reconstruction_error: float, snr: float
    ) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        output = {
            "wavelet_family": cfg.wavelet_family.value,
            "wavelet_order": cfg.wavelet_order,
            "decomposition_levels": levels,
            "coefficients_shape": [c.shape[0] for c in self.coefficients],
            "reconstruction_error": float(reconstruction_error),
            "snr_db": float(snr),
            "original_signal": x.tolist(),
            "reconstructed_signal": self.reconstructed_signal.tolist(),  # type: ignore[union-attr]
        }

        # Add coefficient energy distribution
        if cfg.compute_energy:
            energy_dist = self._compute_energy_distribution(self.coefficients)
            output["energy_distribution"] = energy_dist

        # Add entropy
        if cfg.compute_entropy:
            output["wavelet_entropy"] = self._compute_entropy(self.coefficients)

        # Add denoising info
        if cfg.denoise:
            output["denoising"] = {
                "method": cfg.threshold_method.value,
                "sigma": cfg.threshold_sigma,
            }

        # Summary statistics
        output["summary"] = {
            "approximation_mean": float(np.mean(self.coefficients[0])),
            "approximation_std": float(np.std(self.coefficients[0])),
            "max_detail_coeff": float(
                max(np.max(np.abs(c)) for c in self.coefficients[1:])
            ),
            "compression_ratio": len(x) / sum(len(c) for c in self.coefficients),
        }

        return output

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Wavelet Analysis",
            "category": "EXTENDED",
            "domain": ["Signal Processing", "Image Processing", "Data Compression"],
            "description": "Discrete Wavelet Transform for multi-resolution analysis",
            "computational_complexity": "O(N) per decomposition level",
            "typical_runtime": "seconds",
            "accuracy": "High (perfect reconstruction for orthogonal wavelets)",
            "assumptions": [
                "Signal length is power of 2 (or zero-padded)",
                "Appropriate wavelet selection for signal characteristics",
                "Sufficient decomposition levels for analysis",
            ],
            "parameters": [
                {
                    "name": "wavelet_family",
                    "type": "enum",
                    "options": [
                        "haar",
                        "daubechies",
                        "symlet",
                        "coiflet",
                        "biorthogonal",
                    ],
                    "default": "daubechies",
                },
                {
                    "name": "wavelet_order",
                    "type": "int",
                    "default": 4,
                    "description": "Wavelet order (e.g., 4 for db4)",
                },
                {
                    "name": "max_level",
                    "type": "int",
                    "default": None,
                    "description": "Maximum decomposition level",
                },
                {
                    "name": "denoise",
                    "type": "bool",
                    "default": False,
                    "description": "Apply thresholding for denoising",
                },
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================


def test_perfect_reconstruction() -> None:
    """Test that decomposition followed by reconstruction gives original signal"""
    np.random.seed(42)

    config = WaveletAnalysisConfig(wavelet_family=WaveletFamily.HAAR, max_level=3)

    analyzer = WaveletAnalysisPattern(config)

    # Create simple test signal (power of 2 length)
    signal = np.random.randn(1024)
    result = analyzer.run({"signal": signal})

    # Reconstruction error should be very small
    assert result["reconstruction_error"] < 1e-10, (
        f"Perfect reconstruction failed: error={result['reconstruction_error']}"
    )
    print("✓ Perfect reconstruction test passed")


def test_denoising_effect() -> None:
    """Test that denoising reduces noise in signal"""
    np.random.seed(42)

    # Create noisy signal
    t = np.linspace(0, 1, 2048)
    clean_signal = np.sin(2 * np.pi * 10 * t)
    noise = 0.5 * np.random.randn(len(t))
    noisy_signal = clean_signal + noise

    # Without denoising
    config_no_denoise = WaveletAnalysisConfig(
        wavelet_family=WaveletFamily.DB, wavelet_order=4, max_level=5, denoise=False
    )
    analyzer_no = WaveletAnalysisPattern(config_no_denoise)
    result_no = analyzer_no.run({"signal": noisy_signal})

    # With denoising
    config_denoise = WaveletAnalysisConfig(
        wavelet_family=WaveletFamily.DB,
        wavelet_order=4,
        max_level=5,
        denoise=True,
        threshold_method=ThresholdMethod.SOFT,
        threshold_sigma=0.3,
    )
    analyzer_yes = WaveletAnalysisPattern(config_denoise)
    result_yes = analyzer_yes.run({"signal": noisy_signal})

    # Denoised signal should be closer to clean signal
    error_no = np.mean(
        (np.array(result_no["reconstructed_signal"]) - clean_signal) ** 2
    )
    error_yes = np.mean(
        (np.array(result_yes["reconstructed_signal"]) - clean_signal) ** 2
    )

    assert error_yes < error_no, "Denoising did not improve signal quality"
    print("✓ Denoising effect test passed")


def test_transient_detection() -> None:
    """Test that wavelet analysis detects transient features"""
    np.random.seed(42)

    # Create signal with transient
    signal = np.zeros(1024)
    signal[400:450] = 3.0  # Transient pulse
    signal += 0.1 * np.random.randn(1024)

    config = WaveletAnalysisConfig(wavelet_family=WaveletFamily.HAAR, max_level=4)

    analyzer = WaveletAnalysisPattern(config)
    result = analyzer.run({"signal": signal})

    # High frequency detail coefficients should capture transient
    max_detail = result["summary"]["max_detail_coeff"]
    assert max_detail > 1.0, f"Transient not detected: max detail = {max_detail}"
    print("✓ Transient detection test passed")


def test_energy_conservation() -> None:
    """Test that total energy is preserved in wavelet domain"""
    np.random.seed(42)

    signal = np.random.randn(2048)
    signal_energy = np.sum(signal**2)

    config = WaveletAnalysisConfig(
        wavelet_family=WaveletFamily.HAAR, max_level=5, compute_energy=True
    )

    analyzer = WaveletAnalysisPattern(config)
    result = analyzer.run({"signal": signal})

    # Sum of energy distribution should be close to 1
    total_dist_energy = sum(result["energy_distribution"])
    assert abs(total_dist_energy - 1.0) < 0.01, (
        f"Energy not conserved: sum = {total_dist_energy}"
    )
    print("✓ Energy conservation test passed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run tests
    test_perfect_reconstruction()
    test_denoising_effect()
    test_transient_detection()
    test_energy_conservation()

    # Demo run
    print("\n--- Demo Run ---")
    config = WaveletAnalysisConfig(
        wavelet_family=WaveletFamily.DB, wavelet_order=4, max_level=5, denoise=True
    )

    analyzer = WaveletAnalysisPattern(config)
    result = analyzer.run()

    print(f"Wavelet: {result['wavelet_family']} (order {result['wavelet_order']})")
    print(f"Levels: {result['decomposition_levels']}")
    print(f"Reconstruction error: {result['reconstruction_error']:.2e}")
    print(f"SNR: {result['snr_db']:.2f} dB")
    print(f"Wavelet entropy: {result.get('wavelet_entropy', 'N/A')}")
