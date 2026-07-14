"""
Signal Transduction Models
ODE-based implementations of various signaling pathways

Based on:
- MAPK cascade (Huang-Ferrell, 1996)
- GPCR signaling (Kenakin, 2009)
- Adaptation and oscillations
"""

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks

from .config import SignalTransductionConfig


class MAPKModel:
    """MAPK cascade (Huang-Ferrell) simulation"""

    def __init__(self, config: SignalTransductionConfig) -> None:
        self.config = config

    def simulate(self) -> dict[str, Any]:
        """Run MAPK cascade simulation"""
        cfg = self.config

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        # Initial conditions: all inactive
        y0 = [0.0, 0.0, 0.0, 0.0, 0.0]

        def mapk_equations(t: Any, y: Any) -> Any:
            """Mapk equations."""
            MKKK_star, MKK_P, MKK_PP, MK_P, MK_PP = y

            MKKK = cfg.E1_total - MKKK_star
            MKK = cfg.MAPKK_total - MKK_P - MKK_PP
            MK = cfg.MAPK_total - MK_P - MK_PP

            # MAPKKK activation
            dMKKK_star = (cfg.k1 * cfg.E1_total * MKKK - cfg.k2 * MKKK_star)

            # MAPKK phosphorylation (two steps)
            v1 = cfg.k1 * MKKK_star * MKK
            v2 = cfg.k2 * MKK_P
            v3 = cfg.k3 * MKKK_star * MKK_P
            v4 = cfg.k4 * MKK_PP

            dMKK_P = v1 - v2 - v3 + v4
            dMKK_PP = v3 - v4

            # MAPK phosphorylation (two steps)
            w1 = cfg.k1 * MKK_PP * MK
            w2 = cfg.k2 * MK_P
            w3 = cfg.k3 * MKK_PP * MK_P
            w4 = cfg.k4 * MK_PP

            dMK_P = w1 - w2 - w3 + w4
            dMK_PP = w3 - w4

            return [dMKKK_star, dMKK_P, dMKK_PP, dMK_P, dMK_PP]

        solution = solve_ivp(mapk_equations, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        MKKK_star = solution.y[0]
        MKK_PP = solution.y[2]
        MK_PP = solution.y[4]

        dose_response = self._calculate_dose_response()
        hill_n = self._estimate_hill_coefficient(dose_response)

        metrics = {
            "final_MAPKKK_active": float(MKKK_star[-1]),
            "final_MAPKK_PP": float(MKK_PP[-1]),
            "final_MAPK_PP": float(MK_PP[-1]),
            "max_MAPK_PP": float(np.max(MK_PP)),
            "amplification_factor": float(MK_PP[-1] / MKKK_star[-1]) if MKKK_star[-1] > 0 else 0,
            "hill_coefficient": hill_n,
            "model": "mapk_cascade",
        }

        logs = [
            "MAPK cascade simulation completed",
            f"Final MAPK-PP: {metrics['final_MAPK_PP']:.4f} uM",
            f"Max MAPK-PP: {metrics['max_MAPK_PP']:.4f} uM",
            f"Amplification factor: {metrics['amplification_factor']:.2f}",
            f"Estimated Hill coefficient: {hill_n:.2f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "MAPKKK_star": MKKK_star.tolist(),
            "MAPKK_PP": MKK_PP.tolist(),
            "MAPK_PP": MK_PP.tolist(),
            "dose_response": dose_response,
        }

    def _calculate_dose_response(self) -> dict[str, list[float]]:
        """Calculate MAPK cascade dose-response curve"""
        cfg = self.config

        e1_levels = np.logspace(-3, 0, cfg.num_stimulus_levels)
        responses = []

        for e1 in e1_levels:
            t_span = (0, 1000)
            y0 = [0.0, 0.0, 0.0, 0.0, 0.0]

            def eq(t: Any, y: Any, stim: Any=e1) -> Any:
                """Eq."""
                MKKK_star, MKK_P, MKK_PP, MK_P, MK_PP = y
                MKKK = stim - MKKK_star
                MKK = cfg.MAPKK_total - MKK_P - MKK_PP
                MK = cfg.MAPK_total - MK_P - MK_PP

                dMKKK_star = (cfg.k1 * stim * MKKK - cfg.k2 * MKKK_star)
                v1 = cfg.k1 * MKKK_star * MKK
                v2 = cfg.k2 * MKK_P
                v3 = cfg.k3 * MKKK_star * MKK_P
                v4 = cfg.k4 * MKK_PP
                dMKK_P = v1 - v2 - v3 + v4
                dMKK_PP = v3 - v4
                w1 = cfg.k1 * MKK_PP * MK
                w2 = cfg.k2 * MK_P
                w3 = cfg.k3 * MKK_PP * MK_P
                w4 = cfg.k4 * MK_PP
                dMK_P = w1 - w2 - w3 + w4
                dMK_PP = w3 - w4
                return [dMKKK_star, dMKK_P, dMKK_PP, dMK_P, dMK_PP]

            sol = solve_ivp(eq, t_span, y0, method='RK45')
            responses.append(float(sol.y[4][-1]))

        return {
            "stimulus_levels": e1_levels.tolist(),
            "responses": responses,
        }

    def _estimate_hill_coefficient(self, dose_response: dict[str, list[float]]) -> float:
        """Estimate Hill coefficient from dose-response"""
        S = np.array(dose_response["stimulus_levels"])
        R = np.array(dose_response["responses"])

        if len(S) < 3 or np.max(R) == 0:
            return 1.0

        R_norm = R / np.max(R)

        try:
            ec10_idx = np.where(R_norm >= 0.1)[0][0]
            ec90_idx = np.where(R_norm >= 0.9)[0][0]
            ec10 = S[ec10_idx]
            ec90 = S[ec90_idx]

            n = 2 * np.log10(81) / np.log10(ec90 / ec10) if ec90 > ec10 else 1.0
            return float(n)
        except (ValueError, IndexError, ZeroDivisionError):
            return 1.0

class GPCRModel:
    """GPCR signaling simulation"""

    def __init__(self, config: SignalTransductionConfig) -> None:
        self.config = config

    def simulate(self) -> dict[str, Any]:
        """Run GPCR simulation"""
        cfg = self.config

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        # State: [RL, Ga_GTP, Gbg]
        y0 = [0.0, 0.0, 0.0]

        def gpcr_equations(t: Any, y: Any) -> Any:
            """Gpcr equations."""
            RL, Ga_GTP, Gbg = y
            R = cfg.R_total - RL
            L = cfg.ligand_conc
            G = cfg.G_total - Ga_GTP - Gbg

            ka = 1e6
            kd = 0.1
            k_act = 1.0
            k_hyd = 0.1

            dRL = ka * R * L - kd * RL
            dGa_GTP = k_act * RL * G - k_hyd * Ga_GTP
            dGbg = k_act * RL * G - k_hyd * Gbg

            return [dRL, dGa_GTP, dGbg]

        solution = solve_ivp(gpcr_equations, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        RL = solution.y[0]
        Ga_GTP = solution.y[1]

        metrics = {
            "final_receptor_occupancy": float(RL[-1] / cfg.R_total),
            "final_G_protein_active": float(Ga_GTP[-1] / cfg.G_total),
            "max_response": float(np.max(Ga_GTP)),
            "EC50_approx": cfg.ligand_conc * (0.5 / (RL[-1]/cfg.R_total)) if RL[-1] > 0 else cfg.ligand_conc,
            "model": "gpcr",
        }

        logs = [
            "GPCR simulation completed",
            f"Ligand concentration: {cfg.ligand_conc:.4f} uM",
            f"Receptor occupancy: {metrics['final_receptor_occupancy']*100:.1f}%",
            f"Active G-protein: {metrics['final_G_protein_active']*100:.1f}%",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "receptor_ligand": RL.tolist(),
            "active_G_protein": Ga_GTP.tolist(),
        }

class AdaptationModel:
    """Adaptation model (perfect or near-perfect)"""

    def __init__(self, config: SignalTransductionConfig) -> None:
        self.config = config

    def simulate(self) -> dict[str, Any]:
        """Run adaptation simulation"""
        cfg = self.config

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        # State: [X (response), X_m (modified)]
        y0 = [0.0, 0.0]

        def adaptation_equations(t: Any, y: Any) -> Any:
            """Adaptation equations."""
            X, X_m = y

            S = cfg.stimulus_amp if t < cfg.stimulus_duration else 0

            k_r = 0.1
            k_m = 0.1
            k_dem = 0.01

            dX = k_r * S * (1 - X) - k_m * X
            dX_m = k_m * X - k_dem * X_m

            return [dX, dX_m]

        solution = solve_ivp(adaptation_equations, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        X = solution.y[0]
        X_m = solution.y[1]

        peak_response = float(np.max(X))
        steady_response = float(X[-1]) if t[-1] > cfg.stimulus_duration else 0
        adaptation_error = abs(steady_response) / peak_response if peak_response > 0 else 0

        metrics = {
            "peak_response": peak_response,
            "steady_state_response": steady_response,
            "adaptation_error": adaptation_error,
            "adaptation_quality": "perfect" if adaptation_error < 0.05 else "partial",
            "model": "adaptation",
        }

        logs = [
            "Adaptation simulation completed",
            f"Peak response: {peak_response:.4f}",
            f"Steady-state: {steady_response:.4f}",
            f"Adaptation: {metrics['adaptation_quality']}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "response": X.tolist(),
            "modified": X_m.tolist(),
        }

class RepressilatorModel:
    """Repressilator (Elowitz-Leibler) simulation"""

    def __init__(self, config: SignalTransductionConfig) -> None:
        self.config = config

    def simulate(self) -> dict[str, Any]:
        """Run repressilator simulation"""
        cfg = self.config
        n = cfg.n_genes

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        y0 = [0.0] * (2 * n)
        y0[0] = 0.1

        def repressilator_equations(t: Any, y: Any) -> Any:
            """Repressilator equations."""
            dydt = []
            for i in range(n):
                m = y[2*i]
                p = y[2*i + 1]
                p_prev = y[(2*((i-1)%n) + 1)]

                repression = cfg.alpha / (1 + p_prev**cfg.n_hill)

                dm = repression - cfg.beta * m
                dp = m - p

                dydt.extend([dm, dp])

            return dydt

        solution = solve_ivp(repressilator_equations, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        proteins = [solution.y[2*i + 1] for i in range(n)]

        periods = []
        for p in proteins:
            peaks = self._find_peaks(t, p)
            if len(peaks) > 1:
                periods.append(np.mean(np.diff(peaks)))

        avg_period = float(np.mean(periods)) if periods else 0

        metrics = {
            "num_genes": n,
            "period": avg_period,
            "oscillation_detected": len(periods) > 0 and avg_period > 0,
            "mean_protein_1": float(np.mean(proteins[0])),
            "max_protein_1": float(np.max(proteins[0])),
            "model": "repressilator",
        }

        logs = [
            "Repressilator simulation completed",
            f"Genes in ring: {n}",
            f"Oscillation period: {avg_period:.2f} s" if avg_period > 0 else "No clear oscillation",
            f"Oscillation detected: {metrics['oscillation_detected']}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "proteins": [p.tolist() for p in proteins],
        }

    def _find_peaks(self, t: np.ndarray, signal: np.ndarray) -> list[float]:
        """Find peak times in signal"""
        peaks, _ = find_peaks(signal, height=np.mean(signal))
        return [t[p] for p in peaks]

class ToggleSwitchModel:
    """Genetic toggle switch (Gardner-Collins) simulation"""

    def __init__(self, config: SignalTransductionConfig) -> None:
        self.config = config

    def simulate(self) -> dict[str, Any]:
        """Run toggle switch simulation"""
        cfg = self.config

        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)

        y0 = [0.1, 0.5]

        def toggle_equations(t: Any, y: Any) -> Any:
            """Toggle equations."""
            u, v = y

            du = cfg.alpha / (1 + v**cfg.n_hill) - u
            dv = cfg.alpha / (1 + u**cfg.n_hill) - v

            return [du, dv]

        solution = solve_ivp(toggle_equations, t_span, y0, t_eval=t_eval, method='RK45')

        t = solution.t
        u = solution.y[0]
        v = solution.y[1]

        # Check bistability with reversed initial conditions
        y0_rev = [0.5, 0.1]
        sol_rev = solve_ivp(toggle_equations, t_span, y0_rev, t_eval=t_eval, method='RK45')
        u_rev = sol_rev.y[0]
        v_rev = sol_rev.y[1]

        bistable = abs(u[-1] - u_rev[-1]) > 0.1 and abs(v[-1] - v_rev[-1]) > 0.1

        metrics = {
            "final_u": float(u[-1]),
            "final_v": float(v[-1]),
            "bistable": bistable,
            "steady_state": "high_u" if u[-1] > v[-1] else "high_v",
            "switching_possible": bistable,
            "model": "toggle_switch",
        }

        logs = [
            "Toggle switch simulation completed",
            f"Bistability: {bistable}",
            f"Final state: u={metrics['final_u']:.4f}, v={metrics['final_v']:.4f}",
            f"Dominant protein: {metrics['steady_state']}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "protein_1": u.tolist(),
            "protein_2": v.tolist(),
            "protein_1_alt": u_rev.tolist(),
            "protein_2_alt": v_rev.tolist(),
        }
