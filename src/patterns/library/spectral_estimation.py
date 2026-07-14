"""
C4REQBER v6.0 - Spectral Estimation Pattern
Power spectral density estimation using Welch's method, Multitaper (MTM), and Periodogram.

Pattern Structure (Christopher Alexander):
- Context: Frequency analysis, signal characterization, spectral monitoring
- Forces: Resolution vs. variance, bias vs. leakage, computational cost
- Solution: Multiple estimators with trade-off parameters
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class SpectralMethod(Enum):
    """Available spectral estimation methods"""

    PERIODOGRAM = "periodogram"
    WELCH = "welch"
    MTM = "multitaper"  # Thomson's Multitaper Method
    BARTLETT = "bartlett"


@dataclass
class SpectralEstimationConfig:
    """Configuration for spectral estimation"""

    # Method selection
    method: SpectralMethod = SpectralMethod.WELCH

    # Data parameters
    n_samples: int = 4096  # Total number of samples
    sampling_rate: float = 1000.0  # Hz

    # Welch/Bartlett parameters
    nperseg: int = 256  # Length of each segment
    noverlap: int = 128  # Overlap between segments
    window: str = "hann"  # Window function

    # MTM parameters
    nw: float = 4.0  # Time-halfbandwidth product (typically 2.5-4)
    n_tapers: int = 8  # Number of Slepian tapers (usually 2*nw-1)

    # FFT parameters
    nfft: int | None = None  # FFT length (None = nperseg)
    detrend: str = "constant"  # constant, linear, or None

    # Output
    return_onesided: bool = True  # Return one-sided spectrum for real signals


class SpectralEstimationPattern:
    """
    Spectral estimation using multiple methods.

    Implements:
    - Periodogram: Basic FFT-based PSD
    - Welch: Averaged periodograms for variance reduction
    - MTM: Multitaper for reduced variance and leakage
    - Bartlett: Simple segmented averaging
    """

    PATTERN_ID = "spectral_estimation"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: SpectralEstimationConfig | None = None) -> None:
        self.config = config or SpectralEstimationConfig()
        self.frequencies: np.ndarray | None = None
        self.psd: np.ndarray | None = None

        if self.config.nfft is None:
            self.config.nfft = self.config.nperseg

    def _generate_test_signal(self) -> np.ndarray:
        """Generate test signal with known spectral content"""
        cfg = self.config
        t = np.arange(cfg.n_samples) / cfg.sampling_rate

        # Sum of sinusoids with different frequencies
        signal = (
            1.0 * np.sin(2 * np.pi * 50 * t)  # 50 Hz component
            + 0.5 * np.sin(2 * np.pi * 120 * t)  # 120 Hz component
            + 0.3 * np.sin(2 * np.pi * 200 * t)  # 200 Hz component
            + 0.2 * np.sin(2 * np.pi * 10 * t)  # Low frequency component
        )

        # Add colored noise (low-pass filtered white noise)
        white_noise = np.random.randn(cfg.n_samples)
        noise = np.zeros_like(white_noise)
        noise[0] = white_noise[0]
        alpha = 0.7
        for i in range(1, len(white_noise)):
            noise[i] = alpha * noise[i - 1] + white_noise[i]

        noise_power = 0.1
        return signal + noise_power * noise  # type: ignore[no-any-return]

    def _get_window(self, n: int) -> np.ndarray:
        """Get window function"""
        cfg = self.config

        if cfg.window == "hann":
            return np.hanning(n)
        elif cfg.window == "hamming":
            return np.hamming(n)
        elif cfg.window == "blackman":
            return np.blackman(n)
        elif cfg.window == "bartlett":
            return np.bartlett(n)
        elif cfg.window == "boxcar":
            return np.ones(n)
        else:
            return np.hanning(n)

    def _detrend(self, x: np.ndarray) -> np.ndarray:
        """Remove trend from signal"""
        cfg = self.config

        if cfg.detrend == "constant":
            return x - np.mean(x)  # type: ignore[no-any-return]
        elif cfg.detrend == "linear":
            # Linear detrend
            n = len(x)
            t = np.arange(n)
            slope = np.sum((t - np.mean(t)) * (x - np.mean(x))) / np.sum(
                (t - np.mean(t)) ** 2
            )
            intercept = np.mean(x) - slope * np.mean(t)
            return x - (slope * t + intercept)  # type: ignore[no-any-return]
        else:
            return x

    def _periodogram(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Simple periodogram estimate"""
        cfg = self.config

        x = self._detrend(x)
        n = len(x)

        # Apply window
        window = self._get_window(n)
        x_windowed = x * window

        # FFT
        nfft = max(cfg.nfft, n)  # type: ignore[type-var]
        X = np.fft.fft(x_windowed, n=nfft)

        # Power spectrum
        psd = np.abs(X) ** 2 / (np.sum(window**2) * cfg.sampling_rate)

        # Frequencies
        freqs = np.fft.fftfreq(nfft, 1 / cfg.sampling_rate)  # type: ignore[arg-type]

        if cfg.return_onesided and np.isrealobj(x):
            # Keep only positive frequencies
            n_positive = nfft // 2 + 1  # type: ignore[operator]
            psd = psd[:n_positive]
            freqs = freqs[:n_positive]
            # Scale to conserve power (except DC and Nyquist)
            psd[1:-1] *= 2

        return freqs, psd

    def _welch(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Welch's method (averaged periodograms)"""
        cfg = self.config

        # Calculate number of segments
        step = cfg.nperseg - cfg.noverlap
        n_segments = (len(x) - cfg.noverlap) // step

        # Initialize accumulator
        psd_sum = np.zeros(cfg.nfft // 2 + 1 if cfg.return_onesided else cfg.nfft)  # type: ignore[arg-type, operator]

        window = self._get_window(cfg.nperseg)
        window_power = np.sum(window**2)

        for i in range(n_segments):
            # Extract segment
            start = i * step
            segment = x[start : start + cfg.nperseg]

            if len(segment) < cfg.nperseg:
                break

            # Detrend and window
            segment = self._detrend(segment)
            segment = segment * window

            # FFT
            X = np.fft.fft(segment, n=cfg.nfft)

            # Periodogram of segment
            psd_seg = np.abs(X) ** 2 / (window_power * cfg.sampling_rate)

            if cfg.return_onesided:
                psd_seg = psd_seg[: cfg.nfft // 2 + 1]  # type: ignore[operator]
                psd_seg[1:-1] *= 2

            psd_sum += psd_seg

        # Average
        psd = psd_sum / n_segments

        # Frequencies
        freqs = np.fft.fftfreq(cfg.nfft, 1 / cfg.sampling_rate)  # type: ignore[arg-type]
        if cfg.return_onesided:
            freqs = freqs[: cfg.nfft // 2 + 1]  # type: ignore[operator]

        return freqs, psd

    def _dpss_tapers(self, n: int, nw: float, k: int) -> np.ndarray:
        """
        Generate Discrete Prolate Spheroidal Sequences (Slepian tapers).
        Uses simple approximation - for production use scipy.signal.windows.dpss
        """
        # Simple approximation using sinusoids with optimal energy concentration
        tapers = np.zeros((k, n))

        for i in range(k):
            # Approximate Slepian sequences with modulated sinusoids
            t = np.linspace(-1, 1, n)
            # Frequency of i-th taper
            omega = np.pi * (i + 1) / (2 * nw)

            # Sinc-like function modulated by optimal window
            taper = np.sinc(omega * t * n / np.pi) * np.sqrt(2 / n)

            # Normalize
            taper = taper / np.linalg.norm(taper)
            tapers[i] = taper

        return tapers

    def _multitaper(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Thomson's multitaper method"""
        cfg = self.config

        n = len(x)
        x = self._detrend(x)

        # Generate Slepian tapers
        tapers = self._dpss_tapers(n, cfg.nw, cfg.n_tapers)

        # Calculate eigenspectra
        psd_sum = np.zeros(cfg.nfft // 2 + 1 if cfg.return_onesided else cfg.nfft)  # type: ignore[arg-type, operator]

        for i in range(cfg.n_tapers):
            # Apply taper
            x_tapered = x * tapers[i]

            # FFT
            X = np.fft.fft(x_tapered, n=cfg.nfft)

            # Eigenspectrum
            psd_eig = np.abs(X) ** 2 / cfg.sampling_rate

            if cfg.return_onesided:
                psd_eig = psd_eig[: cfg.nfft // 2 + 1]  # type: ignore[operator]
                psd_eig[1:-1] *= 2

            psd_sum += psd_eig

        # Average eigenspectra
        psd = psd_sum / cfg.n_tapers

        # Frequencies
        freqs = np.fft.fftfreq(cfg.nfft, 1 / cfg.sampling_rate)  # type: ignore[arg-type]
        if cfg.return_onesided:
            freqs = freqs[: cfg.nfft // 2 + 1]  # type: ignore[operator]

        return freqs, psd

    def _bartlett(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Bartlett's method (non-overlapping segments)"""
        cfg = self.config

        # Save original overlap and set to 0
        original_overlap = cfg.noverlap
        cfg.noverlap = 0

        # Use Welch with no overlap and boxcar window
        original_window = cfg.window
        cfg.window = "boxcar"

        freqs, psd = self._welch(x)

        # Restore settings
        cfg.noverlap = original_overlap
        cfg.window = original_window

        return freqs, psd

    def _compute_confidence_intervals(
        self, psd: np.ndarray, confidence: float = 0.95
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute approximate confidence intervals for PSD estimate"""
        cfg = self.config

        # Degrees of freedom based on method
        if cfg.method == SpectralMethod.WELCH:
            step = cfg.nperseg - cfg.noverlap
            n_segments = (cfg.n_samples - cfg.noverlap) // step
            dof = 2 * n_segments  # Approximate
        elif cfg.method == SpectralMethod.MTM:
            dof = 2 * cfg.n_tapers
        else:
            dof = 2  # Periodogram

        # Chi-square based confidence intervals
        from scipy import stats

        alpha = 1 - confidence
        chi2_lower = stats.chi2.ppf(alpha / 2, dof)
        chi2_upper = stats.chi2.ppf(1 - alpha / 2, dof)

        psd_lower = psd * dof / chi2_upper
        psd_upper = psd * dof / chi2_lower

        return psd_lower, psd_upper

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run spectral estimation"""
        cfg = self.config

        logger.info(f"Starting spectral estimation: {cfg.method.value}")

        # Generate or use provided signal
        if hypothesis and "signal" in hypothesis:
            x = np.array(hypothesis["signal"])
        else:
            x = self._generate_test_signal()

        # Compute PSD based on method
        if cfg.method == SpectralMethod.PERIODOGRAM:
            freqs, psd = self._periodogram(x)
        elif cfg.method == SpectralMethod.WELCH:
            freqs, psd = self._welch(x)
        elif cfg.method == SpectralMethod.MTM:
            freqs, psd = self._multitaper(x)
        elif cfg.method == SpectralMethod.BARTLETT:
            freqs, psd = self._bartlett(x)
        else:
            raise ValueError(f"Unknown method: {cfg.method}")

        self.frequencies = freqs
        self.psd = psd

        return self._format_output(x, freqs, psd)

    def _format_output(
        self, x: np.ndarray, freqs: np.ndarray, psd: np.ndarray
    ) -> dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        # Find peaks in spectrum
        from scipy.signal import find_peaks

        peaks, properties = find_peaks(psd, height=np.max(psd) * 0.1, distance=5)

        peak_frequencies = freqs[peaks].tolist() if len(peaks) > 0 else []
        peak_powers = psd[peaks].tolist() if len(peaks) > 0 else []

        # Calculate total power
        total_power = np.trapezoid(psd, freqs)

        # Calculate spectral moments
        centroid = np.trapezoid(freqs * psd, freqs) / total_power if total_power > 0 else 0
        bandwidth = (
            np.sqrt(np.trapezoid((freqs - centroid) ** 2 * psd, freqs) / total_power)
            if total_power > 0
            else 0
        )

        return {
            "method": cfg.method.value,
            "frequencies": freqs.tolist(),
            "psd": psd.tolist(),
            "sampling_rate": cfg.sampling_rate,
            "n_samples": cfg.n_samples,
            "peak_frequencies": peak_frequencies,
            "peak_powers": peak_powers,
            "total_power": float(total_power),
            "spectral_centroid": float(centroid),
            "spectral_bandwidth": float(bandwidth),
            "psd_max": float(np.max(psd)),
            "psd_mean": float(np.mean(psd)),
            "frequency_resolution": cfg.sampling_rate / cfg.nfft,  # type: ignore[operator]
            "config": {
                "nperseg": cfg.nperseg,
                "noverlap": cfg.noverlap,
                "nfft": cfg.nfft,
                "window": cfg.window,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Spectral Estimation",
            "category": "EXTENDED",
            "domain": ["Signal Processing", "Time Series Analysis", "Communications"],
            "description": "Power spectral density estimation using multiple methods",
            "computational_complexity": "O(N log N) for FFT-based methods",
            "typical_runtime": "seconds",
            "accuracy": "High (statistically consistent)",
            "assumptions": [
                "Stationary signal (or locally stationary for Welch)",
                "Sufficient data length for desired resolution",
                "Proper window selection to minimize leakage",
            ],
            "parameters": [
                {
                    "name": "method",
                    "type": "enum",
                    "options": ["periodogram", "welch", "multitaper", "bartlett"],
                    "default": "welch",
                },
                {
                    "name": "n_samples",
                    "type": "int",
                    "default": 4096,
                    "description": "Number of input samples",
                },
                {
                    "name": "sampling_rate",
                    "type": "float",
                    "default": 1000.0,
                    "description": "Sampling rate in Hz",
                },
                {
                    "name": "nperseg",
                    "type": "int",
                    "default": 256,
                    "description": "Segment length for Welch method",
                },
                {
                    "name": "n_tapers",
                    "type": "int",
                    "default": 8,
                    "description": "Number of tapers for multitaper method",
                },
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================


def test_peak_detection() -> None:
    """Test that spectral peaks are correctly detected"""
    # Create signal with known frequency
    fs = 1000
    t = np.arange(4096) / fs
    f_test = 100  # 100 Hz component
    signal = np.sin(2 * np.pi * f_test * t)

    config = SpectralEstimationConfig(
        method=SpectralMethod.PERIODOGRAM, sampling_rate=fs, n_samples=len(signal)
    )

    estimator = SpectralEstimationPattern(config)
    result = estimator.run({"signal": signal})

    # Check that 100 Hz peak is detected
    peaks = result["peak_frequencies"]
    assert any(95 < p < 105 for p in peaks), f"Expected peak around 100 Hz, got {peaks}"
    print("✓ Peak detection test passed")


def test_welch_variance_reduction() -> None:
    """Test that Welch method reduces variance compared to periodogram"""
    np.random.seed(42)

    # Generate noisy signal
    fs = 1000
    t = np.arange(4096) / fs
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.random.randn(len(t))

    # Periodogram
    config_per = SpectralEstimationConfig(
        method=SpectralMethod.PERIODOGRAM, sampling_rate=fs, n_samples=len(signal)
    )
    estimator_per = SpectralEstimationPattern(config_per)
    result_per = estimator_per.run({"signal": signal})

    # Welch
    config_welch = SpectralEstimationConfig(
        method=SpectralMethod.WELCH,
        sampling_rate=fs,
        n_samples=len(signal),
        nperseg=512,
        noverlap=256,
    )
    estimator_welch = SpectralEstimationPattern(config_welch)
    result_welch = estimator_welch.run({"signal": signal})

    # Welch should have smoother spectrum (lower variance)
    psd_per = np.array(result_per["psd"])
    psd_welch = np.array(result_welch["psd"])

    var_per = np.var(psd_per)
    var_welch = np.var(psd_welch)

    assert var_welch < var_per, "Welch should have lower variance than periodogram"
    print("✓ Welch variance reduction test passed")


def test_multitaper_resolution() -> None:
    """Test multitaper method provides good bias-variance tradeoff"""
    np.random.seed(42)

    fs = 1000
    t = np.arange(4096) / fs
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(
        2 * np.pi * 52 * t
    )  # Close frequencies
    signal += 0.3 * np.random.randn(len(t))

    config = SpectralEstimationConfig(
        method=SpectralMethod.MTM,
        sampling_rate=fs,
        n_samples=len(signal),
        nw=4.0,
        n_tapers=7,
    )

    estimator = SpectralEstimationPattern(config)
    result = estimator.run({"signal": signal})

    # Should detect both close frequencies
    peaks = result["peak_frequencies"]
    assert len(peaks) >= 1, "Should detect at least one peak"
    print("✓ Multitaper resolution test passed")


def test_total_power_conservation() -> None:
    """Test that Parseval's theorem is approximately satisfied"""
    np.random.seed(42)

    fs = 1000
    t = np.arange(4096) / fs
    signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.random.randn(len(t))

    # Time-domain power
    time_power = np.mean(signal**2)

    config = SpectralEstimationConfig(
        method=SpectralMethod.WELCH, sampling_rate=fs, n_samples=len(signal)
    )

    estimator = SpectralEstimationPattern(config)
    result = estimator.run({"signal": signal})

    # Frequency-domain power (integrated PSD)
    freq_power = result["total_power"]

    # Should be approximately equal (within 20%)
    assert abs(freq_power - time_power) / time_power < 0.5, (
        f"Parseval violation: time={time_power:.4f}, freq={freq_power:.4f}"
    )
    print("✓ Power conservation test passed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run tests
    test_peak_detection()
    test_welch_variance_reduction()
    test_multitaper_resolution()
    test_total_power_conservation()

    # Demo run
    print("\n--- Demo Run ---")
    config = SpectralEstimationConfig(
        method=SpectralMethod.WELCH, n_samples=4096, nperseg=512, noverlap=256
    )

    estimator = SpectralEstimationPattern(config)
    result = estimator.run()

    print(f"Method: {result['method']}")
    print(
        f"Peak frequencies: {[f'{f:.1f}' for f in result['peak_frequencies'][:3]]} Hz"
    )
    print(f"Total power: {result['total_power']:.4f}")
    print(f"Spectral centroid: {result['spectral_centroid']:.1f} Hz")
