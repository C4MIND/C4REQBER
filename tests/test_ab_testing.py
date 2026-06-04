"""Tests for A/B testing manager."""
from __future__ import annotations

import pytest

from src.pipeline.ab_testing import ABTestManager, Variant, apply_ab_config
from src.pipeline.config import PipelineConfig


class TestABTestManager:
    """Test suite for ABTestManager."""

    def test_register_variant(self):
        ab = ABTestManager()
        cfg = PipelineConfig(name="control")
        vid = ab.register_variant("control", cfg)
        assert isinstance(vid, str)
        assert len(vid) == 12

    def test_assign_user_deterministic(self):
        ab = ABTestManager()
        ab.register_variant("a", PipelineConfig(name="A"))
        ab.register_variant("b", PipelineConfig(name="B"))
        v1 = ab.assign_user("user-1")
        v2 = ab.assign_user("user-1")
        assert v1.variant_id == v2.variant_id

    def test_assign_user_different_users(self):
        ab = ABTestManager()
        ab.register_variant("a", PipelineConfig(name="A"))
        ab.register_variant("b", PipelineConfig(name="B"))
        v1 = ab.assign_user("user-1")
        v2 = ab.assign_user("user-2")
        # They may or may not differ; just ensure no crash
        assert v1.variant_id in ab._variants
        assert v2.variant_id in ab._variants

    def test_record_result(self):
        ab = ABTestManager()
        vid = ab.register_variant("v", PipelineConfig(name="V"))
        ab.record_result(vid, "quality", 0.8)
        ab.record_result(vid, "quality", 0.9)
        results = ab.get_results()
        assert results[vid]["metrics"]["quality"]["count"] == 2
        assert results[vid]["metrics"]["quality"]["mean"] == pytest.approx(0.85)

    def test_best_variant(self):
        ab = ABTestManager()
        v1 = ab.register_variant("low", PipelineConfig(name="Low"))
        v2 = ab.register_variant("high", PipelineConfig(name="High"))
        ab.record_result(v1, "score", 0.5)
        ab.record_result(v2, "score", 0.9)
        best = ab.best_variant("score")
        assert best is not None
        assert best.name == "high"

    def test_is_significant_insufficient_data(self):
        ab = ABTestManager()
        v1 = ab.register_variant("a", PipelineConfig(name="A"))
        v2 = ab.register_variant("b", PipelineConfig(name="B"))
        ab.record_result(v1, "score", 0.5)
        ab.record_result(v2, "score", 0.9)
        # Need >=2 observations per variant
        assert ab.is_significant(v1, v2, "score") is False

    def test_is_significant_with_data(self):
        ab = ABTestManager()
        v1 = ab.register_variant("a", PipelineConfig(name="A"))
        v2 = ab.register_variant("b", PipelineConfig(name="B"))
        for _ in range(10):
            ab.record_result(v1, "score", 0.5)
        for _ in range(10):
            ab.record_result(v2, "score", 0.9)
        result = ab.is_significant(v1, v2, "score")
        assert isinstance(result, bool)

    def test_get_config_for_user(self):
        ab = ABTestManager()
        cfg = PipelineConfig(name="MyConfig")
        ab.register_variant("only", cfg)
        resolved = ab.get_config_for_user("u-1")
        assert resolved.name == "MyConfig"

    def test_apply_ab_config_with_variants(self):
        ab = ABTestManager()
        cfg = PipelineConfig(name="VariantConfig")
        ab.register_variant("v", cfg)
        resolved = apply_ab_config(ab, "u-1")
        assert resolved.name == "VariantConfig"

    def test_apply_ab_config_fallback(self):
        ab = ABTestManager()
        base = PipelineConfig(name="Base")
        resolved = apply_ab_config(ab, "u-1", base_config=base)
        assert resolved.name == "Base"

    def test_apply_ab_config_no_variants_no_base_raises(self):
        ab = ABTestManager()
        with pytest.raises(ValueError):
            apply_ab_config(ab, "u-1")

    def test_traffic_weight(self):
        ab = ABTestManager()
        ab.register_variant("heavy", PipelineConfig(name="H"), traffic_weight=3.0)
        ab.register_variant("light", PipelineConfig(name="L"), traffic_weight=1.0)
        # Deterministic assignment should still work
        v = ab.assign_user("any-user")
        assert v.name in ("heavy", "light")

    def test_unknown_variant_record_raises(self):
        ab = ABTestManager()
        with pytest.raises(ValueError, match="Unknown variant"):
            ab.record_result("bad-id", "score", 1.0)

    def test_variant_mean_std(self):
        v = Variant(variant_id="x", name="X", config=PipelineConfig(name="X"))
        v.record("m", 1.0)
        v.record("m", 3.0)
        assert v.mean("m") == 2.0
        assert v.std("m") == pytest.approx(1.4142, rel=1e-3)

    def test_variant_mean_empty(self):
        v = Variant(variant_id="x", name="X", config=PipelineConfig(name="X"))
        assert v.mean("m") is None
        assert v.std("m") is None
