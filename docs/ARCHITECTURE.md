# TURBO-CDI v8.4 "Prometheus" Architecture

**Version:** 8.4.0  
**Code Name:** Prometheus  
**Last Updated:** 2026-04-14

---

## Executive Summary

TURBO-CDI v8.4 is an **enterprise multi-agent AI platform** for scientific discovery. It unifies a C4³ cognitive engine, 100+ v6 simulation patterns, an autonomous discovery agent, JWT-authenticated REST API, and a Ghost in the Shell-themed web UI. The platform is deployed **exclusively via Docker Compose**.

---

## System Architecture (v8.4)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Web UI (Russian)              │  CLI Tool            │  External Apps  │
│  ──────────────────────────    │  ─────────────────   │  ─────────────  │
│  • Ghost in the Shell theme    │  • discover          │  • Jupyter      │
│  • Pattern browser & runner    │  • patterns list/run │  • Postman      │
│  • C4³ ASCII visualization     │  • solve / validate  │  • Custom bots  │
│  • Three.js C4 cube            │                      │                 │
│  Files: index.html / main.css  │                      │                 │
│         / app.js               │                      │                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP / WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY (nginx + FastAPI)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  nginx (port 3000)            │  FastAPI (port 8000)                     │
│  ────────────────             │  ───────────────────                     │
│  • Serve static web/          │  • Auth (JWT + bcrypt)                   │
│  • Reverse proxy /api         │  • Discovery (/discover)                 │
│  • Disable cache (dev)        │  • Patterns (/patterns/*)                │
│                               │  • Search (/search/papers)               │
│                               │  • WebSocket (/ws/{id})                  │
│                               │  • Health / Metrics                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  AuthManager                  │  RateLimiter         │  CacheManager    │
│  ───────────                  │  ───────────         │  ───────────     │
│  • bcrypt hash/verify         │  • Per-user limits   │  • Redis backend │
│  • JWT encode/decode          │  • Tier-based rules  │  • TTL caching   │
│  • PostgreSQL users table     │                      │                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Discovery Agent              │  One-Shot Solver     │  Pattern Runner  │
│  ───────────────              │  ───────────────     │  ─────────────   │
│  • C4+TRIZ generation         │  • Literature search │  • 100 patterns  │
│  • Cross-domain analogies     │  • Consensus meter   │  • Auto-match    │
│  • Falsifiability scoring     │  • Pattern sim       │  • Async run     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     DATA & INFRASTRUCTURE LAYER                        │
├─────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL 15                │  Redis 7             │  Docker Volumes  │
│  ───────────                  │  ───────             │  ─────────────   │
│  • users                      │  • Session cache     │  • postgres_data │
│  • discoveries                │  • Result cache      │  • redis_data    │
│  • hypotheses                 │  • Rate limit counters                  │
│  • api_logs                   │                                          │
│  Init: migrations/init.sql    │                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## v6 Pattern Integration

### What Changed in v8.4

The orphaned v6 engine (`/Users/figuramax/LocalProjects/v6/`) contained **104 scientific simulation pattern files** (~57,000 lines). In v8.4:

1. **All patterns were copied** into `src/patterns/v6_legacy/`
2. **A compatibility bridge** (`src/patterns/core.py`) was created to normalize `SimulationPattern`/`BasePattern`/`Hypothesis`/`SimulationResult` between v6 and v8
3. **A unified runner** (`src/patterns/runner.py`) dynamically discovers and executes all patterns
4. **100 patterns load and run successfully** via the API

### Pattern Categories

```
Physics         → CFD, Maxwell FDTD, N-body gravity, Quantum circuits,
                  Thermal, Elasticity 3D, Acoustic waves, Plasma PIC
Biology         → Neural network, Connectome, Epidemic SEIR, Protein folding,
                  Enzyme kinetics, Gene regulatory, Synaptic plasticity
Economics       → DSGE, GARCH, Game theory, Portfolio optimization,
                  Supply chain, Input-output, Market microstructure
Engineering     → FEM, MPC, Kalman filter, SLAM, Circuit simulation,
                  PID tuning, Inverse kinematics, Composite mechanics
Earth Science   → Climate GCM, Ocean circulation, Seismic waves, Wildfire,
                  Air quality, Biogeochemistry, Land surface
Social Science  → Social network, Opinion dynamics, Conflict, Urban growth,
                  Migration, Cultural diffusion, Language evolution
```

### Pattern Execution Flow

```
User Request
    │
    ▼
┌─────────────────────────────────────┐
│  POST /patterns/{id}/run            │
│  or POST /discover (auto-matched)   │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  PatternRunner.get_runner()         │
│  • Lazy load module                 │
│  • Instantiate pattern class        │
│  • Build Hypothesis dataclass       │
│  • Detect config signature          │
│  • Call pattern.run()               │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  SimulationResult                   │
│  • metrics (dict)                   │
│  • confidence_score                 │
│  • execution_time                   │
│  • status (completed/failed)        │
└─────────────────────────────────────┘
```

---

## Discovery Data Flow

```
POST /discover
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  1. AUTH & RATE LIMIT                                       │
│     JWT validation → tier check → allow/deny                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  2. LITERATURE SEARCH (Semantic Scholar)                    │
│     Query problem → fetch papers → rank by citations        │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  3. CONSENSUS ANALYSIS                                      │
│     Classify evidence → calculate consensus score           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  4. HYPOTHESIS GENERATION                                   │
│     C4+TRIZ path → cross-domain analogies → hybrid merge    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  5. PATTERN SIMULATION (v6 integration)                     │
│     Match keyword → run pattern → blend confidence          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  6. VALIDATION PLANNING                                     │
│     Generate falsifiability criteria + cost estimates       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  7. SAVE & CACHE                                            │
│     PostgreSQL persistence → Redis cache (TTL 1h)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Structure (v8.4)

```
TURBO-CDI/
├── web/                              # Ghost in the Shell UI
│   ├── index.html                    # Structure (Russian)
│   ├── css/
│   │   ├── main.css                  # All styles
│   │   ├── ghost-terminal.css        # Matrix / terminal fx
│   │   └── c4-design-system.css      # Design tokens
│   └── js/
│       ├── app.js                    # Logic + pattern launcher
│       ├── c4-cube.js                # Three.js 3D cube
│       ├── liquid-animator.js        # Transitions
│       └── turbo-websocket.js        # WS client
│
├── src/
│   ├── api/                          # FastAPI production server
│   │   ├── server.py                 # Main API app
│   │   ├── auth.py                   # JWT + bcrypt
│   │   ├── database.py               # Async PostgreSQL
│   │   ├── cache.py                  # Redis manager
│   │   ├── rate_limiter.py           # Request throttling
│   │   ├── models.py                 # Pydantic schemas
│   │   └── websocket.py              # Connection manager
│   │
│   ├── patterns/                     # v6 integration
│   │   ├── core.py                   # Compatibility bridge
│   │   ├── runner.py                 # Unified execution API
│   │   └── v6_legacy/                # 100 pattern modules
│   │       ├── cfd.py
│   │       ├── monte_carlo.py
│   │       ├── agent_based.py
│   │       ├── quantum.py
│   │       ├── neural_network.py
│   │       └── ... (100 total)
│   │
│   ├── agent/                        # Discovery agent
│   │   └── discovery_agent.py        # C4+TRIZ+Analogy pipeline
│   │
│   ├── solver/                       # One-shot solver
│   │   └── one_shot.py               # Full cycle + pattern sim
│   │
│   ├── validation/                   # Scientific validation
│   │   ├── consensus_meter.py        # Evidence scoring
│   │   └── tracker.py                # Experiment lifecycle
│   │
│   ├── search/                       # Literature search
│   │   └── semantic_scholar.py       # Academic paper client
│   │
│   ├── graph/                        # Knowledge graph
│   │   └── knowledge_graph.py        # NetworkX backend
│   │
│   ├── analogy/                      # Cross-domain reasoning
│   │   └── engine.py                 # TF-IDF / Word2Vec
│   │
│   ├── triz/                         # TRIZ bridge
│   │   └── bridge.py                 # C4-TRIZ mappings
│   │
│   └── cli.py                        # Command-line interface
│
├── migrations/
│   └── init.sql                      # DB schema (users, discoveries, hypotheses)
│
├── archive/                          # Historical reports
│   └── v8-reports/                   # Moved v8 MD files
│
├── docker-compose.yml                # 4-service orchestration
├── Dockerfile.simple                 # API container build
├── nginx.conf                        # Static file server + proxy
└── docs/
    └── ARCHITECTURE.md               # This file
```

---

## Authentication Flow

```
POST /auth/register
    │
    ▼
┌─────────────────────────────────────┐
│  AuthManager.hash_password()        │
│  bcrypt → asyncpg INSERT users      │
└─────────────────────────────────────┘

POST /auth/login
    │
    ▼
┌─────────────────────────────────────┐
│  AuthManager.authenticate()         │
│  Fetch hash → bcrypt.checkpw()      │
│  Create JWT (HS256, 24h expiry)     │
└─────────────────────────────────────┘

Authenticated Request
    │
    ▼
┌─────────────────────────────────────┐
│  get_current_user() dependency      │
│  Decode JWT → fetch user row        │
│  Return user dict or 401            │
└─────────────────────────────────────┘
```

---

## Docker Compose Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **api** | `turbo-cdi-api` (Dockerfile.simple) | 8000 | FastAPI server |
| **web** | `nginx:alpine` | 3000 | Static Ghost UI |
| **postgres** | `postgres:15-alpine` | 5432 | User + discovery data |
| **redis** | `redis:7-alpine` | 6379 | Cache + rate limits |

### Health Checks
- API: `curl -f http://localhost:8000/health`
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| API cold start | ~3s | Python 3.11 + pattern discovery |
| Health check | <50ms | Lightweight DB ping |
| Pattern list | ~100ms | 100 modules already loaded |
| CFD simulation (50×50) | ~700ms | Potential flow solver |
| Agent-Based (100 agents, 1k steps) | ~300ms | Simplified ABM |
| Full discovery cycle | 2–10s | Depends on literature search |
| Docker image size | ~350MB | scipy + numpy + asyncpg |

---

## Security Model

| Layer | Implementation |
|-------|----------------|
| **Transport** | HTTPS recommended in production (nginx TLS) |
| **Authentication** | JWT (HS256), 24h expiration |
| **Passwords** | bcrypt with auto salt |
| **Rate Limiting** | Per-user request windows (Redis-backed) |
| **Input Validation** | Pydantic v2 models on all endpoints |
| **SQL Safety** | asyncpg parameterized queries |
| **Secrets** | `.env` excluded from git via `.gitignore` |

---

## Scaling Strategy

### Current: Single Node Docker Compose
Suitable for local development and small teams.

### Future: Kubernetes
- Horizontal Pod Autoscaling (3–20 replicas)
- Shared PostgreSQL + Redis cluster
- Celery task queue for long-running pattern simulations
- GPU nodes for CUDA-accelerated patterns

---

## Roadmap

### v8.5 (Near-term)
- [ ] Web UI dark-mode toggle independent of Ghost theme
- [ ] Pattern parameter forms (auto-generated from pattern metadata)
- [ ] Discovery result visualization charts
- [ ] Export discoveries to PDF/JSON from web UI

### v9.0 (Mid-term)
- [ ] Multi-user collaboration on discoveries
- [ ] Real-time WebSocket pattern progress bars
- [ ] Plugin system for custom patterns
- [ ] Cloud deployment templates (AWS/GCP)

### v10.0 (Long-term)
- [ ] Auto-experiment design from validated hypotheses
- [ ] Integration with lab equipment APIs
- [ ] Federated discovery across institutions

---

## License

MIT License — TURBO-CDI Team 2026

---

**Architecture Status: PRODUCTION READY** 🚀
