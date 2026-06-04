"""C4REQBER Package Manager — auto-detect, install, manage scientific packages.

Arrow-key TUI menu. Auto-detects installed/available/incompatible packages.
Uses uv for isolated Python environments when needed.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class PackageStatus(Enum):
    INSTALLED = "installed"
    AVAILABLE = "available"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass
class PackageSpec:
    """Definition of an installable scientific package."""

    id: str
    name: str
    pip_name: str
    description: str
    category: str
    min_python: tuple[int, int] | None = None
    max_python: tuple[int, int] | None = None
    uses_gpu: bool = False
    weight_mb: int = 10
    env_vars: dict[str, str] = field(default_factory=dict)
    post_install_check: str = ""
    requires_isolated_env: bool = False

    @property
    def compatible(self) -> bool:
        """Check if this package is compatible with current Python."""
        curr = (sys.version_info.major, sys.version_info.minor)
        if self.min_python and curr < self.min_python:
            return False
        if self.max_python and curr > self.max_python:
            return False
        return True

    @property
    def status(self) -> PackageStatus:
        if not self.compatible and self.requires_isolated_env:
            return self._check_isolated()
        if not self.compatible:
            return self._check_installed_anyway()
        try:
            if self.post_install_check:
                __import__(self.post_install_check)
            else:
                __import__(self.pip_name.replace("-", "_"))
            return PackageStatus.INSTALLED
        except ImportError:
            return PackageStatus.AVAILABLE

    def _check_isolated(self) -> PackageStatus:
        """Check if package is installed in isolated env."""
        env_dir = os.path.expanduser(f"~/.c4reqber/envs/{self.id}")
        if os.path.exists(f"{env_dir}/bin/python"):
            sanitized = re.sub(r"[^a-zA-Z0-9_]", "", self.post_install_check or self.pip_name.replace("-", "_"))
            if not sanitized:
                return PackageStatus.INCOMPATIBLE
            try:
                result = subprocess.run(
                    [f"{env_dir}/bin/python", "-c", f"import {sanitized}"],
                    capture_output=True, timeout=10,
                )
                if result.returncode == 0:
                    return PackageStatus.INSTALLED
            except Exception:
                pass
        return PackageStatus.INCOMPATIBLE

    def _check_installed_anyway(self) -> PackageStatus:
        """Some packages install despite max_python limits (eg OpenMM on 3.14)."""
        try:
            mod_name = self.post_install_check or self.pip_name.replace("-", "_")
            __import__(mod_name)
            return PackageStatus.INSTALLED
        except ImportError:
            return PackageStatus.INCOMPATIBLE


PACKAGES: list[PackageSpec] = [
    PackageSpec(
        id="mlx-lm", name="MLX-LM Local LLM", pip_name="mlx-lm",
        description="Apple Silicon local LLM ($0/MTok). DeepSeek, Qwen, Llama on-device.",
        category="LLM", min_python=(3, 10), uses_gpu=True, weight_mb=200,
        post_install_check="mlx_lm",
    ),
    PackageSpec(
        id="chromadb", name="ChromaDB Vector Store", pip_name="chromadb",
        description="Vector DB for RAG. Caches embeddings, semantic search, agent memory.",
        category="Knowledge", min_python=(3, 9), weight_mb=80,
        post_install_check="chromadb",
    ),
    PackageSpec(
        id="lancedb", name="LanceDB Vector Store", pip_name="lancedb",
        description="Fast vector DB (Rust). Columnar format, zero-config, serverless.",
        category="Knowledge", min_python=(3, 9), weight_mb=40,
        post_install_check="lancedb",
    ),
    PackageSpec(
        id="fastmcp", name="FastMCP Client/Server", pip_name="fastmcp",
        description="Anthropic MCP client + server (22K★). Connect to any MCP tools.",
        category="MCP", min_python=(3, 9), weight_mb=30,
        post_install_check="fastmcp",
    ),
    PackageSpec(
        id="qiskit", name="Qiskit Quantum", pip_name="qiskit",
        description="IBM quantum circuits. Entanglement, Shor/Grover algorithms.",
        category="Simulation", min_python=(3, 9), max_python=(3, 14), weight_mb=50,
        post_install_check="qiskit",
    ),
    PackageSpec(
        id="gym", name="Gymnasium RL", pip_name="gymnasium",
        description="Reinforcement Learning. PPO/A2C/DQN agents from OpenAI Gym.",
        category="AI/ML", min_python=(3, 9), max_python=(3, 14), weight_mb=30,
        post_install_check="gymnasium",
    ),
    PackageSpec(
        id="langgraph", name="LangGraph Agents", pip_name="langgraph",
        description="LLM agents with state graphs. Branching, loops, conditional edges.",
        category="Agent", min_python=(3, 9), weight_mb=40,
        post_install_check="langgraph",
    ),
    PackageSpec(
        id="smithery", name="Smithery MCP Marketplace", pip_name="smithery",
        description="MCP marketplace. Discover & connect any MCP server with one command.",
        category="MCP", min_python=(3, 9), weight_mb=25,
        post_install_check="smithery",
    ),
    PackageSpec(
        id="pymc", name="PyMC Bayesian", pip_name="pymc",
        description="Probabilistic programming. HMC/NUTS samplers, Bayesian statistics.",
        category="Science", min_python=(3, 9), weight_mb=60,
        post_install_check="pymc",
    ),
    PackageSpec(
        id="openmm", name="OpenMM Molecular Dynamics", pip_name="openmm",
        description="Molecular dynamics. Protein folding, Folding@Home, force fields.",
        category="Simulation", min_python=(3, 9), max_python=(3, 14), weight_mb=200,
        post_install_check="openmm",
    ),
    PackageSpec(
        id="deepchem", name="DeepChem Drug Discovery", pip_name="deepchem",
        description="Deep learning for drug discovery. Binding affinity, toxicity prediction.",
        category="Science", min_python=(3, 9), max_python=(3, 13), weight_mb=150,
        requires_isolated_env=True,
    ),
    PackageSpec(
        id="unsloth", name="Unsloth LLM Fine-tuning", pip_name="unsloth",
        description="Local LLM fine-tuning (4-bit QLoRA). Train on your own research papers.",
        category="LLM", min_python=(3, 9), max_python=(3, 13), uses_gpu=True, weight_mb=80,
        requires_isolated_env=True,
    ),
    PackageSpec(
        id="vllm", name="vLLM Server Inference", pip_name="vllm",
        description="High-performance LLM serving. PagedAttention, continuous batching.",
        category="LLM", min_python=(3, 9), max_python=(3, 13), uses_gpu=True, weight_mb=150,
        requires_isolated_env=True,
    ),
    PackageSpec(
        id="nashpy", name="NashPy Game Theory", pip_name="nashpy",
        description="Game theory: Nash equilibria, mixed strategies, evolutionary games.",
        category="Science", min_python=(3, 9), max_python=(3, 12), weight_mb=3,
        requires_isolated_env=True,
    ),
    PackageSpec(
        id="flower", name="Flower Federated Learning", pip_name="flwr",
        description="Federated Learning. Train models across devices without sharing data.",
        category="AI/ML", min_python=(3, 9), max_python=(3, 12), weight_mb=60,
        requires_isolated_env=True,
    ),
]


def detect_all() -> dict[str, PackageStatus]:
    """Scan all known packages and return their status."""
    return {p.id: p.status for p in PACKAGES}


def install_package(package_id: str) -> tuple[bool, str]:
    """Install a package. Returns (success, message)."""
    pkg = next((p for p in PACKAGES if p.id == package_id), None)
    if not pkg:
        return False, f"Package '{package_id}' not found"
    if not pkg.compatible:
        return False, f"Python {sys.version_info.major}.{sys.version_info.minor} incompatible (needs {pkg.min_python} - {pkg.max_python})"

    try:
        if pkg.requires_isolated_env:
            return _install_isolated(pkg)
        return _install_direct(pkg)
    except Exception as e:
        return False, str(e)


def _install_direct(pkg: PackageSpec) -> tuple[bool, str]:
    """Install directly into current environment."""
    uv = shutil.which("uv") or shutil.which("pip")
    if not uv:
        return False, "uv/pip not found"
    result = subprocess.run(
        [uv, "pip", "install", pkg.pip_name, "--break-system-packages", "-q"],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode == 0:
        return True, f"✓ {pkg.name} installed"
    return False, result.stderr[:200]


def _install_isolated(pkg: PackageSpec) -> tuple[bool, str]:
    """Install in isolated Python 3.12 environment via uv."""
    uv = shutil.which("uv")
    if not uv:
        return False, "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"

    env_dir = os.path.expanduser(f"~/.c4reqber/envs/{pkg.id}")
    env_python = f"{env_dir}/bin/python"

    if not os.path.exists(env_python):
        result = subprocess.run(
            [uv, "venv", "--python", "3.12", env_dir],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return False, f"Failed to create venv: {result.stderr[:200]}"

    result = subprocess.run(
        [uv, "pip", "install", pkg.pip_name, "--python", env_python, "-q"],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode == 0:
        return True, f"✓ {pkg.name} installed (isolated env: {env_dir})"
    return False, result.stderr[:200]


def uninstall_package(package_id: str) -> tuple[bool, str]:
    """Uninstall a package."""
    pkg = next((p for p in PACKAGES if p.id == package_id), None)
    if not pkg:
        return False, f"Package '{package_id}' not found"
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", pkg.pip_name, "-y", "-q"],
            capture_output=True, timeout=60,
        )
        return True, f"✓ {pkg.name} removed"
    except Exception as e:
        return False, str(e)
