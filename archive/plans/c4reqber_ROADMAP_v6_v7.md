# C4REQBER FUTURE ROADMAP v6.0.0 → v7.0.0
## Extracted Long-Horizon Strategic Items
### Approved for extraction from Immediate/Short-Term implementation cycles

**Date:** 2026-05-16 | **Source:** c4reqber_improvement_plan_v5.3.3.md
**Rationale:** These 7 items require infrastructure not yet in place (cloud deployment, multi-tenancy, marketplace, hardware, etc.) or represent category-creation moves best timed after the core product is hardened, competitive micro-features are integrated, and user feedback from the v6.0.0 release has been incorporated.

---

## PHASE 1: Cloud & Collaboration (v6.1.0, Months 3-4)

### M-1. C4Reqber Cloud (Hosted SaaS with Free Tier)
| Attribute | Detail |
|-----------|--------|
| **Priority** | HIGH (P1) |
| **Effort** | 40 hours |
| **Dependency** | S-5: Enterprise SSO + RBAC completed first |
| **Competitive Rationale** | No hosted offering = no web presence. ChatGPT/Perplexity/Claude are cloud-first. Users who won't install Python are excluded. |
| **Tiers** | Free (5 solves/mo, 9 C4 states), Pro $20/mo (unlimited, 27 states, Model Council), Enterprise $200/mo/seat (SSO, RBAC, audit) |
| **Architecture** | FastAPI on Fly.io/Railway, PostgreSQL, BYOK model retained, Web UI via React |

### M-2. Scientific Collaboration Platform (Multi-User Pipelines)
| Attribute | Detail |
|-----------|--------|
| **Priority** | HIGH (P1) |
| **Effort** | 35 hours |
| **Dependency** | M-1: Cloud deployment completed first |
| **Competitive Rationale** | No competitor has collaborative scientific discovery. "GitHub for scientific research" — new market niche. |
| **Features** | Workspace model with roles, stage assignment to users, comment threads, shared dependency graph, Git-backed version history, lab report export |

### M-5. Plugin Marketplace with Revenue Share
| Attribute | Detail |
|-----------|--------|
| **Priority** | MEDIUM (P2) |
| **Effort** | 25 hours |
| **Dependency** | S-4: WASM Plugin SDK completed first; M-1: Cloud existing |
| **Competitive Rationale** | OpenClaw Skills / n8n 400+ integrations set ecosystem bar. Transforms C4Reqber from tool to platform. |
| **Economics** | 70/30 revenue share, plugin certification, sandboxed WASM execution, marketplace CLI + web UI |

---

## PHASE 2: Decentralization & Hardware (v6.5.0, Months 6-8)

### L-2. Decentralized C4Reqber (P2P Knowledge Graph + Federated Discovery)
| Attribute | Detail |
|-----------|--------|
| **Priority** | MEDIUM (P2) |
| **Effort** | 100 hours |
| **Competitive Rationale** | No centralized competitor can offer data-privacy-preserving multi-institutional collaboration. Critical for pharma/defense. |
| **Architecture** | libp2p/IPFS P2P networking, cognitive graph sharing (not raw data), federated pipeline execution, zero-knowledge formal verification, cryptographic discovery priority proofs |

### L-3. C4Reqber Hardware Appliance (DGX Spark / Local AI Workstation)
| Attribute | Detail |
|-----------|--------|
| **Priority** | LOW (P3) |
| **Effort** | 60 hours |
| **Competitive Rationale** | Data sovereignty for pharma/defense. NVIDIA NemoClaw on OpenClaw sets precedent. Complete air-gapped scientific discovery workstation. |
| **Specs** | Ubuntu + NVIDIA DGX Spark (128GB), local LLM (Llama4, Qwen, DeepSeek), all formal verification tools, 28 knowledge sources pre-loaded, air-gapped mode, NVIDIA Inception partnership |

---

## PHASE 3: Real-Time & Category Creation (v7.0.0, Months 10-12)

### L-5. Real-Time Collaborative Discovery (WebSocket Live Sessions)
| Attribute | Detail |
|-----------|--------|
| **Priority** | LOW (P3) |
| **Effort** | 40 hours |
| **Competitive Rationale** | "Figma for research" — no tool offers real-time collaborative scientific discovery. Multiple researchers navigating cognitive states simultaneously. |
| **Architecture** | WebSocket shared pipeline state, CRDT for dependency graph edits, real-time cursor presence, shared C4 state visualization, voice/video via Jitsi, collaborative LaTeX paper writing |

### L-6. C4-BENCH Benchmark: Standardized Cognitive Architecture Evaluation
| Attribute | Detail |
|-----------|--------|
| **Priority** | MEDIUM (P2) |
| **Effort** | 30 hours |
| **Competitive Rationale** | No standard benchmark for cognitive architectures exists. Creating it positions C4Reqber as category definer. Competitors must compete on OUR terms. |
| **Dataset** | 500 scientific discovery problems, 10 domains. Metrics: discovery accuracy, novelty detection, formal verification rate, pipeline efficiency, paradigm shift detection. Publish on arxiv + leaderboard at c4bench.ai |

---

## DEPENDENCY GRAPH

```
IMMEDIATE (Week 1) — in progress now
    ↓
SHORT-TERM (Month 1) — S-1 through S-6 (minus roadmap items)
    ↓
S-4 (WASM SDK) + S-5 (Enterprise SSO) → enables →
    M-1 (Cloud SaaS) → enables → M-2 (Collaboration), M-5 (Marketplace)
    ↓
L-2 (P2P Decentralized) | L-3 (Hardware Appliance)
    ↓
L-5 (Real-Time Collab) | L-6 (C4-BENCH)
```

---

## TOTAL EFFORT (Extracted Items)

| Phase | Items | Hours |
|-------|-------|-------|
| Phase 1 (Months 3-4) | M-1, M-2, M-5 | 100 |
| Phase 2 (Months 6-8) | L-2, L-3 | 160 |
| Phase 3 (Months 10-12) | L-5, L-6 | 70 |
| **TOTAL** | **7 items** | **330 hours** |

---

**Status:** Extracted from active implementation cycle per user directive 2026-05-16.
**Next review:** After v6.0.0 release (projected Month 1 completion).
