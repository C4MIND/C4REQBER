# TURBO-CDI v8.4 "Prometheus"

## Enterprise Multi-Agent AI Platform for Scientific Discovery

[![Version](https://img.shields.io/badge/version-8.4.0-blue)](./)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![C4](https://img.shields.io/badge/C4-Z₃³%2027--operators-orange)]()
[![Patterns](https://img.shields.io/badge/v6_patterns-100+-purple)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue)]()

> **"Visualize, Simulate, Validate — The Complete Research Platform"**

---

## What is TURBO-CDI v8.4?

**TURBO-CDI v8.4** is an enterprise-grade scientific discovery platform that unifies:

- **C4³ Cognitive Engine** — 27-state navigation for hypothesis generation
- **v6 Pattern Library** — 100+ runnable simulation patterns (physics, biology, economics, engineering, earth science, social science)
- **Discovery Agent** — Autonomous C4+TRIZ+Analogy pipeline with real-time pattern simulation
- **Validation Hierarchy** — Formal methods → Model checking → Property testing → Monte Carlo
- **Ghost in the Shell Web UI** — Russian-localized interface with matrix/terminal aesthetics
- **Production Auth & API** — JWT-based auth, rate limiting, PostgreSQL+Redis, Docker-only deployment

---

## Key Features

### 1. Web Interface (Ghost in the Shell Theme)
- **3-file architecture**: `index.html` + `css/main.css` + `js/app.js`
- **Russian localization** — all navigation, buttons, labels, and status messages
- **ASCII terminal header** with live clock, matrix rain, hex grid, scan lines
- **C4 ASCII visualization panel** with Z₃³ state space geometry
- **Interactive pattern browser & launcher** — browse 100 patterns by category and run simulations directly from the browser

Access: `http://localhost:3000`

### 2. v6 Scientific Patterns (100+ Simulations)

Integrated domains:

| Domain | Example Patterns |
|--------|------------------|
| **Physics** | CFD, FDTD, Maxwell equations, N-body gravity, quantum circuits, thermal analysis |
| **Biology** | Neural networks, connectome dynamics, epidemic SEIR, protein folding, enzyme kinetics |
| **Economics** | DSGE, GARCH, game theory, portfolio optimization, supply chain |
| **Engineering** | FEM, MPC, Kalman filter, SLAM, circuit simulation, PID tuning |
| **Earth Science** | Climate GCM, ocean circulation, seismic waves, wildfire, air quality |
| **Social Science** | Social network diffusion, opinion dynamics, conflict models, urban growth |

### 3. Discovery Engine with Pattern Simulation

The `/discover` endpoint now automatically:
1. Generates hypotheses via C4+TRIZ+Analogy
2. **Matches each hypothesis to the best v6 pattern**
3. **Runs the simulation** and blends the result into confidence scoring
4. Returns re-ranked hypotheses with simulation metrics

### 4. REST API (FastAPI + WebSocket)

**Public endpoints:**
- `GET /health` — System health
- `GET /patterns` — List all 100 patterns by category
- `GET /patterns/{id}` — Pattern metadata
- `POST /patterns/{id}/run` — Execute a simulation

**Authenticated endpoints:**
- `POST /auth/register` — Create user
- `POST /auth/login` — Get JWT token
- `POST /discover` — Full discovery cycle
- `GET /discoveries` — List user's discoveries
- `POST /search/papers` — Academic paper search
- `WS /ws/{client_id}` — Real-time progress streaming

### 5. CLI Commands

```bash
# Run discovery with automatic pattern simulation
python src/cli.py discover "Optimize fluid flow in a pipe" --max-hypotheses 5

# List all patterns
python src/cli.py patterns list

# Run a specific pattern
python src/cli.py patterns run cfd "Flow in a cylindrical pipe"

# Show pattern metadata
python src/cli.py patterns info cfd
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- `.env` file with `DATABASE_URL`, `JWT_SECRET`, `POSTGRES_PASSWORD`

### Run Everything

```bash
cd /Users/figuramax/LocalProjects/TURBO-CDI

# Start all services (API, Web, PostgreSQL, Redis)
docker compose up -d --build

# Check health
curl http://localhost:8000/health

# Open Web UI
open http://localhost:3000
```

### Register a Test User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret","name":"Researcher"}'
```

### Run a Discovery

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}' | jq -r '.access_token')

curl -X POST http://localhost:8000/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem":"Optimize fluid flow in a pipe","max_hypotheses":3}'
```

---

## Project Structure

```
TURBO-CDI/
├── web/                      # Ghost in the Shell web UI
│   ├── index.html            # Pure HTML structure (Russian)
│   ├── css/
│   │   ├── main.css          # All extracted styles
│   │   ├── ghost-terminal.css
│   │   └── c4-design-system.css
│   └── js/
│       ├── app.js            # Application logic + pattern launcher
│       ├── c4-cube.js
│       ├── liquid-animator.js
│       └── turbo-websocket.js
├── src/
│   ├── api/                  # FastAPI production server
│   │   ├── server.py         # Main API (auth, discover, patterns, ws)
│   │   ├── auth.py           # JWT + bcrypt
│   │   ├── database.py       # Async PostgreSQL
│   │   ├── cache.py          # Redis cache
│   │   └── models.py         # Pydantic schemas
│   ├── patterns/             # v6 pattern integration
│   │   ├── core.py           # Compatibility bridge
│   │   ├── runner.py         # Unified pattern execution API
│   │   └── v6_legacy/        # 100 simulation patterns
│   ├── agent/                # Scientific discovery agent
│   ├── solver/               # One-shot discovery solver
│   ├── validation/           # Consensus meter & falsifiability
│   ├── search/               # Semantic Scholar client
│   └── cli.py                # Command-line interface
├── migrations/
│   └── init.sql              # PostgreSQL schema (users, discoveries, hypotheses)
├── docker-compose.yml
├── Dockerfile.simple
├── nginx.conf
└── docs/
    └── ARCHITECTURE.md
```

---

## Environment Variables

Create `.env` in project root:

```bash
# Database
DATABASE_URL=postgresql://turbo:turbo_secret@localhost:5432/turbo_cdi
POSTGRES_USER=turbo
POSTGRES_PASSWORD=turbo_secret
POSTGRES_DB=turbo_cdi

# Security
JWT_SECRET=your-64-char-hex-secret
API_KEY=your-32-char-api-key

# AI Providers
OPENROUTER_API_KEY=sk-or-...
GROQ_API_KEY=gsk_...
XAI_API_KEY=xai-...
MISTRAL_API_KEY=...
```

---

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for detailed system design, data flow diagrams, and component descriptions.

---

## License

MIT License — TURBO-CDI Team 2026
