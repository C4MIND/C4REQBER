"""
Unit tests for complexity_adapter.py
Tests for ComplexityLevel enum, DisclosureConfig, and filtering logic
"""

import pytest
from pydantic import ValidationError

from src.core.complexity_adapter import (
    ADVANCED_CONFIG,
    CURRENT_CONFIG_VERSION,
    EXPERT_CONFIG,
    LITE_CONFIG,
    ComplexityLevel,
    DisclosureConfig,
    UserLevelStorage,
    get_config,
    validate_level,
)


class TestComplexityLevel:
    """Tests for ComplexityLevel enum"""

    def test_complexity_level_values(self):
        """Test that all levels exist with correct values"""
        assert ComplexityLevel.LITE.value == "lite"
        assert ComplexityLevel.ADVANCED.value == "advanced"
        assert ComplexityLevel.EXPERT.value == "expert"

    def test_complexity_level_iteration(self):
        """Test that we can iterate over all levels"""
        levels = list(ComplexityLevel)
        assert len(levels) == 3
        assert all(isinstance(level, ComplexityLevel) for level in levels)


class TestDisclosureConfig:
    """Tests for DisclosureConfig Pydantic model"""

    def test_default_config(self):
        """Test default values when creating new config"""
        config = DisclosureConfig()

        assert config.show_c4_coordinates is False
        assert config.show_operators is False
        assert config.show_pipeline_steps is False
        assert config.show_agent_details is False
        assert config.show_troubleshooting is False
        assert config.allow_custom_operators is False
        assert config.allow_wasm_upload is False

    def test_custom_config(self):
        """Test creating config with custom values"""
        config = DisclosureConfig(
            show_c4_coordinates=True, show_operators=True, allow_custom_operators=True
        )

        assert config.show_c4_coordinates is True
        assert config.show_operators is True
        assert config.show_pipeline_steps is False  # default
        assert config.allow_custom_operators is True
        assert config.allow_wasm_upload is False  # default

    def test_config_immutability(self):
        """Test that config fields are immutable (Pydantic frozen)"""
        config = DisclosureConfig()

        with pytest.raises(ValidationError):
            config.show_c4_coordinates = True

    def test_config_serialization(self):
        """Test converting config to dict/JSON"""
        config = DisclosureConfig(show_c4_coordinates=True, show_operators=True)

        config_dict = config.model_dump()
        assert config_dict["show_c4_coordinates"] is True
        assert config_dict["show_operators"] is True
        assert "show_pipeline_steps" in config_dict


class TestPreConfiguredConfigs:
    """Tests for LITE_CONFIG, ADVANCED_CONFIG, EXPERT_CONFIG"""

    def test_lite_config(self):
        """Test Lite config has all features hidden"""
        config = LITE_CONFIG

        assert config.show_c4_coordinates is False
        assert config.show_operators is False
        assert config.show_pipeline_steps is False
        assert config.show_agent_details is False
        assert config.show_troubleshooting is False
        assert config.allow_custom_operators is False
        assert config.allow_wasm_upload is False

    def test_advanced_config(self):
        """Test Advanced config shows reasoning but no customization"""
        config = ADVANCED_CONFIG

        assert config.show_c4_coordinates is True
        assert config.show_operators is True
        assert config.show_pipeline_steps is True
        assert config.show_agent_details is True
        assert config.show_troubleshooting is True
        assert config.allow_custom_operators is False
        assert config.allow_wasm_upload is False

    def test_expert_config(self):
        """Test Expert config shows everything including customization"""
        config = EXPERT_CONFIG

        assert config.show_c4_coordinates is True
        assert config.show_operators is True
        assert config.show_pipeline_steps is True
        assert config.show_agent_details is True
        assert config.show_troubleshooting is True
        assert config.allow_custom_operators is True
        assert config.allow_wasm_upload is True


class TestGetConfig:
    """Tests for get_config() function"""

    def test_get_lite_config(self):
        """Test getting Lite config"""
        config = get_config(ComplexityLevel.LITE)
        assert config is LITE_CONFIG

    def test_get_advanced_config(self):
        """Test getting Advanced config"""
        config = get_config(ComplexityLevel.ADVANCED)
        assert config is ADVANCED_CONFIG

    def test_get_expert_config(self):
        """Test getting Expert config"""
        config = get_config(ComplexityLevel.EXPERT)
        assert config is EXPERT_CONFIG

    def test_get_config_invalid_type(self):
        """Test that invalid level raises ValueError"""
        with pytest.raises(ValueError, match="Invalid complexity level"):
            get_config("invalid")  # type: ignore

    def test_get_config_none(self):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError):
            get_config(None)  # type: ignore


class TestValidateLevel:
    """Tests for validate_level() function"""

    def test_validate_lite_string(self):
        """Test validating 'lite' string"""
        level = validate_level("lite")
        assert level == ComplexityLevel.LITE

    def test_validate_advanced_string(self):
        """Test validating 'advanced' string"""
        level = validate_level("advanced")
        assert level == ComplexityLevel.ADVANCED

    def test_validate_expert_string(self):
        """Test validating 'expert' string"""
        level = validate_level("expert")
        assert level == ComplexityLevel.EXPERT

    def test_validate_uppercase_string(self):
        """Test that uppercase strings work"""
        level = validate_level("LITE")
        assert level == ComplexityLevel.LITE

    def test_validate_mixed_case_string(self):
        """Test that mixed case strings work"""
        level = validate_level("LiTe")
        assert level == ComplexityLevel.LITE

    def test_validate_invalid_string(self):
        """Test that invalid strings raise ValueError"""
        with pytest.raises(ValueError, match="Invalid complexity level string"):
            validate_level("invalid")

    def test_validate_empty_string(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError):
            validate_level("")


class TestUserLevelStorage:
    """Tests for UserLevelStorage class"""

    def test_get_default_level(self):
        """Test new users start with Lite"""
        level = UserLevelStorage.get_default_level()
        assert level == ComplexityLevel.LITE

    def test_get_for_existing_user(self):
        """Test existing users get Advanced (preserve experience)"""
        level = UserLevelStorage.get_for_existing_user()
        assert level == ComplexityLevel.ADVANCED


class TestConfigVersion:
    """Test version tracking"""

    def test_current_version_exists(self):
        """Test that version constant is defined"""
        assert CURRENT_CONFIG_VERSION is not None
        assert isinstance(CURRENT_CONFIG_VERSION, str)
        assert len(CURRENT_CONFIG_VERSION) > 0

    def test_version_format(self):
        """Test version follows semver format"""
        assert "." in CURRENT_CONFIG_VERSION  # e.g., "1.0", "2.1"


class TestConfigImmutability:
    """Ensure pre-configured configs cannot be accidentally modified"""

    def test_lite_config_immutable(self):
        """Test LITE_CONFIG is immutable"""
        config = LITE_CONFIG

        with pytest.raises(ValidationError):
            config.show_c4_coordinates = True

        with pytest.raises(ValidationError):
            config.allow_custom_operators = True

    def test_advanced_config_immutable(self):
        """Test ADVANCED_CONFIG is immutable"""
        config = ADVANCED_CONFIG

        with pytest.raises(ValidationError):
            config.allow_custom_operators = True

    def test_expert_config_immutable(self):
        """Test EXPERT_CONFIG is immutable"""
        config = EXPERT_CONFIG

        with pytest.raises(ValidationError):
            config.show_c4_coordinates = False


class TestTypeSafety:
    """Ensure type hints are properly enforced"""

    def test_get_config_return_type(self):
        """Test get_config returns DisclosureConfig"""
        config = get_config(ComplexityLevel.LITE)
        assert isinstance(config, DisclosureConfig)

    def test_validate_level_return_type(self):
        """Test validate_level returns ComplexityLevel"""
        level = validate_level("lite")
        assert isinstance(level, ComplexityLevel)

    def test_config_field_types(self):
        """Test all DisclosureConfig fields are typed as bool"""
        config = DisclosureConfig()

        assert isinstance(config.show_c4_coordinates, bool)
        assert isinstance(config.show_operators, bool)
        assert isinstance(config.show_pipeline_steps, bool)
        assert isinstance(config.show_agent_details, bool)
        assert isinstance(config.show_troubleshooting, bool)
        assert isinstance(config.allow_custom_operators, bool)
        assert isinstance(config.allow_wasm_upload, bool)


# Edge case tests
class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_whitespace_in_validate_level(self):
        """Test validate_level strips whitespace"""
        level = validate_level("  lite  ")
        assert level == ComplexityLevel.LITE

    def test_tabs_newlines_in_validate_level(self):
        """Test validate_level handles tabs/newlines"""
        level = validate_level("\tlite\n")
        assert level == ComplexityLevel.LITE

    def test_config_identity(self):
        """Test that get_config returns same object (not copy)"""
        config1 = get_config(ComplexityLevel.LITE)
        config2 = get_config(ComplexityLevel.LITE)
        assert config1 is config2
        assert config1 is LITE_CONFIG


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
