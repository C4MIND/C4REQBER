# Reorg — Component Analysis (Phase 1, Step 2)

Package-level import-dependency analysis of `src/` **after** the subtraction step
(v6_legacy + v8/ removed). Deterministic: graph → Tarjan SCC → condensation.

## Method & caveat

- Graph nodes = top-level packages under `src/` (89). Edge A→B = a file in A does
  `from src.B …` / `import src.B …`. Weighted by statement count.
- **Caveat:** only **absolute** `src.X` imports are counted. Relative imports
  (`from ..llm`) and **dynamic** loading (`importlib`, plugin registries) are NOT
  captured → real coupling is *denser* than shown. Use this for macro-structure;
  a module-level pass is needed for the exact cut list.
- Measured: 206 package→package edges, 622 import statements.

## Headline: ONE giant cycle + 2 small ones; everything else is acyclic

**Non-trivial SCCs (cyclic clusters — cannot be peeled until cycles are broken):**

1. **The 24-package "core blob"** — mutually entangled:
   `agents, analogy, api, archetypes, auth, c4, core, discovery, exploration,
   export, graph, knowledge, litintel, llm, memory, metamodels, pipeline, plugins,
   publishing, social, solver, triz, validation, verification`
2. **CLI/MCP cluster (4):** `agent, cli, codegen, mcp_server`
3. **patterns ↔ simulations (2)**

The other ~63 packages are acyclic / leaves.

## The cascade insight — the blob is held by a FEW "upward" edges

The 24-blob is NOT 24 independent tangles. It's held together by a small set of
**architectural-violation edges**: low-level/foundational packages importing
high-level orchestration/IO packages. Break these → large parts de-cycle.

What the foundational packages (which SHOULD be leaves) pull:

| Package | imports (→) | The blob-tying edge(s) to break |
|---|---|---|
| **c4** (kernel) | plugins(4), di(1), llm(1), memory(1) | c4→plugins, c4→llm, c4→memory (kernel must depend on NOTHING) |
| **core** (dup of c4) | c4(2), pipeline(1) | core→pipeline (and merge core into c4) |
| **triz** | c4(5), utils(1) | — none; clean once c4 is freed |
| **metamodels** | c4(5) | — none; clean once c4 is freed |
| **verification** | llm(4), pipeline(2), utils(2) | verification→llm, →pipeline (inject instead) |
| **knowledge** | integrations(2), llm(1) | knowledge→llm (inject) |
| **discovery** | llm, pipeline, integrations, knowledge, publishing, c4, patterns, simulations… | genuine hub — break last, via contracts |

**Cascade:** `triz` and `metamodels` depend ONLY on `c4`. The moment `c4` is freed
into a true leaf, they (and `archetypes`, `core` after merge) fall out of the blob
clean. So the cycle-break worklist is ~10–15 *upward* edges, NOT "untangle 24 packages."

## Target ("как надо") vs actual ("как есть")

- Target put **C4 Kernel** as a no-dependency leaf. Reality: `c4` is trapped in the
  blob because it imports `plugins/llm/memory`. The reorg = **invert those edges**
  (DI / move the offending call sites out of the kernel). This is the single
  highest-leverage cut: it unlocks triz, metamodels, archetypes, core.
- `core`/`archetypes` are dups of `c4` (predicted) and are in the blob with it.

## Leaves & isolated

- **39 leaf packages** (fanout=0 — depend on nothing in src): cleanly extractable
  now. Incl. the self-contained algorithm packages: `bayesian, causal, decisions,
  falsification, game_theory, experiment_design, robust_decisions`, plus the true
  utility sinks `di(fanin 23), utils(10), security, cache, integrations`.
- **~25 "isolated"** (fanin=0 AND fanout=0 by absolute imports). **NOT dead** — spot
  check shows they're reached via dynamic loading (e.g. `causal` 39 mentions,
  `bayesian` 24, all have importlib/registry hits). Loosely coupled → easy to
  extract, but **do not delete**. (Confirms the absolute-imports-only caveat.)

## Proposed reorg order (cycle-break first, then peel)

1. **Free `c4`** — break c4→{plugins,llm,memory}, merge `core`+`archetypes` into it.
   → C4 Kernel becomes the leaf it should be; triz/metamodels/… de-cycle automatically.
2. **Extract the genuine leaves** as independent modules (causal, bayesian, decisions,
   falsification, game_theory, experiment_design, robust_decisions…).
3. **Break verification/knowledge upward edges** (inject llm/pipeline) → they layer clean.
4. **Last: the orchestration hub** (discovery + pipeline + agents + api) — break via
   boundary contracts; this is where the remaining cyclic mass lives.
5. **patterns↔simulations** and **cli/mcp/agent** clusters — break their small cycles
   (likely a single back-edge each).
