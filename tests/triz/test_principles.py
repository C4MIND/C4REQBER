"""Tests for src/triz/principles.py"""
import pytest

from src.triz.principles import (
    PRINCIPLES,
    Principle,
    SubPrinciple,
    get_all_principles,
    get_principle,
    search_principles,
)


class TestPrincipleDataclass:
    def test_principle_attributes(self):
        p = PRINCIPLES[1]
        assert isinstance(p, Principle)
        assert p.number == 1
        assert isinstance(p.name, str)
        assert isinstance(p.description, str)
        assert isinstance(p.examples, list)
        assert isinstance(p.sub_principles, list)

    def test_sub_principle_attributes(self):
        p = PRINCIPLES[1]
        for sp in p.sub_principles:
            assert isinstance(sp, SubPrinciple)
            assert isinstance(sp.name, str)
            assert isinstance(sp.description, str)
            assert isinstance(sp.examples, list)


class TestGetPrinciple:
    def test_all_principles_exist(self):
        for i in range(1, 41):
            p = get_principle(i)
            assert p is not None
            assert p.number == i

    def test_invalid_principle(self):
        assert get_principle(0) is None
        assert get_principle(41) is None
        assert get_principle(999) is None


class TestGetAllPrinciples:
    def test_returns_all_40(self):
        all_p = get_all_principles()
        assert len(all_p) == 40

    def test_returns_list_of_principles(self):
        all_p = get_all_principles()
        for p in all_p:
            assert isinstance(p, Principle)


class TestSearchPrinciples:
    def test_search_by_name(self):
        results = search_principles("segmentation")
        assert len(results) > 0
        assert any(p.name.lower() == "segmentation" for p in results)

    def test_search_by_description(self):
        results = search_principles("divide an object")
        assert len(results) > 0

    def test_search_case_insensitive(self):
        r1 = search_principles("SEGMENTATION")
        r2 = search_principles("segmentation")
        assert len(r1) == len(r2)

    def test_search_no_results(self):
        results = search_principles("xyznonexistent123")
        assert results == []

    def test_search_empty(self):
        results = search_principles("")
        # Empty string matches all descriptions, so all principles are returned
        assert len(results) == 40
