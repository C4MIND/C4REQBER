# Журнал изменений — TUI v9 + Backend

> **English version:** [CHANGELOG.md](CHANGELOG.md)

## v9.16.1 (2026-07-12) — Полный test suite зелёный + синхрон доков/сайта

### Production-фиксы (ночной аудит)
- **Полный pytest:** 9 767 passed, 0 failed (causal `d_separated`, цепочка импорта metrics, lazy-init роутеров)
- **`src/causal/`** — `networkx.d_separated` (вместо удалённого `is_d_separator`)
- **`src/api/routers/__init__.py`** — без eager-import всех роутеров (чинит Prometheus/metrics при полной коллекции тестов)
- **`tests/validation/`** — убран `sys.modules` poisoning для `src.agents`
- **MCP / verification / v8 API** — hoare `valid`, lean4 `success`, маппинг статусов hybrid verifier, LRU-кэш verification, единые пути `/v8`
- **`web-v2/` удалён** — основной UI = TUI v9 + `landing/` (GitLab Pages); обновлены CI/Makefile/Docker

### Документация / landing (билингвально)
- `_truths.json` + `scripts/sync_truths_to_docs.py` — README, AGENTS.md, landing i18n (7 языков), `index.html`, `main.js`
- `WHITEPAPER.md` / `WHITEPAPER.ru.md` — метрики из `_truths.json`
- `CHANGELOG.ru.md` — русское зеркало release notes
- Landing API: `/v8` discovery aggregator + legacy `/api/v1`
- `docs/INSTALL.md`, корневой `INSTALL.md` — GitLab clone + `pip install c4reqber` (PyPI live)

---

## v9.16.0 (2026-07-12) — CVC5 / TLA+ / Alloy в production

### Бэкенды верификации
- **CVC5, TLA+, Alloy** — реальные клиенты (не guard-stubs): SMT-LIB2, TLC, Alloy exec
- Усиление **TLAClient** — bounded counters, `-modelcheck -depth`, таймаут 120s
- `HybridVerifier` fast-path для встроенного SMT/TLA/Alloy кода
- `tools/install-verifiers.sh` + `~/.c4reqber/verifiers.env`; интеграция в `blast setup` и MCP
- Few-shot RAG: `cvc5_examples.json`, `tla_examples.json`, `alloy_examples.json`
- `docs/VERIFICATION_BACKENDS.md` — установка + bounded-model guide

### API / TUI / MCP
- `GET /v8/simulations/capabilities` — 38 движков + 10 верификаторов
- CSRF: Bearer bypass для API-клиентов
- TUI overlay i18n (14 ключей, 7 языков); golden snapshots

### Документация
- **`WHITEPAPER.md` + `WHITEPAPER.ru.md`** — технический whitepaper EN/RU
- Landing: 9 карточек верификаторов (CVC5, TLA+, Alloy)

---

## v9.15.0 (2026-07-10) — Production mission release

- **6 verified proposals** в `discoveries/humanity_mission_2026-07-09/`
- Phase F hard gate: отклонение slop, min 600 слов
- GitLab Pages: галерея `landing/discoveries/`
- Эпистемический статус: **research proposals**, не peer-reviewed
