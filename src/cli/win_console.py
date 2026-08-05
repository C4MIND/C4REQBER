"""Windows console encoding helpers — avoid charmap UnicodeEncodeError."""

from __future__ import annotations

import os
import sys


def ensure_cli_utf8() -> None:
    """Reconfigure stdout/stderr to UTF-8 with replace on encode errors.

    Windows PowerShell often uses a legacy code page (cp1251/cp1252). Rich
    markup plus cube-mascot glyphs (◈▣✓) then raise UnicodeEncodeError:
    'charmap' codec can't encode characters...
    """
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, AttributeError):
            continue


def stdout_supports_unicode() -> bool:
    """True when stdout encoding can represent common mascot glyphs."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        "◈▣✓".encode(enc)
        return True
    except (LookupError, UnicodeEncodeError):
        return False
