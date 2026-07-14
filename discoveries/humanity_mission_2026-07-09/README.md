# Verified pipeline outputs — July 2026 mission

Six **research proposals** produced by `blast turbo` through the full HIL discovery pipeline (literature search → gap analysis → hypotheses → simulation → quality gates → Phase F prose).

## Epistemic status (read this first)

These files are **not peer-reviewed dissertations**. Each document states explicitly:

> *RESEARCH HYPOTHESES — untested, require empirical validation. Simulations are computational predictions, not experimental data. Citations need fact-checking before use.*

They are **starting points for human-led research**, not established science. Do not cite them as proven findings.

## What was verified automatically

| Check | Result |
|-------|--------|
| Word count | 4,564–5,395 words each |
| LLM failure placeholders | 0 (`[LLM unavailable]` blocked) |
| Quality gate | A+ (98/100) on all six |
| Literature search | 400–500 sources per run |
| Phase E simulation | PASS (topic-routed, ≤60s budget) |
| Reproducibility | Same command: `./scripts/run_humanity_mission.sh turbo "…" --no-functors --no-iterative` |

## Outputs

| Topic | Words | File |
|-------|------:|------|
| Marine cloud brightening (geoengineering) | 5,083 | [01_marine_cloud_brightening.md](./01_marine_cloud_brightening.md) |
| Compact fusion for distributed clean energy | 4,859 | [02_compact_fusion.md](./02_compact_fusion.md) |
| Epigenetic reversal of cellular aging | 4,564 | [04_epigenetic_aging.md](./04_epigenetic_aging.md) |
| AMR: phage–CRISPR cocktail | 5,058 | [05_amr_phage_crispr.md](./05_amr_phage_crispr.md) |
| Soil carbon / regenerative agriculture | 5,102 | [06_soil_carbon.md](./06_soil_carbon.md) |
| Ocean plastic bioremediation (v2) | 5,395 | [08_ocean_plastic_v2.md](./08_ocean_plastic_v2.md) |

## Media

- TUI screenshots: [`docs/screenshots/`](../../docs/screenshots/)
- Demo video (30s): [`docs/demo/c4reqber_mission_demo_30s.mp4`](../../docs/demo/c4reqber_mission_demo_30s.mp4)
- Web gallery: [c4reqber.org/discoveries/](https://c4reqber.org/discoveries/) (GitLab Pages)

## Retired samples

Earlier **solve/deep-work** batch (`discovery/batch_v3_deepwork`, June 2026) produced ~2.3k-word essays with inflated confidence headers — removed; superseded by the turbo outputs above.

Historical paradigm-shift tests remain in `discovery/archive/` (gitignored, local only).

```bash
source scripts/load_kilo_env.sh   # keys from ~/.kilo/.env
./scripts/run_humanity_mission.sh turbo "your topic" --output out.md --no-functors --no-iterative
```

Mission report (engineering notes): [`ENGINEERING_REPORT.md`](./ENGINEERING_REPORT.md)

---

*Generated 2026-07-09 · c4reqber HIL pipeline · branch `feat/production-upgrade`*
