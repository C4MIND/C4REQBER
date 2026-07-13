# C4REQBER Capital Audit — 2026-07-13

## Outcome

The audit covered the Python backend, API security, discovery pipeline, MCP
surface, Go TUI v9, release packaging, CI gates, public product claims, and the
static landing site.

All confirmed release-blocking defects found in this pass were fixed. The
supported runtime surfaces now pass their local verification gates. This report
does not claim that a large scientific system is defect-free; it records the
evidence produced by this audit.

## Major corrections

- Restored MCP runtime contracts and split the server into a small registration
  facade plus cohesive tool modules.
- Made MCP schemas and the generated registry derive from one source of truth.
- Hardened production JWT/CSRF configuration, CORS registration, trusted proxy
  handling, and multi-worker rate limiting.
- Made prompt-safety scanning fail closed.
- Aligned Python package metadata, Docker requirements, and the lock file.
- Updated vulnerable dependencies and verified the resolved production graph.
- Switched the API container to a non-root runtime user.
- Added configurable discovery evidence floors and simulation timeouts.
- Removed fabricated Bayesian and Monte Carlo evidence when empirical inputs are
  absent.
- Fixed NetworkX 2.x/3.x d-separation compatibility.
- Corrected structural-memory database placement so imports do not write outside
  the repository data directory.
- Fixed TUI v9 SSE reconnection, bounded pending SSE data, restored card IDs,
  backend-owned cost reporting, and locale-dependent tests.
- Completed TUI and landing-page locale parity and corrected visible untranslated
  content.
- Reconciled public metrics with generated repository truths and added a CI drift
  gate.
- Removed the retired parallel TUI v8 tree, launcher, and obsolete architecture
  and onboarding documents.

## Canonical public metrics

- Python tests collected: 9,906
- MCP tools: 21
- CLI commands: 24
- Knowledge sources: 47 configured / 46 wired
- Simulation bridges: 38
- LLM providers: 11
- Formal verification backends: 9

Runtime availability still depends on credentials, installed external engines,
and upstream service health.

## Verification evidence

- Full Python suite: 9,782 passed, 116 skipped, 6 expected failures, 0 failed.
- Focused final regression suite: 36 passed, 1 skipped.
- MCP suite: 25 passed, 1 skipped.
- Go TUI v9: all packages passed with the race detector enabled.
- Ruff: passed.
- mypy: passed with no errors.
- Bandit high-severity scan: passed.
- Production dependency audit: no known vulnerabilities.
- Generated truths, public claims, MCP registry, and seven-locale parity: passed.
- Landing smoke test: no broken images, duplicate IDs, missing image alt text, or
  horizontal overflow at the tested desktop and mobile viewports.
- Diff whitespace validation: passed.

## Residual, non-blocking risks

- The scientific pattern suite emits numerical warnings for deliberately extreme
  edge cases. These are visible and should be reduced incrementally, but they did
  not produce test failures in this pass.
- Optional verification and simulation backends require system packages that are
  not present on every development or CI host.
- The branch contains a large mechanical lint/format pass. It is fully tested but
  should be reviewed as a dedicated merge request rather than mixed with unrelated
  feature work.

## Repository state

The audit changes are intentionally uncommitted on
`fix/capital-audit-wave-a`. The maintainer-only `.env.dontredact` file was not
modified or removed.
