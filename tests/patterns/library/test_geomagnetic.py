"""
Tests for geomagnetic pattern module.
"""

import numpy as np
import pytest

from src.patterns.library.geomagnetic import GeomagneticConfig, GeomagneticPattern


class TestConfig:
    def test_default_config(self):
        cfg = GeomagneticConfig()
        assert cfg.nr == 32
        assert cfg.ntheta == 32
        assert cfg.nphi == 64
        assert cfg.Ra == 1.0e6

    def test_custom_config(self):
        cfg = GeomagneticConfig(nr=16, ntheta=16, nphi=32)
        assert cfg.nr == 16


class TestInit:
    def test_pattern_init_default(self):
        pattern = GeomagneticPattern()
        assert pattern.config is not None
        assert pattern.B_r is not None

    def test_pattern_init_custom(self):
        cfg = GeomagneticConfig(nr=16, ntheta=16, nphi=32)
        pattern = GeomagneticPattern(cfg)
        assert pattern.B_r.shape == (16, 16, 32)


class TestLaplacian:
    def test_spherical_laplacian_shape(self):
        pattern = GeomagneticPattern()
        field = np.ones_like(pattern.T)
        lapl = pattern._spherical_laplacian(field)
        assert lapl.shape == field.shape
        assert np.all(np.isfinite(lapl))


class TestForces:
    def test_coriolis_force(self):
        pattern = GeomagneticPattern()
        pattern.v_phi[:, :, :] = 1.0
        F_r, F_theta, F_phi = pattern._coriolis_force()
        assert F_r.shape == pattern.v_r.shape
        assert np.all(np.isfinite(F_r))

    def test_lorentz_force(self):
        pattern = GeomagneticPattern()
        F_r, F_theta, F_phi = pattern._lorentz_force()
        assert F_r.shape == pattern.v_r.shape
        assert np.all(np.isfinite(F_r))


class TestTendencies:
    def test_velocity_tendency(self):
        pattern = GeomagneticPattern()
        dv_r, dv_theta, dv_phi = pattern._velocity_tendency()
        assert dv_r.shape == pattern.v_r.shape
        assert np.all(np.isfinite(dv_r))

    def test_induction_equation(self):
        pattern = GeomagneticPattern()
        dBr, dBtheta, dBphi = pattern._induction_equation()
        assert dBr.shape == pattern.B_r.shape
        assert np.all(np.isfinite(dBr))

    def test_temperature_tendency(self):
        pattern = GeomagneticPattern()
        dT_dt = pattern._temperature_tendency()
        assert dT_dt.shape == pattern.T.shape
        assert np.all(np.isfinite(dT_dt))


class TestEnergy:
    def test_dipole_moment(self):
        pattern = GeomagneticPattern()
        dipole = pattern._calculate_dipole_moment()
        assert isinstance(dipole, float)
        assert dipole > 0

    def test_magnetic_energy(self):
        pattern = GeomagneticPattern()
        Em = pattern._calculate_magnetic_energy()
        assert isinstance(Em, float)
        assert Em > 0

    def test_kinetic_energy(self):
        pattern = GeomagneticPattern()
        Ek = pattern._calculate_kinetic_energy()
        assert isinstance(Ek, float)
        assert Ek == 0  # Initially zero velocity


class TestStep:
    def test_single_step(self):
        pattern = GeomagneticPattern()
        T_before = pattern.T.copy()
        pattern._step()
        assert not np.allclose(pattern.T, T_before)


class TestRun:
    def test_short_simulation(self):
        cfg = GeomagneticConfig(
            nr=12, ntheta=12, nphi=24, max_time=0.001, dt=1e-7, output_interval=10
        )
        pattern = GeomagneticPattern(cfg)
        result = pattern.run()
        assert "dipole_moment" in result
        assert "magnetic_energy" in result
        assert len(result["time"]) > 0

    def test_metadata(self):
        meta = GeomagneticPattern.get_metadata()
        assert meta["id"] == "geomagnetic"
        assert "parameters" in meta


class TestEdgeCases:
    def test_boundary_conditions(self):
        pattern = GeomagneticPattern()
        pattern._apply_boundary_conditions()
        assert np.all(pattern.v_r[0, :, :] == 0)
        assert np.all(pattern.v_r[-1, :, :] == 0)

    def test_divergence_free_projection(self):
        pattern = GeomagneticPattern()
        pattern._project_divergence_free()
        assert np.all(np.isfinite(pattern.B_r))

    def test_small_grid(self):
        cfg = GeomagneticConfig(nr=8, ntheta=8, nphi=16, max_time=0.0001, dt=1e-7)
        pattern = GeomagneticPattern(cfg)
        result = pattern.run()
        assert "final_state" in result
