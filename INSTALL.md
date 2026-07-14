# C4REQBER Developer Setup Guide

> **Target audience:** Contributors, researchers, and developers who want to run C4REQBER locally or extend it.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | 3.14 recommended for latest features |
| Go | 1.22+ | Required for TUI v9 (Bubble Tea) |
| Git | 2.30+ | For cloning and version control |
| pip | 24+ | For package installation |
| (Optional) Docker | 24+ | For containerized deployment |
| (Optional) conda/mamba | any | For simulation engine dependencies |

**macOS users:** Apple Silicon (M1/M2/M3) is fully supported. Metal is available for some GPU engines (MuJoCo, Taichi). JAX-based engines run CPU-only on macOS.

---

## 2. Quick Start

```bash
# 1. Clone the repository
git clone git@gitlab.com:cognitive-functors/turbo-cdi.git
cd turbo-cdi

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Install CLI dependencies (typer, rich)
pip install typer rich

# 5. Copy environment template
cp .env.example .env

# 6. Run tests
pytest tests/ -q

# 7. Start the API server
python -m src.api.server

# 8. Build TUI v9 (Go)
make -C src/tui/v9 build

# 9. Or use the CLI
python -m src.cli.typer_app --help
```

---

## 3. Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

**Required for development:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `JWT_SECRET` | `dev-secret-CHANGE-IN-PRODUCTION` | JWT signing (dev warning logged) |
| `C4REQBER_JWT_SECRET` | `dev-web3-secret-CHANGE-IN-PRODUCTION` | Web3 auth (dev warning logged) |
| `OPENROUTER_API_KEY` | *(none)* | LLM routing via OpenRouter |
| `BRAVE_API_KEY` | *(none)* | Web search via Brave |

**Optional:**

| Variable | Purpose |
|----------|---------|
| `ENABLE_OPENTELEMETRY=true` | Enable distributed tracing |
| `PROMETHEUS_PORT=9090` | Prometheus metrics port |
| `CUDA_VISIBLE_DEVICES` | GPU device selection |

> ⚠️ **Security:** Never commit `.env` with real secrets. `.env` is in `.gitignore`. `.env.example` contains dummy values only.

---

## 4. Installing Simulation Engines (Optional)

C4REQBER supports 36 simulation engines. Most are **lazy-loaded** — you only need to install the ones you use.

### 4.1 GPU-Aware Install Hints

| Engine | Install Command | GPU | Platform |
|--------|----------------|-----|----------|
| **OpenMM** | `conda install -c conda-forge openmm` | CUDA/OpenCL | Linux/macOS |
| **Psi4** | `conda install -c psi4 psi4` | CUDA (optional) | Linux/macOS |
| **PySCF** | `pip install pyscf` | CPU | All |
| **GROMACS** | `conda install -c conda-forge gromacs` | CUDA | Linux |
| **LAMMPS** | `conda install -c conda-forge lammps` | CUDA | Linux |
| **MuJoCo** | `pip install mujoco` | Metal/CUDA | macOS/Linux |
| **Taichi** | `pip install taichi` | Metal/CUDA | macOS/Linux |
| **JAX MD** | `pip install jax-md` | CPU (macOS) | All |
| **JAX-LaB** | `pip install jaxlab` | CPU (macOS) | All |
| **FEniCSx** | `conda install -c conda-forge fenics-dolfinx` | CPU | Linux/macOS |
| **COBRApy** | `pip install cobra` | CPU | All |
| **Tellurium** | `pip install tellurium` | CPU | All |
| **AutoDock Vina** | `conda install -c conda-forge vina` | CPU | All |
| **SLiM** | `conda install -c conda-forge slim` | CPU | All |
| **BoolNet** | `R -e "BiocManager::install('BoolNet')"` + `pip install rpy2` | CPU | All |

### 4.2 macOS Specific Notes

- **Metal:** Supported by MuJoCo and Taichi. JAX-based engines (JAX MD, JAX-LaB, JaxSim) run CPU-only.
- **OpenMM:** Use `CPU` or `OpenCL` platform. Metal is **not** supported by OpenMM.
- **CUDA:** Not available on macOS. Use CPU or Metal backends.

### 4.3 Checking Availability

```python
from src.simulations.virtual_bio import VirtualBioOrchestrator
orch = VirtualBioOrchestrator()
for domain in orch.list_available():
    print(f"{domain['domain']}: available={domain['available']}")
```

---

## 5. Development Workflow

### 5.1 Running Tests

```bash
# Full test suite
pytest tests/ -q

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific module
pytest tests/simulations/ -v

# Skip flaky benchmarks
pytest tests/ --ignore=tests/benchmarks/ -q
```

### 5.2 Code Style

```bash
# Format with ruff
ruff format src/ tests/

# Lint
ruff check src/ tests/

# Type check (mypy)
mypy src/ --ignore-missing-imports
```

### 5.3 Running Components

```bash
# API server (FastAPI + SSE/WebSocket)
python -m src.api.server
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)
# → http://localhost:8000/metrics (Prometheus)

# MCP server
blast serve --mcp
# → 21 tools exposed for AI agents

# TUI v9 Cockpit (Go + Bubble Tea)
blast tui
blast tui --demo --story=crispr   # no backend required
blast tui --packages              # scientific package installer

# CLI (Typer + Rich)
turbo --help
turbo discover "your problem"
turbo research "query" --limit 10
```

### 5.4 Adding a New Simulation Adapter

1. Create `src/simulations/myengine_bridge.py`:
```python
from .base_adapter import BaseSimulationAdapter, SimulationResult

class MyEngineBridge(BaseSimulationAdapter):
    _engine_name = "myengine"
    _package_checks = ["myengine_pkg"]
    _install_hint = "pip install myengine"

    def run(self, input_data=None):
        def _run(data):
            # Your simulation logic
            return {"result": 42}
        return self._run_wrapped(_run, input_data)
```

2. Register in `src/simulations/runner_v2.py`:
```python
elif engine == "myengine":
    from .myengine_bridge import MyEngineBridge
    bridge = MyEngineBridge()
```

3. Add to `src/simulations/pattern_engine_map.py`:
```python
class EngineType(Enum):
    # ... existing ...
    MYENGINE = "myengine"
```

4. Add pattern mappings in `PATTERN_ENGINE_MAP` and `CATEGORY_ENGINE_MAP`.

---

## 6. Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'httpx'` | `pip install httpx` (optional for async LLM) |
| `ModuleNotFoundError: No module named 'typer'` | `pip install typer rich` |
| `JWT secret warning` | Set `JWT_SECRET` in `.env` for production |
| `CUDA not available` | Expected on macOS/CPU-only machines. Engines fallback to CPU. |
| `Import errors in simulations` | Lazy loading handles this. Install specific engine if needed. |
| `Prometheus duplicate metric` | Fixed in v5.4 — `_safe_metric()` helper handles test environments. |
| `Test flakiness` | `test_mc_convergence_estimates_consistent` is stochastic. Re-run if it fails. |

---

## 7. Project Structure

```
c4reqber/
├── src/
│   ├── api/              # FastAPI server, auth, metrics, tracing
│   ├── auth/             # JWT, Web3 authentication
│   ├── c4/               # C4 cognitive engine (Z₃³ space)
│   ├── cli/              # Typer CLI with Rich UI
│   ├── core/             # CDI, profile manager
│   ├── discovery/        # Gap analysis, already-shifted detector
│   ├── knowledge/        # 33 source adapters, orchestrator, MegaDB
│   ├── metamodels/       # QZRF, MP, IMPACT, MatrixDream
│   ├── mcp_server/       # MCP server (21 tools)
│   ├── models/           # Pydantic schemas
│   ├── observability/    # OpenTelemetry tracing
│   ├── pipeline/         # HIL pipeline, quality gates
│   ├── plugins/          # Plugin registry
│   ├── simulations/      # 38 engine bridges
│   ├── tui/              # Go TUI v9 terminal cockpit
│   └── utils/            # Shared utilities
├── tests/                # Test suite (9,906 collected)
├── dissertations/        # Generated output
├── ARCHITECTURE_C4R.md   # Full system architecture
├── src/tui/v9/ARCHITECTURE.md # TUI-specific architecture
├── AGENTS.md             # Agent developer guide
├── INSTALL.md            # This file
└── README.md             # User-facing overview
```

---

## 8. Getting Help

- **Documentation:** See `ARCHITECTURE_C4R.md` for full system architecture
- **Agent guide:** See `AGENTS.md` for coding conventions and agent preferences
- **Issues:** Open a GitLab issue with `bug`, `feature`, or `question` label
- **Discussions:** Use GitLab issues for architecture questions

---

*Last updated: 2026-07-13*
