"""
Plasma PIC Pattern[str] Core
Core simulation logic for Particle-in-Cell method.
"""


import numpy as np
from scipy.fft import fft, fftfreq, ifft

from .config import Particle, PICConfig


class PICSolver:
    """Particle-in-Cell simulation solver"""

    def __init__(self, config: PICConfig, q_e: float, m_e: float, eps0: float, k_B: float) -> None:
        self.config = config
        self.q_e = q_e
        self.m_e = m_e
        self.eps0 = eps0
        self.k_B = k_B
        self.particles: list[Particle] = []

    def initialize_particles_1d(self) -> None:
        """Initialize particles for 1D simulation"""
        self.particles = []
        cfg = self.config

        n_per_species = cfg.n_particles // cfg.n_species

        v_th_e = np.sqrt(self.k_B * cfg.Te * 11604 / self.m_e)
        v_th_i = np.sqrt(self.k_B * cfg.Ti * 11604 / (cfg.ion_mass_ratio * self.m_e))

        # Electrons (species 0)
        for _i in range(n_per_species):
            x = np.random.uniform(0, cfg.Lx)
            vx = np.random.normal(0, v_th_e)
            p = Particle(x=x, vx=vx, charge=-1.0, mass=1.0, weight=1.0)
            self.particles.append(p)

        # Ions (species 1)
        for _i in range(n_per_species):
            x = np.random.uniform(0, cfg.Lx)
            vx = np.random.normal(0, v_th_i)
            p = Particle(x=x, vx=vx, charge=1.0, mass=cfg.ion_mass_ratio, weight=1.0)
            self.particles.append(p)

    def initialize_particles_2d(self) -> None:
        """Initialize particles for 2D simulation"""
        self.particles = []
        cfg = self.config

        n_per_species = cfg.n_particles // cfg.n_species

        v_th_e = np.sqrt(self.k_B * cfg.Te * 11604 / self.m_e)
        v_th_i = np.sqrt(self.k_B * cfg.Ti * 11604 / (cfg.ion_mass_ratio * self.m_e))

        # Electrons
        for _i in range(n_per_species):
            x = np.random.uniform(0, cfg.Lx)
            y = np.random.uniform(0, cfg.Ly)
            vx = np.random.normal(0, v_th_e)
            vy = np.random.normal(0, v_th_e)
            p = Particle(x=x, y=y, vx=vx, vy=vy, charge=-1.0, mass=1.0, weight=1.0)
            self.particles.append(p)

        # Ions
        for _i in range(n_per_species):
            x = np.random.uniform(0, cfg.Lx)
            y = np.random.uniform(0, cfg.Ly)
            vx = np.random.normal(0, v_th_i)
            vy = np.random.normal(0, v_th_i)
            p = Particle(x=x, y=y, vx=vx, vy=vy, charge=1.0, mass=cfg.ion_mass_ratio, weight=1.0)
            self.particles.append(p)

    def deposit_charge_1d(self) -> np.ndarray:
        """Charge deposition (Cloud-in-Cell) for 1D"""
        cfg = self.config
        rho = np.zeros(cfg.nx)
        dx = cfg.dx

        for p in self.particles:
            i = int(p.x / dx) % cfg.nx
            i_next = (i + 1) % cfg.nx

            dx_i = p.x - i * dx
            w1 = 1 - dx_i / dx
            w2 = dx_i / dx

            charge_density = p.charge * self.q_e * p.weight
            rho[i] += w1 * charge_density
            rho[i_next] += w2 * charge_density

        return rho / dx

    def deposit_charge_2d(self) -> np.ndarray:
        """Charge deposition (Cloud-in-Cell) for 2D"""
        cfg = self.config
        rho = np.zeros((cfg.nx, cfg.ny))
        dx, dy = cfg.dx, cfg.dy

        for p in self.particles:
            i = int(p.x / dx) % cfg.nx
            j = int(p.y / dy) % cfg.ny

            i_next = (i + 1) % cfg.nx
            j_next = (j + 1) % cfg.ny

            dx_i = p.x - i * dx
            dy_j = p.y - j * dy

            wx1 = 1 - dx_i / dx
            wx2 = dx_i / dx
            wy1 = 1 - dy_j / dy
            wy2 = dy_j / dy

            charge_density = p.charge * self.q_e * p.weight

            rho[i, j] += wx1 * wy1 * charge_density
            rho[i_next, j] += wx2 * wy1 * charge_density
            rho[i, j_next] += wx1 * wy2 * charge_density
            rho[i_next, j_next] += wx2 * wy2 * charge_density

        return rho / (dx * dy)

    def solve_poisson_1d(self, rho: np.ndarray) -> np.ndarray:
        """Solve Poisson equation in 1D using FFT"""
        cfg = self.config
        nx = cfg.nx
        dx = cfg.dx

        rho_hat = fft(rho)

        k = 2 * np.pi * fftfreq(nx, dx)
        k[0] = 1.0

        phi_hat = rho_hat / (self.eps0 * k**2)
        phi_hat[0] = 0

        phi = np.real(ifft(phi_hat))
        return phi  # type: ignore[no-any-return]

    def solve_poisson_2d_fft(self, rho: np.ndarray) -> np.ndarray:
        """Solve Poisson equation in 2D using FFT"""
        cfg = self.config
        nx, ny = cfg.nx, cfg.ny
        dx, dy = cfg.dx, cfg.dy

        rho_hat = fft(fft(rho, axis=0), axis=1)

        kx = 2 * np.pi * fftfreq(nx, dx)
        ky = 2 * np.pi * fftfreq(ny, dy)
        KX, KY = np.meshgrid(kx, ky, indexing='ij')

        k2 = KX**2 + KY**2
        k2[0, 0] = 1.0

        phi_hat = rho_hat / (self.eps0 * k2)
        phi_hat[0, 0] = 0

        phi = np.real(ifft(ifft(phi_hat, axis=1), axis=0))
        return phi  # type: ignore[no-any-return]

    def compute_electric_field_1d(self, phi: np.ndarray) -> np.ndarray:
        """Compute electric field from potential (1D)"""
        dx = self.config.dx
        Ex = np.zeros_like(phi)
        Ex[1:-1] = -(phi[2:] - phi[:-2]) / (2 * dx)
        Ex[0] = -(phi[1] - phi[-1]) / (2 * dx)
        Ex[-1] = -(phi[0] - phi[-2]) / (2 * dx)
        return Ex

    def compute_electric_field_2d(self, phi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Compute electric field from potential (2D)"""
        dx, dy = self.config.dx, self.config.dy
        Ex = np.zeros_like(phi)
        Ey = np.zeros_like(phi)

        Ex[1:-1, :] = -(phi[2:, :] - phi[:-2, :]) / (2 * dx)
        Ey[:, 1:-1] = -(phi[:, 2:] - phi[:, :-2]) / (2 * dy)

        return Ex, Ey

    def push_particles_1d(self, Ex: np.ndarray, dt: float) -> None:
        """Push particles using Boris algorithm (1D)"""
        cfg = self.config
        dx = cfg.dx

        for p in self.particles:
            i = int(p.x / dx) % cfg.nx
            i_next = (i + 1) % cfg.nx
            frac = (p.x - i * dx) / dx
            E_particle = (1 - frac) * Ex[i] + frac * Ex[i_next]

            q_m = p.charge * self.q_e / (p.mass * self.m_e)

            if cfg.pusher == "boris":
                v_minus = p.vx + 0.5 * q_m * E_particle * dt
                p.vx = v_minus + 0.5 * q_m * E_particle * dt
            else:
                p.vx += q_m * E_particle * dt

            p.x += p.vx * dt
            p.x = p.x % cfg.Lx

    def push_particles_2d(self, Ex: np.ndarray, Ey: np.ndarray, dt: float) -> None:
        """Push particles using Boris algorithm (2D)"""
        cfg = self.config
        dx, dy = cfg.dx, cfg.dy

        for p in self.particles:
            i = int(p.x / dx) % cfg.nx
            j = int(p.y / dy) % cfg.ny

            frac_x = (p.x - i * dx) / dx
            frac_y = (p.y - j * dy) / dy

            i_next = (i + 1) % cfg.nx
            j_next = (j + 1) % cfg.ny

            Epx = ((1-frac_x)*(1-frac_y)*Ex[i, j] + frac_x*(1-frac_y)*Ex[i_next, j] +
                   (1-frac_x)*frac_y*Ex[i, j_next] + frac_x*frac_y*Ex[i_next, j_next])

            Epy = ((1-frac_x)*(1-frac_y)*Ey[i, j] + frac_x*(1-frac_y)*Ey[i_next, j] +
                   (1-frac_x)*frac_y*Ey[i, j_next] + frac_x*frac_y*Ey[i_next, j_next])

            q_m = p.charge * self.q_e / (p.mass * self.m_e)

            p.vx += q_m * Epx * dt
            p.vy += q_m * Epy * dt

            p.x += p.vx * dt
            p.y += p.vy * dt

            p.x = p.x % cfg.Lx
            p.y = p.y % cfg.Ly

    def compute_kinetic_energy(self) -> float:
        """Compute total kinetic energy"""
        ke = 0.0
        for p in self.particles:
            v2 = p.vx**2 + p.vy**2 + p.vz**2
            m = p.mass * self.m_e
            ke += 0.5 * m * v2 * p.weight
        return ke

    def compute_field_energy_1d(self, Ex: np.ndarray) -> float:
        """Compute electric field energy (1D)"""
        return float(0.5 * self.eps0 * np.sum(Ex**2) * self.config.dx)

    def compute_field_energy_2d(self, Ex: np.ndarray, Ey: np.ndarray) -> float:
        """Compute electric field energy (2D)"""
        return float(0.5 * self.eps0 * np.sum(Ex**2 + Ey**2) * self.config.dx * self.config.dy)

    def compute_total_momentum(self) -> float:
        """Compute total momentum"""
        momentum = 0.0
        for p in self.particles:
            m = p.mass * self.m_e
            momentum += m * p.vx * p.weight
        return momentum

    def compute_thermal_velocity(self, species: int = 0) -> float:
        """Compute RMS thermal velocity for a species"""
        velocities = []
        for p in self.particles:
            if (species == 0 and p.charge < 0) or (species == 1 and p.charge > 0):
                v2 = p.vx**2 + p.vy**2 + p.vz**2
                velocities.append(np.sqrt(v2))
        return float(np.mean(velocities)) if velocities else 0.0
