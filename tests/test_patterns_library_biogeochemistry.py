"""Tests for src/patterns/library/biogeochemistry.py"""
from __future__ import annotations

import numpy as np
import pytest

from patterns.library.biogeochemistry import BiogeochemistryConfig, BiogeochemistryPattern


class TestBiogeochemistryConfig:
    def test_defaults(self):
        cfg = BiogeochemistryConfig()
        assert cfg.nx == 50
        assert cfg.P_max_growth == 1.0
        assert cfg.Z_grazing_max == 0.6

    def test_custom(self):
        cfg = BiogeochemistryConfig(nx=20, days=30)
        assert cfg.nx == 20
        assert cfg.days == 30


class TestBiogeochemistryInit:
    def test_init_default(self):
        pattern = BiogeochemistryPattern()
        assert pattern.N.shape == (50, 50, 10)
        assert pattern.P.shape == pattern.N.shape
        assert pattern.Z.shape == pattern.N.shape
        assert pattern.D.shape == pattern.N.shape

    def test_init_custom(self):
        cfg = BiogeochemistryConfig(nx=20, ny=20, nz=5)
        pattern = BiogeochemistryPattern(cfg)
        assert pattern.N.shape == (20, 20, 5)


class TestBiogeochemistryLight:
    def test_light_profile_shape(self):
        pattern = BiogeochemistryPattern()
        I = pattern._light_profile()
        assert I.shape == pattern.N.shape

    def test_light_decreases_with_depth(self):
        cfg = BiogeochemistryConfig(nx=10, ny=10, nz=5)
        pattern = BiogeochemistryPattern(cfg)
        I = pattern._light_profile()
        # z[0] = -H (deepest), z[-1] = 0 (surface)
        # So I[:,:,-1] is surface (brightest), I[:,:,0] is bottom (darkest)
        assert np.max(I[:, :, -1]) >= np.max(I[:, :, 0])


class TestBiogeochemistryNutrientUptake:
    def test_nutrient_uptake_shape(self):
        pattern = BiogeochemistryPattern()
        I = pattern._light_profile()
        growth = pattern._nutrient_uptake(pattern.N, pattern.P, I)
        assert growth.shape == pattern.P.shape
        assert np.all(growth >= 0)


class TestBiogeochemistryGrazing:
    def test_grazing_shape(self):
        pattern = BiogeochemistryPattern()
        grazing, assimilation = pattern._grazing(pattern.P, pattern.Z)
        assert grazing.shape == pattern.P.shape
        assert assimilation.shape == pattern.Z.shape

    def test_assimilation_less_than_grazing(self):
        pattern = BiogeochemistryPattern()
        grazing, assimilation = pattern._grazing(pattern.P, pattern.Z)
        assert np.all(assimilation <= grazing * pattern.config.Z_assim_eff + 1e-10)


class TestBiogeochemistryMortality:
    def test_mortality_shape(self):
        pattern = BiogeochemistryPattern()
        P_mort, Z_mort = pattern._mortality(pattern.P, pattern.Z)
        assert P_mort.shape == pattern.P.shape
        assert Z_mort.shape == pattern.Z.shape
        assert np.all(P_mort >= 0)


class TestBiogeochemistryRemineralization:
    def test_remineralization_shape(self):
        pattern = BiogeochemistryPattern()
        remin = pattern._remineralization(pattern.D)
        assert remin.shape == pattern.D.shape
        assert np.all(remin >= 0)


class TestBiogeochemistrySinking:
    def test_sinking_shape(self):
        pattern = BiogeochemistryPattern()
        F_sink = pattern._sinking(pattern.D)
        assert F_sink.shape == pattern.D.shape


class TestBiogeochemistryTendencies:
    def test_tendencies_shape(self):
        pattern = BiogeochemistryPattern()
        dN_dt, dP_dt, dZ_dt, dD_dt = pattern._tendencies()
        assert dN_dt.shape == pattern.N.shape
        assert dP_dt.shape == pattern.P.shape
        assert dZ_dt.shape == pattern.Z.shape
        assert dD_dt.shape == pattern.D.shape


class TestBiogeochemistryVerticalMixing:
    def test_vertical_mixing_shape(self):
        pattern = BiogeochemistryPattern()
        dN_dt = pattern._vertical_mixing(pattern.N)
        assert dN_dt.shape == pattern.N.shape

    def test_vertical_mixing_N_boundary(self):
        pattern = BiogeochemistryPattern()
        dN_dt = pattern._vertical_mixing(pattern.N)
        assert np.all(np.isfinite(dN_dt))


class TestBiogeochemistryStep:
    def test_step_nonnegative(self):
        pattern = BiogeochemistryPattern()
        pattern._step()
        assert np.all(pattern.N >= 0)
        assert np.all(pattern.P >= 0)
        assert np.all(pattern.Z >= 0)
        assert np.all(pattern.D >= 0)

    def test_step_changes_fields(self):
        pattern = BiogeochemistryPattern()
        N_before = pattern.N.copy()
        pattern._step()
        assert not np.allclose(pattern.N, N_before)


class TestBiogeochemistryPrimaryProduction:
    def test_primary_production(self):
        pattern = BiogeochemistryPattern()
        PP = pattern._calculate_primary_production()
        assert isinstance(PP, float)
        assert PP >= 0


class TestBiogeochemistryExportFlux:
    def test_export_flux(self):
        pattern = BiogeochemistryPattern()
        export = pattern._calculate_export_flux()
        assert isinstance(export, float)


class TestBiogeochemistryRun:
    def test_short_run(self):
        cfg = BiogeochemistryConfig(nx=10, ny=10, nz=3, days=2, dt=3600)
        pattern = BiogeochemistryPattern(cfg)
        result = pattern.run()
        assert "nutrients" in result
        assert "phytoplankton" in result
        assert len(result["time_days"]) > 0

    def test_run_output(self):
        cfg = BiogeochemistryConfig(nx=10, ny=10, nz=3, days=1, dt=3600)
        pattern = BiogeochemistryPattern(cfg)
        result = pattern.run()
        assert "final_state" in result
        assert "production_stats" in result


class TestBiogeochemistryFormatOutput:
    def test_format_output(self):
        cfg = BiogeochemistryConfig(nx=10, ny=10, nz=3)
        pattern = BiogeochemistryPattern(cfg)
        pattern.history["N"].append(5.0)
        pattern.history["P"].append(0.5)
        pattern.history["time"].append(0.0)
        pattern.history["primary_production"].append(100.0)
        pattern.history["export_flux"].append(10.0)
        result = pattern._format_output()
        assert "final_state" in result
        assert "carbon_biomass" in result["final_state"]


class TestBiogeochemistryMetadata:
    def test_get_metadata(self):
        meta = BiogeochemistryPattern.get_metadata()
        assert meta["id"] == "biogeochemistry"
        assert "parameters" in meta
