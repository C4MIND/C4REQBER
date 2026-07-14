# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""File-based research workflow — load PDFs, images, text from a folder into the pipeline.

Usage:
    blast turbo --folder ~/papers/           # pipeline from local files only
    blast turbo --folder ~/papers/ --hybrid  # local files + 33 sources
    blast turbo "topic"                       # 33 sources only (default)

Supports: PDF (pymupdf/pdfplumber), images (tesseract/easyocr), .txt, .md.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

SUPPORTED = {".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def scan_folder(folder: str) -> list[dict[str, Any]]:
    """Scan folder for supported files, extract text content into source dicts."""
    path = Path(folder).expanduser().resolve()
    if not path.exists():
        logger.warning("Folder not found: %s", path)
        return []

    sources: list[dict[str, Any]] = []
    for f in path.iterdir():
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in SUPPORTED:
            continue

        text = _extract_text(f, ext)
        if text:
            sources.append({
                "title": f.stem.replace("_", " ").replace("-", " ").title(),
                "snippet": text[:500],
                "full_text": text[:5000],
                "authors": "Local File",
                "year": "",
                "venue": f"local://{folder}",
                "url": f"file://{f.absolute()}",
                "source": "local_folder",
                "file_type": ext,
                "file_size": f.stat().st_size,
            })

    logger.info("Scanned %s: %d files → %d sources", folder,
                 sum(1 for _ in path.iterdir() if _.is_file()), len(sources))
    return sources


def _extract_text(filepath: Path, ext: str) -> str:
    """Extract text from file based on extension."""
    if ext in (".txt", ".md"):
        try:
            return filepath.read_text(encoding="utf-8")[:10000]
        except Exception:
            logger.warning("Text file read failed: %s", filepath, exc_info=True)
            return ""

    if ext == ".pdf":
        return _extract_pdf(filepath)

    if ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return _extract_ocr(filepath)

    return ""


def _extract_pdf(filepath: Path) -> str:
    """Extract text from PDF using pymupdf or pdfplumber."""
    for lib in ["pymupdf", "fitz"]:
        try:
            import importlib
            mod = importlib.import_module(lib)
            doc = mod.open(str(filepath))
            pages = [doc[i].get_text() for i in range(min(len(doc), 20))]
            return "\n".join(pages)[:10000]
        except Exception:
            logger.debug("PDF extraction with %s failed for %s", lib, filepath.name, exc_info=True)
            continue

    try:
        import pdfplumber
        with pdfplumber.open(str(filepath)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages[:20]]
            return "\n".join(pages)[:10000]
    except Exception:
        logger.debug("File extraction failed", exc_info=True)

        pass

    logger.debug("No PDF extractor available for %s", filepath.name)
    return ""


def _extract_ocr(filepath: Path) -> str:
    """OCR extraction from image using tesseract or easyocr."""
    # Try tesseract (fast, local)
    try:
        import subprocess
        result = subprocess.run(
            ["tesseract", str(filepath), "stdout", "-l", "eng+rus+chi_sim"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout[:5000]
    except Exception:
        logger.debug("File extraction failed", exc_info=True)

        pass

    # Try easyocr (deep learning based)
    try:
        import easyocr
        reader = easyocr.Reader(["en", "ru", "ch_sim"], gpu=False)
        result = reader.readtext(str(filepath), detail=0)
        return " ".join(result)[:5000]
    except Exception:
        logger.debug("File extraction failed", exc_info=True)

        pass

    logger.debug("No OCR engine available for %s", filepath.name)
    return ""
