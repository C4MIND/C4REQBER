"""Statistical hypothesis validation using SciPy."""
from __future__ import annotations

import logging
import math
import time
import types
from typing import Any

import numpy as np


logger = logging.getLogger("c4reqber.verification.stats")


def _get_real_scipy_stats() -> Any:
    """Import scipy.stats and verify it is a real module (not mocked)."""
    try:
        import scipy.stats as _stats
        if not isinstance(_stats, types.ModuleType):
            return None
        # Sanity check: must have real functions we need
        if not callable(getattr(_stats, "ttest_ind", None)):
            return None
        return _stats
    except Exception:
        return None


class StatisticalValidator:
    """Validate hypotheses via statistical testing.

    Supports:
    - t-test (mean comparison)
    - chi-squared (categorical independence)
    - ks-test (distribution comparison)
    - correlation tests
    """

    @property
    def available(self) -> bool:
        return _get_real_scipy_stats() is not None

    async def verify(
        self,
        hypothesis: str,
        formal_spec: str | None = None,
        context: dict[str, Any] | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        ctx = context or {}
        test_type = ctx.get("test_type", "ttest")
        alpha = ctx.get("alpha", 0.05)

        # Data can be wrapped in "data" key or passed directly in context
        data = ctx.get("data")
        if data is None:
            # Check for direct test-specific keys
            direct_keys = {"group_a", "group_b", "observed", "sample", "reference", "x", "y"}
            if direct_keys.intersection(ctx.keys()):
                data = ctx
            else:
                return {
                    "status": "uncertain",
                    "method": "statistical",
                    "confidence": 0.0,
                    "hypothesis_text": hypothesis,
                    "error_message": "No data provided for statistical test",
                    "execution_time_ms": (time.perf_counter() - start) * 1000,
                    "proof_output": "",
                    "counterexample": None,
                    "metadata": {},
                }

        try:
            from scipy import stats

            if test_type == "ttest":
                result = self._run_ttest(data, alpha)
            elif test_type == "chi2":
                result = self._run_chi2(data, alpha)
            elif test_type == "ks":
                result = self._run_ks(data, alpha)
            elif test_type == "correlation":
                result = self._run_correlation(data, alpha)
            else:
                result = {
                    "status": "error",
                    "method": "statistical",
                    "confidence": 0.0,
                    "hypothesis_text": hypothesis,
                    "error_message": f"Unknown test type: {test_type}",
                    "execution_time_ms": 0.0,
                    "proof_output": "",
                    "counterexample": None,
                    "metadata": {},
                }
        except Exception as exc:
            logger.warning("Statistical validation failed: %s", exc, exc_info=True)
            result = {
                "status": "error",
                "method": "statistical",
                "confidence": 0.0,
                "hypothesis_text": hypothesis,
                "error_message": str(exc),
                "execution_time_ms": (time.perf_counter() - start) * 1000,
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }

        result["execution_time_ms"] = (time.perf_counter() - start) * 1000
        return result

    def _run_ttest(self, data: dict[str, Any], alpha: float) -> dict[str, Any]:
        stats = _get_real_scipy_stats()
        if stats is None:
            return {"status": "error", "method": "statistical", "confidence": 0.0, "error_message": "scipy.stats not available or mocked", "proof_output": "", "counterexample": None, "metadata": {}}

        group_a = np.array(data.get("group_a", []))
        group_b = np.array(data.get("group_b", []))
        if len(group_a) < 2 or len(group_b) < 2:
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "Insufficient data for t-test",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }

        ttest_res = stats.ttest_ind(group_a, group_b)
        t_stat = getattr(ttest_res, "statistic", ttest_res[0] if hasattr(ttest_res, "__getitem__") else float("nan"))
        p_value = getattr(ttest_res, "pvalue", ttest_res[1] if hasattr(ttest_res, "__getitem__") else float("nan"))
        if not isinstance(p_value, (int, float, np.number)) or not isinstance(t_stat, (int, float, np.number)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "t-test produced non-numeric result (possibly mocked)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }
        if math.isnan(float(p_value)) or math.isnan(float(t_stat)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "t-test produced invalid result (NaN)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }
        significant = p_value < alpha
        confidence = 1.0 - float(p_value)

        return {
            "status": "verified" if significant else "rejected",
            "method": "statistical",
            "confidence": min(confidence, 1.0),
            "proof_output": f"t-statistic={t_stat:.4f}, p-value={p_value:.4e}, alpha={alpha}",
            "counterexample": None,
            "metadata": {"t_stat": float(t_stat), "p_value": float(p_value), "alpha": alpha},
        }

    def _run_chi2(self, data: dict[str, Any], alpha: float) -> dict[str, Any]:
        stats = _get_real_scipy_stats()
        if stats is None:
            return {"status": "error", "method": "statistical", "confidence": 0.0, "error_message": "scipy.stats not available or mocked", "proof_output": "", "counterexample": None, "metadata": {}}

        observed = np.array(data.get("observed", []))
        if observed.size == 0:
            return {"status": "uncertain", "method": "statistical", "confidence": 0.0, "error_message": "No observed data", "proof_output": "", "counterexample": None, "metadata": {}}

        chi2_res = stats.chi2_contingency(observed)
        chi2 = getattr(chi2_res, "statistic", chi2_res[0] if hasattr(chi2_res, "__getitem__") else float("nan"))
        p_value = getattr(chi2_res, "pvalue", chi2_res[1] if hasattr(chi2_res, "__getitem__") else float("nan"))
        dof = getattr(chi2_res, "dof", chi2_res[2] if hasattr(chi2_res, "__getitem__") and len(chi2_res) > 2 else 0)
        if not isinstance(p_value, (int, float, np.number)) or not isinstance(chi2, (int, float, np.number)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "Chi2 test produced non-numeric result (possibly mocked)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }
        if math.isnan(float(p_value)) or math.isnan(float(chi2)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "Chi2 test produced invalid result (NaN)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }
        significant = p_value < alpha

        return {
            "status": "verified" if significant else "rejected",
            "method": "statistical",
            "confidence": min(1.0 - float(p_value), 1.0),
            "proof_output": f"chi2={chi2:.4f}, p={p_value:.4e}, dof={dof}",
            "counterexample": None,
            "metadata": {"chi2": float(chi2), "p_value": float(p_value), "dof": int(dof)},
        }

    def _run_ks(self, data: dict[str, Any], alpha: float) -> dict[str, Any]:
        stats = _get_real_scipy_stats()
        if stats is None:
            return {"status": "error", "method": "statistical", "confidence": 0.0, "error_message": "scipy.stats not available or mocked", "proof_output": "", "counterexample": None, "metadata": {}}

        sample = np.array(data.get("sample", []))
        reference = data.get("reference")
        if reference == "normal":
            ks_res = stats.kstest(sample, "norm", args=(np.mean(sample), np.std(sample)))
        elif isinstance(reference, (list, np.ndarray)):
            ks_res = stats.ks_2samp(sample, np.array(reference))
        else:
            return {"status": "error", "method": "statistical", "confidence": 0.0, "error_message": "Invalid KS test reference", "proof_output": "", "counterexample": None, "metadata": {}}

        stat = getattr(ks_res, "statistic", ks_res[0] if hasattr(ks_res, "__getitem__") else float("nan"))
        p_value = getattr(ks_res, "pvalue", ks_res[1] if hasattr(ks_res, "__getitem__") else float("nan"))
        if not isinstance(p_value, (int, float, np.number)) or not isinstance(stat, (int, float, np.number)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "KS test produced non-numeric result (possibly mocked)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }
        if math.isnan(float(p_value)) or math.isnan(float(stat)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "KS test produced invalid result (NaN)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }

        significant = p_value < alpha
        return {
            "status": "verified" if significant else "rejected",
            "method": "statistical",
            "confidence": min(1.0 - float(p_value), 1.0),
            "proof_output": f"KS-statistic={stat:.4f}, p={p_value:.4e}",
            "counterexample": None,
            "metadata": {"ks_stat": float(stat), "p_value": float(p_value)},
        }

    def _run_correlation(self, data: dict[str, Any], alpha: float) -> dict[str, Any]:
        stats = _get_real_scipy_stats()
        if stats is None:
            return {"status": "error", "method": "statistical", "confidence": 0.0, "error_message": "scipy.stats not available or mocked", "proof_output": "", "counterexample": None, "metadata": {}}

        x = np.array(data.get("x", []))
        y = np.array(data.get("y", []))
        if len(x) < 3 or len(y) < 3:
            return {"status": "uncertain", "method": "statistical", "confidence": 0.0, "error_message": "Insufficient data for correlation", "proof_output": "", "counterexample": None, "metadata": {}}

        pearson_res = stats.pearsonr(x, y)
        corr = getattr(pearson_res, "statistic", pearson_res[0] if hasattr(pearson_res, "__getitem__") else float("nan"))
        p_value = getattr(pearson_res, "pvalue", pearson_res[1] if hasattr(pearson_res, "__getitem__") else float("nan"))
        if not isinstance(p_value, (int, float, np.number)) or not isinstance(corr, (int, float, np.number)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "Correlation test produced non-numeric result (possibly mocked)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }
        if math.isnan(float(p_value)) or math.isnan(float(corr)):
            return {
                "status": "uncertain",
                "method": "statistical",
                "confidence": 0.0,
                "error_message": "Correlation test produced invalid result (NaN)",
                "proof_output": "",
                "counterexample": None,
                "metadata": {},
            }
        significant = p_value < alpha
        return {
            "status": "verified" if significant else "rejected",
            "method": "statistical",
            "confidence": min(1.0 - float(p_value), 1.0),
            "proof_output": f"Pearson r={corr:.4f}, p={p_value:.4e}",
            "counterexample": None,
            "metadata": {"pearson_r": float(corr), "p_value": float(p_value)},
        }
