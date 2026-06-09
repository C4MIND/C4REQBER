# CLAUDE.md — Project guidance

## ⚠️ Recovery baseline — `pre-reorg-baseline`

Before starting the Phase 1 reordering/cleanup, the pre-change state was tagged.
**If the reordering goes wrong, recover the original code from this tag.**

- **Tag:** `pre-reorg-baseline` (annotated) — `main @ 1fbb72a`, c4reqber/turbo-cdi v5.6.0 as-is.
- Inspect it:        `git show pre-reorg-baseline`
- Diff current vs baseline:  `git diff pre-reorg-baseline`
- Restore a single file:   `git checkout pre-reorg-baseline -- <path>`
- Restore everything (new branch): `git switch -c recover-baseline pre-reorg-baseline`
- Hard-reset main back (destructive): `git reset --hard pre-reorg-baseline`

> The tag is currently **local only** — push it before relying on it as an offsite backup:
> `git push origin pre-reorg-baseline`

## Phase 1 — reordering (in progress, started 2026-06-07)

Goal: organize the existing Python **in place** (NOT a fresh parallel tree — the dead
`v8/` directory is a corpse of that failed approach; don't repeat it).

Order of work:
1. **Subtraction** — delete dead code: `v6_legacy` (~39k LOC), the dead `v8/` parallel app
   (~15.5k, serves no live routes), the `src/tui` launcher shim; merge obvious dups
   (`core`→`c4`, `agent`→`agents`).
2. **Component analysis** on the survivor (SCCs, seams).
3. **Reorg** into ~16 target modules with a contract at each boundary.
4. **Carve the worker boundary** — heavy Python (numerics/sims/embeddings) → isolated
   workers behind a process + serializable contract ("Python in a separate barrel").
5. New features are born **into the clean structure**, never bolted onto legacy.

This in-place cleanup is also the scaffold for a possible later Agda-core rewrite
(same module boundaries + contracts + worker boundary), so it is no-regret either way.

Baseline metrics (at the tag): `src/` ~200k LOC Python, 86 packages.
