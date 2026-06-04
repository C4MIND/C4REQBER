from __future__ import annotations


"""C4 Mascot — Meta-Mind Commentary System."""

import random


MASCOT_COMMENTS = {
    "start": [
        "Cognitive space deployed. 27 dimensions.",
        "Pattern recognition active. 27-dimensional C4 space.",
        "C4 information entity activated.",
    ],
    "discovery": [
        "Isomorphism detected. Unindexed.",
        "TRIZ contradiction resolved. Principle applied.",
        "Structural resonance: 0.87. Match recorded.",
    ],
    "complete": [
        "Discovery recorded in cognitive history.",
        "Pipeline step completed. Output stored.",
        "State cached. Reusable for future queries.",
    ],
    "error": [
        "Anomaly in cognitive field. Restarting...",
        "Information noise. Filtering.",
    ],
}


class MascotCommentary:
    """Meta-mind narrator for C4 cube. Aligns with SOUL.md voice: technical, concise, direct."""

    def __init__(self, local_model_path: str | None = None) -> None:
        self.local_model: str | None = None
        if local_model_path:
            self._load_local_model(local_model_path)

    def comment(self, phase: str) -> str:
        """Generate commentary for current pipeline phase. Aligns with SOUL.md."""
        return self._build_comment(phase)

    def _load_local_model(self, path: str) -> None:
        """Try to load a local LLM model for commentary generation."""
        try:
            import httpx
            httpx.get("http://localhost:11434/api/tags", timeout=2)
            self.local_model = "ollama"
            return
        except (ImportError, httpx.HTTPError):
            pass
        try:
            import httpx
            httpx.get("http://localhost:1234/v1/models", timeout=2)
            self.local_model = "lmstudio"
            return
        except (ImportError, httpx.HTTPError):
            pass
        self.local_model = None

    def _build_comment(self, phase: str) -> str:
        """Construct comment with SOUL.md consistency check."""
        base_comments = MASCOT_COMMENTS.get(phase, MASCOT_COMMENTS["discovery"])
        comment = random.choice(base_comments)
        # Soul consistency check: remove forbidden emotive terms
        forbidden_terms = {
            "curious", "interesting", "great", "amazing", "wow",
            "happy", "excellent", "awesome", "unexpected", "surprising"
        }
        for term in forbidden_terms:
            if term in comment.lower():
                comment = comment.replace(term, "detected" if term in {"curious", "interesting"} else "processed")
        # Enforce conciseness (<80 chars)
        if len(comment) > 80:
            comment = comment[:77] + "..."
        return comment
