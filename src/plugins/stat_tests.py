"""Statistical Tests Plugin — Welch t-test, Mann-Whitney, Cohen's d, chi-squared.

Does NOT duplicate: Monte Carlo (simulation), Hash (fingerprint), Text Distance (similarity).
UNIQUE: p-values, effect sizes, statistical inference — what scientists actually need.
"""
from __future__ import annotations

import logging
import math
from typing import Any


logger = logging.getLogger(__name__)


def welch_ttest(sample1: list[float], sample2: list[float]) -> dict[str, Any]:
    """Welch's t-test (unequal variance) — returns t-statistic, p-value, Cohen's d."""
    n1, n2 = len(sample1), len(sample2)
    if n1 < 2 or n2 < 2:
        return {"error": "Need at least 2 samples per group"}

    mean1 = sum(sample1) / n1
    mean2 = sum(sample2) / n2
    var1 = sum((x - mean1) ** 2 for x in sample1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in sample2) / (n2 - 1)

    se = math.sqrt(var1 / n1 + var2 / n2)
    if se == 0:
        return {"t_statistic": 0.0, "p_value": 1.0, "cohens_d": 0.0, "significant": False}

    t = (mean1 - mean2) / se

    # Welch-Satterthwaite degrees of freedom
    df_num = (var1 / n1 + var2 / n2) ** 2
    df_den = (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
    df = df_num / df_den if df_den > 0 else n1 + n2 - 2

    # Approximate p-value via Abramowitz & Stegun formula
    x = df / (df + t * t)
    p = _incomplete_beta(df / 2, 0.5, x) if df > 0 and x > 0 else 1.0

    pooled_sd = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    cohens_d = abs(mean1 - mean2) / pooled_sd if pooled_sd > 0 else 0.0

    effect = "large" if cohens_d >= 0.8 else "medium" if cohens_d >= 0.5 else "small"
    return {
        "t_statistic": round(t, 4),
        "p_value": round(p, 6),
        "df": round(df, 2),
        "cohens_d": round(cohens_d, 4),
        "effect_size": effect,
        "significant": p < 0.05,
        "sample_sizes": [n1, n2],
    }


def mann_whitney(sample1: list[float], sample2: list[float]) -> dict[str, Any]:
    """Mann-Whitney U test — non-parametric alternative to t-test."""
    n1, n2 = len(sample1), len(sample2)
    if n1 < 2 or n2 < 2:
        return {"error": "Need at least 2 samples per group"}

    # Rank all values
    combined = [(x, 0) for x in sample1] + [(x, 1) for x in sample2]
    combined.sort(key=lambda p: p[0])

    ranks = {}
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 1) / 2  # 1-based ranking average
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    r1 = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u = min(u1, u2)

    # Normal approximation
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu) / sigma if sigma > 0 else 0.0
    p = 2 * (1 - _normal_cdf(abs(z)))

    return {
        "u_statistic": round(u, 2),
        "z_score": round(z, 4),
        "p_value": round(p, 6),
        "significant": p < 0.05,
        "sample_sizes": [n1, n2],
    }


def chi_squared(observed: list[list[float]]) -> dict[str, Any]:
    """Chi-squared test of independence on contingency table."""
    if not observed or not observed[0]:
        return {"error": "Need non-empty contingency table"}

    rows = len(observed)
    cols = len(observed[0])
    total = sum(sum(row) for row in observed)
    if total == 0:
        return {"error": "All values are zero"}

    row_sums = [sum(row) for row in observed]
    col_sums = [sum(observed[r][c] for r in range(rows)) for c in range(cols)]

    chi2 = 0.0
    for r in range(rows):
        for c in range(cols):
            expected = row_sums[r] * col_sums[c] / total
            if expected > 0:
                chi2 += (observed[r][c] - expected) ** 2 / expected

    df = (rows - 1) * (cols - 1)
    # Wilson-Hilferty approximation for chi-squared p-value
    p = _chi2_pvalue(chi2, df) if df > 0 else 1.0

    return {
        "chi2": round(chi2, 4),
        "df": df,
        "p_value": round(p, 6),
        "significant": p < 0.05,
        "cramers_v": round(math.sqrt(chi2 / (total * (min(rows, cols) - 1))) if total > 0 and min(rows, cols) > 1 else 0, 4),
    }


# ── Internal math helpers ──────────────────────────────────────────────

def _normal_cdf(z: float) -> float:
    """Standard normal CDF via Abramowitz & Stegun 26.2.17."""
    if z < -8:
        return 0.0
    if z > 8:
        return 1.0
    # Hart's algorithm
    x = abs(z)
    t = 1.0 / (1.0 + 0.2316419 * x)
    poly = t * (0.31938153 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    phi = 1.0 - (1.0 / math.sqrt(2 * math.pi)) * math.exp(-x * x / 2.0) * poly
    return phi if z > 0 else 1.0 - phi


def _incomplete_beta(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function via continued fraction."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    # Lentz's continued fraction
    tiny = 1e-30
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1)
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 200):
        m2 = 2 * m
        aa = m * (b - m) * x / ((a + m2 - 1) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        del_ = d * c
        h *= del_
        if abs(del_ - 1.0) < 3e-7:
            break
    return h * (x ** a) * ((1 - x) ** b) / (a * _beta_approx(a, b))


def _beta_approx(a: float, b: float) -> float:
    """Stirling approximation for Beta(a,b)."""
    return math.exp(
        (a - 0.5) * math.log(a) + (b - 0.5) * math.log(b) - (a + b - 0.5) * math.log(a + b) + 0.5 * math.log(2 * math.pi) - math.log(a) - math.log(b) + math.log(a + b)
    ) if a > 0 and b > 0 else 1.0


def _chi2_pvalue(chi2: float, df: int) -> float:
    """Chi-squared survival function."""
    if df <= 0:
        return 1.0
    return 1.0 - _incomplete_beta(df / 2, 1 / 2, df / (df + chi2)) if chi2 >= 0 else 1.0


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run statistical tests on provided data.

    Input via kwargs:
        test: "ttest" | "mannwhitney" | "chisq"
        sample1, sample2: list of floats (for ttest/mannwhitney)
        observed: list of lists (for chisq contingency table)
    """
    test = kwargs.get("test", "ttest")
    try:
        if test == "mannwhitney":
            s1 = kwargs.get("sample1", [])
            s2 = kwargs.get("sample2", [])
            return mann_whitney(s1, s2)
        elif test == "chisq":
            return chi_squared(kwargs.get("observed", []))
        else:
            s1 = kwargs.get("sample1", [])
            s2 = kwargs.get("sample2", [])
            return welch_ttest(s1, s2)
    except Exception as e:
        logger.warning("stat_tests failed: %s", e)
        return {"error": str(e), "test": test}
