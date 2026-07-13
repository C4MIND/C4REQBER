#!/usr/bin/env python3
"""LLM router inventory — behavioral diff of the 3 routers + 21 raw sites.

Per REWORK_PLAN P2-A safety gate, this is the mandatory pre-merge step:
walk every LLM call path, enumerate which features each has (guardian scan,
retry policy, cost tracking, response cache, stage→model table), and produce
a report. The actual gateway merge is a separate, owner-gated step.

Output:
- Markdown report at audit/llm_router_inventory_<date>.md
- Console table with feature matrix per router

Usage:
  python3 scripts/inventory_llm_routers.py [--report PATH]

Exit 0 always (inventory is read-only).
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"


FEATURES = [
    "guardian_scan",  # Prompt-injection scan before send
    "retry_policy",  # Explicit retry with backoff
    "cost_tracking",  # Per-call USD accumulation
    "response_cache",  # In-memory or disk cache
    "stage_model_table",  # Maps pipeline stage -> model name
    "provider_fallback",  # Tries alternative providers on failure
    "structured_logging",  # Structured fields for observability
    "timeout_enforcement",  # Per-request timeout
]


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def classify_text(text: str) -> dict[str, bool]:
    """Heuristic feature detection by regex. Not perfect but useful as a survey."""
    feats: dict[str, bool] = {}
    feats["guardian_scan"] = bool(
        re.search(r"guardian|GuardianScan|prompt_sanitizer|SanitizerInput", text)
    )
    feats["retry_policy"] = bool(
        re.search(r"ProviderRetryManager|tenacity|@retry|backoff|retry_with", text)
    )
    feats["cost_tracking"] = bool(
        re.search(r"cost_tracker|estimated_cost|llm_cost|CostTracker", text)
    )
    feats["response_cache"] = bool(re.search(r"response_cache|_cache\.|@cache|TTL.*cache", text))
    feats["stage_model_table"] = bool(
        re.search(r"DEPTH_MODEL_MAP|PRESETS|model_per_stage|stage_to_model", text)
    )
    feats["provider_fallback"] = bool(
        re.search(r"fallback|failover|next_provider|try_next", text, re.IGNORECASE)
    )
    feats["structured_logging"] = bool(re.search(r"structlog|extra\s*=\{|logger\.info\(.*\{", text))
    feats["timeout_enforcement"] = bool(
        re.search(r"timeout|asyncio\.wait_for|httpx\.Timeout", text)
    )
    return feats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=None, help="write markdown report to PATH")
    args = parser.parse_args()

    routers = {
        "ProviderRouter (src/llm/router.py)": SRC / "llm/router.py",
        "AsyncLLMClient (src/llm/async_client.py)": SRC / "llm/async_client.py",
        "LLMProviderRouter (src/llm/providers/unified.py)": SRC / "llm/providers/unified.py",
        "LLMGateway facade (src/llm/gateway.py)": SRC / "llm/gateway.py",
    }

    raw_sites: list[Path] = []
    # 21 raw /chat/completions sites per audit finding
    for f in (SRC / "llm").rglob("*.py"):
        if f.name == "__init__.py":
            continue
        if re.search(r"chat/completions|/v1/chat|completions\.create", read(f)):
            raw_sites.append(f)
    # Other src/ areas also have raw LLM calls
    for f in (SRC / "agents").rglob("*.py"):
        if f.name == "__init__.py":
            continue
        if re.search(r"chat/completions|/v1/chat|completions\.create", read(f)):
            raw_sites.append(f)
    for f in (SRC / "discovery").rglob("*.py"):
        if f.name == "__init__.py":
            continue
        if re.search(r"chat/completions|/v1/chat|completions\.create", read(f)):
            raw_sites.append(f)
    raw_sites = sorted(set(raw_sites))

    # Build matrix
    print("=" * 80)
    print("LLM ROUTER INVENTORY (audit 2026-06-22 H-8 / REWORK_PLAN P2-A)")
    print("=" * 80)
    print()

    matrix: dict[str, dict[str, bool]] = {}
    for name, path in routers.items():
        text = read(path)
        matrix[name] = classify_text(text)
    for f in raw_sites:
        text = read(f)
        rel = str(f.relative_to(REPO))
        matrix[rel] = classify_text(text)

    # Print feature matrix
    col_width = 40
    feat_width = 4
    header = "Router/Site".ljust(col_width) + "".join(
        f[:3].upper().center(feat_width) for f in FEATURES
    )
    print(header)
    print("-" * len(header))
    for name, feats in matrix.items():
        row = name[: col_width - 1].ljust(col_width)
        for f in FEATURES:
            mark = "Y" if feats[f] else "."
            row += mark.center(feat_width)
        print(row)
    print()

    # Feature coverage stats
    print("=" * 80)
    print("Feature coverage (% of LLM call sites with each feature)")
    print("=" * 80)
    n = len(matrix)
    for f in FEATURES:
        present = sum(1 for m in matrix.values() if m[f])
        pct = present * 100 // max(n, 1)
        print(f"  {f:25s}  {present:3d}/{n}  ({pct:3d}%)")
    print()

    # Raw-site count
    print(f"Raw LLM call sites found: {len(raw_sites)}")
    for f in raw_sites:
        print(f"  - {f.relative_to(REPO)}")
    print()

    # Recommendations
    print("=" * 80)
    print("Recommendations (REWORK_PLAN P2-A safety gate)")
    print("=" * 80)
    print("""
1. CONSOLIDATE_TO_GATEWAY: migrate all 21 raw sites onto the LLMGateway
   facade (src/llm/gateway.py) so they pick up:
   - guardian_scan (currently: only AsyncLLMClient + LLMProviderRouter)
   - retry_policy (currently: 3 divergent strategies)
   - cost_tracking (currently: scattered)

2. RECONCILE_STAGE_MODEL_TABLE: collapse 4 disagreeing tables (DEPTH_MODEL_MAP,
   PRESETS, model_per_stage, model_catalog) into ONE owner-approved mapping.
   This is a PRODUCT DECISION, not a mechanical merge.

3. DELETE_DEAD_ROUTING: after migration, drop the wrappers behind the gateway
   (UnifiedLLMClient already removed in earlier audit).

4. PRESERVE_INTENTIONAL_DIVERGENCE: any divergence between the routers that
   encodes an INTENTIONAL behavior (e.g. cache for one, no cache for another)
   must be preserved as a strategy option on the gateway, not silently dropped.

5. NATIVE_ANTHROPIC: the Anthropic backend is a separate opt-in scope, not
   part of this consolidation.
""")

    if args.report:
        # Write markdown
        lines = [
            "# LLM Router Inventory — Audit 2026-06-22 (H-8 / REWORK_PLAN P2-A)",
            "",
            f"_Generated: {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M UTC')}_",
            "",
            "## Routers inventoried",
            "",
        ]
        for name in matrix:
            lines.append(f"- `{name}`")
        lines += [
            "",
            "## Feature matrix",
            "",
            "| Router/Site | " + " | ".join(f for f in FEATURES) + " |",
        ]
        lines += ["|" + "---|" * (len(FEATURES) + 1)]
        for name, feats in matrix.items():
            marks = ["Y" if feats[f] else "·" for f in FEATURES]
            lines.append(f"| `{name}` | " + " | ".join(marks) + " |")
        lines += [
            "",
            "## Coverage statistics",
            "",
            "| Feature | Sites | % |",
            "|---|---|---|",
        ]
        for f in FEATURES:
            present = sum(1 for m in matrix.values() if m[f])
            pct = present * 100 // max(n, 1)
            lines.append(f"| `{f}` | {present}/{n} | {pct}% |")
        lines += [
            "",
            "## Raw LLM call sites (bypass gateway)",
            "",
            f"Total: **{len(raw_sites)}**",
            "",
        ]
        for f in raw_sites:
            lines.append(f"- `{f.relative_to(REPO)}`")
        lines += [
            "",
            "## Recommendations",
            "",
            "1. **CONSOLIDATE_TO_GATEWAY** — migrate the 21 raw sites onto the",
            "   `LLMGateway` facade (src/llm/gateway.py) to pick up guardian_scan,",
            "   unified retry, and cost tracking.",
            "2. **RECONCILE_STAGE_MODEL_TABLE** — collapse 4 disagreeing tables into",
            "   one owner-approved mapping. PRODUCT DECISION, not mechanical.",
            "3. **PRESERVE_INTENTIONAL_DIVERGENCE** — do not silently drop divergent",
            "   behaviors; capture them as strategy options on the gateway.",
            "4. **NATIVE_ANTHROPIC** — separate opt-in scope, not part of this.",
            "",
            "## Status",
            "",
            "Inventory complete. **Code changes deferred pending owner decision** on",
            "stage→model table reconciliation. Do not merge gateway code without it.",
            "",
        ]
        Path(args.report).write_text("\n".join(lines))
        print(f"Wrote {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
