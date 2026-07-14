"""Tests for src/patents/ — patent client imports."""
from __future__ import annotations


def test_import_smoke():
    from src.patents import client, uspto_client


def test_patent_dataclass():
    from src.patents.uspto_client import Patent
    p = Patent(
        patent_id="US123456",
        title="Test Patent",
        abstract="A test",
        assignee="Test Corp",
        inventors=["Inventor"],
        filing_date="2025-01-01",
        grant_date=None,
        claims_count=5,
        citations=[],
        classification="G06N",
    )
    assert p.patent_id == "US123456"
    assert p.title == "Test Patent"
    assert p.claims_count == 5


def test_get_patent_client():
    from src.patents.uspto_client import get_patent_client
    client = get_patent_client()
    assert client is not None
