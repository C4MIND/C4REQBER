from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.c4.path_manifest import PathManifest, PathRegistry


class TestPathManifestFromToml:
    def test_from_toml_valid_content(self) -> None:
        content = """\
name = "test-path"
description = "A test scientist path"
c4_layer = 2
scientist = "Curie"
depends_on = ["path-a", "path-b"]
tools = ["tool1", "tool2"]
priority = 3
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            tmp_path = Path(f.name)

        try:
            manifest = PathManifest.from_toml(tmp_path)
            assert manifest is not None
            assert manifest.name == "test-path"
            assert manifest.description == "A test scientist path"
            assert manifest.c4_layer == 2
            assert manifest.scientist == "Curie"
            assert manifest.depends_on == ["path-a", "path-b"]
            assert manifest.tools == ["tool1", "tool2"]
            assert manifest.priority == 3
        finally:
            tmp_path.unlink()

    def test_from_toml_empty_content(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("")
            tmp_path = Path(f.name)

        try:
            manifest = PathManifest.from_toml(tmp_path)
            assert manifest is not None
            assert manifest.name != ""
            assert manifest.c4_layer == 1
            assert manifest.priority == 5
        finally:
            tmp_path.unlink()

    def test_from_toml_nonexistent_file(self) -> None:
        manifest = PathManifest.from_toml(Path("/nonexistent/path.toml"))
        assert manifest is None

    def test_from_toml_comments_and_whitespace(self) -> None:
        content = """\
# This is a comment
name = "curie-path"

description = "Marie Curie path"
c4_layer = 3
scientist = "Curie"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            tmp_path = Path(f.name)

        try:
            manifest = PathManifest.from_toml(tmp_path)
            assert manifest is not None
            assert manifest.name == "curie-path"
            assert manifest.c4_layer == 3
            assert manifest.scientist == "Curie"
        finally:
            tmp_path.unlink()


class TestPathRegistry:
    def test_by_layer_filtering(self) -> None:
        registry = PathRegistry()
        registry._manifests = {}
        registry._manifests["a"] = PathManifest(
            name="a", description="", c4_layer=1, scientist="general"
        )
        registry._manifests["b"] = PathManifest(
            name="b", description="", c4_layer=2, scientist="general"
        )
        registry._manifests["c"] = PathManifest(
            name="c", description="", c4_layer=1, scientist="general"
        )

        layer1 = registry.by_layer(1)
        assert len(layer1) == 2
        assert all(m.c4_layer == 1 for m in layer1)

        layer2 = registry.by_layer(2)
        assert len(layer2) == 1
        assert layer2[0].name == "b"

        layer3 = registry.by_layer(3)
        assert len(layer3) == 0

    def test_by_scientist_filtering_case_insensitive(self) -> None:
        registry = PathRegistry()
        registry._manifests = {}
        registry._manifests["a"] = PathManifest(
            name="a", description="", c4_layer=1, scientist="Einstein"
        )
        registry._manifests["b"] = PathManifest(
            name="b", description="", c4_layer=2, scientist="Curie"
        )
        registry._manifests["c"] = PathManifest(
            name="c", description="", c4_layer=1, scientist="EINSTEIN"
        )

        einsteins = registry.by_scientist("einstein")
        assert len(einsteins) == 2

        curies = registry.by_scientist("curie")
        assert len(curies) == 1
        assert curies[0].name == "b"

        none = registry.by_scientist("turing")
        assert len(none) == 0

    def test_all_sorted_by_layer_and_priority(self) -> None:
        registry = PathRegistry()
        registry._manifests = {}
        registry._manifests["b"] = PathManifest(
            name="b", description="", c4_layer=2, scientist="g", priority=5
        )
        registry._manifests["a"] = PathManifest(
            name="a", description="", c4_layer=1, scientist="g", priority=3
        )
        registry._manifests["c"] = PathManifest(
            name="c", description="", c4_layer=1, scientist="g", priority=7
        )

        all_ = registry.all
        assert len(all_) == 3
        assert all_[0].name == "c"
        assert all_[1].name == "a"
        assert all_[2].name == "b"
