"""Tests for src/knowledge/local_files.py — file scanning and text extraction."""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.knowledge.local_files import SUPPORTED, _extract_text, scan_folder


class TestSupportedExtensions:
    def test_contains_expected_extensions(self) -> None:
        assert ".pdf" in SUPPORTED
        assert ".txt" in SUPPORTED
        assert ".md" in SUPPORTED
        assert ".png" in SUPPORTED
        assert ".jpg" in SUPPORTED
        assert ".jpeg" in SUPPORTED
        assert ".tiff" in SUPPORTED
        assert ".bmp" in SUPPORTED

    def test_is_set(self) -> None:
        assert isinstance(SUPPORTED, set)


class TestExtractText:
    def test_txt_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Hello, this is a test file content for extraction.")
            tmp_path = f.name
        try:
            result = _extract_text(Path(tmp_path), ".txt")
            assert "Hello, this is a test file content" in result
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestScanFolder:
    def test_with_txt_file_in_tempdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "sample.txt"
            txt_path.write_text("Sample content for scan_folder test.", encoding="utf-8")
            results = scan_folder(str(tmpdir))
            assert len(results) == 1
            source = results[0]
            assert source["file_type"] == ".txt"
            assert "Sample" in source["snippet"]

    def test_non_existent_folder_returns_empty(self) -> None:
        results = scan_folder("/nonexistent/path/for/testing/local_files")
        assert results == []
