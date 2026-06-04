"""
Tests for wildfire pattern module.
"""
import numpy as np
import pytest

from src.patterns.library.wildfire import WildfireConfig, WildfirePattern



class TestConfig:
    def test_default_config(self):
        cfg = WildfireConfig()
        assert cfg.nx == 200
        assert cfg.ny == 200
        assert cfg.hours == 24
        assert cfg.fuel_type == "mixed_wood"

    def test_custom_config(self):
        cfg = WildfireConfig(nx=50, ny=50, hours=2)
        assert cfg.nx == 50
        assert cfg.hours == 2


class TestInit:
    def test_pattern_init_default(self):
        pattern = WildfirePattern()
        assert pattern.config is not None
        assert pattern.fuel.shape == (200, 200)

    def test_pattern_init_custom(self):
        cfg = WildfireConfig(nx=50, ny=50)
        pattern = WildfirePattern(cfg)
        assert pattern.fuel.shape == (50, 50)


class TestRothermel:
    def test_ros_positive(self):
        pattern = WildfirePattern()
        ros = pattern._rothermel_ros()
        assert isinstance(ros, float)
        assert ros > 0

    def test_ros_wind_effect(self):
        cfg_low = WildfireConfig(wind_speed=5.0)
        cfg_high = WildfireConfig(wind_speed=20.0)
        pattern_low = WildfirePattern(cfg_low)
        pattern_high = WildfirePattern(cfg_high)
        assert pattern_high._rothermel_ros() >= pattern_low._rothermel_ros()


class TestSlope:
    def test_slope_factor_flat(self):
        cfg = WildfireConfig(slope=0.0)
        pattern = WildfirePattern(cfg)
        sf = pattern._slope_factor(25, 25)
        assert sf >= 1.0

    def test_slope_factor_steep(self):
        cfg = WildfireConfig(slope=0.3)
        pattern = WildfirePattern(cfg)
        sf = pattern._slope_factor(25, 25)
        assert sf > 1.0


class TestIntensity:
    def test_fire_intensity(self):
        pattern = WildfirePattern()
        intensity = pattern._fire_intensity_calc(10.0)
        assert isinstance(intensity, float)
        assert intensity > 0


class TestSpotting:
    def test_spotting_enabled(self):
        cfg = WildfireConfig(spotting_enabled=True)
        pattern = WildfirePattern(cfg)
        pattern.fire_intensity[25, 25] = 5000
        n_before = len(pattern.spot_fires)
        pattern._spotting([(25, 25)], 1.0)
        assert len(pattern.spot_fires) >= n_before

    def test_spotting_disabled(self):
        cfg = WildfireConfig(spotting_enabled=False)
        pattern = WildfirePattern(cfg)
        pattern._spotting([(25, 25)], 1.0)
        assert len(pattern.spot_fires) == 0


class TestCrownFire:
    def test_crown_fire_transition(self):
        cfg = WildfireConfig(crown_fire_enabled=True, fuel_type="conifer")
        pattern = WildfirePattern(cfg)
        pattern.fire_intensity[25, 25] = 5000
        pattern._crown_fire_transition()
        assert pattern.crown_fire[25, 25]

    def test_crown_fire_disabled(self):
        cfg = WildfireConfig(crown_fire_enabled=False)
        pattern = WildfirePattern(cfg)
        pattern.fire_intensity[25, 25] = 5000
        pattern._crown_fire_transition()
        assert not pattern.crown_fire[25, 25]


class TestBurnedArea:
    def test_burned_area(self):
        pattern = WildfirePattern()
        pattern.fuel[20:30, 20:30] = 0
        area = pattern._calculate_burned_area()
        assert isinstance(area, float)
        assert area > 0

    def test_fire_perimeter(self):
        pattern = WildfirePattern()
        pattern.fuel[23:27, 23:27] = 0
        perimeter = pattern._calculate_fire_perimeter()
        assert isinstance(perimeter, float)
        assert perimeter > 0


class TestStep:
    def test_single_step(self):
        pattern = WildfirePattern()
        pattern.fire_intensity[50, 50] = 1000
        pattern._step(0.5)
        assert np.any(pattern.fire_intensity > 0)


class TestRun:
    def test_short_simulation(self):
        cfg = WildfireConfig(nx=50, ny=50, hours=1, dt=60, output_interval=5)
        pattern = WildfirePattern(cfg)
        result = pattern.run()
        assert "burned_area_ha" in result
        assert "final_state" in result
        assert len(result["time_hours"]) > 0

    def test_metadata(self):
        meta = WildfirePattern.get_metadata()
        assert meta["id"] == "wildfire"
        assert "parameters" in meta


class TestEdgeCases:
    def test_suppression(self):
        cfg = WildfireConfig(suppression_enabled=True, suppression_start=0.5)
        pattern = WildfirePattern(cfg)
        pattern.fire_intensity[25, 25] = 1000
        pattern._suppression(1.0)
        assert pattern.fire_intensity[25, 25] < 1000

    def test_no_fuel_no_spread(self):
        cfg = WildfireConfig(nx=20, ny=20)
        pattern = WildfirePattern(cfg)
        pattern.fuel[:, :] = 0
        pattern.fire_intensity[10, 10] = 1000
        pattern._fire_spread(0.5)
        assert np.sum(pattern.fire_intensity > 100) <= 1

    def test_fire_class(self):
        cfg = WildfireConfig(nx=20, ny=20, hours=1, dt=60)
        pattern = WildfirePattern(cfg)
        result = pattern.run()
        assert result["final_state"]["fire_class"] in ["Low", "Moderate", "High", "Very High", "Extreme"]
