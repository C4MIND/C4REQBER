# TURBO-CDI v8.0 — Batched Execution Plan

**Date:** 2026-05-01
**Status:** v7.5 COMPLETE (10/10), v8.0 Ready
**Mission:** Multi-Engine Physics Integration, Mega-Database, Formal Verification, Social Platforms
**Execution Model:** Batch-based agent orchestration (proven in v7.5: 17 batches, 17 agents)

---

## v8.0 Scope (UPDATED)

### INCLUDED in v8.0:
- ✅ **Multi-Engine Physics Integration** (auto-detect: GPU→Newton, CPU→TorchSim/JaxSim)
- ✅ **vast.ai Cloud Delegate** (optional paid GPU acceleration)
- ✅ **Mega-Database Integration** (arXiv, PubMed, ORCID, 30+ sources)
- ✅ **Formal Verification** (Lean 4, Agda, Coq)
- ✅ **Social Media Tracking** (Grok/X.ai, Mastodon)
- ✅ **Preprint Auto-Posting** (SciMatic, ResearchGate)
- ✅ **International Sources** (CNKI, CiNii, RSCI)
- ✅ **Patent Search** (USPTO, EPO, WIPO)
- ✅ **Code/Dataset Integration** (GitHub, Zenodo, Figshare)
- ✅ **v8 Frontend Pages**
- ✅ **v8 API Router** (/v8/*)
- ✅ **v8 Tests + Docs**

### EXCLUDED (ROADMAP - Future Versions):
- ❌ Grants/Funding APIs (NIH, NSF, EU CORDIS) → v9.0
- ❌ Patent Search (USPTO, EPO, WIPO) → v9.0
- ❌ Collaboration features → v9.0
- ❌ News tracking → v9.0

---

## Physics Engines — Deep Analysis (2025-2026)

### 🏆 MIT/BSD Licensed (RECOMMENDED for commercial use):

| Engine | License | Stars | Backend | GPU | Mac | Best For |
|--------|---------|-------|---------|-----|-----|----------|
| **TorchSim** | MIT | 446⭐ | PyTorch | ✅ CUDA | ✅ | Atomistic/Molecular, MLIP |
| **JaxSim** | BSD-3 | 187⭐ | JAX | ✅ GPU/TPU | ✅ | Robotics, Multibody dynamics |
| **Kinetix** | MIT | 238⭐ | JAX | ✅ GPU/TPU | ✅ | 2D physics, RL |
| **torch-diffsim** | MIT | 55⭐ | PyTorch | ✅ CUDA | ✅ | FEM, minimal differentiable |
| **evoxels** | MIT | 31⭐ | PyTorch/JAX | ✅ GPU | ✅ | Voxel microstructure |
| **MechanicsDSL** | MIT | 3⭐ | JAX | ✅ GPU/TPU | ✅ | Custom physics DSL, 15 code generators |
| **Schr** | MIT | new | JAX | ✅ GPU | ✅ | Quantum mechanics + QED |
| **JAX-MPM** | MIT | 3⭐ | JAX | ✅ GPU | ✅ | Granular materials, geomechanics |
| **JaxLayerLumos** | MIT | 23⭐ | JAX | ✅ GPU/TPU | ✅ | Optics/RF multilayer |

### ⚡ Apache 2.0 Licensed (permissive, commercial OK):

| Engine | License | Stars | Backend | GPU | Mac | Best For |
|--------|---------|-------|---------|-----|-----|----------|
| **Newton** | Apache 2.0 | 4227⭐ | NVIDIA Warp | ✅ CUDA | ⚠️ CPU only | General physics, MuJoCo Warp |
| **NVIDIA Warp** | Apache 2.0 | 6488⭐ | CUDA | ✅ CUDA | ⚠️ CPU only | Low-level GPU kernels |
| **Rewarped** | Apache 2.0 | 179⭐ | NVIDIA Warp | ✅ CUDA | ⚠️ CPU only | Differentiable multiphysics |
| **NVIDIA PhysicsNeMo** | Apache 2.0 | 2697⭐ | PyTorch | ✅ CUDA | ✅ | Physics-ML, AI4Science |
| **Brax** | Apache 2.0 | 3119⭐ | JAX | ✅ GPU/TPU | ✅ | RL physics (deprecated → MJX) |

### ⚠️ GPL-3.0 Licensed (NOT for commercial closed-source):

| Engine | License | Stars | Backend | GPU | Mac | Best For |
|--------|---------|-------|---------|-----|-----|----------|
| **JAX-FEM** | GPL-3.0 | 651⭐ | JAX | ✅ GPU/TPU | ✅ | FEM, topology optimization |
| **JAX-PF** | GPL-3.0 | 21⭐ | JAX | ✅ GPU | ✅ | Phase field |
| **Dedalus** | GPL-3.0 | 681⭐ | Python+MPI | ⚠️ CPU | ✅ | PDE solver, spectral methods |

---

## Multi-Engine Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TURBO-CDI v8 Physics Layer                    │
├─────────────────────────────────────────────────────────────────┤
│  AUTO-DETECT ENVIRONMENT                                         │
│  ├── has_nvidia_gpu() → Newton (Apache 2.0, 4227⭐)             │
│  ├── has_apple_silicon() → JaxSim/TorchSim (BSD-3/MIT)         │
│  └── cpu_only() → TorchSim (MIT, 446⭐) ← DEFAULT               │
├─────────────────────────────────────────────────────────────────┤
│  PRIMARY ENGINES (Cross-Platform, MIT/BSD)                       │
│  ├── TorchSim (MIT) ← atomistic/molecular, MLIP                 │
│  ├── JaxSim (BSD-3) ← robotics, multibody dynamics              │
│  ├── MechanicsDSL (MIT) ← custom physics DSL                    │
│  └── Schr (MIT) ← quantum mechanics + QED                       │
├─────────────────────────────────────────────────────────────────┤
│  GPU-ACCELERATED (NVIDIA only, Apache 2.0)                       │
│  ├── Newton (Apache 2.0) ← MuJoCo Warp, general physics         │
│  └── Rewarped (Apache 2.0) ← differentiable multiphysics        │
├─────────────────────────────────────────────────────────────────┤
│  CLOUD DELEGATE (optional, paid)                                 │
│  └── vast.ai integration ← Newton GPU in cloud                  │
├─────────────────────────────────────────────────────────────────┤
│  SPECIALIZED (domain-specific, MIT)                              │
│  ├── JAX-MPM (MIT) ← granular materials                         │
│  ├── JaxLayerLumos (MIT) ← optics/RF                            │
│  └── Kinetix (MIT) ← 2D physics, RL                             │
└─────────────────────────────────────────────────────────────────┘
```

### Selection Logic:

```python
def select_physics_engine(domain: str) -> str:
    """Auto-select physics engine based on hardware and domain."""
    
    # Hardware detection
    has_nvidia = torch.cuda.is_available() and "NVIDIA" in torch.cuda.get_device_name()
    has_apple = platform.system() == "Darwin" and platform.machine() == "arm64"
    
    # Domain-specific selection
    if domain == "robotics":
        return "jaxsim"  # BSD-3, JAX native
    
    if domain == "quantum":
        return "schr"  # MIT, JAX native
    
    if domain == "atomistic" or domain == "molecular":
        return "torchsim"  # MIT, PyTorch native
    
    if domain == "granular" or domain == "geomechanics":
        return "jax_mpm"  # MIT, JAX native
    
    # General physics with GPU acceleration
    if has_nvidia:
        return "newton"  # Apache 2.0, NVIDIA Warp, fastest
    
    # Fallback to cross-platform
    if has_apple:
        return "jaxsim"  # BSD-3, works on Apple Silicon
    
    return "torchsim"  # MIT, works everywhere
```

### vast.ai Integration:

```python
class VastAIDelegate:
    """Delegate GPU-intensive physics to vast.ai cloud."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = VastClient(api_key)
    
    async def run_newton_simulation(self, config: dict) -> SimulationResult:
        """Run Newton physics simulation on vast.ai GPU instance."""
        
        # Find cheapest GPU instance
        instance = await self.client.search_instances(
            gpu_name="RTX 4090",
            min_gpu_ram=24,
            max_price_per_hour=0.50
        )
        
        # Deploy and run
        result = await instance.run_simulation(
            engine="newton",
            config=config,
            timeout=3600
        )
        
        return result
```

---

## BATCH EXECUTION PLAN

### BATCH GROUP A: Multi-Engine Physics Layer (Integration with 162 Existing Patterns)

| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| A1 | Physics Auto-Detector | `src/simulations/auto_engine.py` | AGENT-DETECT | HIGH |
| A2 | TorchSim Bridge | `src/simulations/torchsim_bridge.py` | AGENT-TORCHSIM | HIGH |
| A3 | JaxSim Bridge | `src/simulations/jaxsim_bridge.py` | AGENT-JAXSIM | HIGH |
| A4 | Newton Bridge (GPU) | `src/simulations/newton_bridge.py` | AGENT-NEWTON | HIGH |
| A5 | Schr Bridge (Quantum) | `src/simulations/schr_bridge.py` | AGENT-SCHR | MEDIUM |
| A6 | vast.ai Delegate | `src/simulations/vastai_delegate.py` | AGENT-VASTAI | MEDIUM |
| A7 | Pattern-Engine Mapper | `src/simulations/pattern_engine_map.py` | AGENT-MAPPER | HIGH |
| A8 | PatternRunner v2 | `src/simulations/runner_v2.py` | AGENT-RUNNER | HIGH |
| A9 | GPU Migration Guide | `src/simulations/gpu_upgrade.py` | AGENT-GPU-UP | MEDIUM |

### Pattern-to-Engine Mapping (162 patterns):

| Pattern Category | Count | Recommended Engine | Acceleration |
|------------------|-------|-------------------|--------------|
| CFD (cfd, climate_gcm, cloud_microphysics) | 15 | Newton (GPU) | 10-100x |
| Continuum (continuum_mechanics, elasticity_3d) | 8 | Newton (GPU) | 10-50x |
| Atomistic (dft, crystal_growth, composite_mechanics) | 12 | TorchSim (MIT) | 5-20x |
| Rigid Body (double_pendulum, agent_based) | 10 | JaxSim (BSD-3) | 2-10x |
| Quantum (if any) | TBD | Schr (MIT) | N/A |
| Biological (epidemic_*, hodgkin_huxley) | 20 | CPU (NumPy) | baseline |
| Economic (dsge, garch, game_theory) | 15 | CPU (NumPy) | baseline |
| Other (cellular_automata, fractal_*) | 82 | CPU/GPU optional | varies |

### Integration Strategy:

```python
# src/simulations/runner_v2.py
class PatternRunnerV2(PatternRunner):
    """Enhanced PatternRunner with multi-engine support."""
    
    def __init__(self):
        super().__init__()
        self.engine_map = PatternEngineMap()
        self.auto_detector = PhysicsAutoDetector()
    
    def run(self, pattern_id: str, hypothesis: dict) -> dict:
        """Run pattern with optimal engine."""
        
        # Get pattern metadata
        pattern = self._patterns[pattern_id]
        metadata = pattern.get_metadata()
        
        # Auto-select engine
        engine_name = self.engine_map.get_engine(pattern_id, metadata)
        
        # Execute with selected engine
        if engine_name == "newton" and self.auto_detector.has_nvidia_gpu:
            return self._run_with_newton(pattern, hypothesis)
        elif engine_name == "torchsim":
            return self._run_with_torchsim(pattern, hypothesis)
        elif engine_name == "jaxsim":
            return self._run_with_jaxsim(pattern, hypothesis)
        else:
            return pattern.run(hypothesis)  # Legacy CPU fallback
```

### BATCH GROUP B: Mega-Database Core
| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| B1 | arXiv Client | `src/knowledge/arxiv_client.py` | AGENT-ARXIV | HIGH |
| B2 | PubMed Client | `src/knowledge/pubmed_client.py` | AGENT-PUBMED | HIGH |
| B3 | ORCID Client | `src/knowledge/orcid_client.py` | AGENT-ORCID | HIGH |
| B4 | Semantic Scholar | `src/knowledge/semantic_scholar.py` | AGENT-SEMSCHOLAR | HIGH |
| B5 | CrossRef Client | `src/knowledge/crossref_client.py` | AGENT-CROSSREF | MEDIUM |
| B6 | Mega-DB Router | `src/knowledge/mega_db.py` | AGENT-MEGADB | HIGH |

### BATCH GROUP C: Preprint & Code Sources
| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| C1 | bioRxiv/medRxiv | `src/knowledge/preprint_clients.py` | AGENT-PREPRINT | MEDIUM |
| C2 | GitHub Search | `src/knowledge/github_client.py` | AGENT-GITHUB | MEDIUM |
| C3 | Zenodo/Figshare | `src/knowledge/dataset_clients.py` | AGENT-DATASET | MEDIUM |

### BATCH GROUP D: International Sources
| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| D1 | CiNii (Japan) | `src/knowledge/cinii_client.py` | AGENT-CINII | MEDIUM |
| D2 | RSCI (Russia) | `src/knowledge/rsci_client.py` | AGENT-RSCI | MEDIUM |
| D3 | BASE (Bielefeld) | `src/knowledge/base_client.py` | AGENT-BASE | MEDIUM |

### BATCH GROUP E: ~~Patent Search~~ (MOVED TO ROADMAP)
**REMOVED from v8.0** - Patents integration scheduled for v9.0 ROADMAP

### BATCH GROUP F: Social Media
| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| F1 | Grok/X.ai Client | `src/social/grok_client.py` | AGENT-GROK | HIGH |
| F2 | Mastodon Client | `src/social/mastodon_client.py` | AGENT-MASTODON | MEDIUM |
| F3 | ResearchGate | `src/social/researchgate_client.py` | AGENT-RG | LOW |

### BATCH GROUP G: Formal Verification
| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| G1 | Lean 4 Client | `src/verification/lean4_client.py` | AGENT-LEAN4 | HIGH |
| G2 | Agda Bridge | `src/verification/agda_bridge.py` | AGENT-AGDA | MEDIUM |
| G3 | Proof Generator | `src/verification/proof_gen.py` | AGENT-PROOF | MEDIUM |

### BATCH GROUP H: API & Frontend
| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| H1 | v8 API Router | `src/api/v8_router.py` | AGENT-API | HIGH |
| H2 | v8 Schemas | `src/api/v8_schemas.py` | AGENT-SCHEMAS | HIGH |
| H3 | Knowledge Page | `web-v2/src/pages/KnowledgePage.tsx` | AGENT-FE-KNOW | HIGH |
| H4 | Verify Page | `web-v2/src/pages/VerifyPage.tsx` | AGENT-FE-VERIFY | HIGH |
| H5 | Social Page | `web-v2/src/pages/SocialPage.tsx` | AGENT-FE-SOCIAL | MEDIUM |
| H6 | Physics Page | `web-v2/src/pages/PhysicsPage.tsx` | AGENT-FE-PHYS | MEDIUM |

### BATCH GROUP I: Tests & Docs
| Batch | Task | Files | Agent | Priority |
|-------|------|-------|-------|----------|
| I1 | v8 API Tests | `tests/api/test_v8_router.py` | AGENT-TEST-API | HIGH |
| I2 | Knowledge Tests | `tests/knowledge/` | AGENT-TEST-KNOW | HIGH |
| I3 | Physics Tests | `tests/simulations/test_newton.py` | AGENT-TEST-PHYS | MEDIUM |
| I4 | v8 Completion Report | `docs/V8_0_COMPLETION_REPORT.md` | AGENT-REPORT | LOW |

---

## EXECUTION SUMMARY

| Group | Batches | Files | Priority |
|-------|---------|-------|----------|
| A: Multi-Engine Physics | 9 | 9 | HIGH |
| B: Mega-Database | 6 | 6 | HIGH |
| C: Preprint/Code | 3 | 3 | MEDIUM |
| D: International | 3 | 3 | MEDIUM |
| E: Patents | — | — | **REMOVED → ROADMAP** |
| F: Social | 3 | 3 | HIGH/MED |
| G: Verification | 3 | 3 | HIGH/MED |
| H: API/Frontend | 6 | 6 | HIGH |
| I: Tests/Docs | 4 | 4+ | HIGH/MED |
| **TOTAL** | **37** | **37+** | — |

---

## VERIFICATION CHECKLIST

After each batch group:
- [ ] All files created
- [ ] Imports working
- [ ] Basic tests pass
- [ ] No hardcoded secrets
- [ ] License compliance verified

After v8.0 complete:
- [ ] All 38 batches executed
- [ ] All tests pass
- [ ] API documentation updated
- [ ] Frontend pages working
- [ ] Grade: 10/10

---

## LICENSE COMPLIANCE MATRIX

### Physics Engines (MIT/BSD/Apache - ALL COMMERCIAL OK):
| Engine | License | Commercial | Attribution | Notes |
|--------|---------|------------|-------------|-------|
| TorchSim | MIT | ✅ | Required | AI for Science journal |
| JaxSim | BSD-3 | ✅ | Required | IEEE RA-L 2026 |
| Newton | Apache 2.0 | ✅ | Required | Linux Foundation |
| Rewarped | Apache 2.0 | ✅ | Required | ICLR 2025 |
| Schr | MIT | ✅ | Required | JAX native |
| JAX-MPM | MIT | ✅ | Required | arXiv 2025 |
| Kinetix | MIT | ✅ | Required | ICLR 2025 Oral |
| torch-diffsim | MIT | ✅ | Required | PyTorch native |
| MechanicsDSL | MIT | ✅ | Required | 15 code generators |

### Data Sources:
| Source | License | Commercial Use | Attribution | Notes |
|--------|---------|----------------|-------------|-------|
| arXiv | Open | ✅ | Optional | |
| PubMed | Open | ✅ | Optional | |
| ORCID | CC0 | ✅ | Optional | Public data |
| Semantic Scholar | Non-commercial | ⚠️ | Required | Check use case |
| CrossRef | Open | ✅ | Optional | |
| Grok/X.ai | Paid | ✅ | N/A | Token-based |
| Mastodon | AGPLv3 | ✅ | Required | If modified, share code |
| Sci-Hub | ❌ ILLEGAL | ❌ | ❌ | DO NOT USE |

### Cloud Services:
| Service | License | Commercial | Notes |
|---------|---------|------------|-------|
| vast.ai | Paid API | ✅ | Pay-per-GPU-hour |

**Action:** Add license checker to all external API clients and physics engines.

---

## READY TO EXECUTE

**Total:** 38 batches, ~35 agents
**Estimated time:** 3-4 hours with parallel execution
**Target grade:** 10/10

**Execution order:**
1. **Batch A1-A8:** Multi-Engine Physics (8 agents parallel)
2. **Batch B1-B6:** Mega-Database (6 agents parallel)
3. **Batch C1-C3:** Preprint/Code (3 agents parallel)
4. **Batch D1-D3:** International (3 agents parallel)
5. **Batch E1-E2:** Patents (2 agents parallel)
6. **Batch F1-F3:** Social (3 agents parallel)
7. **Batch G1-G3:** Verification (3 agents parallel)
8. **Batch H1-H6:** API/Frontend (6 agents parallel)
9. **Batch I1-I4:** Tests/Docs (4 agents parallel)

**Next step:** Execute Batch A1 (Physics Auto-Detector)
