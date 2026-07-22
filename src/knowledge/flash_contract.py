"""FlashResult SSOT — shared by CLI, MCP, API composer, and (via JSON) TUI."""

from __future__ import annotations

from typing import Any, Literal, TypedDict, cast


FlashStatus = Literal["success", "partial", "error"]
TerminalEventType = Literal["complete", "partial", "failed"]


class CitationCard(TypedDict, total=False):
    title: str
    authors: list[str] | str
    year: Any
    doi: str
    url: str
    source: str
    verified: bool
    verify_verdict: str


class FlashSearchMeta(TypedDict, total=False):
    domain: str
    sources_used: list[str]
    errors: dict[str, Any]
    tavily: str
    found: int
    verified: int


class FlashResult(TypedDict, total=False):
    status: FlashStatus
    mode: str
    answer: str
    sources: list[CitationCard]
    unverified_hits: list[CitationCard]
    source_count: int
    found_count: int
    verified_count: int
    usp_context: dict[str, Any]
    quality_score: int | float
    search_meta: FlashSearchMeta
    warnings: list[str]
    context_length: int
    # Composer framing (§4.1) — keep C4/TRIZ/hyp; never gut Flash to bare Q&A
    c4_path: dict[str, Any]
    triz_principles: list[dict[str, Any]]
    hypothesis: dict[str, Any]
    problem: str
    domain: str
    pipeline_version: str
    total_time_seconds: float
    errors: list[str]


FLASH_RESULT_CORE_KEYS: frozenset[str] = frozenset(
    {
        "status",
        "answer",
        "sources",
        "unverified_hits",
        "verified_count",
        "found_count",
        "warnings",
        "search_meta",
    }
)


def count_verified_sources(papers: list[dict[str, Any]] | None) -> int:
    """Count CitationVerifier-confirmed papers (verified flag or VERIFIED|PARTIAL)."""
    if not papers:
        return 0
    n = 0
    for p in papers:
        if p.get("verified") is True:
            n += 1
            continue
        verdict = str(p.get("verify_verdict") or "").upper()
        if verdict in {"VERIFIED", "PARTIAL"}:
            n += 1
    return n


def sanitize_biblio_row(paper: dict[str, Any]) -> dict[str, Any]:
    """Shared bibliography sanitize — delegates to flash_sources.sanitize_paper."""
    from src.knowledge.flash_sources import sanitize_paper

    return sanitize_paper(paper)


def source_cards_from_papers(
    papers: list[dict[str, Any]] | None,
    *,
    sanitize: bool = True,
    limit: int | None = 10,
) -> dict[str, Any]:
    """Partition sanitized papers into verified source cards + unverified hits."""
    from src.knowledge.flash_sources import format_source_card

    rows = [p for p in (papers or []) if isinstance(p, dict)]
    if sanitize:
        rows = [sanitize_biblio_row(p) for p in rows]

    verified_cards: list[CitationCard] = []
    unverified_cards: list[CitationCard] = []
    for row in rows:
        card = cast(CitationCard, format_source_card(row))
        verdict = str(row.get("verify_verdict") or "").upper()
        if row.get("verified") is True or verdict in {"VERIFIED", "PARTIAL"}:
            verified_cards.append(card)
        else:
            unverified_cards.append(card)

    if limit is not None:
        verified_cards = verified_cards[:limit]
        unverified_cards = unverified_cards[:limit]

    return {
        "sources": verified_cards,
        "unverified_hits": unverified_cards,
        "verified_count": count_verified_sources(rows),
        "found_count": len(rows),
    }


def derive_terminal(result_status: str | None) -> tuple[TerminalEventType, str]:
    """Map result.status → (SSE event type, job status value).

    Polling treats complete|partial|failed as terminal (see TUI JobStatus.Completed).
    Never emit SSE type=complete for partial/error outcomes.
    """
    st = (result_status or "").strip().lower()
    if st in {"failed", "error", "aborted"}:
        return "failed", "failed"
    if st in {"success", "complete", "ok"}:
        return "complete", "complete"
    # partial, missing, unknown → fail-closed (no celebration)
    return "partial", "partial"


def celebration_allowed(result_status: str | None) -> bool:
    """True only for success/complete — TUI toast.complete + burst gate."""
    st = (result_status or "").strip().lower()
    return st in {"success", "complete", "ok"}
