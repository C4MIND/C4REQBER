"""
Tests for src/metamodels/mp/library.py and its submodules.

Covers: MPDimension, Metaprogram, MPProfile, MPLibrary — profiles, rotation, prompts.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.metamodels.mp.core import Metaprogram, MPDimension, MPProfile
from src.metamodels.mp.data import CORE_METAPROGRAMS
from src.metamodels.mp.patterns import MPLibrary


# ═══════════════════════════════════════════════════════════════════
# MPDimension
# ═══════════════════════════════════════════════════════════════════


class TestMPDimension:
    def test_all_dimensions(self):
        dims = list(MPDimension)
        assert len(dims) == 10
        assert MPDimension.THINKING in dims
        assert MPDimension.FEELING in dims
        assert MPDimension.DOING in dims
        assert MPDimension.RELATING in dims
        assert MPDimension.PERCEIVING in dims
        assert MPDimension.IDENTITY in dims
        assert MPDimension.TIME in dims
        assert MPDimension.CHUNKING in dims
        assert MPDimension.DIRECTION in dims
        assert MPDimension.REASON in dims

    def test_dimension_values(self):
        assert MPDimension.THINKING.value == "thinking"
        assert MPDimension.FEELING.value == "feeling"
        assert MPDimension.TIME.value == "time"


# ═══════════════════════════════════════════════════════════════════
# Metaprogram
# ═══════════════════════════════════════════════════════════════════


class TestMetaprogram:
    def test_creation(self):
        mp = Metaprogram(
            id="MP-99",
            name="Test/Program",
            name_ru="Тест/Программа",
            dimension=MPDimension.THINKING,
            pole_a="left",
            pole_b="right",
            description="A test metaprogram",
            agent_prompt_suffix="Test suffix.",
        )
        assert mp.id == "MP-99"
        assert mp.name == "Test/Program"
        assert mp.dimension == MPDimension.THINKING
        assert mp.pole_a == "left"
        assert mp.pole_b == "right"
        assert mp.agent_prompt_suffix == "Test suffix."

    def test_profile_prompt_balanced(self):
        mp = Metaprogram(
            id="MP-99",
            name="X/Y",
            name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left",
            pole_b="right",
            description="Test",
        )
        prompt = mp.profile_prompt("balanced")
        assert "Balance left and right" in prompt

    def test_profile_prompt_a(self):
        mp = Metaprogram(
            id="MP-99",
            name="X/Y",
            name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left",
            pole_b="right",
            description="Test",
        )
        prompt = mp.profile_prompt("a")
        assert "Prioritize left over right" in prompt

    def test_profile_prompt_b(self):
        mp = Metaprogram(
            id="MP-99",
            name="X/Y",
            name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left",
            pole_b="right",
            description="Test",
        )
        prompt = mp.profile_prompt("b")
        assert "Prioritize right over left" in prompt

    def test_profile_prompt_invalid_leaning(self):
        mp = Metaprogram(
            id="MP-99",
            name="X/Y",
            name_ru="X/Y",
            dimension=MPDimension.THINKING,
            pole_a="left",
            pole_b="right",
            description="Test",
        )
        prompt = mp.profile_prompt("invalid")
        assert "Balance left and right" in prompt  # defaults to balanced


# ═══════════════════════════════════════════════════════════════════
# CORE_METAPROGRAMS data
# ═══════════════════════════════════════════════════════════════════


class TestCoreMetaprograms:
    def test_count(self):
        assert len(CORE_METAPROGRAMS) == 23

    def test_all_have_id(self):
        for mp in CORE_METAPROGRAMS:
            assert mp.id.startswith("MP-")
            assert len(mp.id) >= 4

    def test_all_have_name(self):
        for mp in CORE_METAPROGRAMS:
            assert mp.name
            assert mp.name_ru

    def test_dimensions_covered(self):
        dims = {mp.dimension for mp in CORE_METAPROGRAMS}
        assert MPDimension.THINKING in dims
        assert MPDimension.FEELING in dims
        assert MPDimension.DOING in dims
        assert MPDimension.RELATING in dims
        assert MPDimension.PERCEIVING in dims
        assert MPDimension.TIME in dims
        assert MPDimension.CHUNKING in dims
        assert MPDimension.DIRECTION in dims
        assert MPDimension.REASON in dims

    def test_thinking_mps(self):
        thinking = [mp for mp in CORE_METAPROGRAMS if mp.dimension == MPDimension.THINKING]
        assert len(thinking) == 5
        ids = {mp.id for mp in thinking}
        assert ids == {"MP-01", "MP-02", "MP-03", "MP-04", "MP-05"}

    def test_mp01_toward_away(self):
        mp = next(mp for mp in CORE_METAPROGRAMS if mp.id == "MP-01")
        assert mp.pole_a == "toward goals"
        assert mp.pole_b == "away from problems"
        assert "Focus on achieving positive outcomes" in mp.agent_prompt_suffix

    def test_mp05_rational_intuitive(self):
        mp = next(mp for mp in CORE_METAPROGRAMS if mp.id == "MP-05")
        assert mp.pole_a == "logical analysis"
        assert mp.pole_b == "gut feeling"

    def test_mp14_visual_auditory_kinesthetic(self):
        mp = next(mp for mp in CORE_METAPROGRAMS if mp.id == "MP-14")
        assert mp.pole_a == "see patterns"
        assert mp.pole_b == "hear relationships"
        assert mp.dimension == MPDimension.PERCEIVING

    def test_mp16_past_present_future(self):
        mp = next(mp for mp in CORE_METAPROGRAMS if mp.id == "MP-16")
        assert mp.pole_a == "learn from history"
        assert mp.pole_b == "focus on now"
        assert mp.dimension == MPDimension.TIME


# ═══════════════════════════════════════════════════════════════════
# MPLibrary
# ═══════════════════════════════════════════════════════════════════


class TestMPLibrary:
    def test_init_loads_programs(self):
        lib = MPLibrary()
        assert len(lib.programs) == 23

    def test_get_existing(self):
        lib = MPLibrary()
        mp = lib.get("MP-01")
        assert mp is not None
        assert mp.name == "Toward/Away"

    def test_get_missing(self):
        lib = MPLibrary()
        assert lib.get("MP-999") is None

    def test_by_dimension(self):
        lib = MPLibrary()
        thinking = lib.by_dimension(MPDimension.THINKING)
        assert len(thinking) == 5
        feeling = lib.by_dimension(MPDimension.FEELING)
        assert len(feeling) == 3

    def test_by_dimension_empty(self):
        lib = MPLibrary()
        # IDENTITY has no MPs in core data
        assert lib.by_dimension(MPDimension.IDENTITY) == []

    def test_all_programs(self):
        lib = MPLibrary()
        assert len(lib.all_programs()) == 23

    def test_all_profiles(self):
        lib = MPLibrary()
        profiles = lib.all_profiles()
        assert set(profiles) == {"systems", "pragmatic", "creative", "critical", "intuitive"}

    def test_get_profile_systems(self):
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        assert profile is not None
        assert profile.name == "Systems Thinker"
        assert profile.settings["MP-03"] == "a"  # Global
        assert profile.settings["MP-15"] == "a"  # Abstract
        assert profile.settings["MP-19"] == "a"  # Deep

    def test_get_profile_pragmatic(self):
        lib = MPLibrary()
        profile = lib.get_profile("pragmatic")
        assert profile is not None
        assert profile.name == "Pragmatic Executor"
        assert profile.settings["MP-02"] == "b"  # Procedures
        assert profile.settings["MP-03"] == "b"  # Detail
        assert profile.settings["MP-15"] == "b"  # Concrete
        assert profile.settings["MP-10"] == "a"  # Fast

    def test_get_profile_creative(self):
        lib = MPLibrary()
        profile = lib.get_profile("creative")
        assert profile is not None
        assert profile.name == "Creative Explorer"
        assert profile.settings["MP-02"] == "a"  # Options
        assert profile.settings["MP-06"] == "a"  # Optimistic
        assert profile.settings["MP-22"] == "a"  # Possibility
        assert profile.settings["MP-20"] == "a"  # Goal

    def test_get_profile_critical(self):
        lib = MPLibrary()
        profile = lib.get_profile("critical")
        assert profile is not None
        assert profile.name == "Critical Analyst"
        assert profile.settings["MP-04"] == "b"  # Mismatch
        assert profile.settings["MP-06"] == "b"  # Pessimistic
        assert profile.settings["MP-23"] == "a"  # Evidence
        assert profile.settings["MP-05"] == "a"  # Rational

    def test_get_profile_intuitive(self):
        lib = MPLibrary()
        profile = lib.get_profile("intuitive")
        assert profile is not None
        assert profile.name == "Intuitive Synthesizer"
        assert profile.settings["MP-05"] == "b"  # Intuitive
        assert profile.settings["MP-04"] == "a"  # Match
        assert profile.settings["MP-14"] == "b"  # Auditory

    def test_get_profile_missing(self):
        lib = MPLibrary()
        assert lib.get_profile("nonexistent") is None

    def test_profiles_have_all_mp_ids(self):
        lib = MPLibrary()
        all_ids = {p.id for p in lib.programs}
        for name in lib.all_profiles():
            profile = lib.get_profile(name)
            profile_ids = set(profile.settings.keys())
            assert profile_ids == all_ids, f"Profile {name} missing MPs"


# ═══════════════════════════════════════════════════════════════════
# MPProfile
# ═══════════════════════════════════════════════════════════════════


class TestMPProfile:
    def test_to_prompt(self):
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        prompt = profile.to_prompt(lib)
        assert "Agent Profile: Systems Thinker" in prompt
        assert "Global/Detail: global/big picture" in prompt

    def test_to_prompt_with_missing_mp(self):
        lib = MPLibrary()
        profile = MPProfile(
            name="Test",
            name_ru="Тест",
            settings={"MP-999": "a"},  # non-existent
        )
        prompt = profile.to_prompt(lib)
        assert "Agent Profile: Test" in prompt
        # Should not crash, just skip missing MP

    def test_profile_settings_are_strings(self):
        lib = MPLibrary()
        for name in lib.all_profiles():
            profile = lib.get_profile(name)
            for _mp_id, setting in profile.settings.items():
                assert setting in {"a", "b", "balanced"}


# ═══════════════════════════════════════════════════════════════════
# MP Rotation
# ═══════════════════════════════════════════════════════════════════


class TestMPRotation:
    def test_rotate_profiles_returns_three(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Solve a complex problem", n=3)
        assert len(profiles) == 3

    def test_rotate_profiles_includes_systems_and_critical(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Any problem")
        names = [p.name for p in profiles]
        assert "Systems Thinker" in names
        assert "Critical Analyst" in names

    def test_rotate_profiles_creative_for_design(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Design a new product")
        names = [p.name for p in profiles]
        assert "Creative Explorer" in names

    def test_rotate_profiles_pragmatic_for_implement(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Implement the solution")
        names = [p.name for p in profiles]
        assert "Pragmatic Executor" in names

    def test_rotate_profiles_intuitive_for_sense(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Sense the pattern")
        names = [p.name for p in profiles]
        assert "Intuitive Synthesizer" in names

    def test_rotate_profiles_random_fallback(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Something generic")
        names = [p.name for p in profiles]
        assert len(names) == 3
        assert "Systems Thinker" in names
        assert "Critical Analyst" in names
        third = [n for n in names if n not in ("Systems Thinker", "Critical Analyst")][0]
        assert third in {"Creative Explorer", "Pragmatic Executor", "Intuitive Synthesizer"}

    def test_rotate_profiles_respects_n(self):
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Design", n=2)
        assert len(profiles) == 2

    def test_rotate_profiles_diverse(self):
        lib = MPLibrary()
        # Run multiple times to verify diversity
        all_thirds = set()
        for _ in range(10):
            profiles = lib.rotate_profiles("Build and deploy")
            names = [p.name for p in profiles]
            all_thirds.update(names)
        assert "Pragmatic Executor" in all_thirds or len(all_thirds) >= 2


# ═══════════════════════════════════════════════════════════════════
# Backward Compatibility Wrapper
# ═══════════════════════════════════════════════════════════════════


class TestBackwardCompat:
    def test_wrapper_imports(self):
        from src.metamodels.mp.library import (
            CORE_METAPROGRAMS,
            Metaprogram,
            MPDimension,
            MPLibrary,
            MPProfile,
        )

        assert CORE_METAPROGRAMS is not None
        assert MPDimension is not None
        assert MPProfile is not None
        assert Metaprogram is not None
        assert MPLibrary is not None

    def test_wrapper_same_objects(self):
        from src.metamodels.mp.library import MPLibrary as WrappedLib
        from src.metamodels.mp.patterns import MPLibrary as DirectLib

        assert WrappedLib is DirectLib
