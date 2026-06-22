# Deferred work — 2026-06-22 audit

This document captures items that the `REWORK_PLAN.md` and `MASTER_AUDIT_2026-06-22.md`
recommend deferring or skipping, with the reasoning preserved for future
maintainers. Treat each entry as an explicit "we considered this, here's why
we're not doing it now."

---

## DEFERRED: P2-D — Pattern base + worker-boundary POC

**Source:** REWORK_PLAN §P2-D + §P4-2

**What it is:** Consolidate the three parallel "pattern" conventions
(`SimulationPattern` in `src/patterns/core.py`, `BasePattern` in
`src/patterns/library/base.py`, and ~46 bare classes) onto one ABC with a
serializable `SimulationResult` type. Move the runner to a process boundary
for interruptible simulations.

**What's already landed:**
- `PatternResult` dataclass for the P2-D ABC PoC (`cb29bac`).

**Why deferred (verbatim from REWORK_PLAN):**
> "Revised recommendation: defer all of P2-D until the worker boundary (P4) is
> greenlit, then do it *as part of* building that POC. Every slice is
> semantic migration of working numeric code, and the reflection runner
> already provides a working unification seam at the single `run_pattern`
> chokepoint. Speculative consolidation now = churn without a consumer,
> against the dead-end-Python stance. The one thing P4 genuinely needs (a
> serializable result across the process boundary) is cheapest to add *at
> the chokepoint when the worker exists*, not by migrating 53 patterns up
> front."

**When to revisit:** When (if) the P4 worker boundary becomes a real
priority. Track via the REWORK_PLAN P4-2 mini-plan (not yet started).

---

## DEFERRED: P4 — Worker-boundary POC (embeddings + patterns/simulations)

**Source:** REWORK_PLAN §P4-1 + §P4-2

**What it is:** Carve out the heavy-Python surface (numerics, simulations,
embeddings) into isolated workers behind a process + serializable contract.
The `embeddings` worker is ~95% ready (single function to migrate). The
`patterns + simulations` worker depends on the P2-D serializable result.

**Why deferred:** P4 is a `no-regret-as-proof` track, not a user-facing fix.
The REWORK_PLAN's posture is "Python is a tidy dead-end" — building
elaborate worker scaffolding on Python we're going to discard is wasted
churn. P4 becomes valuable only if the Agda rewrite is actually greenlit.

**Cost of deferring:** None in the short term. The current `embeddings`
engine and `PatternRunner` (reflection-based) work fine.

**When to revisit:** Only if the Agda-core rewrite is approved and a
worker boundary is needed to run Python workers safely from a typed core.
Until then, leave as-is.

---

## DEFERRED: P2-A A2 — LLM cross-cutting unification

**Source:** REWORK_PLAN §P2-A2

**What it is:** A1 (already landed) consolidated the LLM gateway facades
equivalence-preservingly. A2 would go further: apply guardian + cost +
cache + retry uniformly to every call, regardless of which path the caller
was on. This is a *behavior change* (calls that previously bypassed
guardian would now be scanned; calls without a retry policy would gain one).

**Why deferred (verbatim from REWORK_PLAN):**
> "A2 — cross-cutting unification (separate, opt-in, owner-gated): apply
> guardian/cost/cache/one-retry-policy uniformly to every call. This is
> the audit's real prize but it **changes behavior** → defer; do it
> deliberately, per-concern, with the owner aware (e.g. 'now every LLM
> call is guardian-scanned')."

**Status:** Owner-gated. Requires the maintainer to opt in per-concern
("apply guardian to all LLM calls", "unify retry policy to backoff X",
etc.). Not a single mechanical change.

**When to revisit:** When the maintainer is ready to commit to the
specific behavior changes. The `audit/llm_router_inventory_2026-06-22.md`
already inventories which routers have which features; A2 is a product
decision about which features to enforce where.

---

## DEFERRED: P3-3 — Persistence decision (SQLite vs Postgres)

**Source:** REWORK_PLAN §P3-3

**What it is:** Currently the project ships both:
- `src/api/db_manager.py` (SQLite, used by `db_manager.SQLiteDatabase`),
  with the round-5 audit fixes (WAL, `busy_timeout=5000`,
  `foreign_keys=ON`).
- `src/api/database.py` (Postgres module) — removed in P1 (was never
  imported).
- `k8s/postgres.yaml`, `k8s/migrate-job.yaml`, `alembic/` scaffolding,
  `docker-compose.prod.yml` with Postgres service, `docker-compose.test.yml`
  with Postgres service.

**Why deferred:** This is a *deployment* decision, not a code-quality one.
Postgres + k8s + Alembic scaffolding is correct for production-on-k8s
deployments. SQLite + `src/api/db_manager.py` is correct for single-node
or test deployments. Both are wired but the project hasn't picked one
authoritatively.

**Proposed resolution (REWORK_PLAN §P3-3 options):**
1. Drop k8s/Postgres scaffolding → SQLite-only (simpler, no prod-grade
   HA but works for the AI-agents-MCP use case).
2. Implement real Postgres CRUD + real Alembic migrations (production-grade
   but multi-day work).

**Recommendation:** Option 1 (drop). The MCP server use case is
horizontal-scaling-of-stateless-agents-with-a-shared-state, which works
fine on SQLite (with WAL for concurrent reads). Postgres adds operational
complexity that no current consumer needs. *But this is a deploy decision,
not a code-cleanup decision — defer to the maintainer.*

---

## DEFERRED: Phase 1 reorg (reorg/* + stab/* branches, 26 commits)

**Source:** MERGE_PLAN.md, frozen at 2026-06-08

**What it is:** 26 commits on `reorg/01-subtraction` → `reorg/12-arch-doc`
+ `stab/01-bug-sweep` → `stab/08-import-sweep` representing an in-place
refactor of the Python codebase (~84.5k LOC deletion in MR-1, 11-commit
core de-cycling refactor in MR-2, etc.).

**Why deferred:** Since the reorg was frozen (2026-06-08), `feat/production-upgrade`
has accumulated 91+ commits of Round 5 audit work that touches most of
the same modules the reorg was refactoring. The reorg branches are likely
significantly drifted from the post-audit codebase, with merge conflicts
on the LLM / pipeline / API paths in particular.

**Proposed resolution:**
- **(a) Rebase:** bring `stab/08-import-sweep` up to current
  `feat/production-upgrade` head. High conflict risk on LLM paths. The
  work was *good* (proper dead-code deletion, acyclic dependency graph)
  but the cost of rebasing is real.
- **(b) Abandon:** per the REWORK_PLAN "Python is a tidy dead-end" stance,
  the refactor was for a Python codebase we're not going to expand much.
  Close `reorg/*` and `stab/*` branches with a pointer to this deferral.
  The 26 commits stay reachable in git history; the work is preserved
  for reference but not pursued.

**Recommendation:** (b) Abandon. The refactor's *substance* (dead-code
deletion, dependency de-cycling) is already done *post hoc* by the Round 1
P1 subtraction (155 files deleted) and Round 5 audit. The remaining value
of the reorg was the dependency-graph re-organization, which the audit's
quick wins have already partially achieved (8-package DAG mentioned in
the master audit).

**Action taken (2026-06-22):** Tagged the reorg tip
(`stab/08-import-sweep` = `9c44cee`) as `archive/phase1-reorg-2026-06-08`
so the work is preserved in history. The 18 working branches
(`reorg/01..12` + `stab/01..08`) remain reachable but not pursued.
The tag's annotation includes the exact `git branch -D` command for a
future maintainer who wants to clean them up. No branches were deleted
(this audit only tags; deletion is a separate explicit step).

---

## Summary table

| ID | Item | Reason | Revisit when |
|----|------|--------|--------------|
| P2-D | Pattern base + worker POC | Speculative without P4 consumer | P4 greenlit |
| P4 | Worker-boundary POC | "Python is a tidy dead-end" | Agda rewrite approved |
| P2-A A2 | LLM cross-cutting unification | Behavior change, owner-gated | Maintainer opts in |
| P3-3 | SQLite vs Postgres | Deploy decision | Maintainer picks one |
| Phase 1 reorg | 26 commits on reorg/* | Drifted, post-Round-5 | Maintainer picks (a) rebase or (b) abandon |
