# GPU Setup Guide

> How to run simulations on local GPU vs cloud (vast.ai)

---

## Local GPU Auto-Detect

```bash
blast simulate --detect-gpu
blast simulate --list
blast simulate --engine newtonian --dry-run
```

**Supported backends (when installed):**
- **NVIDIA CUDA** — `nvidia-smi` detection, cuDNN auto-check
- **Apple Metal / MPS** — `torch.backends.mps.is_available()`
- **AMD ROCm** — experimental, via `HIP_VISIBLE_DEVICES`

Many P1 bridges only become **SUCCESS** when real inputs are provided
(`.tpr`, `wrfout`, topology+trajectory, OpenFOAM `case_dir`, etc.).
Import-only / stub responses surface as `unavailable` (not fake success).
NumPy / non-engine fallbacks use `partial` + `engine_truth: not_*` — see
[HONESTY_CONTRACT.md](HONESTY_CONTRACT.md).

**Newton:** prefer project `.venv` (Python 3.11) + `NEWTON_PYTHON` / Warp cache
under `.cache/warp`. CPU-only Newton path is not claimed as GPU-accelerated.

**If not detected:**
```bash
# The engine will print exact install commands, e.g.:
# conda install -c conda-forge openmm
# pip install openmm
```

---

## Engine Categories

| Category | Engines | Typical Install |
|----------|---------|-----------------|
| **Molecular Dynamics** | GROMACS, LAMMPS, OpenMM, MDAnalysis | `conda install -c conda-forge gromacs` |
| **Quantum Chemistry** | PySCF, Psi4, Quantum ESPRESSO | `pip install pyscf` |
| **CFD** | OpenFOAM, FEniCSx | `conda install -c conda-forge fenics` |
| **Neuroscience** | NEURON, Brian2, Jaxley | `pip install neuron` |
| **Systems Biology** | COPASI, Tellurium | `pip install tellurium` |
| **Multi-physics** | MuJoCo, PyBullet, Taichi | `pip install mujoco` |
| **Astrophysics** | Rebound, AMUSE | `pip install rebound` |
| **ML/MD** | JAX MD, JAX-LaB | `pip install jax-md` |

Also: TUI capabilities overlay (`blast tui` → `Ctrl+Shift+C`) and MCP tool `c4_simulate`.

---

## Cloud GPU (vast.ai)

```bash
# Cost estimation only (no remote job is submitted)
blast simulate --engine gromacs --estimate-cost
```

**Honest limit:** remote vast.ai SSH/script execution is **not implemented**.
`--estimate-cost` prints local pricing heuristics; it does not rent GPUs or return simulated success.

**Workflow:**
1. `blast simulate --engine <name> --dry-run` → availability + install hints
2. Install locally (or implement a real remote runner)
3. Re-run without `--dry-run` with required input files

---

## Honest Fallback

If an engine is missing or returns a stub payload, c4reqber reports
`status=unavailable` / `stub=True` and exit code `2` from `blast simulate`.
Quality gates and MCP `c4_simulate` treat skipped/stub results as incomplete —
not PASS 1.0.
