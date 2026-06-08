# Merge plan — Phase-1 reorg + stabilization stack

**Status (2026-06-08):** 26 commits sit on top of `main` as a single **linear** chain.
The tip branch `stab/08-import-sweep` is a strict superset of every other
`reorg/*` and `stab/*` branch — they are stacked, not divergent. The full local
suite is **green** (logic 5251 passed / 0 failed; connectome 42 passed;
import sweep 1131 modules OK / 0 import-time failures; ruff step passes). `main`
is untouched.

Recovery tags: `pre-reorg-baseline` (full rollback), `reorg-decycle-24to8`,
`reorg-core-decycled`.

## The stack (oldest → newest)

```
main
 ├─ 15ef1cc docs: CLAUDE.md + recovery baseline        ┐
 ├─ e319b56 delete v6_legacy (~39k LOC)                 │ MR-1 Subtraction
 ├─ adb2412 delete dead v8/ app (~15.5k LOC)            │ → reorg/01-subtraction
 └─ 83f3913 component analysis doc                      ┘
 ├─ 29d5777 free C4 kernel → c4_analysis                ┐
 ├─ 77ffc8c pipeline config → contracts, free core      │
 ├─ 9fc9f9d Guardian → security, break llm→agents        │
 ├─ 860c5eb event bus → infrastructure                   │ MR-2 Core de-cycling
 ├─ 34423f9 parsimony/recursive_validation → discovery   │ → reorg/11-review-fixes
 ├─ 265c115 split discovery god-module out of API         │
 ├─ b83798e inject solve pipeline, dissolve 4-blob        │
 ├─ db7a67f decouple pipeline↔agents engine cycle         │
 ├─ ac7718f dev_mode auth → api, dissolve api↔auth        │
 ├─ a1479c1 strict-review punch-list (B1/B2/B3/H1)        │
 └─ 6ae0e39 real missing-import bug in api shell (mypy)   ┘
 └─ ebe3899 ARCHITECTURE_DECISIONS.md                    ┘ MR-3 Arch doc → reorg/12-arch-doc
 ├─ 5e616ff fix broken triz import (ImportError)        ┐
 ├─ da16096 hang-proof suite (per-test timeout)          │
 ├─ f6a9bc3 pandas required, not optional                │
 ├─ 346c5e5 delete dead+broken terminal.py               │ MR-4 Stabilization
 ├─ c6cc553 connectome t_max 60→30 (fit sim budget)      │ → stab/08-import-sweep
 ├─ 55186d1 add 5 imported-but-unlisted deps             │
 ├─ 41368b6 MERGE_PLAN.md                                │
 ├─ cf1d96c remove triple @dataclass breaking REPL       │
 └─ c182889 clear 4 import-sweep failures (bs4 dep etc.) ┘
```
(SHAs for connectome onward shifted from an earlier push — the t_max commit
was amended to also update its test, and the stack rebased on top.)

## Recommended grouping — 4 themed MRs

| MR | Theme | Source branch | Commits | Notes |
|----|-------|---------------|---------|-------|
| 1 | Subtraction (delete dead code) | `reorg/01-subtraction` | 4 | ~84.5k LOC removed (v6_legacy + dead v8/) + analysis docs. Large but mechanical. |
| 2 | Core de-cycling refactor | `reorg/11-review-fixes` | 11 | The real refactor: 24-pkg import-blob → 0. Deserves the closest review. |
| 3 | Architecture decision doc | `reorg/12-arch-doc` | 1 | Docs only. |
| 4 | Stabilization | `stab/08-import-sweep` | 9 | Bug fixes, test hardening, deps (incl. bs4/textual/z3), connectome perf, REPL dataclass fix, dead-code deletion, import-sweep cleanup. |

## Option A — stacked MRs (recommended; preserves granular history, reviewable themes)

Open 4 MRs, each targeting the previous group's branch, merge **bottom-up**:

```
MR-1  reorg/01-subtraction  → main
MR-2  reorg/11-review-fixes  → reorg/01-subtraction
MR-3  reorg/12-arch-doc      → reorg/11-review-fixes
MR-4  stab/08-import-sweep   → reorg/12-arch-doc
```

After MR-1 merges into `main`, retarget MR-2 to `main` (GitLab usually offers
this automatically), and so on up the stack. New-MR URLs (from the push):

- MR-1: https://gitlab.com/cognitive-functors/turbo-cdi/-/merge_requests/new?merge_request%5Bsource_branch%5D=reorg%2F01-subtraction
- MR-4: https://gitlab.com/cognitive-functors/turbo-cdi/-/merge_requests/new?merge_request%5Bsource_branch%5D=stab%2F08-import-sweep

Set the target branch per the table when creating each.

## Option B — single MR (lowest ceremony)

Because the chain is linear and the suite is green, one MR brings everything:

```
stab/08-import-sweep → main
```

One review, one merge. Loses the themed review boundaries — pick this only if
the reorg work has already been reviewed elsewhere.

## Verification before merging

- Local suite is green; **CI on `main` only turns green after the merge** (the
  pandas + per-test-timeout fixes that likely caused past CI failures live on
  these branches).
- `glab`/`gh` are not available in the working environment — MRs must be opened
  from the GitLab UI (URLs above) or a machine that has `glab`.
- If CI still fails post-merge, the missing piece is a CI-log read (neither the
  local env nor past sessions could access GitLab CI logs) — paste the failing
  job log to pin it.
