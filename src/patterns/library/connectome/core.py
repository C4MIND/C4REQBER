"""
Connectome Pattern[str] Core
Core simulation logic for brain network dynamics.
"""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np

from .config import ConnectomeConfig


class ConnectomeSimulator:
    """Simulates whole-brain connectome dynamics"""

    def __init__(self, config: ConnectomeConfig, rng: np.random.Generator) -> None:
        self.config = config
        self.rng = rng
        self.structural_connectivity: np.ndarray | None = None

    def generate_connectivity(self) -> np.ndarray:
        """Generate synthetic structural connectivity matrix"""
        cfg = self.config
        N = cfg.num_regions

        # Base connectivity (sparse random)
        SC = self.rng.random((N, N))
        SC = (SC < cfg.connection_density).astype(float)

        # Remove self-connections
        np.fill_diagonal(SC, 0)

        # Make symmetric (undirected)
        SC = (SC + SC.T) / 2
        SC = (SC > 0).astype(float)

        # Add weights (log-normal distribution)
        weights = np.exp(self.rng.normal(0, 1, (N, N)))
        SC = SC * weights

        # Normalize rows
        row_sums = SC.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        SC = SC / row_sums

        self.structural_connectivity = SC
        return SC  # type: ignore[no-any-return]

    async def run_kuramoto(self) -> dict[str, Any]:
        """Kuramoto oscillator model on connectome"""
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity

        # Initialize phases
        theta = self.rng.uniform(0, 2*np.pi, N)

        # Intrinsic frequencies
        omega = self.rng.normal(cfg.omega_mean * 2 * np.pi, cfg.omega_std * 2 * np.pi, N)

        t_max = cfg.t_max
        dt = cfg.dt
        n_steps = int(t_max / dt)
        transient_steps = int(cfg.transient / dt)

        theta_history = []

        for step in range(n_steps):
            t = step * dt

            # Stimulation
            stim = 0.0
            if cfg.stimulation_site is not None and cfg.stimulation_amp > 0:
                stim = cfg.stimulation_amp * np.sin(2 * np.pi * cfg.stimulation_freq * t)

            # Phase differences
            phase_diff = theta[:, None] - theta[None, :]

            # Kuramoto dynamics
            dtheta = omega + cfg.coupling_strength * (SC * np.sin(phase_diff)).sum(axis=1)
            dtheta += self.rng.normal(0, cfg.noise_level, N)

            if cfg.stimulation_site is not None:
                dtheta[cfg.stimulation_site] += stim

            theta += dtheta * dt
            theta = np.mod(theta, 2 * np.pi)

            if step >= transient_steps:
                theta_history.append(theta.copy())

            if step % 1000 == 0:
                await asyncio.sleep(0)

        theta_arr = np.array(theta_history)

        # Calculate functional connectivity (phase synchronization)
        fc = self._calculate_fc_kuramoto(theta_arr)

        # Calculate order parameters
        order_global, order_local = self._calculate_order_parameters(theta_arr, SC)  # type: ignore[arg-type]

        metrics = self._calculate_network_metrics(theta_arr, fc, SC, order_global, order_local)

        logs = [
            "Kuramoto connectome simulation completed",
            f"Network: {N} regions, {np.sum(SC > 0)//2} connections",  # type: ignore[operator]
            f"Global order parameter: {np.mean(order_global):.4f}",
            f"Mean FC correlation: {metrics['fc_mean']:.4f}",
            f"FC variance: {metrics['fc_variance']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "functional_connectivity": fc.tolist(),
            "structural_connectivity": SC.tolist(),  # type: ignore[union-attr]
            "order_global": order_global.tolist(),
        }

    def _calculate_fc_kuramoto(self, theta: np.ndarray) -> np.ndarray:
        """Calculate functional connectivity from phase time series"""
        N = theta.shape[1]
        fc = np.zeros((N, N))

        for i in range(N):
            for j in range(i+1, N):
                phase_diff = theta[:, i] - theta[:, j]
                plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                fc[i, j] = plv
                fc[j, i] = plv

        return fc

    def _calculate_order_parameters(
        self, theta: np.ndarray, SC: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Calculate global and local order parameters"""
        N = theta.shape[1]

        r_global = np.abs(np.mean(np.exp(1j * theta), axis=1))

        r_local = np.zeros(len(theta))
        for t in range(len(theta)):
            for i in range(N):
                neighbors = SC[i] > 0
                if np.sum(neighbors) > 0:
                    r_local[t] += np.abs(np.mean(np.exp(1j * theta[t, neighbors])))
            r_local[t] /= N

        return r_global, r_local

    async def run_wilson_cowan(self) -> dict[str, Any]:
        """Wilson-Cowan firing rate model"""
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity

        E = self.rng.uniform(0, 0.1, N)
        I = self.rng.uniform(0, 0.1, N)

        n_steps = int(cfg.t_max / cfg.dt)
        transient_steps = int(cfg.transient / cfg.dt)

        E_history = []

        for step in range(n_steps):
            coupling = cfg.coupling_strength * (SC @ E)  # type: ignore[operator]

            S_E = 1 / (1 + np.exp(-(E - I + coupling - 4)))
            S_I = 1 / (1 + np.exp(-(E - I - 2)))

            dE = (-E + S_E) / cfg.tau_exc * cfg.dt
            dI = (-I + S_I) / cfg.tau_inh * cfg.dt

            E += dE
            I += dI

            E += self.rng.normal(0, cfg.noise_level, N)
            I += self.rng.normal(0, cfg.noise_level, N)

            E = np.clip(E, 0, 1)
            I = np.clip(I, 0, 1)

            if step >= transient_steps:
                E_history.append(E.copy())

            if step % 1000 == 0:
                await asyncio.sleep(0)

        E_arr = np.array(E_history)
        fc = np.corrcoef(E_arr.T)

        metrics = {
            "mean_activity": float(np.mean(E_arr)),
            "fc_mean": float(np.mean(fc[np.triu_indices_from(fc, k=1)])),
            "fc_variance": float(np.var(fc[np.triu_indices_from(fc, k=1)])),
            "model": "wilson_cowan",
        }

        logs = [
            "Wilson-Cowan connectome simulation completed",
            f"Mean activity: {metrics['mean_activity']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "functional_connectivity": fc.tolist(),
        }

    async def run_hopf(self) -> dict[str, Any]:
        """Hopf bifurcation model"""
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity

        z = self.rng.normal(0, 0.1, N) + 1j * self.rng.normal(0, 0.1, N)

        n_steps = int(cfg.t_max / cfg.dt)
        transient_steps = int(cfg.transient / cfg.dt)

        z_history = []

        for step in range(n_steps):
            omega = cfg.omega_mean * 2 * np.pi
            coupling = cfg.coupling_strength * (SC @ z)
            noise = self.rng.normal(0, cfg.noise_level, N) + 1j * self.rng.normal(0, cfg.noise_level, N)

            dz = (cfg.a + 1j * omega) * z - np.abs(z)**2 * z + coupling + noise
            z += dz * cfg.dt

            if step >= transient_steps:
                z_history.append(z.copy())

            if step % 1000 == 0:
                await asyncio.sleep(0)

        z_arr = np.array(z_history)
        x_arr = np.real(z_arr)

        fc = np.corrcoef(x_arr.T)

        metrics = {
            "mean_amplitude": float(np.mean(np.abs(z_arr))),
            "fc_mean": float(np.mean(fc[np.triu_indices_from(fc, k=1)])),
            "model": "hopf",
        }

        logs = [
            "Hopf connectome simulation completed",
            f"Mean amplitude: {metrics['mean_amplitude']:.4f}",
        ]

        return {
            "metrics": metrics,
            "logs": logs,
            "functional_connectivity": fc.tolist(),
        }

    async def run_fitzhugh_nagumo(self) -> dict[str, Any]:
        """FitzHugh-Nagumo model on network"""
        cfg = self.config
        N = cfg.num_regions
        SC = self.structural_connectivity

        v = self.rng.normal(-1, 0.1, N)
        w = self.rng.normal(0, 0.1, N)

        a, b, c = 0.7, 0.8, 3.0
        I = 0.5

        n_steps = int(cfg.t_max / cfg.dt)
        transient_steps = int(cfg.transient / cfg.dt)

        v_history = []

        for step in range(n_steps):
            coupling = cfg.coupling_strength * (SC @ v)  # type: ignore[operator]

            dv = (c * (v - v**3/3 + w + I) + coupling) * cfg.dt
            dw = (-(v - a + b * w) / c) * cfg.dt

            v += dv
            w += dw

            if step >= transient_steps:
                v_history.append(v.copy())

            if step % 1000 == 0:
                await asyncio.sleep(0)

        v_arr = np.array(v_history)
        fc = np.corrcoef(v_arr.T)

        metrics = {
            "mean_activity": float(np.mean(v_arr)),
            "fc_mean": float(np.mean(fc[np.triu_indices_from(fc, k=1)])),
            "model": "fitzhugh_nagumo",
        }

        return {
            "metrics": metrics,
            "logs": ["FitzHugh-Nagumo connectome simulation completed"],
            "functional_connectivity": fc.tolist(),
        }

    def calculate_network_metrics(
        self, activity: np.ndarray, fc: np.ndarray,
        sc: np.ndarray, order_global: np.ndarray, order_local: np.ndarray
    ) -> dict[str, float]:
        """Calculate network metrics"""

        fc_triu = fc[np.triu_indices_from(fc, k=1)]
        fc_mean = float(np.mean(fc_triu))
        fc_var = float(np.var(fc_triu))

        sc_triu = sc[np.triu_indices_from(sc, k=1)]
        if np.std(sc_triu) > 0 and np.std(fc_triu) > 0:
            sc_fc_corr = float(np.corrcoef(sc_triu, fc_triu)[0, 1])
        else:
            sc_fc_corr = 0.0

        mean_order = float(np.mean(order_global))
        var_order = float(np.var(order_global))
        metastability = float(np.std(order_global))

        return {
            "fc_mean": fc_mean,
            "fc_variance": fc_var,
            "sc_fc_correlation": sc_fc_corr,
            "mean_order_parameter": mean_order,
            "order_variance": var_order,
            "metastability": metastability,
            "integration": fc_mean,
            "segregation": fc_var,
            "mean_activity": float(np.mean(activity)),
            "activity_variance": float(np.var(activity)),
        }

    def _calculate_network_metrics(self, *args: Any, **kwargs: Any) -> Any:
        """Alias for calculate_network_metrics"""
        return self.calculate_network_metrics(*args, **kwargs)
