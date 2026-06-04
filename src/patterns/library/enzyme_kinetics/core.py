"""
Enzyme Kinetics Pattern[str] Core
Core simulation logic for enzyme kinetics models.
"""

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from .config import EnzymeKineticsConfig, KineticModel


class EnzymeKineticsSimulator:
    """Simulates enzyme kinetics for various models"""

    def __init__(self, config: EnzymeKineticsConfig) -> None:
        self.config = config

    def simulate(self) -> dict[str, Any]:
        """Run simulation based on model type"""
        if self.config.model == KineticModel.MICHAELIS_MENTEN:
            return self._michaelis_menten_simulation()
        elif self.config.model == KineticModel.BRIGGS_HALDANE:
            return self._briggs_haldane_simulation()
        elif self.config.model == KineticModel.COMPETITIVE_INHIBITION:
            return self._competitive_inhibition_simulation()
        elif self.config.model == KineticModel.HILL:
            return self._hill_simulation()
        else:
            return self._mwc_simulation()

    def _michaelis_menten_simulation(self) -> dict[str, Any]:
        """Michaelis-Menten kinetics simulation"""
        cfg = self.config

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.P0]

        def mm_kinetics(t: Any, y: Any) -> Any:
            """Mm kinetics."""
            S, P = y
            v = cfg.Vmax * S / (cfg.Km + S)
            dSdt = -v
            dPdt = v
            return [dSdt, dPdt]

        solution = solve_ivp(mm_kinetics, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        S = solution.y[0]
        P = solution.y[1]
        v = cfg.Vmax * S / (cfg.Km + S)

        S_range = np.logspace(np.log10(cfg.substrate_range[0]),
                               np.log10(cfg.substrate_range[1]), cfg.num_points)
        v_curve = cfg.Vmax * S_range / (cfg.Km + S_range)

        inv_S = 1 / S_range
        inv_v = 1 / v_curve

        metrics = self._calculate_mm_metrics(t, S, P, v, S_range, v_curve)

        logs = [
            "Michaelis-Menten simulation completed",
            f"Parameters: Vmax={cfg.Vmax:.2f} uM/s, Km={cfg.Km:.2f} uM",
            f"Initial substrate: {cfg.S0:.2f} uM",
            f"Final product: {P[-1]:.2f} uM",
            f"Initial velocity: {v[0]:.4f} uM/s",
            f"Km from fit: {metrics['fitted_Km']:.2f} uM",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "velocity": v.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v": v_curve.tolist(),
            "lineweaver_S": inv_S.tolist(),
            "lineweaver_v": inv_v.tolist(),
        }

    def _briggs_haldane_simulation(self) -> dict[str, Any]:
        """Briggs-Haldane (explicit intermediate) simulation"""
        cfg = self.config

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.ES0, cfg.P0]

        def bh_kinetics(t: Any, y: Any) -> Any:
            """Bh kinetics."""
            S, ES, P = y
            E = cfg.E0 - ES

            dSdt = -cfg.k1 * E * S + cfg.k_1 * ES
            dESdt = cfg.k1 * E * S - cfg.k_1 * ES - cfg.k2 * ES
            dPdt = cfg.k2 * ES

            return [dSdt, dESdt, dPdt]

        solution = solve_ivp(bh_kinetics, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        S = solution.y[0]
        ES = solution.y[1]
        P = solution.y[2]
        E = cfg.E0 - ES

        apparent_Vmax = cfg.k2 * cfg.E0
        apparent_Km = (cfg.k_1 + cfg.k2) / cfg.k1

        metrics = {
            "apparent_Vmax": apparent_Vmax,
            "apparent_Km": apparent_Km,
            "k1": cfg.k1,
            "k_1": cfg.k_1,
            "k2": cfg.k2,
            "final_product": float(P[-1]),
            "final_substrate": float(S[-1]),
            "max_ES": float(np.max(ES)),
            "model": "briggs_haldane",
        }

        logs = [
            "Briggs-Haldane simulation completed",
            f"Rate constants: k1={cfg.k1}, k-1={cfg.k_1}, k2={cfg.k2}",
            f"Apparent Vmax: {apparent_Vmax:.2f} uM/s",
            f"Apparent Km: {apparent_Km:.2f} uM",
            f"Max ES complex: {metrics['max_ES']:.4f} uM",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "enzyme_substrate": ES.tolist(),
            "free_enzyme": E.tolist(),
            "product": P.tolist(),
        }

    def _competitive_inhibition_simulation(self) -> dict[str, Any]:
        """Competitive inhibition simulation"""
        cfg = self.config

        def inhibited_rate(S: Any, I: Any) -> Any:
            """Inhibited rate."""
            alpha = 1 + I / cfg.Ki
            Km_app = cfg.Km * alpha
            return cfg.Vmax * S / (Km_app + S)

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.P0]

        def inhibited_kinetics(t: Any, y: Any) -> Any:
            """Inhibited kinetics."""
            S, P = y
            v = inhibited_rate(S, cfg.I0)
            return [-v, v]

        solution = solve_ivp(inhibited_kinetics, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        S = solution.y[0]
        P = solution.y[1]
        v = np.array([inhibited_rate(s, cfg.I0) for s in S])

        S_range = np.linspace(cfg.substrate_range[0], cfg.substrate_range[1], cfg.num_points)
        v_no_inhibitor = cfg.Vmax * S_range / (cfg.Km + S_range)
        v_with_inhibitor = [inhibited_rate(s, cfg.I0) for s in S_range]

        alpha = 1 + cfg.I0 / cfg.Ki
        Km_app = cfg.Km * alpha

        metrics = {
            "Vmax": cfg.Vmax,
            "Km": cfg.Km,
            "Km_apparent": Km_app,
            "inhibition_factor": alpha,
            "I0": cfg.I0,
            "Ki": cfg.Ki,
            "percent_inhibition": (1 - v[-1] / (cfg.Vmax * S[-1] / (cfg.Km + S[-1]))) * 100,
            "model": "competitive_inhibition",
        }

        logs = [
            "Competitive inhibition simulation completed",
            f"[I] = {cfg.I0:.2f} uM, Ki = {cfg.Ki:.2f} uM",
            f"Apparent Km: {Km_app:.2f} uM (factor: {alpha:.2f})",
            f"Vmax unchanged: {cfg.Vmax:.2f} uM/s",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "velocity": v.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v_control": v_no_inhibitor.tolist(),
            "saturation_v_inhibited": v_with_inhibitor,
        }

    def _hill_simulation(self) -> dict[str, Any]:
        """Hill equation (cooperative binding) simulation"""
        cfg = self.config

        def hill_rate(S: Any) -> Any:
            return cfg.Vmax * S**cfg.n / (cfg.Kd**cfg.n + S**cfg.n)

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.P0]

        def hill_kinetics(t: Any, y: Any) -> Any:
            """Hill kinetics."""
            S, P = y
            v = hill_rate(S)
            return [-v, v]

        solution = solve_ivp(hill_kinetics, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        S = solution.y[0]
        P = solution.y[1]

        S_range = np.logspace(np.log10(cfg.substrate_range[0]),
                               np.log10(cfg.substrate_range[1]), cfg.num_points)
        v_curve = [hill_rate(s) for s in S_range]

        EC50 = cfg.Kd

        Y = np.array(v_curve) / cfg.Vmax
        log_S = np.log10(S_range[Y > 0.01])
        logit_Y = np.log10(Y[Y > 0.01] / (1 - Y[Y > 0.01]))

        if len(log_S) > 2:
            hill_slope = np.polyfit(log_S, logit_Y, 1)[0]
        else:
            hill_slope = cfg.n

        metrics = {
            "Vmax": cfg.Vmax,
            "n": cfg.n,
            "Kd": cfg.Kd,
            "EC50": EC50,
            "hill_slope_fitted": hill_slope,
            "cooperativity": "positive" if cfg.n > 1 else ("negative" if cfg.n < 1 else "none"),
            "final_product": float(P[-1]),
            "model": "hill",
        }

        logs = [
            "Hill equation simulation completed",
            f"Hill coefficient n = {cfg.n:.2f}",
            f"Kd = {cfg.Kd:.2f} uM, EC50 = {EC50:.2f} uM",
            f"Cooperativity: {metrics['cooperativity']}",
            f"Fitted Hill slope: {hill_slope:.2f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v": v_curve,
            "hill_plot_x": log_S.tolist(),
            "hill_plot_y": logit_Y.tolist(),
        }

    def _mwc_simulation(self) -> dict[str, Any]:
        """Monod-Wyman-Changeux allosteric model"""
        cfg = self.config

        def mwc_fraction_active(S: Any) -> Any:
            """Mwc fraction active."""
            L = cfg.L
            c = cfg.c
            n = cfg.n

            alpha = S / cfg.Kd

            Y = (alpha * (1 + alpha)**(n-1) + L * c * alpha * (1 + c * alpha)**(n-1)) / \
                ((1 + alpha)**n + L * (1 + c * alpha)**n)

            return Y

        S_range = np.logspace(np.log10(cfg.substrate_range[0]),
                               np.log10(cfg.substrate_range[1]), cfg.num_points)
        fraction_active = [mwc_fraction_active(s) for s in S_range]
        v_curve = [cfg.Vmax * f for f in fraction_active]

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        y0 = [cfg.S0, cfg.P0]

        def mwc_kinetics(t: Any, y: Any) -> Any:
            """Mwc kinetics."""
            S, P = y
            f = mwc_fraction_active(S)
            v = cfg.Vmax * f
            return [-v, v]

        solution = solve_ivp(mwc_kinetics, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        S = solution.y[0]
        P = solution.y[1]

        metrics = {
            "Vmax": cfg.Vmax,
            "L": cfg.L,
            "c": cfg.c,
            "n": cfg.n,
            "Kd": cfg.Kd,
            "T0_R0_ratio": cfg.L,
            "final_product": float(P[-1]),
            "model": "mwc",
        }

        logs = [
            "MWC allosteric model simulation completed",
            f"Allosteric constant L = {cfg.L:.2f}",
            f"Non-exclusive binding c = {cfg.c:.4f}",
            f"T0/R0 ratio: {cfg.L:.2f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "substrate": S.tolist(),
            "product": P.tolist(),
            "saturation_S": S_range.tolist(),
            "saturation_v": v_curve,
            "fraction_active": fraction_active,
        }

    def _calculate_mm_metrics(
        self, t: np.ndarray, S: np.ndarray, P: np.ndarray,
        v: np.ndarray, S_range: np.ndarray, v_curve: np.ndarray
    ) -> dict[str, float]:
        """Calculate Michaelis-Menten metrics"""

        inv_S = 1 / S_range[S_range > 0]
        inv_v = 1 / np.array(v_curve)[S_range > 0]

        if len(inv_S) > 2:
            slope, intercept = np.polyfit(inv_S, inv_v, 1)
            fitted_Vmax = 1 / intercept if intercept > 0 else self.config.Vmax
            fitted_Km = slope / intercept if intercept > 0 else self.config.Km
        else:
            fitted_Vmax = self.config.Vmax
            fitted_Km = self.config.Km

        v0 = float(v[0]) if len(v) > 0 else 0
        S_final = float(S[-1]) if len(S) > 0 else 0
        P_final = float(P[-1]) if len(P) > 0 else 0

        extent = (self.config.S0 - S_final) / self.config.S0 if self.config.S0 > 0 else 0
        catalytic_efficiency = fitted_Vmax / fitted_Km if fitted_Km > 0 else 0

        return {
            "fitted_Vmax": fitted_Vmax,
            "fitted_Km": fitted_Km,
            "input_Vmax": self.config.Vmax,
            "input_Km": self.config.Km,
            "initial_velocity": v0,
            "final_substrate": S_final,
            "final_product": P_final,
            "reaction_extent": extent,
            "catalytic_efficiency": catalytic_efficiency,
            "model": "michaelis_menten",  # type: ignore[dict-item]
        }
