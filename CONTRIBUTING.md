# Contributing to c4reqber

## Development Setup

```bash
git clone https://gitlab.com/c4reqber/c4reqber.git
cd c4reqber
cp .env.example .env
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and fill in required keys. Minimum:
- `OPENROUTER_API_KEY` — LLM provider (required for pipeline)
- All others optional — system degrades gracefully

## Code Quality Gates

All contributions must pass:

| Gate | Command | Status |
|------|---------|--------|
| Lint | `make lint` | **0 errors** (ruff + eslint) |
| Typecheck | `make typecheck` | **0 errors** (mypy + tsc) |
| Tests | `make test-backend` | 1,400+ passing |

- **ruff**: `E`, `F`, `I`, `B`, `W`, `UP` rules active
- **mypy**: `disallow_untyped_defs=false` (legacy), `ignore_missing_imports=true`
- **eslint/tsc**: soft-fail when npm not installed

## Testing

```bash
make test              # Full test suite
make test-backend      # Python tests only
pytest tests/pipeline/ # Core pipeline tests (60)
```

- Add tests for every new module
- Test behavior through public API, not implementation details
- Use `conftest.py` shared fixtures where possible
- Minimum 80% coverage for new code

## Linting & Type Checking

```bash
make lint              # ruff + ESLint
make typecheck         # mypy (core modules strict)
make format            # black + prettier
```

- Pre-commit hooks enforce formatting
- Core modules (`src/c4/`, `src/pipeline/`, `src/llm/`, `src/discovery/`) under strict mypy
- Simulation/TUI/pattern modules relaxed

## Pull Request Process

1. Create feature branch from `main`
2. Add tests for new functionality
3. Run `make test && make lint && make typecheck` — all must pass
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Update `AGENTS.md` if project state changed
6. Submit PR with description of changes

## Architecture

- **5 layers**: TUI/CLI/MCP → API (FastAPI) → Core Engines → Cognitive → Knowledge/Verification
- **Pipeline**: 12-stage HILDiscoveryPipeline with PluginStageRouter A-G
- **Verification**: 10 backends with guardrails (complexity pre-flight, memory caps, hang detection)
- **Output**: 6 formats with auto-detection (dissertation, article, whitepaper, blueprint, code, verification_report)

## Adding a New Feature

### New Verification Backend
1. Create `src/verification/{name}_client.py`
2. Add to `BACKEND_TIMEOUTS` in `timer.py`
3. Add `_compile_{name}()` to `hybrid_verifier.py`
4. Update `BACKEND_GUARDS` in `guardrails.py`
5. Add to relevant output profiles in `output_profiles.py`

### New Knowledge Source
1. Create `src/knowledge/sources/{name}.py` with `search_sources()` and `is_available()`
2. Register in `orchestrator.py`
3. Update `AGENTS.md` knowledge sources count

### New MCP Tool
1. Add `@server.tool("{name}")` decorated async function in `server.py`
2. Update `__init__.py` exports
3. Add to `tool_schemas.py` inputSchema/outputSchema
4. Add test in `tests/mcp_server/`

## Getting Help

- `AGENTS.md` — complete project context for AI agents
- `docs/ARCHITECTURE.md` — architecture deep-dive
- `docs/ROADMAP_TO_100.md` — improvement plan
- `CHANGELOG.md` — all changes per version
- `/help` in TUI — keyboard shortcuts + CLI reference

## License

AGPL-3.0 (open-source) / Commercial license available. All contributions must be under AGPL-3.0.

## Why `from src.X` Imports?

The codebase uses `from src.X` (and `import src.X`) throughout (~1200 statements
across ~400 files). This is intentional and tracked in `REWORK_PLAN.md → P3-4`.

**Why not rename to `from c4reqber.X`?**
1. **Mechanical blast radius**: 399 files / 1220 statements would all need to
   be updated atomically, with import-graph verification, before the rename
   can ship. A half-rename breaks the entire test suite.
2. **Architectural debate**: `REWORK_PLAN.md → P3-4` notes the rename is
   *conditional* on continuing to invest in Python. The owner has flagged
   Python as "a tidy dead-end" pending the Agda-core rewrite.
3. **pyproject.toml** declares `packages = ["src"]` and `[project.scripts] =
   src.cli.blast_app:app` — this works for `pip install -e .` from source
   (the only supported install path until TestPyPI publication lands via
   `.github/workflows/pypi-publish.yml`).
4. **Test discovery**: `pytest.ini` sets `pythonpath = src`. Combined with
   `src/__init__.py`, all internal imports resolve consistently.

**Until P3-4 ships, the rule is: all internal Python imports use `from src.X`.**
External consumers (once published to PyPI) can use either `import c4reqber` or
`import src` since both entry points will be exposed.

**How to verify nothing accidentally drops the prefix:**
```bash
grep -rE "^(from|import) (?!src\.)[a-zA-Z]" src/ | grep -v __pycache__
# Should only show legitimate third-party imports
```

**Tracking**: see `audit/MASTER_AUDIT_2026-06-22.md` → H-5 and
`REWORK_PLAN.md` → P3-4.
