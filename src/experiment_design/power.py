"""Power Analysis for C4REQBER.

Sample size calculations, power curves, and effect size estimation
for t-tests, ANOVA, and proportions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy import stats


@dataclass(frozen=True)
class PowerResult:
    """PowerResult."""
    test_type: str
    sample_size: int | None
    power: float
    effect_size: float
    alpha: float
    parameters: dict[str, float]

    def to_dict(self) -> dict[str, float | int | str | None]:
        return {
            "test_type": self.test_type,
            "sample_size": self.sample_size,
            "power": self.power,
            "effect_size": self.effect_size,
            "alpha": self.alpha,
            **self.parameters,
        }


def cohens_d(
    group1: NDArray[np.float64],
    group2: NDArray[np.float64],
    pooled: bool = True,
) -> float:
    """Cohens d."""
    m1, m2 = float(np.mean(group1)), float(np.mean(group2))
    if pooled:
        n1, n2 = len(group1), len(group2)
        var1, var2 = float(np.var(group1, ddof=1)), float(np.var(group2, ddof=1))
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return 0.0
        return float((m1 - m2) / pooled_std)
    std1, std2 = float(np.std(group1, ddof=1)), float(np.std(group2, ddof=1))
    denom = np.sqrt((std1**2 + std2**2) / 2)
    if denom == 0:
        return 0.0
    return float((m1 - m2) / denom)


def eta_squared(anova_f: float, df_between: int, df_within: int) -> float:
    """Eta squared."""
    if anova_f <= 0:
        return 0.0
    return float((anova_f * df_between) / (anova_f * df_between + df_within))


def partial_eta_squared(anova_f: float, df_effect: int, df_error: int) -> float:
    """Partial eta squared."""
    if anova_f <= 0:
        return 0.0
    return float((anova_f * df_effect) / (anova_f * df_effect + df_error))


def ttest_sample_size(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.8,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
    ratio: float = 1.0,
) -> PowerResult:
    """Ttest sample size."""
    if effect_size == 0:
        raise ValueError("effect_size must be non-zero")
    if alternative == "two-sided":
        alpha_adj = alpha / 2
    else:
        alpha_adj = alpha
    z_alpha = stats.norm.ppf(1 - alpha_adj)
    z_beta = stats.norm.ppf(power)
    n_per_group = ((z_alpha + z_beta) / effect_size) ** 2 * (1 + 1 / ratio) / 2
    n = int(np.ceil(n_per_group))
    actual_power = ttest_power(effect_size, n, alpha, alternative)
    return PowerResult(
        test_type="t_test_independent",
        sample_size=n,
        power=actual_power,
        effect_size=effect_size,
        alpha=alpha,
        parameters={"ratio": ratio, "alternative": alternative},  # type: ignore[dict-item]
    )


def ttest_power(
    effect_size: float,
    n_per_group: int,
    alpha: float = 0.05,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> float:
    """Ttest power."""
    if alternative == "two-sided":
        alpha_adj = alpha / 2
    else:
        alpha_adj = alpha
    df = 2 * n_per_group - 2
    ncp = effect_size * np.sqrt(n_per_group / 2)
    crit_t = stats.t.ppf(1 - alpha_adj, df)
    if alternative == "two-sided":
        power = 1 - stats.nct.cdf(crit_t, df, ncp) + stats.nct.cdf(-crit_t, df, ncp)
    elif alternative == "greater":
        power = 1 - stats.nct.cdf(crit_t, df, ncp)
    else:
        power = stats.nct.cdf(-crit_t, df, ncp)
    return float(power)


def anova_sample_size(
    effect_size: float,
    k_groups: int,
    alpha: float = 0.05,
    power: float = 0.8,
) -> PowerResult:
    """Anova sample size."""
    if effect_size <= 0:
        raise ValueError("effect_size must be > 0")
    if k_groups < 2:
        raise ValueError("k_groups must be >= 2")
    k_groups - 1
    z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)
    n_per_group = ((z_alpha + z_beta) / effect_size) ** 2
    n = max(2, int(np.ceil(n_per_group)))
    actual_power = anova_power(effect_size, k_groups, n, alpha)
    while actual_power < power and n < 1_000_000:
        n += 1
        actual_power = anova_power(effect_size, k_groups, n, alpha)
    return PowerResult(
        test_type="anova_one_way",
        sample_size=n,
        power=actual_power,
        effect_size=effect_size,
        alpha=alpha,
        parameters={"k_groups": k_groups},
    )


def anova_power(
    effect_size: float,
    k_groups: int,
    n_per_group: int,
    alpha: float = 0.05,
) -> float:
    """Anova power."""
    df_between = k_groups - 1
    df_within = k_groups * (n_per_group - 1)
    ncp = effect_size**2 * n_per_group * k_groups
    crit_f = stats.f.ppf(1 - alpha, df_between, df_within)
    return float(1 - stats.ncf.cdf(crit_f, df_between, df_within, ncp))


def proportion_sample_size(
    p1: float,
    p2: float,
    alpha: float = 0.05,
    power: float = 0.8,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> PowerResult:
    """Proportion sample size."""
    if not (0 < p1 < 1 and 0 < p2 < 1):
        raise ValueError("Proportions must be in (0, 1)")
    if alternative == "two-sided":
        alpha_adj = alpha / 2
    else:
        alpha_adj = alpha
    z_alpha = stats.norm.ppf(1 - alpha_adj)
    z_beta = stats.norm.ppf(power)
    p_avg = (p1 + p2) / 2
    delta = abs(p1 - p2)
    if delta == 0:
        raise ValueError("p1 and p2 must differ")
    n = (
        z_alpha * np.sqrt(2 * p_avg * (1 - p_avg))
        + z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2 / delta**2
    n = int(np.ceil(n))
    actual_power = proportion_power(p1, p2, n, alpha, alternative)
    effect_size = delta / np.sqrt(p_avg * (1 - p_avg))
    return PowerResult(
        test_type="proportion_two_sample",
        sample_size=n,
        power=actual_power,
        effect_size=float(effect_size),
        alpha=alpha,
        parameters={"p1": p1, "p2": p2, "alternative": alternative},  # type: ignore[dict-item]
    )


def proportion_power(
    p1: float,
    p2: float,
    n_per_group: int,
    alpha: float = 0.05,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> float:
    """Proportion power."""
    if alternative == "two-sided":
        alpha_adj = alpha / 2
    else:
        alpha_adj = alpha
    p_avg = (p1 + p2) / 2
    se_null = np.sqrt(2 * p_avg * (1 - p_avg) / n_per_group)
    se_alt = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / n_per_group)
    delta = p1 - p2
    z_alpha = stats.norm.ppf(1 - alpha_adj)
    if alternative == "two-sided":
        crit_low = -z_alpha * se_null
        crit_high = z_alpha * se_null
        power = (
            1 - stats.norm.cdf((crit_high - delta) / se_alt)
            + stats.norm.cdf((crit_low - delta) / se_alt)
        )
    elif alternative == "greater":
        crit = z_alpha * se_null
        power = 1 - stats.norm.cdf((crit - delta) / se_alt)
    else:
        crit = -z_alpha * se_null
        power = stats.norm.cdf((crit - delta) / se_alt)
    return float(power)


def power_curve_ttest(
    effect_size: float,
    sample_sizes: NDArray[np.int64] | list[int],
    alpha: float = 0.05,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> NDArray[np.float64]:
    """Power curve ttest."""
    sizes = np.asarray(sample_sizes, dtype=np.int64)
    powers = np.array([ttest_power(effect_size, int(n), alpha, alternative) for n in sizes])
    return powers


def power_curve_anova(
    effect_size: float,
    k_groups: int,
    sample_sizes: NDArray[np.int64] | list[int],
    alpha: float = 0.05,
) -> NDArray[np.float64]:
    """Power curve anova."""
    sizes = np.asarray(sample_sizes, dtype=np.int64)
    powers = np.array([anova_power(effect_size, k_groups, int(n), alpha) for n in sizes])
    return powers


def power_curve_proportion(
    p1: float,
    p2: float,
    sample_sizes: NDArray[np.int64] | list[int],
    alpha: float = 0.05,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> NDArray[np.float64]:
    """Power curve proportion."""
    sizes = np.asarray(sample_sizes, dtype=np.int64)
    powers = np.array([proportion_power(p1, p2, int(n), alpha, alternative) for n in sizes])
    return powers
