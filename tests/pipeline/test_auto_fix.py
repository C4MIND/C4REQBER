import sys

import pytest

from src.pipeline.auto_fix import AUTO_FIX_REGISTRY, KNOWN_BROKEN, SelfHealingImporter


class TestSelfHealingImporter:
    def test_importer_registered_in_meta_path(self):
        importer = SelfHealingImporter()
        assert any(isinstance(h, SelfHealingImporter) for h in sys.meta_path), (
            "SelfHealingImporter not in sys.meta_path"
        )

    def test_find_spec_known_broken_module(self):
        importer = SelfHealingImporter()
        spec = importer.find_spec("src.knowledge.multi_source", path=None, target=None)
        assert spec is not None
        assert spec.origin is None or "orchestrator" in spec.origin

    def test_find_spec_unknown_module(self):
        importer = SelfHealingImporter()
        spec = importer.find_spec("completely.unknown.module", path=None, target=None)
        assert spec is None


class TestAutoFixRegistry:
    def test_no_noop_entries(self):
        for fix in AUTO_FIX_REGISTRY:
            assert fix.pattern != fix.replacement, f"No-op entry: {fix.description}"

    def test_known_broken_has_entries(self):
        assert len(KNOWN_BROKEN) > 0
        assert "src.knowledge.multi_source" in KNOWN_BROKEN
