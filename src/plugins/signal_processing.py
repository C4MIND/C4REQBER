"""Signal Processing Plugin — FFT, spectral power, peak detection, convolution.

Does NOT duplicate: Monte Carlo (simulation), dist_analyzer (distribution fitting).
UNIQUE: Frequency-domain analysis for simulation output, periodic pattern detection.
"""
from __future__ import annotations

import math
from typing import Any


def dft(data: list[float]) -> dict[str, Any]:
    """Discrete Fourier Transform (DFT) — naive O(n²) for simplicity.

    Returns magnitude spectrum. For large data, use numpy FFT instead.
    """
    n = len(data)
    if n < 2:
        return {"error": "Need at least 2 data points"}

    # Remove mean (DC component)
    mean = sum(data) / n
    centered = [x - mean for x in data]

    magnitudes = []
    max_mag = 0.0
    peak_freq = 0

    for k in range(n // 2 + 1):
        real = sum(centered[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = sum(centered[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        mag = math.sqrt(real * real + imag * imag) / n
        magnitudes.append(round(mag, 6))
        if k > 0 and mag > max_mag:
            max_mag = mag
            peak_freq = k

    # Dominant frequency
    dominant = peak_freq / n if n > 0 else 0.0

    # Spectral flatness (Wiener entropy) — how "tonal" vs "noise-like"
    log_sum = sum(math.log(m + 1e-12) for m in magnitudes[1:] if m > 0)
    if len(magnitudes) > 1:
        geo_mean = math.exp(log_sum / (len(magnitudes) - 1))
        arith_mean = sum(magnitudes[1:]) / (len(magnitudes) - 1) if len(magnitudes) > 1 else 1.0
        flatness = geo_mean / arith_mean if arith_mean > 0 else 1.0
    else:
        flatness = 1.0

    return {
        "magnitudes": magnitudes[:20],
        "n": n,
        "dominant_frequency": round(dominant, 6),
        "dominant_magnitude": round(max_mag, 6),
        "spectral_flatness": round(flatness, 4),
        "flatness_label": "tonal" if flatness < 0.3 else "mixed" if flatness < 0.7 else "noise-like",
        "total_power": round(sum(m * m for m in magnitudes), 6),
    }


def convolution(signal: list[float], kernel: list[float]) -> dict[str, Any]:
    """1D convolution: signal * kernel."""
    if not signal or not kernel:
        return {"error": "Signal and kernel required"}

    result = []
    n_s = len(signal)
    n_k = len(kernel)

    for i in range(n_s + n_k - 1):
        conv = 0.0
        for j in range(max(0, i - n_s + 1), min(n_k, i + 1)):
            if i - j < n_s:
                conv += signal[i - j] * kernel[j]
        result.append(round(conv, 6))

    return {
        "result": result[:50],
        "length": len(result),
    }


def peak_detection(data: list[float], threshold: float | None = None, min_distance: int = 1) -> dict[str, Any]:
    """Detect peaks in a signal.

    A point is a peak if it's higher than its neighbors and above threshold.
    """
    n = len(data)
    if n < 3:
        return {"error": "Need at least 3 data points"}

    if threshold is None:
        threshold = sum(data) / n + (max(data) - min(data)) * 0.3

    peaks: list[dict[str, Any]] = []
    for i in range(1, n - 1):
        if data[i] > data[i - 1] and data[i] > data[i + 1] and data[i] >= threshold:
            if not peaks or (i - peaks[-1]["index"] >= min_distance):
                peaks.append({
                    "index": i,
                    "value": round(data[i], 4),
                    "prominence": round(data[i] - max(data[i - 1], data[i + 1]), 4),
                })

    return {
        "peaks": peaks[:10],
        "count": len(peaks),
        "threshold": round(threshold, 4),
        "n": n,
    }


def autocorrelation_signal(data: list[float], max_lag: int | None = None) -> dict[str, Any]:
    """Signal autocorrelation — find periodicity."""
    n = len(data)
    if n < 4:
        return {"error": "Need at least 4 data points"}

    max_lag = max_lag or n // 2
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data)

    if variance == 0:
        return {"acf": [1.0] * min(max_lag, n - 1), "periodicity": None, "n": n}

    acf = []
    max_acf = 0.0
    best_lag = 0

    for lag in range(1, min(max_lag + 1, n)):
        cov = sum((data[i] - mean) * (data[i - lag] - mean) for i in range(lag, n))
        acf_val = cov / variance
        acf.append(round(acf_val, 6))
        if acf_val > max_acf and lag > 1:
            max_acf = acf_val
            best_lag = lag

    period = best_lag if max_acf > 0.3 else None

    return {
        "acf": acf,
        "periodicity": {"lag": period, "strength": round(max_acf, 4)} if period else None,
        "n": n,
    }


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run signal processing on provided data.

    metric: "dft" | "convolution" | "peaks" | "autocorr"
    data: list of floats
    kernel: list of floats (for convolution)
    """
    metric = kwargs.get("metric", "dft")
    data = kwargs.get("data", [])

    try:
        if metric == "convolution":
            return convolution(data, kwargs.get("kernel", []))
        elif metric == "peaks":
            return peak_detection(data, kwargs.get("threshold"), kwargs.get("min_distance", 1))
        elif metric == "autocorr":
            return autocorrelation_signal(data, kwargs.get("max_lag"))
        else:
            return dft(data)
    except Exception as e:
        return {"error": str(e), "metric": metric}
