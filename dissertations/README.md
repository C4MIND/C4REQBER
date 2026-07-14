# c4reqber — Research proposal outputs

**Do not expect files here.** Runtime outputs go to `dissertations/live/` (gitignored).

## Curated examples (production)

Verified **July 2026** `blast turbo` proposals (4.5k–5.4k words, quality gate A+ 98, epistemic disclaimers):

→ [`discoveries/humanity_mission_2026-07-09/README.md`](../discoveries/humanity_mission_2026-07-09/README.md)

Web gallery: [c4reqber.org/discoveries/](https://c4reqber.org/discoveries/)

## Retired (removed)

| Batch | Mode | Why removed |
|-------|------|-------------|
| `discovery/batch_v3_deepwork` | `UniversalSolvePipeline` deep-work | ~2.3k words, 10 citations, fake “Confidence: 0.95” headers, meta-program theatre — superseded by July 2026 turbo outputs |
| `discovery/batch_v3_enhanced` | Re-run stubs | Mostly empty placeholders |
| `dissertations/dissertation_01–10` | Static templates | ~1k words each, unverified formal-verification claims in old README |

Historical archive (local only, gitignored): `discovery/archive/` — paradigm-shift tests from May–June 2026.

## Reproduce

```bash
source scripts/load_kilo_env.sh
./scripts/run_humanity_mission.sh turbo "your topic" --output out.md --no-functors --no-iterative
```

---

*AGPL-3.0 · c4reqber v5.6+*
