"""Tests for src/compliance/license_checker.py."""
from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from src.compliance.license_checker import BSD_ALLOWED, check_commercial_use


def test_bsd_allowed():
    assert "lean4" in BSD_ALLOWED
    assert "metarocq" in BSD_ALLOWED


def test_allow_normal_source():
    assert check_commercial_use("arXiv") is True
    assert check_commercial_use("PubMed") is True


def test_reject_non_commercial():
    with patch("sys.stdout", new=StringIO()) as out:
        result = check_commercial_use("Semantic Scholar")
    assert result is False


def test_reject_proprietary():
    with patch("sys.stdout", new=StringIO()) as out:
        result = check_commercial_use("ResearchGate")
    assert result is False


def test_grok_warning():
    with patch("sys.stdout", new=StringIO()) as out:
        result = check_commercial_use("Grok (X.ai)")
    assert result is False


def test_bsd_allowed_returns_true():
    for source in BSD_ALLOWED:
        assert check_commercial_use(source) is True
