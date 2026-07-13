#!/usr/bin/env python3
"""Inject site-base.js into all landing HTML heads (after viewport meta)."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "landing"
MARKER = "site-base.js"


def site_base_src(html_path: Path) -> str:
    depth = len(html_path.relative_to(ROOT).parts) - 1
    return ("../" * depth) + "js/site-base.js"


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    src = site_base_src(path)
    tag = f'<script src="{src}"></script>'
    pattern = re.compile(
        r'(<meta name="viewport" content="width=device-width, initial-scale=1\.0">)',
        re.MULTILINE,
    )
    if not pattern.search(text):
        raise SystemExit(f"no viewport meta in {path}")
    new_text = pattern.sub(r"\1\n" + tag, text, count=1)
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    for html in sorted(ROOT.rglob("*.html")):
        if patch_file(html):
            changed += 1
            print(f"patched {html.relative_to(ROOT)}")
    print(f"done: {changed} files")


if __name__ == "__main__":
    main()
