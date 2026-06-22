"""Time Series Plugin — autocorrelation, stationarity, trend decomposition.

Does NOT duplicate: dist_analyzer (fits distributions), stat_tests (p-values).
UNIQUE: Time-domain analysis for citation velocity, temporal KG, simulation output.
"""
from __future__ import annotations

import math
from typing import Any


def autocorrelation(data: list[float], max_lag: int = 10) -> dict[str, Any]:
    """Autocorrelation function (ACF) for lags 1..max_lag.

    Used for: citation velocity analysis, temporal KG periodicity detection.
    """
    n = len(data)
    if n < 4:
        return {"error": "Need at least 4 data points"}

    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data)
    if variance == 0:
        return {"acf": [1.0] * min(max_lag, n - 1), "mean": mean, "n": n, "white_noise": True}

    acf = []
    for lag in range(1, min(max_lag + 1, n)):
        cov = sum((data[i] - mean) * (data[i - lag] - mean) for i in range(lag, n))
        acf.append(round(cov / variance, 6))

    # Check if data is white noise (all ACF ≈ 0 within 2/sqrt(n) bounds)
    threshold = 2 / math.sqrt(n)
    white_noise = all(abs(a) < threshold for a in acf)

    # Trend detection: ACF decays slowly → trend
    has_trend = len(acf) >= 3 and all(a > 0.5 for a in acf[:3])

    return {
        "acf": acf,
        "mean": round(mean, 4),
        "n": n,
        "white_noise": white_noise,
        "has_trend": has_trend,
        "sig_threshold": round(threshold, 4),
    }


def stationarity_test(data: list[float]) -> dict[str, Any]:
    """Approximate Dickey-Fuller test for stationarity.

    H0: unit root (non-stationary). Reject if test_stat < critical_value.
    """
    n = len(data)
    if n < 5:
        return {"error": "Need at least 5 data points"}

    # Compute Δy_t = y_t - y_{t-1}, regress on y_{t-1}
    diff = [data[i] - data[i - 1] for i in range(1, n)]
    lagged = data[:-1]

    diff_mean = sum(diff) / len(diff)
    lagged_mean = sum(lagged) / len(lagged)

    # Simple OLS: Δy = α + β*y_{t-1}
    num = sum((diff[i] - diff_mean) * (lagged[i] - lagged_mean) for i in range(len(diff)))
    den = sum((x - lagged_mean) ** 2 for x in lagged)

    if den == 0:
        return {"error": "Constant series"}

    beta = num / den
    alpha = diff_mean - beta * lagged_mean

    # Residual standard error
    residuals = [diff[i] - (alpha + beta * lagged[i]) for i in range(len(diff))]
    rse = math.sqrt(sum(r ** 2 for r in residuals) / (len(diff) - 2)) if len(diff) > 2 else 1.0

    # Test statistic = β / SE(β)
    se_beta = rse / math.sqrt(den) if den > 0 else 1.0
    test_stat = beta / se_beta if se_beta > 0 else 0.0

    # Critical values (approximate)
    stationary = test_stat < -2.86

    slope = sum((i - (n - 1) / 2) * (data[i] - sum(data) / n) for i in range(n)) / \
            sum((i - (n - 1) / 2) ** 2 for i in range(n)) if n > 1 else 0.0

    return {
        "test_statistic": round(test_stat, 4),
        "p_value_approx": "<0.01" if test_stat < -3.43 else "<0.05" if test_stat < -2.86 else "<0.10" if test_stat < -2.57 else ">0.10",
        "stationary": stationary,
        "drift": round(alpha, 4),
        "slope": round(slope, 6),
        "n": n,
    }


def trend_decomposition(data: list[float]) -> dict[str, Any]:
    """Simple moving-average trend decomposition.

    trend = MA(smoothing_window). residual = data - trend.
    """
    n = len(data)
    if n < 4:
        return {"error": "Need at least 4 data points"}

    window = max(3, n // 4)
    half = window // 2

    trend = []
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        window_data = data[lo:hi]
        trend.append(sum(window_data) / len(window_data))

    residual = [data[i] - trend[i] for i in range(n)]
    trend_strength = 1 - sum(r ** 2 for r in residual) / sum((x - sum(data) / n) ** 2 for x in data) if sum((x - sum(data) / n) ** 2 for x in data) > 0 else 0.0

    return {
        "trend": [round(t, 4) for t in trend[:20]],  # first 20 points
        "residual": [round(r, 4) for r in residual[:20]],
        "trend_strength": round(trend_strength, 4),
        "window": window,
        "n": n,
    }


def growth_rate(data: list[float]) -> dict[str, Any]:
    """Compound annual growth rate (CAGR) and period-over-period changes.

    Used for: citation velocity analysis.
    """
    n = len(data)
    if n < 2:
        return {"error": "Need at least 2 data points"}

    first = data[0]
    last = data[-1]

    # CAGR
    years = n - 1
    cagr = (last / first) ** (1 / years) - 1 if first > 0 and years > 0 else 0.0

    # Period-over-period growth
    pop = []
    for i in range(1, n):
        if data[i - 1] > 0:
            pop.append(round((data[i] - data[i - 1]) / data[i - 1], 4))
        else:
            pop.append(0.0)

    mean_growth = sum(pop) / len(pop) if pop else 0.0
    accelerating = len(pop) >= 3 and pop[-1] > pop[-2] > pop[-3]

    return {
        "cagr": round(cagr, 6),
        "growth_rates": pop[:20],
        "mean_growth": round(mean_growth, 4),
        "accelerating": accelerating,
        "n": n,
    }


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run time series analysis on provided data.

    metric: "autocorr" | "stationarity" | "trend" | "growth"
    data: list of floats
    """
    metric = kwargs.get("metric", "autocorr")
    data = kwargs.get("data", [])

    try:
        if metric == "stationarity":
            return stationarity_test(data)
        elif metric == "trend":
            return trend_decomposition(data)
        elif metric == "growth":
            return growth_rate(data)
        else:
            return autocorrelation(data, kwargs.get("max_lag", 10))
    except Exception as e:
        return {"error": str(e), "metric": metric}
