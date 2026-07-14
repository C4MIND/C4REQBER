"""Tests for src/di/container.py — DIContainer."""
from __future__ import annotations

import pytest

from src.di.container import DIContainer, get_container, reset_container


class TestDIContainer:
    def test_register_and_resolve(self):
        c = DIContainer()
        c.register("test", 42)
        assert c.resolve("test") == 42

    def test_has(self):
        c = DIContainer()
        assert not c.has("missing")
        c.register("x", 1)
        assert c.has("x")

    def test_resolve_missing_raises(self):
        c = DIContainer()
        with pytest.raises(KeyError):
            c.resolve("nonexistent")

    def test_get_or_register_new(self):
        c = DIContainer()
        result = c.get_or_register("factory", lambda: "created")
        assert result == "created"
        assert c.resolve("factory") == "created"

    def test_get_or_register_existing(self):
        c = DIContainer()
        c.register("x", "original")
        result = c.get_or_register("x", lambda: "new")
        assert result == "original"

    def test_register_overwrite(self):
        c = DIContainer()
        c.register("x", 1)
        c.register("x", 2)
        assert c.resolve("x") == 2


class TestGlobalContainer:
    def setup_method(self):
        reset_container()

    def test_get_container(self):
        c = get_container()
        assert isinstance(c, DIContainer)

    def test_reset_container(self):
        c = get_container()
        c.register("temp", "value")
        reset_container()
        assert not c.has("temp")
