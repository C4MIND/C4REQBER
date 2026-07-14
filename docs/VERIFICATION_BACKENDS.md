# Verification Backends — c4reqber v9.16

**Truth source:** `_truths.json` — **9 real backends**, **0 guard-stubs**.

| Backend | Role | Install |
|---------|------|---------|
| Lean4 | Dependent types, mathematics | `elan` / `brew install elan-init` |
| Coq | Inductive proofs | `brew install coq` |
| Dafny | Imperative + contracts | `brew install dafny` |
| Agda | Constructive type theory | `brew install agda` |
| Z3 / Hoare | SMT + imperative logic | `pip install z3-solver` |
| Haskell | Typecheck + QuickCheck | `brew install ghc` |
| **CVC5** | Industrial SMT-LIB2 | `bash tools/install-verifiers.sh` |
| **TLA+** | Temporal / concurrent specs | `bash tools/install-verifiers.sh` (tla2tools.jar) |
| **Alloy** | Relational model finding | `brew install alloy-analyzer` or JAR |

Smoke test: `python3 scripts/verify_backends_smoke.py`

---

## TLA+ / TLC — bounded models required

TLC explores **finite** state spaces. An unbounded counter:

```tla
EXTENDS Naturals
VARIABLE x
Init == x = 0
Next == x' = x + 1   (* infinite — TLC will run until timeout or 65535-state limit *)
```

will **not** terminate in reasonable time. `-depth N` **without** `-modelcheck` does not fix this; c4reqber always invokes:

```text
tlc -modelcheck -workers 1 -depth 10 <module>.tla
```

### Correct bounded pattern

```tla
---- MODULE Counter ----
EXTENDS Naturals
VARIABLE x
Init == x = 0
Next == /\ x < 5 /\ x' = x + 1
====
```

Optional config block (separate with `---CFG---` in MCP/API input):

```text
---CFG---
INIT Init
NEXT Next
```

Or with named constant:

```tla
Next == /\ x < MAX /\ x' = x + 1
```

```text
---CFG---
CONSTANT MAX = 12
INIT Init
NEXT Next
```

### Pre-flight guard (TLAClient)

Before spawning TLC, `TLAClient.verify()` rejects:

- `EXTENDS Naturals` or `Integers`
- `x' = x + 1` increment
- **no** `x < N`, `x < MAX`, or `CONSTANT MAX` in spec + cfg

Returns `valid: false` with hint — **no 30-minute runaway**.

### Timeouts

| Phase | Limit |
|-------|-------|
| TLC subprocess | 120s default (`BACKEND_TIMEOUTS["tla"]` hard cap) |
| Pipeline soft | 30s (VerificationTimer) |

### Install

```bash
bash tools/install-verifiers.sh   # downloads ~/.tlaplus/tla2tools.jar
export TLA_TOOLS_JAR=~/.tlaplus/tla2tools.jar   # written to ~/.c4reqber/verifiers.env
```

---

## CVC5

SMT-LIB2 via `cvc5` binary. Auto-selected for `(declare-` / `(check-sat)` claims.

## Alloy

`sig` / `run` / `check` models. Scope must be finite (`run … for 3`).

---

See also: [WHITEPAPER.md](../WHITEPAPER.md) · [WHITEPAPER.ru.md](../WHITEPAPER.ru.md) · [ARCHITECTURE.md](ARCHITECTURE.md)
