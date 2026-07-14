"""Tests for src/compat.py"""
import sys
from unittest.mock import patch

import pytest


class TestCompatUTC:
    def test_utc_import_py311(self):
        with patch.object(sys, "version_info", (3, 11)):
            with patch("builtins.__import__") as mock_import:
                from src import compat
                assert compat.UTC is not None

    def test_utc_value(self):
        from datetime import timezone

        from src.compat import UTC
        assert UTC is timezone.utc
