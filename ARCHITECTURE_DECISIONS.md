# Architecture Decisions — review agenda after Phase 1 (reordering)

**Status:** Phase 1 (in-place structural cleanup) is complete and validated.
This document is the agenda for the **architectural review** that should set
direction before any further structural work. It is NOT a plan to execute — it is
a list of decisions for the project author to make.

> **Why now:** the mechanical cleanup (deletions, de-cycling, contracts) is done.
> Everything remaining is an *architectural decision*, not a mechanical move.
> Cutting further now would pre-empt decisions this review should own.

---

## 1. What Phase 1 did (current state)

All on `origin`, across 11 stacked branches `reorg/01..11`, `main` untouched.
Every step compile-checked, AST-verified, and test-validated; a strict self-review
pass found and fixed one real bug (see §6).

| Metric | Before | After |
|---|---|---|
| Core dependency-blob (largest import SCC) | **24 packages** | **0** (fully decomposed) |
| Dead code removed | — | **~84.5k LOC** (`v6_legacy` + the dead `v8/` parallel app) |
| `c4` kernel | trapped in the blob | **clean leaf** (depends on nothing) |
| 1189-line discovery god-module in an API router | — | split: domain logic → `discovery/pipeline_logic` |

Foundational types extracted to neutral leaf packages: `contracts`
(pipeline config + protocols), `security` (guardian), `infrastructure` (event bus).

**Two reviews, do not conflate:**
- **Code-review / merge** of `reorg/01..11` — *"is the cleanup correct?"* → yes,
  validated; needs the author's approval + a merge decision (§5).
- **Architectural review** (this doc) — *"where do we go?"* → decisions §3.

---

## 2. Dependency structure now

The pathological 24-package cycle is gone. Remaining non-trivial cycles are small,
local, and **genuine couplings (not misplaced code)** — left intentionally as-is:

- `{agent, cli, codegen, mcp_server}` — the CLI/MCP/agent tooling layer (3 mutual
  pairs that call each other's entry points).
- `{patterns, simulations}` — `PatternRunnerV2(PatternRunner)` subclass + patterns
  using the simulations GPU bridges.

Packages are now **separable** but still sit in the *old* 86-package layout — they
have NOT been reorganized into a target structure (that's decision **B**).

Target decomposition (from `REORG_ANALYSIS.md`): ~16 logical modules across tiers
(core domain · IO host · workers · clients). This is the structure the eventual
Agda-core / Python-worker split would also use.

---

## 3. Decisions to make (the agenda)

### A. Direction: Agda core + Python workers, or disciplined Python? — **THE fork**
Long-running design discussion concluded that a full-Agda rewrite is the wrong
call, but an **Agda-core (C4 algebra + pipeline DSL + verification orchestration,
`--safe`, `Fin`-based — no cubical) + Python workers via IPC** is coherent and
arguably better. Phase 1's cleanup is deliberately the *scaffold* for that split
(same module boundaries, the worker process-boundary already exists). 
- **Decides:** project author (+ the contributor, whose participation is conditional
  on this fork going to Agda-core).
- **Blocks:** B, C, D, E — almost everything downstream.

### B. Adopt the ~16-module target layout — now (Python) or defer to Agda?
Packages are separable; physically reorganizing them into the target modules is the
next structural step. If A → Agda, much Python reorg is throwaway → defer.
If A → Python, do it.
- **Decides:** author. **Depends on:** A.

### C. The two genuine cycles — accept or redesign?
`{patterns,simulations}` and the CLI/tooling cluster. Breaking them = either
cosmetic `importlib` graph-gaming (not recommended) or a real redesign
(compose-over-inherit for the runner; consolidate the CLI tooling into one package).
Recommendation: **accept** unless redesigned deliberately.
- **Decides:** author.

### D. Shim debt — migration + deletion schedule
5 back-compat re-export shims exist (`pipeline.config`, `pipeline.events`,
`api…discovery.search`, `base.PipelineStage`, `agents.__init__→Guardian`). They are
correct and identity-verified, but leave two import paths for each symbol. Needs a
follow-up: migrate consumers to canonical paths, delete the shims.
- **Decides:** author (when). Mechanical once decided.

### E. `agents/pipeline.py` shadow hack
`src/agents/pipeline.py` (9.3 KB, holds `UniversalSolvePipeline`) is shadowed by the
package `src/agents/pipeline/`, which loads the file via a `sys.path` hack in its
`__init__`. Load-bearing but nasty. Fix = rename the file out of the shadow.
- **Decides:** author (priority).

### F. License inconsistency — **needs a legal decision**
Root `LICENSE` says **Apache-2.0**; the README badge, `pyproject`, and **every
source-file header** say **AGPL-3.0**. The project is currently in a contradictory
licensing state. Predates all reorg work.
- **Decides:** author (legal).

### G. Test/CI runnability gap
`patterns` is too slow to run fully; `simulations` **hangs** (engine bridges need
GPU/external tools). ~Half the codebase has tests that won't run in a vanilla CI
without GPU. The "9908 tests" headline is misleading. This limits confidence in any
future large refactor.
- **Decides:** author (accept / invest in CI).

---

## 4. Recovery & provenance (for the reviewer)

- `pre-reorg-baseline` — original v5.6.0 state (full rollback point).
- `reorg-decycle-24to8` — midpoint.
- `reorg-core-decycled` — end of de-cycling (current).
- 11 branches `reorg/01..11`, all pushed, each a single-concern reviewable diff.

Restore anything: `git checkout pre-reorg-baseline -- <path>`.

---

## 5. Merge strategy for the 11 reorg branches (open question)
They are **stacked** (`01→02→…→11`): `reorg/11` cannot merge until the earlier ones
do, in order. Options: (a) 11 sequential MRs; (b) squash into a few logical MRs
(e.g. "subtraction", "de-cycling", "review-fixes"); (c) one big MR. Recommendation:
group into ~3 MRs by theme for reviewability without 11 round-trips.
- **Decides:** author.

---

## 6. Validation summary (what backs "it's correct")
- AST-verified de-cycling at every step; `compileall` clean throughout.
- `mypy --name-defined` clean across all 158 changed files (caught one real bug the
  test suite missed — a missing `re`/`LLMProviderRouter` import in the API shell
  after the god-module split — now fixed; vindicated running types where tests
  don't cover the handlers).
- Re-export shims verified by object **identity** (`is`), incl. the `event_bus`
  singleton (one bus, not two).
- Test suites run green where runnable: `c4, api, discovery, pipeline, validation,
  agents, security, knowledge` (~1500+ passed, 0 refactor-related failures; the
  only failures were missing optional deps). `patterns`/`simulations` not fully
  runnable here — see G.

> Note: blob metrics in commit messages for `reorg/02..06` were computed with an
> early regex tool later found to miscount imports inside docstrings; the final
> state is AST-verified. Treat those intermediate numbers as approximate.
