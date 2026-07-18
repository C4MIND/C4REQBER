"""Shared polite contact email for OpenAlex / Crossref / Unpaywall mailto."""

from __future__ import annotations

import os


def contact_email() -> str:
    """Return a non-example.com contact email for academic API politeness.

    Prefer env (C4_CONTACT_EMAIL, CROSSREF_MAILTO, UNPAYWALL_EMAIL, OPENALEX_MAILTO).
    Falls back to a stable project address — never example.com.
    """
    for key in (
        "C4_CONTACT_EMAIL",
        "CROSSREF_MAILTO",
        "UNPAYWALL_EMAIL",
        "OPENALEX_MAILTO",
    ):
        val = (os.environ.get(key) or "").strip()
        if val and "example.com" not in val.lower():
            return val
    return "c4reqber@c4reqber.org"
