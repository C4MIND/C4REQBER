"""Tests for src/patterns/library/sea_ice.py"""
from __future__ import annotations

import numpy as np
import pytest

from patterns.library.sea_ice import SeaIceConfig, SeaIcePattern


class TestSeaIceConfig:
    def test_defaults(self):
        cfg = SeaIceConfig()
        assert cfg.nx == 100
        assert cfg.albedo_ice == 0.65
        assert cfg.T_freeze == -1.8

    def test_custom(self):
        cfg = SeaIceConfig(nx=50, days=30)
        assert cfg.nx == 50
        assert cfg.days == 30


class TestSeaIceInit:
    def test_init_default(self):
        pattern = SeaIcePattern()
        assert pattern.a_ice.shape == (100, 100)
        assert pattern.h_ice.shape == (100, 100)
        assert pattern.T_ice.shape == (100, 100)

    def test_init_custom(self):
        cfg = SeaIceConfig(nx=50, ny=50)
        pattern = SeaIcePattern(cfg)
        assert pattern.a_ice.shape == (50, 50)

    def test_initial_ice_center(self):
        pattern = SeaIcePattern()
        assert np.sum(pattern.a_ice > 0) > 0


class TestSeaIceForcing:
    def test_update_atmospheric_forcing(self):
        cfg = SeaIceConfig(nx=20, ny=20)
        pattern = SeaIcePattern(cfg)
        pattern._update_atmospheric_forcing(0)
        T_day0 = pattern.T_atm.copy()
        pattern._update_atmospheric_forcing(180)
        T_day180 = pattern.T_atm.copy()
        # Day 0 is peak summer (sin(pi/2)=1), day 180 is peak winter
        assert np.mean(T_day0) > np.mean(T_day180)


class TestSeaIceAlbedo:
    def test_calculate_albedo_shape(self):
        pattern = SeaIcePattern()
        albedo = pattern._calculate_albedo()
        assert albedo.shape == pattern.a_ice.shape

    def test_albedo_range(self):
        pattern = SeaIcePattern()
        albedo = pattern._calculate_albedo()
        assert np.all(albedo >= pattern.config.albedo_water)
        assert np.all(albedo <= pattern.config.albedo_ice)

    def test_albedo_melt_pond(self):
        pattern = SeaIcePattern()
        pattern.T_ice[:, :] = 0.0
        albedo = pattern._calculate_albedo()
        assert np.all(np.isfinite(albedo))


class TestSeaIceEnergyBalance:
    def test_surface_energy_balance_shape(self):
        pattern = SeaIcePattern()
        Q_net, T_surf = pattern._surface_energy_balance()
        assert Q_net.shape == pattern.a_ice.shape
        assert np.all(np.isfinite(Q_net))


class TestSeaIceThermodynamics:
    def test_thermodynamics_shape(self):
        pattern = SeaIcePattern()
        dh_dt, da_dt = pattern._thermodynamics()
        assert dh_dt.shape == pattern.h_ice.shape
        assert da_dt.shape == pattern.a_ice.shape

    def test_thermodynamics_open_water(self):
        pattern = SeaIcePattern()
        pattern.a_ice[:, :] = 0.0
        pattern.T_ice[:, :] = pattern.config.T_freeze - 1.0
        dh_dt, da_dt = pattern._thermodynamics()
        assert np.all(np.isfinite(dh_dt))


class TestSeaIceDynamics:
    def test_dynamics_shape(self):
        pattern = SeaIcePattern()
        du_dt, dv_dt = pattern._dynamics()
        assert du_dt.shape == pattern.u.shape
        assert dv_dt.shape == pattern.v.shape

    def test_dynamics_with_ice(self):
        pattern = SeaIcePattern()
        pattern.a_ice[:, :] = 0.8
        pattern.u[:, :] = 0.1
        pattern.v[:, :] = 0.1
        du_dt, dv_dt = pattern._dynamics()
        assert np.all(np.isfinite(du_dt))


class TestSeaIceAdvection:
    def test_advect_ice_bounded(self):
        pattern = SeaIcePattern()
        pattern.u[:, :] = 0.1
        pattern._advect_ice()
        assert np.all(pattern.h_ice >= 0)
        assert np.all(pattern.h_ice <= pattern.config.h_max)
        assert np.all(pattern.a_ice >= 0)
        assert np.all(pattern.a_ice <= 1)


class TestSeaIceStep:
    def test_step_bounded(self):
        pattern = SeaIcePattern()
        pattern._step(0)
        assert np.all(pattern.h_ice >= 0)
        assert np.all(pattern.a_ice >= 0)
        assert np.all(pattern.a_ice <= 1)
        assert np.all(pattern.T_ice >= -50)
        assert np.all(pattern.T_ice <= 10)


class TestSeaIceRun:
    def test_short_run(self):
        cfg = SeaIceConfig(nx=20, ny=20, days=5)
        pattern = SeaIcePattern(cfg)
        result = pattern.run()
        assert "ice_volume" in result
        assert "ice_extent" in result
        assert len(result["time_days"]) > 0

    def test_run_output(self):
        cfg = SeaIceConfig(nx=20, ny=20, days=3)
        pattern = SeaIcePattern(cfg)
        result = pattern.run()
        assert "final_state" in result
        assert "statistics" in result


class TestSeaIceFormatOutput:
    def test_format_output(self):
        cfg = SeaIceConfig(nx=20, ny=20)
        pattern = SeaIcePattern(cfg)
        pattern.history["volume"].append(1e12)
        pattern.history["extent"].append(1.0)
        pattern.history["time"].append(0.0)
        pattern.history["volume"].append(1.1e12)
        pattern.history["extent"].append(1.1)
        pattern.history["time"].append(1.0)
        result = pattern._format_output()
        assert "final_state" in result
        assert "mean_concentration" in result["final_state"]


class TestSeaIceMetadata:
    def test_get_metadata(self):
        meta = SeaIcePattern.get_metadata()
        assert meta["id"] == "sea_ice"
        assert "parameters" in meta
