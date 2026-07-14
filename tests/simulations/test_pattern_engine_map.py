"""Tests for src/simulations/pattern_engine_map.py."""
from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from simulations.pattern_engine_map import (
    EngineType,
    PatternEngineMap,
    PatternMetadata,
    get_engine,
    get_gpu_accelerated_patterns,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def mapper():
    """Fresh PatternEngineMap instance."""
    return PatternEngineMap()


# ═══════════════════════════════════════════════════════════════════
# EngineType Enum
# ═══════════════════════════════════════════════════════════════════


class TestEngineType:
    """Test EngineType enum."""

    def test_values(self):
        assert EngineType.NEWTON.value == "newton"
        assert EngineType.JAXSIM.value == "jaxsim"
        assert EngineType.TORCHSIM.value == "torchsim"
        assert EngineType.SCHR.value == "schr"
        assert EngineType.LEGACY.value == "legacy"


# ═══════════════════════════════════════════════════════════════════
# PatternEngineMap Init
# ═══════════════════════════════════════════════════════════════════


class TestPatternEngineMapInit:
    """Test PatternEngineMap initialization."""

    def test_init(self, mapper):
        assert isinstance(mapper._pattern_cache, dict)
        assert isinstance(mapper._custom_mappings, dict)


# ═══════════════════════════════════════════════════════════════════
# get_engine
# ═══════════════════════════════════════════════════════════════════


class TestGetEngine:
    """Test get_engine method."""

    def test_known_pattern(self, mapper):
        assert mapper.get_engine("cfd") == "newton"
        assert mapper.get_engine("molecular_dynamics") == "torchsim"
        assert mapper.get_engine("double_pendulum") == "jaxsim"
        assert mapper.get_engine("quantum_harmonic") == "schr"

    def test_unknown_pattern(self, mapper):
        assert mapper.get_engine("unknown_pattern_xyz") == "legacy"

    def test_custom_mapping(self, mapper):
        mapper.register_custom_mapping("my_pattern", "jaxsim")
        assert mapper.get_engine("my_pattern") == "jaxsim"

    def test_custom_mapping_invalid_engine(self, mapper):
        mapper.register_custom_mapping("my_pattern", "invalid_engine")
        assert mapper.get_engine("my_pattern") == "legacy"

    def test_metadata_custom_engine(self, mapper):
        result = mapper.get_engine("unknown", metadata={"custom_engine": "newton"})
        assert result == "newton"

    def test_metadata_custom_engine_invalid(self, mapper):
        result = mapper.get_engine("unknown", metadata={"custom_engine": "bad_engine"})
        assert result == "legacy"

    def test_metadata_category(self, mapper):
        result = mapper.get_engine("unknown", metadata={"category": "cfd"})
        assert result == "newton"

    def test_metadata_category_normalized(self, mapper):
        result = mapper.get_engine("unknown", metadata={"category": "fluid dynamics"})
        assert result == "newton"

    def test_metadata_prefer_gpu(self, mapper):
        result = mapper.get_engine("unknown", metadata={"prefer_gpu": True})
        assert result == "newton"

    def test_metadata_complex(self, mapper):
        result = mapper.get_engine("unknown", metadata={
            "category": "quantum",
            "complexity": "high",
            "prefer_gpu": True,
        })
        assert result == "schr"

    def test_custom_mapping_priority(self, mapper):
        mapper.register_custom_mapping("test_pattern", "jaxsim")
        assert mapper.get_engine("test_pattern") == "jaxsim"


# ═══════════════════════════════════════════════════════════════════
# _validate_engine
# ═══════════════════════════════════════════════════════════════════


class TestValidateEngine:
    """Test _validate_engine method."""

    def test_valid_engines(self, mapper):
        assert mapper._validate_engine("newton") is True
        assert mapper._validate_engine("jaxsim") is True
        assert mapper._validate_engine("torchsim") is True
        assert mapper._validate_engine("schr") is True
        assert mapper._validate_engine("legacy") is True

    def test_invalid_engine(self, mapper):
        assert mapper._validate_engine("invalid") is False
        assert mapper._validate_engine("") is False


# ═══════════════════════════════════════════════════════════════════
# _normalize_category
# ═══════════════════════════════════════════════════════════════════


class TestNormalizeCategory:
    """Test _normalize_category method."""

    def test_exact_match(self, mapper):
        assert mapper._normalize_category("cfd") == "cfd"
        assert mapper._normalize_category("continuum") == "continuum"

    def test_aliases(self, mapper):
        assert mapper._normalize_category("fluid") == "cfd"
        assert mapper._normalize_category("fluid_dynamics") == "cfd"
        assert mapper._normalize_category("computational_fluid_dynamics") == "cfd"
        assert mapper._normalize_category("solid_mechanics") == "continuum"
        assert mapper._normalize_category("structural") == "continuum"
        assert mapper._normalize_category("materials") == "atomistic"
        assert mapper._normalize_category("md") == "atomistic"
        assert mapper._normalize_category("rigid") == "rigid_body"
        assert mapper._normalize_category("robotics") == "rigid_body"
        assert mapper._normalize_category("electromagnetic") == "em"
        assert mapper._normalize_category("electromagnetics") == "em"
        assert mapper._normalize_category("acoustics") == "acoustic"
        assert mapper._normalize_category("astrophysics") == "astro"

    def test_hyphens_and_spaces(self, mapper):
        assert mapper._normalize_category("fluid-dynamics") == "cfd"
        assert mapper._normalize_category("solid mechanics") == "continuum"

    def test_unknown(self, mapper):
        assert mapper._normalize_category("exotic") == "exotic"


# ═══════════════════════════════════════════════════════════════════
# get_gpu_accelerated_patterns
# ═══════════════════════════════════════════════════════════════════


class TestGPUAcceleratedPatterns:
    """Test get_gpu_accelerated_patterns method."""

    def test_returns_list(self, mapper):
        patterns = mapper.get_gpu_accelerated_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_contains_known_patterns(self, mapper):
        patterns = mapper.get_gpu_accelerated_patterns()
        assert "cfd" in patterns
        assert "molecular_dynamics" in patterns
        assert "double_pendulum" in patterns
        assert "quantum_harmonic" in patterns

    def test_sorted(self, mapper):
        patterns = mapper.get_gpu_accelerated_patterns()
        assert patterns == sorted(patterns)


# ═══════════════════════════════════════════════════════════════════
# get_acceleration_factor
# ═══════════════════════════════════════════════════════════════════


class TestAccelerationFactor:
    """Test get_acceleration_factor method."""

    def test_known_patterns(self, mapper):
        assert mapper.get_acceleration_factor("cfd") == 50.0
        assert mapper.get_acceleration_factor("molecular_dynamics") == 18.0
        assert mapper.get_acceleration_factor("double_pendulum") == 5.0

    def test_unknown_pattern_returns_one(self, mapper):
        assert mapper.get_acceleration_factor("unknown_xyz") == 1.0

    def test_category_prefix_match(self, mapper):
        assert mapper.get_acceleration_factor("cfd_custom") == 50.0
        assert mapper.get_acceleration_factor("continuum_test") == 25.0
        assert mapper.get_acceleration_factor("atomistic_test") == 15.0
        assert mapper.get_acceleration_factor("rigid_test") == 5.0
        assert mapper.get_acceleration_factor("quantum_test") == 20.0
        assert mapper.get_acceleration_factor("particle_test") == 25.0
        assert mapper.get_acceleration_factor("em_test") == 35.0
        assert mapper.get_acceleration_factor("acoustic_test") == 30.0
        assert mapper.get_acceleration_factor("astro_test") == 40.0


# ═══════════════════════════════════════════════════════════════════
# register_custom_mapping
# ═══════════════════════════════════════════════════════════════════


class TestRegisterCustomMapping:
    """Test register_custom_mapping method."""

    def test_register_valid(self, mapper):
        mapper.register_custom_mapping("my_pattern", "newton")
        assert mapper._custom_mappings["my_pattern"] == "newton"

    def test_register_invalid_ignored(self, mapper):
        mapper.register_custom_mapping("my_pattern", "bad_engine")
        assert "my_pattern" not in mapper._custom_mappings

    def test_register_overwrite(self, mapper):
        mapper.register_custom_mapping("my_pattern", "newton")
        mapper.register_custom_mapping("my_pattern", "jaxsim")
        assert mapper._custom_mappings["my_pattern"] == "jaxsim"


# ═══════════════════════════════════════════════════════════════════
# get_patterns_by_engine
# ═══════════════════════════════════════════════════════════════════


class TestGetPatternsByEngine:
    """Test get_patterns_by_engine method."""

    def test_newton_patterns(self, mapper):
        patterns = mapper.get_patterns_by_engine("newton")
        assert "cfd" in patterns
        assert "climate_gcm" in patterns
        assert "n_body" in patterns

    def test_torchsim_patterns(self, mapper):
        patterns = mapper.get_patterns_by_engine("torchsim")
        assert "molecular_dynamics" in patterns
        assert "dft" in patterns

    def test_jaxsim_patterns(self, mapper):
        patterns = mapper.get_patterns_by_engine("jaxsim")
        assert "double_pendulum" in patterns

    def test_schr_patterns(self, mapper):
        patterns = mapper.get_patterns_by_engine("schr")
        assert "quantum_harmonic" in patterns

    def test_legacy_patterns(self, mapper):
        patterns = mapper.get_patterns_by_engine("legacy")
        assert isinstance(patterns, list)

    def test_no_patterns_for_invalid(self, mapper):
        patterns = mapper.get_patterns_by_engine("invalid")
        assert patterns == []


# ═══════════════════════════════════════════════════════════════════
# get_engine_stats
# ═══════════════════════════════════════════════════════════════════


class TestGetEngineStats:
    """Test get_engine_stats method."""

    def test_structure(self, mapper):
        stats = mapper.get_engine_stats()
        assert "newton" in stats
        assert "jaxsim" in stats
        assert "torchsim" in stats
        assert "schr" in stats
        assert "legacy" in stats

    def test_newton_stats(self, mapper):
        stats = mapper.get_engine_stats()
        newton_stats = stats["newton"]
        assert "pattern_count" in newton_stats
        assert "patterns" in newton_stats
        assert "avg_acceleration" in newton_stats
        assert newton_stats["pattern_count"] > 0

    def test_legacy_stats(self, mapper):
        stats = mapper.get_engine_stats()
        legacy_stats = stats["legacy"]
        assert legacy_stats["pattern_count"] == 0
        assert legacy_stats["avg_acceleration"] == 0.0


# ═══════════════════════════════════════════════════════════════════
# is_gpu_pattern
# ═══════════════════════════════════════════════════════════════════


class TestIsGPUPattern:
    """Test is_gpu_pattern method."""

    def test_known_gpu_patterns(self, mapper):
        assert mapper.is_gpu_pattern("cfd") is True
        assert mapper.is_gpu_pattern("molecular_dynamics") is True
        assert mapper.is_gpu_pattern("quantum_harmonic") is True

    def test_unknown_pattern(self, mapper):
        assert mapper.is_gpu_pattern("unknown_xyz") is False


# ═══════════════════════════════════════════════════════════════════
# recommend_engine
# ═══════════════════════════════════════════════════════════════════


class TestRecommendEngine:
    """Test recommend_engine method."""

    def test_legacy_pattern(self, mapper):
        result = mapper.recommend_engine("unknown_pattern")
        assert result == "legacy"

    def test_requires_gradients(self, mapper):
        result = mapper.recommend_engine("cfd", requires_gradients=True)
        assert result == "jaxsim"

    def test_large_grid(self, mapper):
        result = mapper.recommend_engine("cfd", grid_size=(200, 200, 200))
        assert result == "newton"

    def test_small_grid(self, mapper):
        result = mapper.recommend_engine("cfd", grid_size=(10, 10))
        assert result == "legacy"

    def test_medium_grid(self, mapper):
        result = mapper.recommend_engine("cfd", grid_size=(100, 100))
        assert result == "newton"

    def test_gradients_with_torchsim(self, mapper):
        result = mapper.recommend_engine("molecular_dynamics", requires_gradients=True)
        # torchsim is not in ("newton", "jaxsim") so it returns base_engine
        assert result == "torchsim"


# ═══════════════════════════════════════════════════════════════════
# PatternMetadata
# ═══════════════════════════════════════════════════════════════════


class TestPatternMetadata:
    """Test PatternMetadata dataclass."""

    def test_defaults(self):
        meta = PatternMetadata(pattern_id="test", category="test", complexity="low")
        assert meta.typical_grid_size is None
        assert meta.time_steps is None
        assert meta.requires_gradients is False
        assert meta.custom_engine is None

    def test_custom_values(self):
        meta = PatternMetadata(
            pattern_id="cfd",
            category="fluid",
            complexity="high",
            typical_grid_size=(256, 256, 256),
            time_steps=1000,
            requires_gradients=True,
            custom_engine="newton",
        )
        assert meta.typical_grid_size == (256, 256, 256)
        assert meta.time_steps == 1000
        assert meta.requires_gradients is True
        assert meta.custom_engine == "newton"


# ═══════════════════════════════════════════════════════════════════
# PATTERN_ENGINE_MAP Constant
# ═══════════════════════════════════════════════════════════════════


class TestPatternEngineMapConstant:
    """Test the module-level PATTERN_ENGINE_MAP constant."""

    def test_is_dict(self):
        from simulations.pattern_engine_map import PATTERN_ENGINE_MAP
        assert isinstance(PATTERN_ENGINE_MAP, dict)
        assert len(PATTERN_ENGINE_MAP) > 0


# ═══════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_get_engine(self):
        assert get_engine("cfd") == "newton"
        assert get_engine("unknown") == "legacy"

    def test_get_gpu_accelerated_patterns(self):
        patterns = get_gpu_accelerated_patterns()
        assert isinstance(patterns, list)
        assert "cfd" in patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
