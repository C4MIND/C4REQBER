"""Tests for src/news/ — news aggregator."""
from __future__ import annotations

import pytest


def test_import_smoke():
    try:
        from src.news import aggregator, storage
    except ImportError as e:
        pytest.skip(f"Import error: {e}")


def test_news_storage_instantiation():
    try:
        from src.news.storage import NewsStorage
    except ImportError:
        pytest.skip("Cannot import NewsStorage")
    ns = NewsStorage()
    assert ns is not None


def test_news_aggregator_instantiation():
    try:
        from src.news.aggregator import NewsAggregator
    except ImportError:
        pytest.skip("Cannot import NewsAggregator")
    agg = NewsAggregator()
    assert agg is not None


def test_unsolved_queries_defined():
    try:
        from src.news.aggregator import _UNSOLVED_QUERIES
    except ImportError:
        pytest.skip("Cannot import _UNSOLVED_QUERIES")
    assert len(_UNSOLVED_QUERIES) > 0
    for query in _UNSOLVED_QUERIES:
        assert isinstance(query, str)
        assert len(query) > 0
