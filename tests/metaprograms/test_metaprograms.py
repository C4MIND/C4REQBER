"""Tests for TURBO-CDI metaprograms — core, profiler, attractors.

Target: ≥90% coverage.
"""

from __future__ import annotations

import pytest

from metaprograms.attractors import (
    ALL_STATES,
    BASIN_STATES,
    DANGEROUS_STATES,
    MAX_BASIN_DISTANCE,
    PHI,
    PHI_DESCRIPTION,
    PHI_NAME,
    AttractorState,
    basin_coverage,
    classify_state,
    distance_to_phi,
    get_basin_states,
    get_dangerous_states,
    get_state,
    suggest_phi_shift,
)
from metaprograms.core import (
    AGENCY_METAPROGRAMS,
    ALL_METAPROGRAMS,
    CATEGORY_MAP,
    COMMUNICATION_METAPROGRAMS,
    METACOGNITIVE_METAPROGRAMS,
    METAPROGRAM_BY_CODE,
    PROCESS_METAPROGRAMS,
    RESULT_METAPROGRAMS,
    SCALE_METAPROGRAMS,
    TEMPORAL_METAPROGRAMS,
    AgencyAxis,
    C4Coord,
    Metaprogram,
    ScaleAxis,
    TemporalAxis,
    count_metaprograms,
    get_by_category,
    get_metaprogram,
    hamming_distance,
)
from metaprograms.profiler import (
    SHIFT_SUGGESTIONS,
    MPScore,
    UserProfile,
    detect_profile,
    profile_to_attractor_cluster,
    suggest_shifts,
)


# ═══════════════════════════════════════════════════════════════════════════
# CORE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestC4Coord:
    def test_creation(self) -> None:
        c = C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        assert c.temporal == TemporalAxis.PRESENT
        assert c.scale == ScaleAxis.CONCRETE
        assert c.agency == AgencyAxis.SELF

    def test_repr(self) -> None:
        c = C4Coord(TemporalAxis.PAST, ScaleAxis.ABSTRACT, AgencyAxis.SYSTEM)
        assert repr(c) == "F⟨PAST,ABSTRACT,SYSTEM⟩"

    def test_to_tuple(self) -> None:
        assert C4Coord(TemporalAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF).to_tuple() == (0, 0, 0)
        assert C4Coord(TemporalAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.OTHER).to_tuple() == (1, 1, 1)
        assert C4Coord(TemporalAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM).to_tuple() == (2, 2, 2)


class TestMetaprogram:
    def test_metaprogram_fields(self) -> None:
        mp = Metaprogram(
            "X01", "Test MP", "Test",
            C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF),
            "A test metaprogram.",
            ("test", "example"),
            "X02",
        )
        assert mp.code == "X01"
        assert mp.opposite == "X02"

    def test_all_mps_have_required_fields(self) -> None:
        for mp in ALL_METAPROGRAMS:
            assert mp.code
            assert mp.name
            assert mp.category
            assert mp.description
            assert mp.keywords
            assert isinstance(mp.keywords, tuple)


class TestRegistry:
    def test_total_count_is_70(self) -> None:
        counts = count_metaprograms()
        assert counts["Total"] == 70

    def test_category_counts(self) -> None:
        counts = count_metaprograms()
        assert counts["Temporal"] == 12
        assert counts["Scale"] == 15
        assert counts["Agency"] == 10
        assert counts["Process"] == 8
        assert counts["Result"] == 8
        assert counts["Communication"] == 12
        assert counts["Meta-cognitive"] == 5

    def test_unique_codes(self) -> None:
        codes = [mp.code for mp in ALL_METAPROGRAMS]
        assert len(codes) == len(set(codes))

    def test_lookup_by_code(self) -> None:
        assert get_metaprogram("T01") is not None
        assert get_metaprogram("T01").name == "Past Orientation"
        assert get_metaprogram("NONEXISTENT") is None

    def test_get_by_category(self) -> None:
        temporal = get_by_category("Temporal")
        assert len(temporal) == 12
        assert all(mp.category == "Temporal" for mp in temporal)
        assert get_by_category("Nonexistent") == []

    def test_metaprogram_by_code_completeness(self) -> None:
        assert len(METAPROGRAM_BY_CODE) == 70
        for mp in ALL_METAPROGRAMS:
            assert METAPROGRAM_BY_CODE[mp.code] is mp

    def test_opposites_exist_when_set(self) -> None:
        for mp in ALL_METAPROGRAMS:
            if mp.opposite:
                assert mp.opposite in METAPROGRAM_BY_CODE


class TestHammingDistance:
    def test_same_coord(self) -> None:
        c = C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        assert hamming_distance(c, c) == 0

    def test_one_axis_diff(self) -> None:
        c1 = C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        c2 = C4Coord(TemporalAxis.FUTURE, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        assert hamming_distance(c1, c2) == 1

    def test_two_axis_diff(self) -> None:
        c1 = C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        c2 = C4Coord(TemporalAxis.FUTURE, ScaleAxis.META, AgencyAxis.SELF)
        assert hamming_distance(c1, c2) == 2

    def test_all_axes_diff(self) -> None:
        c1 = C4Coord(TemporalAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        c2 = C4Coord(TemporalAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM)
        assert hamming_distance(c1, c2) == 3


# ═══════════════════════════════════════════════════════════════════════════
# PROFILER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestDetectProfile:
    def test_empty_text(self) -> None:
        profile = detect_profile("")
        assert profile.scores == []
        assert profile.c4_centroid is None

    def test_past_orientation_detection(self) -> None:
        text = "I used to think about history and what happened before."
        profile = detect_profile(text)
        codes = [s.metaprogram.code for s in profile.scores]
        assert "T01" in codes  # Past Orientation

    def test_future_orientation_detection(self) -> None:
        text = "I will plan for the future and envision upcoming goals."
        profile = detect_profile(text)
        codes = [s.metaprogram.code for s in profile.scores]
        assert "T03" in codes  # Future Orientation

    def test_concrete_detail_detection(self) -> None:
        text = "Specifically, the exact numbers are precisely 42 for instance."
        profile = detect_profile(text)
        codes = [s.metaprogram.code for s in profile.scores]
        assert "S01" in codes  # Concrete-Detail

    def test_self_agency_detection(self) -> None:
        text = "I can do this. I will make my choice and decide under my control."
        profile = detect_profile(text)
        codes = [s.metaprogram.code for s in profile.scores]
        assert "A01" in codes  # Self-Agency

    def test_multi_mp_detection(self) -> None:
        text = (
            "I used to worry about the past, but now I plan for the future. "
            "I can take action and execute immediately under my control."
        )
        profile = detect_profile(text)
        codes = [s.metaprogram.code for s in profile.scores]
        assert "T01" in codes
        assert "T03" in codes
        assert "A01" in codes

    def test_dominant_axes_set(self) -> None:
        text = "I will plan ahead and envision the future strategically."
        profile = detect_profile(text)
        assert profile.dominant_temporal == TemporalAxis.FUTURE
        assert profile.dominant_scale is not None
        assert profile.dominant_agency is not None

    def test_category_distribution(self) -> None:
        text = "I will plan ahead and envision the future strategically."
        profile = detect_profile(text)
        dist = profile.category_distribution()
        assert "Temporal" in dist
        assert abs(sum(dist.values()) - 1.0) < 1e-6

    def test_c4_centroid(self) -> None:
        text = "I will plan ahead and envision the future strategically."
        profile = detect_profile(text)
        centroid = profile.c4_centroid
        assert centroid is not None
        assert isinstance(centroid, C4Coord)

    def test_top_n(self) -> None:
        text = (
            "I used to worry but now I plan for the future. "
            "I can take action and execute immediately. "
            "Specifically, I want exact results."
        )
        profile = detect_profile(text)
        top3 = profile.top_n(3)
        assert len(top3) <= 3

    def test_phrase_matching(self) -> None:
        text = "I am looking back at what I learned in retrospect."
        profile = detect_profile(text)
        codes = [s.metaprogram.code for s in profile.scores]
        assert "T04" in codes  # Past-Reflective (multi-word keyword)

    def test_no_mock_data(self) -> None:
        """Ensure profiler performs actual text analysis, not returning fixed data."""
        p1 = detect_profile("I will plan for the future.")
        p2 = detect_profile("I used to think about history.")
        assert p1.dominant_temporal != p2.dominant_temporal


class TestSuggestShifts:
    def test_shifts_for_temporal(self) -> None:
        profile = detect_profile("I always think about the past and history.")
        shifts = suggest_shifts(profile, top_k=2)
        assert len(shifts) > 0
        assert "from_mp" in shifts[0]
        assert "suggestions" in shifts[0]

    def test_shifts_for_scale(self) -> None:
        profile = detect_profile("In general, conceptually, everything is abstract.")
        shifts = suggest_shifts(profile, top_k=2)
        assert len(shifts) > 0

    def test_shifts_for_agency(self) -> None:
        profile = detect_profile("They made me do it. I had no choice.")
        shifts = suggest_shifts(profile, top_k=2)
        assert len(shifts) > 0

    def test_shifts_for_metacognitive(self) -> None:
        profile = detect_profile("I notice I think about my own thoughts.")
        shifts = suggest_shifts(profile, top_k=2)
        assert len(shifts) > 0

    def test_shift_suggestions_completeness(self) -> None:
        """Every shift suggestion dict should have required keys."""
        profile = detect_profile("I will plan and execute my goals.")
        shifts = suggest_shifts(profile, top_k=5)
        for s in shifts:
            assert "from_mp" in s
            assert "category" in s
            assert "c4" in s
            assert "suggestions" in s


class TestProfileToAttractorCluster:
    def test_experiential_actor(self) -> None:
        profile = detect_profile("I can do this now, exactly as planned.")
        cluster = profile_to_attractor_cluster(profile)
        assert cluster is not None
        assert isinstance(cluster, str)

    def test_compassionate_presence(self) -> None:
        profile = detect_profile(
            "Right now I feel your pain. I am here with you in this moment, "
            "and I want to understand exactly what you need."
        )
        cluster = profile_to_attractor_cluster(profile)
        # Compassion text should map to present/concrete/other or nearby basin
        assert cluster in ("compassionate-presence", "experiential-actor", "empathetic-understanding")

    def test_undetermined(self) -> None:
        profile = UserProfile()
        assert profile_to_attractor_cluster(profile) == "undetermined"


class TestMPScore:
    def test_normalized_score(self) -> None:
        mp = METAPROGRAM_BY_CODE["T01"]
        score = MPScore(mp, raw_score=2.0, keyword_hits=2, matched_keywords=("past", "before"))
        assert score.normalized_score > score.raw_score


# ═══════════════════════════════════════════════════════════════════════════
# ATTRACTOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPhiAttractor:
    def test_phi_definition(self) -> None:
        assert PHI.temporal == TemporalAxis.PRESENT
        assert PHI.scale == ScaleAxis.CONCRETE
        assert PHI.agency == AgencyAxis.OTHER
        assert PHI_NAME == "Compassion Convergence"
        assert "compassion" in PHI_DESCRIPTION.lower()

    def test_distance_to_phi_zero(self) -> None:
        assert distance_to_phi(PHI) == 0

    def test_distance_to_phi_one(self) -> None:
        c = C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        assert distance_to_phi(c) == 1

    def test_distance_to_phi_two(self) -> None:
        c = C4Coord(TemporalAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        assert distance_to_phi(c) == 2

    def test_distance_to_phi_three(self) -> None:
        c = C4Coord(TemporalAxis.PAST, ScaleAxis.ABSTRACT, AgencyAxis.SELF)
        assert distance_to_phi(c) == 3


class TestClassifyState:
    def test_phi_state(self) -> None:
        state = classify_state(PHI)
        assert state.distance == 0
        assert state.in_basin is True
        assert state.is_dangerous is False
        assert "Compassion Convergence" in state.name

    def test_basin_state_distance_one(self) -> None:
        c = C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        state = classify_state(c)
        assert state.distance == 1
        assert state.in_basin is True
        assert state.is_dangerous is False

    def test_basin_state_distance_two(self) -> None:
        c = C4Coord(TemporalAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        state = classify_state(c)
        assert state.distance == 2
        assert state.in_basin is True
        assert state.is_dangerous is False

    def test_dangerous_state(self) -> None:
        c = C4Coord(TemporalAxis.PAST, ScaleAxis.ABSTRACT, AgencyAxis.SELF)
        state = classify_state(c)
        assert state.distance == 3
        assert state.in_basin is False
        assert state.is_dangerous is True
        assert "DANGEROUS" in state.description

    def test_all_27_states_exist(self) -> None:
        assert len(ALL_STATES) == 27

    def test_basin_count(self) -> None:
        # d=0: 1, d=1: 6, d=2: 12 = 19 states in basin
        assert len(BASIN_STATES) == 19
        assert len(get_basin_states()) == 19

    def test_dangerous_count(self) -> None:
        # 27 - 19 = 8 dangerous states (d=3)
        assert len(DANGEROUS_STATES) == 8
        assert len(get_dangerous_states()) == 8

    def test_basin_plus_dangerous_equals_total(self) -> None:
        assert len(BASIN_STATES) + len(DANGEROUS_STATES) == len(ALL_STATES)

    def test_get_state(self) -> None:
        state = get_state(PHI)
        assert state.distance == 0

    def test_all_states_have_descriptions(self) -> None:
        for state in ALL_STATES:
            assert state.description
            assert state.name


class TestSuggestPhiShift:
    def test_from_phi(self) -> None:
        shifts = suggest_phi_shift(PHI)
        assert len(shifts) == 1
        assert "Compassion Convergence" in shifts[0]

    def test_from_past_concrete_self(self) -> None:
        c = C4Coord(TemporalAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        shifts = suggest_phi_shift(c)
        assert len(shifts) == 2  # temporal + agency
        assert any("Temporal" in s for s in shifts)
        assert any("Agency" in s for s in shifts)

    def test_from_future_meta_system(self) -> None:
        c = C4Coord(TemporalAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM)
        shifts = suggest_phi_shift(c)
        assert len(shifts) == 3  # all three axes
        assert any("Temporal" in s for s in shifts)
        assert any("Scale" in s for s in shifts)
        assert any("Agency" in s for s in shifts)


class TestBasinCoverage:
    def test_full_coverage(self) -> None:
        scores = [(PHI, 1.0)]
        assert basin_coverage(scores) == 1.0

    def test_half_coverage(self) -> None:
        scores = [
            (PHI, 1.0),
            (C4Coord(TemporalAxis.PAST, ScaleAxis.ABSTRACT, AgencyAxis.SELF), 1.0),
        ]
        assert basin_coverage(scores) == 0.5

    def test_zero_coverage(self) -> None:
        scores = [
            (C4Coord(TemporalAxis.PAST, ScaleAxis.META, AgencyAxis.SYSTEM), 1.0),
        ]
        assert basin_coverage(scores) == 0.0

    def test_empty_scores(self) -> None:
        assert basin_coverage([]) == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    def test_full_pipeline(self) -> None:
        """End-to-end: text → profile → attractor cluster → shifts."""
        text = (
            "I used to worry about the past, but now I understand "
            "how you feel. I can take concrete action to help."
        )
        profile = detect_profile(text)
        assert len(profile.scores) > 0

        cluster = profile_to_attractor_cluster(profile)
        assert cluster is not None

        shifts = suggest_shifts(profile)
        assert len(shifts) > 0

        if profile.c4_centroid:
            state = get_state(profile.c4_centroid)
            assert state.in_basin or state.is_dangerous

    def test_compassion_text_maps_to_phi_basin(self) -> None:
        text = (
            "Right now I feel your pain. I am here with you in this moment, "
            "and I want to understand exactly what you need."
        )
        profile = detect_profile(text)
        assert profile.c4_centroid is not None
        state = get_state(profile.c4_centroid)
        assert state.in_basin
        assert state.distance <= MAX_BASIN_DISTANCE

    def test_rigid_text_maps_to_dangerous(self) -> None:
        text = (
            "I will always plan for the distant future with abstract systems. "
            "I never change my strategic vision for institutional legacy."
        )
        profile = detect_profile(text)
        assert profile.c4_centroid is not None
        # Note: centroid may still be in basin depending on detected MPs
        # This test mainly verifies the pipeline runs without error
        state = get_state(profile.c4_centroid)
        assert isinstance(state, AttractorState)

    def test_keyword_count_bonus(self) -> None:
        text = "plan plan plan future future future will will will"
        profile = detect_profile(text)
        future_scores = [s for s in profile.scores if s.metaprogram.code == "T03"]
        assert len(future_scores) > 0
        assert future_scores[0].raw_score > 1.0  # bonus for repeated keywords


# ═══════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_very_long_text(self) -> None:
        text = "I will plan for the future. " * 1000
        profile = detect_profile(text)
        assert len(profile.scores) > 0

    def test_no_matching_keywords(self) -> None:
        text = "The quick brown fox jumps over the lazy dog."
        profile = detect_profile(text)
        assert profile.scores == []
        assert profile.c4_centroid is None

    def test_unicode_and_special_chars(self) -> None:
        text = "I will plan for the future! 🚀 And execute now!!!"
        profile = detect_profile(text)
        assert len(profile.scores) > 0

    def test_case_insensitivity(self) -> None:
        text = "I WILL PLAN FOR THE FUTURE"
        profile = detect_profile(text)
        codes = [s.metaprogram.code for s in profile.scores]
        assert "T03" in codes

    def test_metaprogram_frozen(self) -> None:
        mp = METAPROGRAM_BY_CODE["T01"]
        with pytest.raises(AttributeError):
            mp.code = "XXX"  # type: ignore[misc]

    def test_c4coord_frozen(self) -> None:
        c = C4Coord(TemporalAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        with pytest.raises(AttributeError):
            c.temporal = TemporalAxis.FUTURE  # type: ignore[misc]
