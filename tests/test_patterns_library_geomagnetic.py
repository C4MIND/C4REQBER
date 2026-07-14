"""Tests for src/patterns/library/geomagnetic.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from patterns.library.geomagnetic import GeomagneticConfig, GeomagneticPattern


class TestGeomagneticConfig:
    def test_defaults(self):
        cfg = GeomagneticConfig()
        assert cfg.nr == 32
        assert cfg.ntheta == 32
        assert cfg.nphi == 64
        assert cfg.Ra == 1.0e6

    def test_custom(self):
        cfg = GeomagneticConfig(nr=16, ntheta=16, nphi=32, Ra=1e5)
        assert cfg.nr == 16
        assert cfg.Ra == 1e5


class TestGeomagneticPatternInit:
    def test_init_default(self):
        pattern = GeomagneticPattern()
        assert pattern.config is not None
        assert pattern.B_r.shape == (32, 32, 64)
        assert pattern.v_r.shape == pattern.B_r.shape

    def test_init_custom(self):
        cfg = GeomagneticConfig(nr=16, ntheta=16, nphi=32)
        pattern = GeomagneticPattern(cfg)
        assert pattern.B_r.shape == (16, 16, 32)


class TestGeomagneticGrid:
    def test_grid_coordinates(self):
        cfg = GeomagneticConfig(nr=16, ntheta=16, nphi=32)
        pattern = GeomagneticPattern(cfg)
        assert len(pattern.r) == 16
        assert len(pattern.theta) == 16
        assert len(pattern.phi) == 32

    def test_cartesian_coords(self):
        pattern = GeomagneticPattern()
        assert pattern.X.shape == pattern.B_r.shape
        assert pattern.Y.shape == pattern.B_r.shape
        assert pattern.Z.shape == pattern.B_r.shape


class TestGeomagneticFields:
    def test_dipole_initialization(self):
        cfg = GeomagneticConfig(dipole_tilt=0.0)
        pattern = GeomagneticPattern(cfg)
        assert not np.all(pattern.B_r == 0)

    def test_temperature_perturbation(self):
        pattern = GeomagneticPattern()
        assert not np.all(pattern.T == 0)


class TestGeomagneticSphericalLaplacian:
    def test_spherical_laplacian_shape(self):
        pattern = GeomagneticPattern()
        field = np.ones_like(pattern.T)
        lapl = pattern._spherical_laplacian(field)
        assert lapl.shape == field.shape

    def test_spherical_laplacian_finite(self):
        pattern = GeomagneticPattern()
        field = np.random.randn(*pattern.T.shape)
        lapl = pattern._spherical_laplacian(field)
        assert np.all(np.isfinite(lapl))


class TestGeomagneticCoriolis:
    def test_coriolis_force_shape(self):
        pattern = GeomagneticPattern()
        F_r, F_theta, F_phi = pattern._coriolis_force()
        assert F_r.shape == pattern.v_r.shape
        assert np.all(np.isfinite(F_r))

    def test_coriolis_with_velocity(self):
        pattern = GeomagneticPattern()
        pattern.v_phi[:, :, :] = 1.0
        F_r, F_theta, F_phi = pattern._coriolis_force()
        assert not np.all(F_theta == 0)


class TestGeomagneticLorentz:
    def test_lorentz_force_shape(self):
        pattern = GeomagneticPattern()
        F_r, F_theta, F_phi = pattern._lorentz_force()
        assert F_r.shape == pattern.v_r.shape
        assert np.all(np.isfinite(F_r))


class TestGeomagneticVelocityTendency:
    def test_velocity_tendency_shape(self):
        pattern = GeomagneticPattern()
        dv_r, dv_theta, dv_phi = pattern._velocity_tendency()
        assert dv_r.shape == pattern.v_r.shape
        assert np.all(np.isfinite(dv_r))


class TestGeomagneticInduction:
    def test_induction_equation_shape(self):
        pattern = GeomagneticPattern()
        dBr, dBtheta, dBphi = pattern._induction_equation()
        assert dBr.shape == pattern.B_r.shape
        assert np.all(np.isfinite(dBr))


class TestGeomagneticTemperatureTendency:
    def test_temperature_tendency_shape(self):
        pattern = GeomagneticPattern()
        dT_dt = pattern._temperature_tendency()
        assert dT_dt.shape == pattern.T.shape
        assert np.all(np.isfinite(dT_dt))


class TestGeomagneticBoundaryConditions:
    def test_apply_boundary_conditions(self):
        pattern = GeomagneticPattern()
        pattern.v_r[:, :, :] = 1.0
        pattern.v_theta[:, :, :] = 1.0
        pattern.v_phi[:, :, :] = 1.0
        pattern._apply_boundary_conditions()
        assert np.all(pattern.v_r[0, :, :] == 0)
        assert np.all(pattern.v_r[-1, :, :] == 0)
        assert np.all(pattern.T[0, :, :] == 1.0)
        assert np.all(pattern.T[-1, :, :] == 0.0)


class TestGeomagneticDipoleMoment:
    def test_dipole_moment(self):
        pattern = GeomagneticPattern()
        dipole = pattern._calculate_dipole_moment()
        assert isinstance(dipole, float)
        assert dipole >= 0


class TestGeomagneticEnergy:
    def test_magnetic_energy(self):
        pattern = GeomagneticPattern()
        Em = pattern._calculate_magnetic_energy()
        assert isinstance(Em, float)
        assert Em > 0

    def test_kinetic_energy_zero(self):
        pattern = GeomagneticPattern()
        Ek = pattern._calculate_kinetic_energy()
        assert isinstance(Ek, float)
        assert Ek == 0

    def test_kinetic_energy_nonzero(self):
        pattern = GeomagneticPattern()
        pattern.v_r[:, :, :] = 1.0
        Ek = pattern._calculate_kinetic_energy()
        assert Ek > 0


class TestGeomagneticDivergenceFree:
    def test_project_divergence_free(self):
        pattern = GeomagneticPattern()
        pattern.B_r[:, :, :] = 1.0
        pattern._project_divergence_free()
        assert np.all(np.isfinite(pattern.B_r))


class TestGeomagneticStep:
    def test_step_changes_fields(self):
        pattern = GeomagneticPattern()
        T_before = pattern.T.copy()
        pattern._step()
        assert not np.allclose(pattern.T, T_before)

    def test_step_finite(self):
        pattern = GeomagneticPattern()
        pattern._step()
        assert np.all(np.isfinite(pattern.B_r))
        assert np.all(np.isfinite(pattern.T))


class TestGeomagneticRun:
    def test_short_run(self):
        cfg = GeomagneticConfig(nr=12, ntheta=12, nphi=24, max_time=0.001, dt=1e-7, output_interval=10)
        pattern = GeomagneticPattern(cfg)
        result = pattern.run()
        assert "dipole_moment" in result
        assert "magnetic_energy" in result
        assert len(result["time"]) > 0

    def test_run_no_output(self):
        cfg = GeomagneticConfig(nr=12, ntheta=12, nphi=24, max_time=0.0001, dt=1e-7, output_interval=10000)
        pattern = GeomagneticPattern(cfg)
        result = pattern.run()
        assert "final_state" in result


class TestGeomagneticFormatOutput:
    def test_format_output_with_history(self):
        cfg = GeomagneticConfig(nr=12, ntheta=12, nphi=24)
        pattern = GeomagneticPattern(cfg)
        pattern.history["dipole_moment"].append(1.0)
        pattern.history["magnetic_energy"].append(1.0)
        pattern.history["kinetic_energy"].append(1.0)
        pattern.history["time"].append(0.0)
        result = pattern._format_output()
        assert "final_state" in result
        assert "parameters" in result

    def test_format_output_empty_history(self):
        pattern = GeomagneticPattern()
        result = pattern._format_output()
        assert result["final_state"]["dipole_moment"] == 0


class TestGeomagneticMetadata:
    def test_get_metadata(self):
        meta = GeomagneticPattern.get_metadata()
        assert meta["id"] == "geomagnetic"
        assert "parameters" in meta
        assert len(meta["assumptions"]) > 0
