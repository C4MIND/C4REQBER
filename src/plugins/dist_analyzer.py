"""Distribution Analyzer Plugin — fit, KS test, bootstrap CI.

Does NOT duplicate: Monte Carlo (simulation), stat_tests (t-test), modular_math (arithmetic).
UNIQUE: Distribution fitting, goodness-of-fit, bootstrap confidence intervals.
"""
from __future__ import annotations

import math
import random
from typing import Any


def ks_test(data: list[float], dist_type: str = "normal") -> dict[str, Any]:
    """Kolmogorov-Smirnov goodness-of-fit test.

    Compares empirical CDF against theoretical CDF (normal by default).
    """
    if len(data) < 5:
        return {"error": "Need at least 5 data points"}

    n = len(data)
    mean = sum(data) / n
    var = sum((x - mean) ** 2 for x in data) / n
    sd = math.sqrt(var) if var > 0 else 1.0

    sorted_data = sorted(data)
    d_max = 0.0

    for i, x in enumerate(sorted_data):
        empirical = (i + 1) / n

        if dist_type == "exponential":
            theoretical = 1.0 - math.exp(-x / mean) if mean > 0 else 0.0
        elif dist_type == "uniform":
            a, b = min(data), max(data)
            theoretical = (x - a) / (b - a) if b > a else 0.5
        else:  # normal
            theoretical = _normal_cdf((x - mean) / sd)

        d_max = max(d_max, abs(empirical - theoretical))

    # KS critical value approximation
    critical_05 = 1.36 / math.sqrt(n)
    significant = d_max > critical_05

    # Fit quality
    fit_quality = "good" if d_max < 0.05 else "moderate" if d_max < 0.1 else "poor" if d_max < 0.2 else "very poor"

    return {
        "ks_statistic": round(d_max, 6),
        "critical_value_0.05": round(critical_05, 6),
        "significant": significant,  # True = DOES NOT fit
        "fit_quality": fit_quality,
        "distribution": dist_type,
        "mean": round(mean, 4),
        "std": round(sd, 4),
        "n": n,
    }


def bootstrap_ci(data: list[float], confidence: float = 0.95, n_bootstrap: int = 1000) -> dict[str, Any]:
    """Bootstrap confidence interval for the mean."""
    if len(data) < 3:
        return {"error": "Need at least 3 data points"}

    n = len(data)
    random.seed(42)
    means = []
    for _ in range(n_bootstrap):
        sample = [random.choice(data) for _ in range(n)]
        means.append(sum(sample) / n)

    means.sort()
    alpha = (1 - confidence) / 2
    lo = means[int(alpha * n_bootstrap)]
    hi = means[int((1 - alpha) * n_bootstrap)]
    sample_mean = sum(data) / n

    return {
        "mean": round(sample_mean, 6),
        "ci_lower": round(lo, 6),
        "ci_upper": round(hi, 6),
        "confidence": confidence,
        "n_bootstrap": n_bootstrap,
        "n": n,
    }


def fit_power_law(data: list[float]) -> dict[str, Any]:
    """Fit power-law distribution P(x) ∝ x^(-α) via MLE.

    Useful for: citation distributions, network degree, wealth/income.
    """
    positive = [x for x in data if x > 0]
    if len(positive) < 5:
        return {"error": "Need at least 5 positive values for power-law fit"}

    x_min = min(positive)
    n = len(positive)
    log_sum = sum(math.log(x / x_min) for x in positive)

    alpha = 1 + n / log_sum if log_sum > 0 else 0.0

    # Goodness: compare empirical vs theoretical tail
    sorted_data = sorted(positive, reverse=True)
    empirical = [i / n for i in range(1, n + 1)]
    theoretical = [(x / x_min) ** (1 - alpha) if alpha > 1 else 1.0 for x in sorted_data]

    r2_num = sum((e - t) ** 2 for e, t in zip(empirical, theoretical, strict=False))
    r2_den = sum((e - sum(empirical) / n) ** 2 for e in empirical)
    r_squared = 1 - r2_num / r2_den if r2_den > 0 else 0.0

    return {
        "alpha": round(alpha, 4),
        "x_min": x_min,
        "r_squared": round(r_squared, 4),
        "fit_quality": "good" if r_squared > 0.9 else "moderate" if r_squared > 0.7 else "poor",
        "n": n,
        "interpretation": "heavy-tailed" if alpha < 3 else "light-tailed" if alpha > 3 else "scale-free",
    }


def outlier_detection(data: list[float], method: str = "iqr") -> dict[str, Any]:
    """Detect outliers via IQR or Z-score method."""
    if len(data) < 4:
        return {"error": "Need at least 4 data points"}

    sorted_data = sorted(data)
    n = len(sorted_data)

    if method == "zscore":
        mean = sum(data) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in data) / n)
        threshold = 3.0
        outliers = [x for x in data if abs(x - mean) / sd > threshold] if sd > 0 else []
    else:  # IQR
        q1 = sorted_data[n // 4]
        q3 = sorted_data[3 * n // 4]
        iqr = q3 - q1
        lo = q1 - 1.5 * iqr
        hi = q3 + 1.5 * iqr
        outliers = [x for x in data if x < lo or x > hi]

    return {
        "outliers": [round(x, 4) for x in outliers],
        "count": len(outliers),
        "percentage": round(100 * len(outliers) / n, 2),
        "method": method,
        "n": n,
    }


# ── Internal helpers ───────────────────────────────────────────────────

def _normal_cdf(z: float) -> float:
    if z < -8:
        return 0.0
    if z > 8:
        return 1.0
    x = abs(z)
    t = 1.0 / (1.0 + 0.2316419 * x)
    poly = t * (0.31938153 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    phi = 1.0 - (1.0 / math.sqrt(2 * math.pi)) * math.exp(-x * x / 2.0) * poly
    return phi if z > 0 else 1.0 - phi


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run distribution analysis on provided data.

    Auto-selects analysis based on available kwargs.
    """
    metric = kwargs.get("metric", "ks_test")
    data = kwargs.get("data", [])

    try:
        if metric == "bootstrap_ci":
            return bootstrap_ci(data, kwargs.get("confidence", 0.95))
        elif metric == "power_law":
            return fit_power_law(data)
        elif metric == "outliers":
            return outlier_detection(data, kwargs.get("method", "iqr"))
        else:  # ks_test
            return ks_test(data, kwargs.get("dist", "normal"))
    except Exception as e:
        return {"error": str(e), "metric": metric}
