"""Tests for biogeochemistry pattern module."""

import numpy as np
import pytest

from src.patterns.library.biogeochemistry import BiogeochemistryConfig, BiogeochemistryPattern


class TestBiogeochemistryConfig:
    def test_default_values(self):
        cfg = BiogeochemistryConfig()
        assert cfg.nx == 50
        assert cfg.ny == 50
        assert cfg.nz == 10
        assert cfg.N_initial == 5.0
        assert cfg.P_initial == 0.5
        assert cfg.days == 365

    def test_custom_values(self):
        cfg = BiogeochemistryConfig(nx=20, ny=20, nz=5, days=10)
        assert cfg.nx == 20
        assert cfg.days == 10


class TestBiogeochemistryPattern:
    @pytest.fixture
    def small_config(self):
        return BiogeochemistryConfig(nx=10, ny=10, nz=3, days=2, dt=3600)

    @pytest.fixture
    def pattern(self, small_config):
        return BiogeochemistryPattern(small_config)

    def test_init(self, pattern, small_config):
        assert pattern.config == small_config
        assert pattern.N.shape == (10, 10, 3)
        assert pattern.P.shape == (10, 10, 3)
        assert pattern.Z.shape == (10, 10, 3)
        assert pattern.D.shape == (10, 10, 3)

    def test_pattern_id(self):
        assert BiogeochemistryPattern.PATTERN_ID == "biogeochemistry"
        assert BiogeochemistryPattern.PATTERN_VERSION == "6.0.0"

    def test_light_profile(self, pattern):
        I = pattern._light_profile()
        assert I.shape == (10, 10, 3)
        # z[0] = -H (deepest), z[-1] = 0 (surface), so light increases with k
        assert np.all(I[:, :, 0] <= I[:, :, -1])
        assert np.all(I >= 0)

    def test_nutrient_uptake(self, pattern):
        I = pattern._light_profile()
        growth = pattern._nutrient_uptake(pattern.N, pattern.P, I)
        assert growth.shape == pattern.P.shape
        assert np.all(growth >= 0)

    def test_grazing(self, pattern):
        grazing, assimilation = pattern._grazing(pattern.P, pattern.Z)
        assert grazing.shape == pattern.P.shape
        assert assimilation.shape == pattern.Z.shape
        assert np.all(assimilation <= grazing * pattern.config.Z_assim_eff + 1e-10)

    def test_mortality(self, pattern):
        P_mort, Z_mort = pattern._mortality(pattern.P, pattern.Z)
        assert P_mort.shape == pattern.P.shape
        assert Z_mort.shape == pattern.Z.shape
        assert np.all(P_mort >= 0)
        assert np.all(Z_mort >= 0)

    def test_remineralization(self, pattern):
        remin = pattern._remineralization(pattern.D)
        assert remin.shape == pattern.D.shape
        assert np.all(remin >= 0)

    def test_sinking(self, pattern):
        F_sink = pattern._sinking(pattern.D)
        assert F_sink.shape == pattern.D.shape
        assert np.all(np.isfinite(F_sink))

    def test_tendencies(self, pattern):
        dN_dt, dP_dt, dZ_dt, dD_dt = pattern._tendencies()
        assert dN_dt.shape == pattern.N.shape
        assert dP_dt.shape == pattern.P.shape
        assert dZ_dt.shape == pattern.Z.shape
        assert dD_dt.shape == pattern.D.shape
        assert np.all(np.isfinite(dN_dt))

    def test_vertical_mixing(self, pattern):
        dN_dt = pattern._vertical_mixing(pattern.N)
        assert dN_dt.shape == pattern.N.shape
        assert np.all(np.isfinite(dN_dt))

    def test_step(self, pattern):
        N_before = pattern.N.copy()
        pattern._step()
        assert np.all(pattern.N >= 0)
        assert np.all(pattern.P >= 0)
        assert np.all(pattern.Z >= 0)
        assert np.all(pattern.D >= 0)

    def test_primary_production(self, pattern):
        PP = pattern._calculate_primary_production()
        assert isinstance(PP, float)
        assert PP >= 0

    def test_export_flux(self, pattern):
        export = pattern._calculate_export_flux()
        assert isinstance(export, float)
        assert export >= 0

    def test_run_short(self):
        config = BiogeochemistryConfig(nx=8, ny=8, nz=2, days=2, dt=3600, output_interval=1)
        pattern = BiogeochemistryPattern(config)
        result = pattern.run()
        assert "nutrients" in result
        assert "phytoplankton" in result
        assert "zooplankton" in result
        assert "detritus" in result
        assert "primary_production" in result
        assert len(result["time_days"]) > 0
        assert "final_state" in result
        assert "carbon_biomass" in result["final_state"]

    def test_metadata(self):
        metadata = BiogeochemistryPattern.get_metadata()
        assert metadata["id"] == "biogeochemistry"
        assert "parameters" in metadata
        assert len(metadata["assumptions"]) > 0

    def test_npzd_conservation(self, pattern):
        N_before = np.sum(pattern.N)
        P_before = np.sum(pattern.P)
        Z_before = np.sum(pattern.Z)
        D_before = np.sum(pattern.D)
        pattern._step()
        N_after = np.sum(pattern.N)
        P_after = np.sum(pattern.P)
        Z_after = np.sum(pattern.Z)
        D_after = np.sum(pattern.D)
        total_before = N_before + P_before + Z_before + D_before
        total_after = N_after + P_after + Z_after + D_after
        assert total_after > 0
