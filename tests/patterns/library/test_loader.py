"""Tests for loader pattern module."""

import pytest
import asyncio

from src.patterns.library.loader import (
    PatternTier,
    PatternManifest,
    PatternLoader,
    get_pattern_loader,
)


class TestPatternTier:
    def test_tiers_exist(self):
        assert PatternTier.CORE is not None
        assert PatternTier.ESSENTIAL is not None
        assert PatternTier.EXTENDED is not None
        assert PatternTier.ON_DEMAND is not None
        assert PatternTier.VALIDATION is not None


class TestPatternManifest:
    def test_default_creation(self):
        manifest = PatternManifest(
            id="test",
            name="Test Pattern",
            category="test",
            tier=PatternTier.CORE,
            module_path="test.module",
            class_name="TestPattern",
        )
        assert manifest.id == "test"
        assert manifest.loaded is False
        assert manifest.available is True
        assert manifest.estimated_size_mb == 10.0

    def test_post_init_description(self):
        manifest = PatternManifest(
            id="test",
            name="Test Pattern",
            category="test",
            tier=PatternTier.CORE,
            module_path="test.module",
            class_name="TestPattern",
        )
        assert "Test Pattern" in manifest.description

    def test_with_dependencies(self):
        manifest = PatternManifest(
            id="test",
            name="Test",
            category="test",
            tier=PatternTier.EXTENDED,
            module_path="test.module",
            class_name="TestPattern",
            dependencies=["numpy", "scipy"],
            optional_dependencies=["pandas"],
        )
        assert manifest.dependencies == ["numpy", "scipy"]
        assert manifest.optional_dependencies == ["pandas"]


class TestPatternLoader:
    @pytest.fixture
    def loader(self):
        return PatternLoader()

    def test_init(self, loader):
        assert len(loader.manifests) > 0
        assert len(loader.loaded_modules) == 0
        assert loader.auto_install is False

    def test_register_all_manifests(self, loader):
        assert "monte_carlo" in loader.manifests
        assert "agent_based" in loader.manifests
        assert "system_dynamics" in loader.manifests
        assert "circuit_simulation" in loader.manifests

    def test_get_manifest(self, loader):
        manifest = loader.get_manifest("monte_carlo")
        assert manifest is not None
        assert manifest.id == "monte_carlo"
        assert manifest.tier == PatternTier.CORE

    def test_get_manifest_missing(self, loader):
        assert loader.get_manifest("nonexistent") is None

    def test_list_available_all(self, loader):
        all_manifests = loader.list_available()
        assert len(all_manifests) > 0

    def test_list_available_by_tier(self, loader):
        core = loader.list_available(PatternTier.CORE)
        assert len(core) >= 4
        for m in core:
            assert m.tier == PatternTier.CORE

    def test_get_status(self, loader):
        status = loader.get_status()
        assert "total_patterns" in status
        assert "loaded_patterns" in status
        assert "by_tier" in status
        assert status["total_patterns"] > 0

    def test_check_package_numpy(self, loader):
        assert loader._check_package("numpy") is True

    def test_check_package_missing(self, loader):
        assert loader._check_package("nonexistent_package_xyz") is False

    @pytest.mark.asyncio
    async def test_load_pattern_unknown(self, loader):
        result = await loader.load_pattern("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_load_pattern_already_loaded(self, loader):
        loader.manifests["test_loaded"] = PatternManifest(
            id="test_loaded",
            name="Test",
            category="test",
            tier=PatternTier.CORE,
            module_path="numpy",
            class_name="ndarray",
            loaded=True,
        )
        result = await loader.load_pattern("test_loaded")
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_default(self, loader):
        loaded = await loader.initialize()
        assert isinstance(loaded, list)

    @pytest.mark.asyncio
    async def test_initialize_core_only(self, loader):
        loaded = await loader.initialize([PatternTier.CORE])
        assert isinstance(loaded, list)

    def test_pattern_might_handle(self, loader):
        from src.patterns.core import Hypothesis

        h = Hypothesis(title="finite element stress analysis", description="structural mechanics")
        manifest = loader.manifests.get("fem")
        if manifest:
            result = asyncio.run(loader._pattern_might_handle(manifest, h))
            assert result is True

    def test_singleton(self):
        loader1 = get_pattern_loader()
        loader2 = get_pattern_loader()
        assert loader1 is loader2

    def test_manifest_attributes(self, loader):
        manifest = loader.manifests["monte_carlo"]
        assert manifest.loaded is True
        assert manifest.available is True
        assert "numpy" in manifest.dependencies

    def test_on_demand_patterns_exist(self, loader):
        on_demand = loader.list_available(PatternTier.ON_DEMAND)
        assert len(on_demand) > 0
        ids = [m.id for m in on_demand]
        assert "quantum_circuit" in ids or "climate_gcm" in ids
