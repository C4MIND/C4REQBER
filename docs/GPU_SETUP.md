# GPU Setup Guide

> How to run simulations on local GPU vs cloud (vast.ai)

---

## Local GPU Auto-Detect

```bash
blast simulate --engine openmm --detect-gpu
```

**Supported backends:**
- **NVIDIA CUDA** — `nvidia-smi` detection, cuDNN auto-check
- **Apple Metal / MPS** — `torch.backends.mps.is_available()`
- **AMD ROCm** — experimental, via `HIP_VISIBLE_DEVICES`

**If not detected:**
```bash
# The engine will print exact install commands:
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

---

## Cloud GPU (vast.ai)

For engines too large for local hardware:

```bash
# Cost estimation before running
blast simulate --engine gromacs --estimate-cost

# Example output:
# Local: 8h on RTX 4090 ($0)
# vast.ai: 1h on A100 ($0.80)
# vast.ai: 2h on RTX 3090 ($0.40)
```

**Workflow:**
1. `blast simulate --engine <name> --dry-run` → shows exact conda/pip commands
2. Install locally OR rent on vast.ai
3. Re-run without `--dry-run`

---

## Honest Fallback

If engine not installed, c4reqber automatically falls back to:
- Toy analytical model (same physics equations, coarse grid)
- Clear labeling: `[FALLBACK: toy model — install <engine> for full simulation]`
- No fake data — equations are real, just lower resolution
