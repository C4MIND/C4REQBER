# Simulation Engines Setup Guide — C4REQBER v5.6.0

> **Last updated:** 2026-06-03 | **Target:** Developers who want all 38 simulation engines

C4REQBER supports **38 simulation bridges**. All are **lazy-loaded** — the system checks availability at runtime and skips missing engines gracefully. You only need to install the engines you actually use.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Core runtime |
| conda or mamba | any | For compiled C++/Fortran engines |
| CUDA toolkit | 12.x | Optional — for GPU engines on Linux |
| Homebrew (macOS) | latest | For macOS dependencies |

**Platform matrix:**
- **Linux (Ubuntu 22.04+):** Full support — all 38 engines installable
- **macOS (Apple Silicon):** ~30 engines — no CUDA, Metal replaces CUDA for some
- **Windows (WSL2):** ~25 engines — use WSL2 for Linux compatibility

---

## Tier 1 — pip install (Python-native, easiest)

```bash
# Molecular dynamics + chemistry
pip install pyscf psi4 openmm

# Neuroscience + bio
pip install neuron tellurium cobra

# Robotics + physics
pip install mujoco taichi

# ML + math
pip install jax jax-md diffeqpy

# Other
pip install xarray mesa simpy rebound amuse-py
pip install autogrid vina  # AutoDock
```

**Notes:**
- `PySCF` — pure Python, no compile needed. CPU only.
- `Psi4` — conda recommended (`conda install -c psi4 psi4`)
- `OpenMM` — conda recommended for CUDA support (`conda install -c conda-forge openmm`)
- `MuJoCo` — includes native binaries, works on macOS Metal
- `Taichi` — auto-detects CUDA/Metal/Vulkan

---

## Tier 2 — conda install (Compiled C++/Fortran)

```bash
# Create a dedicated env (recommended)
conda create -n c4engines python=3.11
conda activate c4engines

# Molecular dynamics
conda install -c conda-forge gromacs lammps mdanalysis

# CFD
conda install -c conda-forge fenics-dolfinx openfoam

# Climate / geoscience
conda install -c conda-forge wrf-python

# Other
conda install -c conda-forge slim  # population genetics
conda install -c conda-forge vina  # docking (alternative to pip)
```

**Notes:**
- `GROMACS` — Linux only for GPU. macOS CPU works.
- `LAMMPS` — GPU via Kokkos. Complex build — use conda.
- `OpenFOAM` — Linux only. macOS unsupported.
- `FEniCSx` — works on macOS but no GPU.

---

## Tier 3 — Special installs

### BoolNet (R package)

```bash
# Install R first: https://cran.r-project.org/
R -e "install.packages('BiocManager'); BiocManager::install('BoolNet')"
pip install rpy2
```

### MATLAB Engine (optional)

```bash
# Requires MATLAB installed locally
# Path varies by MATLAB version:
# macOS: cd /Applications/MATLAB_R2024a.app/extern/engines/python && python setup.py install
# Linux: cd /usr/local/MATLAB/R2024a/extern/engines/python && python setup.py install
```

### JAX-based engines (JAX MD, JAX-LaB)

```bash
# CPU-only (default, works everywhere)
pip install jax jax-md

# GPU (Linux only)
pip install jax[cuda12] jax-md
```

**macOS note:** JAX has no CUDA support on macOS. Use CPU backend or Metal-enabled forks.

---

## Tier 4 — GPU-only / Platform-specific

### NVIDIA CUDA bridges

```bash
# Requires: CUDA 12.x, cuDNN, NVIDIA driver 535+
# These are internal bridges, not pip packages:
# - nvidia_bridge.py (41,930 lines — CUDA wrappers)
# - newton_bridge.py (22,443 lines — physics engine)

# Verify CUDA
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### macOS Metal

```bash
# MuJoCo — uses Metal automatically on Apple Silicon
pip install mujoco

# Taichi — Metal backend
pip install taichi
python -c "import taichi; ti.init(arch=ti.metal)"
```

---

## Availability Check

Run this to see which engines are available on your machine:

```python
from src.simulations.virtual_bio import VirtualBioOrchestrator
from src.simulations.runner_v2 import PatternRunnerV2

# Check all simulation domains
orch = VirtualBioOrchestrator()
for domain in orch.list_available():
    print(f"{domain['domain']}: available={domain['available']}")

# Check all 38 bridges
from src.simulations import runner_v2
runner = PatternRunnerV2()
print(f"Registered engines: {len(runner.engine_map)}")
```

Or use the CLI:

```bash
blast sim --list   # List available simulation engines
blast sim --status # Show GPU/CPU status
```

---

## Engine Reference Table

| Engine | Domain | Install | GPU | macOS | Linux |
|--------|--------|---------|-----|-------|-------|
| PySCF | Quantum chemistry | `pip` | No | ✅ | ✅ |
| Psi4 | Quantum chemistry | `conda` | Optional | ✅ | ✅ |
| OpenMM | MD | `conda` | CUDA/OpenCL | ✅ | ✅ |
| GROMACS | MD | `conda` | CUDA | ❌ | ✅ |
| LAMMPS | MD | `conda` | Kokkos | ❌ | ✅ |
| MDAnalysis | MD analysis | `conda` | No | ✅ | ✅ |
| MuJoCo | Robotics | `pip` | Metal/CUDA | ✅ | ✅ |
| PyBullet | Robotics | `pip` | No | ✅ | ✅ |
| Taichi | Graphics/PDE | `pip` | Metal/CUDA | ✅ | ✅ |
| FEniCSx | FEM/PDE | `conda` | No | ✅ | ✅ |
| OpenFOAM | CFD | `conda` | No | ❌ | ✅ |
| WRF | Climate | `conda` | No | ❌ | ✅ |
| NEURON | Neuroscience | `pip` | No | ✅ | ✅ |
| Brian2 | Neuroscience | `pip` | No | ✅ | ✅ |
| Jaxley | Neuroscience | `pip` | No | ✅ | ✅ |
| Tellurium | Systems biology | `pip` | No | ✅ | ✅ |
| COPASI | Systems biology | `pip` | No | ✅ | ✅ |
| COBRApy | Metabolism | `pip` | No | ✅ | ✅ |
| Vina | Docking | `pip/conda` | No | ✅ | ✅ |
| SLiM | Population genetics | `conda` | No | ✅ | ✅ |
| BoolNet | Boolean networks | R + `rpy2` | No | ✅ | ✅ |
| JAX MD | ML force fields | `pip` | CUDA | ✅(CPU) | ✅ |
| JAX-LaB | ML dynamics | `pip` | CUDA | ✅(CPU) | ✅ |
| ModelingToolkit.jl | Julia DEs | `julia` | No | ✅ | ✅ |
| diffeqpy | Python DEs | `pip` | No | ✅ | ✅ |
| Rebound | N-body | `pip` | No | ✅ | ✅ |
| AMUSE | Astrophysics | `pip` | No | ✅ | ✅ |
| xarray | Geoscience | `pip` | No | ✅ | ✅ |
| Mesa | Agent-based | `pip` | No | ✅ | ✅ |
| SimPy | Discrete event | `pip` | No | ✅ | ✅ |
| Quantum ESPRESSO | DFT | `conda` | CUDA | ❌ | ✅ |
| MATLAB | General | MATLAB | No | ✅ | ✅ |
| nvidia_bridge | GPU compute | CUDA | CUDA | ❌ | ✅ |
| newton_bridge | Physics | Built-in | CUDA | ✅(CPU) | ✅ |
| torchsim_bridge | PyTorch sim | `pip` | CUDA | ✅(MPS) | ✅ |
| jaxsim_bridge | JAX sim | `pip` | CPU | ✅ | ✅ |
| schr_bridge | Schrödinger | `pip` | No | ✅ | ✅ |
| mirrorfish_bridge | Custom | Built-in | No | ✅ | ✅ |

---

## Minimal Setup (Core-only)

If you only need the discovery pipeline without simulations:

```bash
# Just the Python backend — no conda, no GPU
pip install -r requirements.txt
python -m src.api.server
```

Simulations are **truly optional**. The pipeline works with `simulation_enabled=false`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `conda: command not found` | Install [Miniforge](https://github.com/conda-forge/miniforge) |
| `CUDA not available` | Expected on macOS. Use CPU or Metal backends. |
| `ImportError: libX.so` | Missing system library. `sudo apt-get install build-essential` (Linux) or `xcode-select --install` (macOS) |
| `R_HOME not set` | `export R_HOME=/usr/lib/R` (Linux) or `/Library/Frameworks/R.framework/Resources` (macOS) |
| Engine shows `available=false` | Check install path is in `PATH` / `PYTHONPATH` |
