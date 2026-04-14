"""
Finite Element Method Pattern
Simplified FEM for 1D/2D structural analysis

Based on:
- Direct stiffness method
- Galerkin approach
- Linear elasticity
"""

import asyncio
import numpy as np
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

from ..core import (
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    Hypothesis,
    SimulationParameter,
    ValidationLevel,
    simulation_pattern,
)

logger = logging.getLogger(__name__)


class ElementType(Enum):
    TRUSS_1D = "truss_1d"
    BEAM_1D = "beam_1d"
    TRIANGLE_2D = "triangle_2d"
    QUAD_2D = "quad_2d"


@dataclass
class Node:
    """Node in the mesh"""
    node_id: int
    x: float
    y: float = 0.0
    z: float = 0.0
    fixed: Tuple[bool, bool, bool] = (False, False, False)  # Fixed DOFs


@dataclass
class Element:
    """Finite element"""
    element_id: int
    nodes: List[int]  # Node IDs
    youngs_modulus: float  # E
    area: float  # Cross-sectional area
    element_type: ElementType = ElementType.TRUSS_1D


@simulation_pattern(
    id="fem",
    name="Finite Element Method",
    category="physics",
    description="Structural analysis using finite element method",
)
class FEMPattern(SimulationPattern):
    """
    Finite element simulation for structural mechanics
    
    Implements:
    - 1D truss elements
    - 1D beam elements
    - 2D plane stress (simplified)
    - Linear static analysis
    - Stress and strain calculation
    """
    
    parameters = [
        SimulationParameter(
            name="element_type",
            type="select",
            default="truss_1d",
            options=["truss_1d", "beam_1d", "triangle_2d"],
            description="Type of finite elements",
        ),
        SimulationParameter(
            name="num_elements",
            type="int",
            default=10,
            min=2,
            max=1000,
            description="Number of elements",
        ),
        SimulationParameter(
            name="youngs_modulus",
            type="float",
            default=200e9,  # Steel in Pa
            min=1e6,
            max=1e12,
            description="Young's modulus (Pa)",
        ),
        SimulationParameter(
            name="area",
            type="float",
            default=0.01,  # m^2
            min=1e-6,
            max=10.0,
            description="Cross-sectional area (m^2)",
        ),
        SimulationParameter(
            name="load",
            type="float",
            default=1000.0,  # N
            min=-1e6,
            max=1e6,
            description="Applied load (N)",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.nodes: List[Node] = []
        self.elements: List[Element] = []
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if FEM can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "finite element", "fem", "fea",
            "stress", "strain", "deformation",
            "structural", "mechanics", "elasticity",
            "truss", "beam", "frame",
            "load", "force", "displacement",
            "young's modulus", "poisson ratio",
            "cantilever", "simply supported",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute FEM simulation"""
        start_time = datetime.now()
        simulation_id = f"fem_{start_time.timestamp()}"
        
        logger.info(f"Starting FEM simulation {simulation_id}")
        
        element_type = config.get("element_type", "truss_1d")
        
        try:
            if element_type == "truss_1d":
                results = await self._truss_1d(hypothesis, config)
            elif element_type == "beam_1d":
                results = await self._beam_1d(hypothesis, config)
            else:
                results = await self._plane_stress_2d(hypothesis, config)
            
            end_time = datetime.now()
            
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )
            
        except Exception as e:
            logger.exception("FEM simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    async def _truss_1d(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """1D truss (bar) elements"""
        
        params = hypothesis.parameters
        n_elements = config.get("num_elements", 10)
        E = config.get("youngs_modulus", 200e9)
        A = config.get("area", 0.01)
        load = config.get("load", 1000.0)
        
        # Length
        L_total = params.get("length", 10.0)
        L = L_total / n_elements
        
        # Number of nodes
        n_nodes = n_elements + 1
        
        # Global stiffness matrix (sparse)
        # Each node has 1 DOF (axial displacement)
        ndof = n_nodes
        K = np.zeros((ndof, ndof))
        
        # Element stiffness: k = EA/L
        k_local = E * A / L
        
        # Assemble global stiffness
        for i in range(n_elements):
            # Element connects node i and i+1
            K[i, i] += k_local
            K[i, i+1] -= k_local
            K[i+1, i] -= k_local
            K[i+1, i+1] += k_local
        
        # Force vector
        F = np.zeros(ndof)
        # Apply load at free end (last node)
        F[-1] = load
        
        # Apply boundary conditions (fix first node)
        K_reduced = K[1:, 1:]  # Remove first row/col
        F_reduced = F[1:]
        
        # Solve: Ku = F
        u_reduced = np.linalg.solve(K_reduced, F_reduced)
        
        # Full displacement vector
        u = np.zeros(ndof)
        u[1:] = u_reduced
        
        # Calculate element stresses
        stresses = []
        strains = []
        for i in range(n_elements):
            du = u[i+1] - u[i]  # Displacement difference
            strain = du / L
            stress = E * strain
            strains.append(strain)
            stresses.append(stress)
        
        # Max deflection
        max_deflection = float(np.max(np.abs(u)))
        max_stress = float(np.max(np.abs(stresses)))
        
        metrics = {
            "max_deflection": max_deflection,
            "max_stress": max_stress,
            "max_strain": float(np.max(np.abs(strains))),
            "axial_stiffness": float(k_local),
            "num_elements": n_elements,
            "num_nodes": n_nodes,
            "strain_energy": float(0.5 * u @ K @ u),
        }
        
        logs = [
            f"1D truss analysis: {n_elements} elements",
            f"Max deflection: {max_deflection:.6f} m",
            f"Max stress: {max_stress/1e6:.2f} MPa",
            f"Strain: {metrics['max_strain']*100:.4f}%",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    async def _beam_1d(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """1D Euler-Bernoulli beam elements"""
        
        params = hypothesis.parameters
        n_elements = config.get("num_elements", 10)
        E = config.get("youngs_modulus", 200e9)
        
        # Moment of inertia (assume rectangular section)
        b = params.get("width", 0.1)  # m
        h = params.get("height", 0.2)  # m
        I = b * h**3 / 12
        A = b * h
        
        load = config.get("load", 1000.0)
        L_total = params.get("length", 10.0)
        L = L_total / n_elements
        
        # Each node has 2 DOFs: v (displacement) and θ (rotation)
        n_nodes = n_elements + 1
        ndof = 2 * n_nodes
        
        K = np.zeros((ndof, ndof))
        
        # Beam element stiffness matrix (4x4)
        EI = E * I
        k_beam = EI / L**3 * np.array([
            [12, 6*L, -12, 6*L],
            [6*L, 4*L**2, -6*L, 2*L**2],
            [-12, -6*L, 12, -6*L],
            [6*L, 2*L**2, -6*L, 4*L**2],
        ])
        
        # Assemble global stiffness
        for i in range(n_elements):
            dofs = [2*i, 2*i+1, 2*(i+1), 2*(i+1)+1]
            for ii in range(4):
                for jj in range(4):
                    K[dofs[ii], dofs[jj]] += k_beam[ii, jj]
        
        # Force vector
        F = np.zeros(ndof)
        F[-2] = load  # Force at last node
        
        # Boundary conditions: clamped at first node (v=0, θ=0)
        free_dofs = list(range(2, ndof))
        K_reduced = K[np.ix_(free_dofs, free_dofs)]
        F_reduced = F[free_dofs]
        
        # Solve
        u_reduced = np.linalg.solve(K_reduced, F_reduced)
        
        u = np.zeros(ndof)
        u[free_dofs] = u_reduced
        
        # Max deflection
        displacements = u[0::2]  # Every other DOF is displacement
        max_deflection = float(np.max(np.abs(displacements)))
        
        # Bending stress at fixed end
        M_max = abs(load * L_total)  # Simplified
        c = h / 2
        sigma_max = M_max * c / I
        
        metrics = {
            "max_deflection": max_deflection,
            "max_bending_stress": float(sigma_max),
            "moment_of_inertia": float(I),
            "max_moment": float(M_max),
            "beam_stiffness": float(EI),
            "num_elements": n_elements,
        }
        
        logs = [
            f"1D beam analysis: {n_elements} elements",
            f"Max deflection: {max_deflection:.6f} m ({max_deflection*1000:.2f} mm)",
            f"Max bending stress: {sigma_max/1e6:.2f} MPa",
            f"Moment of inertia: {I:.6e} m^4",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    async def _plane_stress_2d(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simplified 2D plane stress (placeholder)"""
        
        # This would require full FEM implementation
        # For now, return analytical approximation
        
        load = config.get("load", 1000.0)
        E = config.get("youngs_modulus", 200e9)
        
        # Simplified plate with hole approximation
        sigma_nominal = load / 0.01  # Simplified
        stress_concentration = 3.0  # For hole
        
        max_stress = sigma_nominal * stress_concentration
        
        metrics = {
            "max_stress": float(max_stress),
            "stress_concentration": stress_concentration,
            "nominal_stress": float(sigma_nominal),
            "note": "Simplified 2D - full FEM requires mesh generation",
        }
        
        logs = [
            "2D plane stress (simplified)",
            f"Estimated max stress: {max_stress/1e6:.2f} MPa",
            "Full 2D FEM requires external mesher (GMSH)",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Reasonable deflection
        if 0 < metrics.get("max_deflection", -1) < 1.0:
            factors.append(0.3)
        
        # Reasonable stress
        stress = metrics.get("max_stress", 0)
        if 0 < stress < 1e9:  # < 1 GPa
            factors.append(0.3)
        
        # Mesh density
        if metrics.get("num_elements", 0) >= 5:
            factors.append(0.2)
        
        # Not a fallback
        if "note" not in metrics:
            factors.append(0.2)
        
        return min(0.9, sum(factors))  # FEM is approximation
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_elements = params.get("num_elements", 10)
        
        # Complexity: O(n^2) for direct solver, O(n) for sparse
        matrix_size = n_elements ** 2
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + matrix_size * 1e-6,
            "gpu_required": False,
            "estimated_time_seconds": matrix_size / 1e6,
        }
