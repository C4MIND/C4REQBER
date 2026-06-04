"""Tests for composite_mechanics pattern module."""

import numpy as np
import pytest

from src.patterns.library.composite_mechanics import (

    CompositeMechanicsConfig,
    CompositeMechanicsPattern,
    HomogenizationMethod,
    InclusionShape,
    LoadingType,
)


class TestCompositeMechanicsEnums:
    def test_homogenization_methods(self):
        assert HomogenizationMethod.MORI_TANAKA.value == "mori_tanaka"
        assert HomogenizationMethod.RULE_OF_MIXTURES.value == "rule_of_mixtures"
        assert HomogenizationMethod.HALPIN_TSAI.value == "halpin_tsai"
        assert HomogenizationMethod.SELF_CONSISTENT.value == "self_consistent"
        assert HomogenizationMethod.FEA_BASED.value == "fea_based"

    def test_inclusion_shapes(self):
        assert InclusionShape.SPHERE.value == "sphere"
        assert InclusionShape.CYLINDER.value == "cylinder"
        assert InclusionShape.DISK.value == "disk"
        assert InclusionShape.ELLIPSOID.value == "ellipsoid"

    def test_loading_types(self):
        assert LoadingType.UNIAXIAL.value == "uniaxial"
        assert LoadingType.BIAXIAL.value == "biaxial"
        assert LoadingType.SHEAR.value == "shear"
        assert LoadingType.HYDROSTATIC.value == "hydrostatic"


class TestCompositeMechanicsConfig:
    def test_default_values(self):
        cfg = CompositeMechanicsConfig()
        assert cfg.volume_fraction == 0.30
        assert cfg.inclusion_shape == InclusionShape.CYLINDER
        assert cfg.method == HomogenizationMethod.MORI_TANAKA
        assert cfg.loading == LoadingType.UNIAXIAL

    def test_custom_values(self):
        cfg = CompositeMechanicsConfig(
            volume_fraction=0.5,
            method=HomogenizationMethod.HALPIN_TSAI,
            inclusion_shape=InclusionShape.SPHERE,
        )
        assert cfg.volume_fraction == 0.5
        assert cfg.method == HomogenizationMethod.HALPIN_TSAI


class TestCompositeMechanicsPattern:
    @pytest.fixture
    def default_pattern(self):
        return CompositeMechanicsPattern()

    def test_init(self, default_pattern):
        assert default_pattern.C_eff is None
        assert default_pattern.E_eff is None
        assert default_pattern.nu_eff is None

    def test_pattern_id(self):
        assert CompositeMechanicsPattern.PATTERN_ID == "composite_mechanics"
        assert CompositeMechanicsPattern.PATTERN_VERSION == "6.0.0"

    def test_isotropic_stiffness(self, default_pattern):
        C = default_pattern._isotropic_stiffness(1e9, 0.3)
        assert C.shape == (6, 6)
        assert C[0, 0] > 0
        assert C[3, 3] > 0

    def test_eshelby_tensor_cylinder(self, default_pattern):
        S = default_pattern._calculate_eshelby_tensor()
        assert S.shape == (6, 6)
        assert np.all(np.isfinite(S))

    def test_eshelby_tensor_sphere(self):
        config = CompositeMechanicsConfig(inclusion_shape=InclusionShape.SPHERE)
        pattern = CompositeMechanicsPattern(config)
        S = pattern._calculate_eshelby_tensor()
        assert S.shape == (6, 6)
        assert np.all(np.isfinite(S))

    def test_rule_of_mixtures(self, default_pattern):
        E_eff, nu_eff = default_pattern._rule_of_mixtures()
        assert E_eff > default_pattern.config.E_matrix
        assert E_eff < default_pattern.config.E_inclusion
        assert 0 < nu_eff < 0.5

    def test_mori_tanaka(self, default_pattern):
        C_eff, E_eff, nu_eff = default_pattern._mori_tanaka()
        assert C_eff.shape == (6, 6)
        assert E_eff > 0
        assert 0 < nu_eff < 0.5

    def test_halpin_tsai(self, default_pattern):
        E_eff, nu_eff = default_pattern._halpin_tsai()
        assert E_eff > 0
        assert 0 < nu_eff < 0.5

    def test_self_consistent(self, default_pattern):
        E_eff, nu_eff = default_pattern._self_consistent()
        assert E_eff > 0
        assert 0 < nu_eff < 0.5

    def test_fea_homogenization(self, default_pattern):
        C_eff, E_eff, nu_eff = default_pattern._fea_homogenization()
        assert C_eff.shape == (6, 6)
        assert E_eff > 0

    def test_stress_concentration(self, default_pattern):
        Kt = default_pattern._calculate_stress_concentration()
        assert Kt > 1.0

    def test_failure_index(self, default_pattern):
        stress = np.array([100e6, 0, 0, 0, 0, 0])
        fi = default_pattern._calculate_failure_index(stress)
        assert "matrix_von_mises" in fi
        assert "fiber_max_stress" in fi
        assert "overall" in fi
        assert fi["overall"] >= 0

    def test_run_rule_of_mixtures(self):
        config = CompositeMechanicsConfig(method=HomogenizationMethod.RULE_OF_MIXTURES)
        pattern = CompositeMechanicsPattern(config)
        result = pattern.run()
        assert result["method"] == "rule_of_mixtures"
        assert "effective_properties" in result
        assert result["property_enhancement"]["within_bounds"] is True

    def test_run_mori_tanaka(self):
        config = CompositeMechanicsConfig(method=HomogenizationMethod.MORI_TANAKA)
        pattern = CompositeMechanicsPattern(config)
        result = pattern.run()
        assert result["method"] == "mori_tanaka"
        assert result["property_enhancement"]["within_bounds"] is True

    def test_run_halpin_tsai(self):
        config = CompositeMechanicsConfig(method=HomogenizationMethod.HALPIN_TSAI)
        pattern = CompositeMechanicsPattern(config)
        result = pattern.run()
        assert result["method"] == "halpin_tsai"

    def test_run_self_consistent(self):
        config = CompositeMechanicsConfig(method=HomogenizationMethod.SELF_CONSISTENT)
        pattern = CompositeMechanicsPattern(config)
        result = pattern.run()
        assert result["method"] == "self_consistent"

    def test_run_fea_based(self):
        config = CompositeMechanicsConfig(
            method=HomogenizationMethod.FEA_BASED, mesh_size=20
        )
        pattern = CompositeMechanicsPattern(config)
        result = pattern.run()
        assert result["method"] == "fea_based"

    def test_run_with_failure(self):
        config = CompositeMechanicsConfig(
            method=HomogenizationMethod.MORI_TANAKA,
            compute_failure_index=True,
            strain_magnitude=0.02,
        )
        pattern = CompositeMechanicsPattern(config)
        result = pattern.run()
        assert "failure_index" in result
        assert "failure_predicted" in result

    def test_volume_fraction_effect(self):
        vfs = [0.1, 0.3, 0.5]
        E_values = []
        for vf in vfs:
            config = CompositeMechanicsConfig(
                method=HomogenizationMethod.MORI_TANAKA, volume_fraction=vf
            )
            pattern = CompositeMechanicsPattern(config)
            result = pattern.run()
            E_values.append(result["effective_properties"]["E_eff"])
        for i in range(len(E_values) - 1):
            assert E_values[i] < E_values[i + 1]

    def test_bounds_check(self):
        config = CompositeMechanicsConfig(
            method=HomogenizationMethod.MORI_TANAKA, volume_fraction=0.3
        )
        pattern = CompositeMechanicsPattern(config)
        result = pattern.run()
        assert result["property_enhancement"]["within_bounds"] is True

    def test_metadata(self):
        metadata = CompositeMechanicsPattern.get_metadata()
        assert metadata["id"] == "composite_mechanics"
        assert "parameters" in metadata
