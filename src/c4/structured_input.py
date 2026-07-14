# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import re


PREFIXES: dict[str, str] = {
    "REQ:": "cyan",
    "HYP:": "yellow",
    "DATA:": "green",
    "CONSTRAINT:": "magenta",
    "VERIFY:": "bold cyan",
    "ASSUME:": "dim",
    "GOAL:": "bold yellow",
}

FORMAL_KEYWORDS: list[str] = [
    "forall", "exists", "implies", "iff", "not", "and", "or",
    "theorem", "lemma", "proof", "axiom", "corollary",
    "invariant", "precondition", "postcondition", "assert",
]


def parse_structured_input(text: str) -> dict[str, list[str]]:
    """Parse structured input."""
    sections: dict[str, list[str]] = {}
    current_section = "_raw"
    for line in text.splitlines():
        stripped = line.strip()
        matched = False
        for prefix in PREFIXES:
            if stripped.startswith(prefix):
                current_section = prefix.rstrip(":")
                sections.setdefault(current_section, []).append(stripped[len(prefix):].strip())
                matched = True
                break
        if not matched and stripped:
            sections.setdefault(current_section, []).append(stripped)
    return sections


def highlight_formal_notation(text: str) -> str:
    """Highlight formal notation."""
    for kw in FORMAL_KEYWORDS:
        text = re.sub(rf"\b{kw}\b", f"[bold yellow]{kw}[/]", text, flags=re.IGNORECASE)
    return text


def render_structured_sections(text: str) -> str:
    """Render structured sections."""
    sections = parse_structured_input(text)
    output = []
    for prefix, style in PREFIXES.items():
        key = prefix.rstrip(":")
        if key in sections:
            for item in sections[key]:
                output.append(f"[{style}]{prefix}[/] {item}")
    if "_raw" in sections:
        for item in sections["_raw"]:
            output.append(f"[dim]{item}[/]")
    return "\n".join(output) if output else text
