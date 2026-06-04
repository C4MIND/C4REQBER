# C4-META Semantic Isomorphisms
## Informational Isomorphisms Between C4 Coordinate Framings

**Document:** C4_META_SEMANTIC_ISOMORPHISMS.md
**Framework:** C44TCDI
**Date:** May 2026
**Classification:** Meta-Cognitive Architecture — Theoretical

---

## 1. The Canonical C4-META Structure

The **authoritative** C4-META coordinate system, as defined in the foundational research:

| Dimension | Coordinate 0 | Coordinate 1 | Coordinate 2 |
|-----------|-------------|-------------|-------------|
| **Time** (T) | Past | Present | Future |
| **Scale** (S) | Concrete | Abstract | Meta |
| **Agency** (A) | Self | Other | System |

This forms the group **Z₃³** with 27 discrete cognitive states. Each state is a triple `(t, s, a)` where each coordinate ∈ {0, 1, 2}.

**Formal property:** The diameter of this state space graph is **exactly 6** (proven in Agda, `adaptive-topology/formal-proofs/c4-comp-v5.agda:838-885`). Any two cognitive states are reachable from each other in ≤6 operator steps.

---

## 2. The Engagement-Scope-Operation Isomorphism

During the competitive analysis research, an **alternative semantic framing** emerged that maps cleanly onto the same Z₃³ structure:

| Dimension | Coordinate 0 | Coordinate 1 | Coordinate 2 |
|-----------|-------------|-------------|-------------|
| **Engagement** (E) | Passive | Active | Immersive |
| **Scope** (Sc) | Local | Regional | Global |
| **Operation** (O) | Analyze | Synthesize | Transform |

This is **not** the canonical C4-META framing. It is a **semantic isomorphism** — a different interpretation of the same mathematical structure that reveals different conceptual mappings.

---

## 3. The Isomorphism Mapping

### 3.1 Why These Mappings Are Equivalent

Both framings describe the same Z₃³ group. The isomorphism preserves:
- **Algebraic structure:** Addition modulo 3 on each axis
- **Graph metric:** Hamming-like distance (sum of cyclic distances per axis)
- **Diameter:** 6 steps maximum between any two states
- **Cayley graph:** Same vertex set, same edge set, same generators

### 3.2 Semantic Mapping Table

The two framings are **informationally isomorphic** — they encode the same structural relations but with different semantic labels:

| Canonical (Time×Scale×Agency) | Alternative (Engagement×Scope×Operation) | Structural Property |
|-------------------------------|------------------------------------------|---------------------|
| Past (t=0) | Passive (e=0) | External observation, not yet engaged |
| Present (t=1) | Active (e=1) | Current engagement, processing |
| Future (t=2) | Immersive (e=2) | Fully embedded, predictive simulation |
| Concrete (s=0) | Local (sc=0) | Specific instance, particular domain |
| Abstract (s=1) | Regional (sc=1) | Cross-context pattern, neighborhood of domains |
| Meta (s=2) | Global (sc=2) | Universal principle, all domains |
| Self (a=0) | Analyze (o=0) | Decomposition, internal structure examination |
| Other (a=1) | Synthesize (o=1) | Integration, combining perspectives |
| System (a=2) | Transform (o=2) | Restructuring, paradigm shift |

### 3.3 Why the Alternative Framing Emerged

The Engagement-Scope-Operation framing emerged from **task-type classification** in the CLI UX design:
- "refactor", "deep" → deep-work layout (Immersive × Global × Analyze)
- "session", "multi-agent" → collaborative layout (Active × Regional × Synthesize)
- "solve", "discover" → standard layout (Active × Local × Analyze)

This is a **user-facing** semantic layer that maps to the same underlying cognitive states. It is not a different architecture — it is a **different vocabulary for the same architecture**.

---

## 4. Which Framing to Use When

### Use Canonical (Time×Scale×Agency) for:
- Formal proofs and Agda verification
- Mathematical publications
- Cross-domain theory (physics, biology, sociology analogies)
- Historical-trajectory reasoning (how a field evolved)

### Use Alternative (Engagement×Scope×Operation) for:
- CLI/TUI UX design
- Task-type auto-detection
- User-facing documentation
- Operational mode descriptions

### Never Confuse Them in:
- API contracts (use canonical only)
- Database schemas (use canonical only)
- Academic publications (use canonical only)
- MCP tool definitions (use canonical only)

---

## 5. Additional Semantic Isomorphisms

The Z₃³ structure supports **multiple valid semantic mappings**. Other isomorphisms that have been explored:

### 5.1 TRIZ-Resonance Isomorphism

| Canonical | TRIZ Mapping |
|-----------|-------------|
| Time | Evolution direction (before/after/during contradiction) |
| Scale | Abstraction level (parameter/principle/meta-principle) |
| Agency | Agent type (human/inventor/system) |

### 5.2 Physics Isomorphism

| Canonical | Physics Mapping |
|-----------|----------------|
| Time | Temporal dimension (t) |
| Scale | Spatial scale (micro/meso/macro) |
| Agency | Observer frame (rest/moving/accelerated) |

### 5.3 Biological Isomorphism

| Canonical | Biology Mapping |
|-----------|----------------|
| Time | Developmental stage (embryo/juvenile/adult) |
| Scale | Biological level (molecular/cellular/organism) |
| Agency | Selection level (gene/individual/group) |

---

## 6. Implementation Notes

### 6.1 Code Coherence

The codebase must maintain **one canonical representation** internally:
```python
# src/c4/engine.py — canonical only
class C4State:
    time: TimeDimension      # 0=Past, 1=Present, 2=Future
    scale: ScaleDimension    # 0=Concrete, 1=Abstract, 2=Meta
    agency: AgencyDimension  # 0=Self, 1=Other, 2=System
```

The alternative framing is a **presentation-layer** concern:
```python
# src/tui/detector.py — alternative for UX only
class TaskTypeDetector:
    def detect(self, query: str) -> tuple[str, str, str]:
        # Returns (engagement, scope, operation) for UI only
        # Maps to canonical internally before any C4 operation
```

### 6.2 Migration Path

If any code uses the alternative framing internally, it must be refactored:
1. Identify all places using Engagement/Scope/Operation as state coordinates
2. Map each to canonical Time/Scale/Agency
3. Move alternative labels to presentation layer only
4. Update tests to use canonical coordinates

---

## 7. Conclusion

C4-META is a **mathematical structure** (Z₃³), not a fixed semantic interpretation. The canonical Time×Scale×Agency framing is the authoritative representation used in formal proofs. The Engagement×Scope×Operation framing is a valid semantic isomorphism useful for UX design. Both describe the same 27-state cognitive space with diameter 6.

**Rule:** One canonical form for the engine. Multiple semantic skins for the user.

---

*Document prepared by Reqber Architecture Team*
*Framework: C44TCDI v4.2.1*
*Mathematical Foundation: adaptive-topology/formal-proofs/*
