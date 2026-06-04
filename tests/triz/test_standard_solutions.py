"""
Tests for TRIZ 76 Standard Solutions Database.
Verifies completeness, structure, and search functionality.
"""
import pytest

from src.triz.standard_solutions import (
    ALL_STANDARD_SOLUTIONS,
    CLASS_1_SOLUTIONS,
    CLASS_2_SOLUTIONS,
    CLASS_3_SOLUTIONS,
    CLASS_4_SOLUTIONS,
    CLASS_5_SOLUTIONS,
    SOLUTIONS_BY_CLASS,
    SOLUTIONS_BY_ID,
    count_solutions,
    get_all_solutions,
    get_solution,
    get_solutions_by_class,
    search_solutions,
)


# =============================================================================
# COUNT TESTS
# =============================================================================

class TestCounts:
    def test_total_count_is_76(self):
        counts = count_solutions()
        assert counts["total"] == 76

    def test_class_counts(self):
        counts = count_solutions()
        assert counts["Class 1"] == 13
        assert counts["Class 2"] == 23
        assert counts["Class 3"] == 6
        assert counts["Class 4"] == 17
        assert counts["Class 5"] == 17
        assert sum([counts["Class 1"], counts["Class 2"], counts["Class 3"],
                    counts["Class 4"], counts["Class 5"]]) == 76


# =============================================================================
# STRUCTURE TESTS
# =============================================================================

class TestStructure:
    def test_all_solutions_have_id(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            assert sol.id
            assert "." in sol.id

    def test_all_solutions_have_name(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            assert sol.name
            assert len(sol.name) > 3

    def test_all_solutions_have_description(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            assert sol.description
            assert len(sol.description) > 20

    def test_all_solutions_have_applicability(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            assert sol.applicability
            assert len(sol.applicability) > 10

    def test_all_solutions_have_c4_trajectory(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            assert len(sol.c4_trajectory) >= 2
            for t, s, a in sol.c4_trajectory:
                assert 0 <= t <= 2
                assert 0 <= s <= 2
                assert 0 <= a <= 2

    def test_all_solutions_have_examples(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            assert len(sol.examples) >= 2

    def test_no_duplicate_ids(self):
        ids = [s.id for s in ALL_STANDARD_SOLUTIONS]
        assert len(ids) == len(set(ids))

    def test_id_format(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            parts = sol.id.split(".")
            assert len(parts) in (2, 3), f"Invalid ID format: {sol.id}"
            for p in parts:
                assert p.isdigit(), f"Non-numeric ID part: {sol.id}"


# =============================================================================
# CLASS 1 TESTS
# =============================================================================

class TestClass1:
    def test_all_class_1_present(self):
        assert len(CLASS_1_SOLUTIONS) == 13

    def test_class_1_ids(self):
        ids = [s.id for s in CLASS_1_SOLUTIONS]
        assert "1.1.1" in ids
        assert "1.2.5" in ids

    def test_get_by_id(self):
        sol = get_solution("1.1.1")
        assert sol is not None
        assert "Complete" in sol.name or "Incomplete" in sol.name

    def test_class_1_has_sufield_focus(self):
        for sol in CLASS_1_SOLUTIONS:
            text = (sol.name + " " + sol.description).lower()
            assert any(k in text for k in ["su-field", "field", "substance", "magnetic", "gas", "void", "bubble", "particle"])

    def test_class_2_harmful_focus(self):
        for sol in CLASS_2_SOLUTIONS:
            text = (sol.name + " " + sol.description).lower()
            assert any(k in text for k in ["harmful", "protect", "remove", "damage", "shield", "wear", "fatigue", "friction", "corrosion"])

    def test_class_4_detection_focus(self):
        for sol in CLASS_4_SOLUTIONS:
            text = (sol.name + " " + sol.description).lower()
            assert any(k in text for k in ["measure", "detect", "indicator", "sensor", "frequency", "signal", "imaging"])

    def test_class_5_simplification_focus(self):
        for sol in CLASS_5_SOLUTIONS:
            text = (sol.name + " " + sol.description).lower()
            assert any(k in text for k in ["simpl", "eliminat", "reduce", "remov", "invert", "ideal", "replace", "combine", "merge", "modular", "parallel", "waste", "reuse", "environment", "divide", "segment", "speciali", "self-service"])


# =============================================================================
# SEARCH TESTS
# =============================================================================

class TestSearch:
    def test_search_by_name(self):
        results = search_solutions("ferromagnetic")
        assert len(results) > 0
        for r in results:
            assert "ferromagnetic" in r.name.lower() or "ferromagnetic" in r.description.lower()

    def test_search_by_id(self):
        results = search_solutions("2.1")
        assert len(results) > 0
        for r in results:
            assert r.id.startswith("2.1")

    def test_search_no_results(self):
        results = search_solutions("xyznonexistent123")
        assert len(results) == 0

    def test_get_solutions_by_class(self):
        c1 = get_solutions_by_class("Class 1")
        assert len(c1) == 13
        c2 = get_solutions_by_class("Class 2")
        assert len(c2) == 23

    def test_get_all_solutions(self):
        all_sols = get_all_solutions()
        assert len(all_sols) == 76


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestSerialization:
    def test_to_dict_structure(self):
        sol = get_solution("1.1.1")
        assert sol is not None
        d = sol.to_dict()
        assert "id" in d
        assert "name" in d
        assert "description" in d
        assert "applicability" in d
        assert "c4_trajectory" in d
        assert "examples" in d
        assert "related_principles" in d

    def test_all_solutions_serializable(self):
        for sol in ALL_STANDARD_SOLUTIONS:
            d = sol.to_dict()
            assert isinstance(d["id"], str)
            assert isinstance(d["name"], str)
            assert isinstance(d["examples"], list)
            assert isinstance(d["c4_trajectory"], list)
