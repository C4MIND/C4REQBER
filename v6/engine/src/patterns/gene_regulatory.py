"""
Gene Regulatory Pattern
Boolean/ODE hybrid modeling of gene regulatory networks

Based on:
- Thomas' logical analysis (1973)
- Glass-Kauffman switching networks
- Sanchez et al. piecewise-linear differential equations
- Boolean threshold networks
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Tuple, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from scipy.integrate import solve_ivp

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


class GRNModel(Enum):
    BOOLEAN = "boolean"
    ODE = "ode"
    HYBRID = "hybrid"
    THRESHOLD = "threshold"


@dataclass
class GeneRegulatoryConfig:
    """Gene regulatory network configuration"""
    # Model selection
    model: GRNModel = GRNModel.HYBRID
    
    # Network topology
    num_genes: int = 5
    connectivity: float = 0.3  # Fraction of possible edges
    
    # Dynamics
    t_max: float = 100.0  # Arbitrary time units
    dt: float = 0.01
    
    # ODE parameters
    gamma: float = 1.0  # Degradation rate
    alpha: float = 10.0  # Production rate
    theta: float = 0.5  # Activation threshold
    hill_n: float = 2.0  # Hill coefficient for ODE
    
    # Boolean parameters
    update_mode: str = "synchronous"  # synchronous, asynchronous
    num_steps: int = 100
    
    # Initial state
    initial_state: Optional[List[float]] = None
    
    # Analysis
    find_attractors: bool = True
    perturbation_genes: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model.value,
            "num_genes": self.num_genes,
            "connectivity": self.connectivity,
            "t_max": self.t_max,
            "dt": self.dt,
            "gamma": self.gamma,
            "alpha": self.alpha,
            "theta": self.theta,
            "hill_n": self.hill_n,
            "update_mode": self.update_mode,
            "num_steps": self.num_steps,
            "initial_state": self.initial_state,
            "find_attractors": self.find_attractors,
            "perturbation_genes": self.perturbation_genes,
        }


@simulation_pattern(
    id="gene_regulatory",
    name="Gene Regulatory Network",
    category="biology",
    description="Boolean/ODE hybrid modeling of gene regulatory dynamics",
)
class GeneRegulatoryPattern(SimulationPattern):
    """
    Gene regulatory network (GRN) simulation
    
    Models how genes regulate each other through transcription factors.
    Supports multiple modeling formalisms:
    
    1. Boolean: Discrete ON/OFF dynamics
    2. ODE: Continuous Hill-function based
    3. Hybrid: Switching between Boolean states
    4. Threshold: Piecewise-linear differential equations
    
    Applications:
    - Cell fate decision
    - Developmental patterning
    - Cancer progression
    - Synthetic gene circuits
    """
    
    parameters = [
        SimulationParameter(
            name="model",
            type="select",
            default="hybrid",
            options=["boolean", "ode", "hybrid", "threshold"],
            description="GRN modeling formalism",
        ),
        SimulationParameter(
            name="num_genes",
            type="int",
            default=5,
            min=2,
            max=100,
            description="Number of genes in network",
        ),
        SimulationParameter(
            name="connectivity",
            type="float",
            default=0.3,
            min=0.0,
            max=1.0,
            description="Network connectivity",
        ),
        SimulationParameter(
            name="gamma",
            type="float",
            default=1.0,
            min=0.01,
            max=10.0,
            description="Degradation rate",
        ),
        SimulationParameter(
            name="alpha",
            type="float",
            default=10.0,
            min=0.1,
            max=100.0,
            description="Production rate",
        ),
        SimulationParameter(
            name="hill_n",
            type="float",
            default=2.0,
            min=0.1,
            max=20.0,
            description="Hill coefficient",
        ),
        SimulationParameter(
            name="t_max",
            type="float",
            default=100.0,
            min=10.0,
            max=1000.0,
            description="Simulation duration",
        ),
        SimulationParameter(
            name="update_mode",
            type="select",
            default="synchronous",
            options=["synchronous", "asynchronous"],
            description="Boolean update mode",
        ),
    ]
    
    def __init__(self):
        super().__init__()
        self.config: GeneRegulatoryConfig = GeneRegulatoryConfig()
        self.rng = np.random.default_rng(seed=42)
        self.adjacency: Optional[np.ndarray] = None
        self.regulation_types: Optional[np.ndarray] = None
        
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if GRN can simulate this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        
        keywords = [
            "gene", "regulatory", "network", "grn", "transcription",
            "expression", "boolean", "attractor", "cell fate", "differentiation",
            "development", "morphogen", "pattern formation", "toggle",
            "switch", "bistable", "multistable", "epigenetic",
        ]
        
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute GRN simulation"""
        start_time = datetime.now()
        simulation_id = f"grn_{start_time.timestamp()}"
        
        logger.info(f"Starting GRN simulation {simulation_id}")
        
        try:
            # Parse configuration
            self.config = self._parse_config(config)
            
            # Generate network topology
            self._generate_network()
            
            # Run simulation based on model type
            if self.config.model == GRNModel.BOOLEAN:
                results = await self._boolean_simulation()
            elif self.config.model == GRNModel.ODE:
                results = await self._ode_simulation()
            elif self.config.model == GRNModel.HYBRID:
                results = await self._hybrid_simulation()
            else:
                results = await self._threshold_simulation()
            
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
            logger.exception("GRN simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    def _parse_config(self, config: Dict[str, Any]) -> GeneRegulatoryConfig:
        """Parse configuration dictionary"""
        cfg = GeneRegulatoryConfig()
        
        if "model" in config:
            cfg.model = GRNModel(config["model"])
        if "num_genes" in config:
            cfg.num_genes = int(config["num_genes"])
        if "connectivity" in config:
            cfg.connectivity = float(config["connectivity"])
        if "t_max" in config:
            cfg.t_max = float(config["t_max"])
        if "dt" in config:
            cfg.dt = float(config["dt"])
        if "gamma" in config:
            cfg.gamma = float(config["gamma"])
        if "alpha" in config:
            cfg.alpha = float(config["alpha"])
        if "theta" in config:
            cfg.theta = float(config["theta"])
        if "hill_n" in config:
            cfg.hill_n = float(config["hill_n"])
        if "update_mode" in config:
            cfg.update_mode = config["update_mode"]
        if "num_steps" in config:
            cfg.num_steps = int(config["num_steps"])
        if "initial_state" in config:
            cfg.initial_state = config["initial_state"]
        if "find_attractors" in config:
            cfg.find_attractors = bool(config["find_attractors"])
            
        return cfg
    
    def _generate_network(self):
        """Generate random gene regulatory network topology"""
        cfg = self.config
        n = cfg.num_genes
        
        # Adjacency matrix: 1 = connection exists
        self.adjacency = (self.rng.random((n, n)) < cfg.connectivity).astype(int)
        # No self-loops
        np.fill_diagonal(self.adjacency, 0)
        
        # Regulation type: 1 = activation, -1 = repression
        self.regulation_types = np.where(
            self.rng.random((n, n)) < 0.5, 1, -1
        ) * self.adjacency
    
    async def _boolean_simulation(self) -> Dict[str, Any]:
        """Boolean network simulation"""
        
        cfg = self.config
        n = cfg.num_genes
        
        # Initialize state
        if cfg.initial_state:
            state = np.array(cfg.initial_state[:n])
        else:
            state = self.rng.integers(0, 2, n)
        
        # Store trajectory
        trajectory = [state.copy()]
        
        # Boolean update rules (threshold functions)
        def update_rule(s: np.ndarray) -> np.ndarray:
            # For each gene, sum inputs and apply threshold
            new_state = np.zeros(n, dtype=int)
            for i in range(n):
                # Weighted sum of inputs
                total = np.sum(self.regulation_types[:, i] * s)
                # Threshold at 0
                new_state[i] = 1 if total > 0 else 0
            return new_state
        
        # Simulate
        for step in range(cfg.num_steps):
            if cfg.update_mode == "synchronous":
                new_state = update_rule(state)
            else:  # asynchronous - update one random gene
                new_state = state.copy()
                i = self.rng.integers(0, n)
                total = np.sum(self.regulation_types[:, i] * state)
                new_state[i] = 1 if total > 0 else 0
            
            state = new_state
            trajectory.append(state.copy())
            
            # Check for fixed point
            if len(trajectory) > 1:
                if np.array_equal(trajectory[-1], trajectory[-2]):
                    break
            
            if step % 100 == 0:
                await asyncio.sleep(0)
        
        trajectory = np.array(trajectory)
        
        # Find attractor
        attractor_state = trajectory[-1].tolist()
        is_fixed_point = len(trajectory) < cfg.num_steps + 1
        
        # Calculate metrics
        metrics = {
            "num_genes": n,
            "num_edges": int(np.sum(self.adjacency)),
            "attractor_state": attractor_state,
            "attractor_type": "fixed_point" if is_fixed_point else "cycle_or_long",
            "trajectory_length": len(trajectory),
            "hamming_distance_initial_final": int(np.sum(trajectory[0] != trajectory[-1])),
            "model": "boolean",
        }
        
        # Attractor search if requested
        if cfg.find_attractors and n <= 10:  # Only for small networks
            attractors = self._find_all_attractors()
            metrics["num_attractors"] = len(attractors)
        
        logs = [
            f"Boolean network simulation completed",
            f"Genes: {n}, Edges: {metrics['num_edges']}",
            f"Attractor type: {metrics['attractor_type']}",
            f"Final state: {attractor_state}",
        ]
        
        if "num_attractors" in metrics:
            logs.append(f"Total attractors found: {metrics['num_attractors']}")
        
        return {
            "metrics": metrics,
            "logs": logs,
            "trajectory": trajectory.tolist(),
            "attractor": attractor_state,
        }
    
    def _find_all_attractors(self) -> List[Tuple]:
        """Find all attractors by exhaustive search (for small networks)"""
        n = self.config.num_genes
        attractors = []
        visited = set()
        
        def state_to_tuple(s):
            return tuple(s)
        
        def update(s):
            new = np.zeros(n, dtype=int)
            for i in range(n):
                total = np.sum(self.regulation_types[:, i] * s)
                new[i] = 1 if total > 0 else 0
            return new
        
        for initial in range(2**n):
            state = np.array([(initial >> i) & 1 for i in range(n)])
            path = []
            
            while state_to_tuple(state) not in visited:
                visited.add(state_to_tuple(state))
                path.append(state.copy())
                state = update(state)
                
                # Check for cycle
                if state_to_tuple(state) in [state_to_tuple(p) for p in path]:
                    # Found attractor
                    attractor_start = next(
                        i for i, p in enumerate(path) 
                        if state_to_tuple(p) == state_to_tuple(state)
                    )
                    attractor = tuple(state_to_tuple(p) for p in path[attractor_start:])
                    if attractor not in attractors:
                        attractors.append(attractor)
                    break
        
        return attractors
    
    async def _ode_simulation(self) -> Dict[str, Any]:
        """ODE-based continuous simulation"""
        
        cfg = self.config
        n = cfg.num_genes
        
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        # Initial conditions
        if cfg.initial_state:
            y0 = np.array(cfg.initial_state[:n])
        else:
            y0 = self.rng.uniform(0, 1, n)
        
        def grn_odes(t, y):
            dydt = np.zeros(n)
            for i in range(n):
                # Sum regulatory inputs
                regulation = 0
                for j in range(n):
                    if self.adjacency[j, i]:
                        reg = self.regulation_types[j, i]
                        if reg > 0:  # Activation
                            regulation += self._hill_activation(y[j])
                        else:  # Repression
                            regulation += self._hill_repression(y[j])
                
                # Production minus degradation
                production = cfg.alpha * regulation / max(1, np.sum(self.adjacency[:, i]))
                degradation = cfg.gamma * y[i]
                
                dydt[i] = production - degradation
            
            return dydt
        
        solution = solve_ivp(grn_odes, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        y = solution.y
        
        # Calculate steady-state
        final_state = y[:, -1]
        
        metrics = {
            "num_genes": n,
            "num_edges": int(np.sum(self.adjacency)),
            "final_expression": final_state.tolist(),
            "mean_expression": float(np.mean(final_state)),
            "expression_variance": float(np.var(final_state)),
            "num_active_genes": int(np.sum(final_state > cfg.theta)),
            "model": "ode",
        }
        
        logs = [
            f"ODE gene regulatory simulation completed",
            f"Final active genes: {metrics['num_active_genes']}/{n}",
            f"Mean expression: {metrics['mean_expression']:.4f}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "expression": y.T.tolist(),
        }
    
    def _hill_activation(self, x: float) -> float:
        """Hill function for activation"""
        return x**self.config.hill_n / (self.config.theta**self.config.hill_n + x**self.config.hill_n)
    
    def _hill_repression(self, x: float) -> float:
        """Hill function for repression"""
        return self.config.theta**self.config.hill_n / (self.config.theta**self.config.hill_n + x**self.config.hill_n)
    
    async def _hybrid_simulation(self) -> Dict[str, Any]:
        """Hybrid Boolean-ODE simulation"""
        
        cfg = self.config
        n = cfg.num_genes
        
        # Use Boolean logic but with continuous transitions
        # Each gene has continuous level that switches when threshold crossed
        
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        # State: continuous levels
        y0 = self.rng.uniform(0, 1, n)
        
        def hybrid_odes(t, y):
            dydt = np.zeros(n)
            # Boolean state based on threshold
            bool_state = (y > cfg.theta).astype(int)
            
            for i in range(n):
                # Boolean update rule
                total = np.sum(self.regulation_types[:, i] * bool_state)
                target = 1.0 if total > 0 else 0.0
                
                # Smooth switching towards target
                dydt[i] = cfg.gamma * (target - y[i])
            
            return dydt
        
        solution = solve_ivp(hybrid_odes, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        y = solution.y
        
        # Count switches
        bool_traj = (y > cfg.theta).astype(int)
        switches = np.sum(np.abs(np.diff(bool_traj, axis=1)))
        
        metrics = {
            "num_genes": n,
            "total_switches": int(switches),
            "final_boolean_state": bool_traj[:, -1].tolist(),
            "mean_switches_per_gene": float(switches / n),
            "model": "hybrid",
        }
        
        logs = [
            f"Hybrid GRN simulation completed",
            f"Total state switches: {switches}",
            f"Final Boolean state: {metrics['final_boolean_state']}",
        ]
        
        return {
            "metrics": metrics,
            "logs": logs,
            "time": t.tolist(),
            "levels": y.T.tolist(),
            "boolean": bool_traj.T.tolist(),
        }
    
    async def _threshold_simulation(self) -> Dict[str, Any]:
        """Piecewise-linear (Glass-Kauffman) simulation"""
        
        cfg = self.config
        n = cfg.num_genes
        
        # Similar to hybrid but with explicit thresholds
        t_span = (0, cfg.t_max)
        t_eval = np.arange(0, cfg.t_max, cfg.dt)
        
        y0 = self.rng.uniform(0, 1, n)
        
        def threshold_odes(t, y):
            dydt = np.zeros(n)
            bool_state = (y > cfg.theta).astype(int)
            
            for i in range(n):
                # Production depends on Boolean state
                total = np.sum(self.regulation_types[:, i] * bool_state)
                if total > 0:
                    production = cfg.alpha
                else:
                    production = 0.1  # Leaky transcription
                
                dydt[i] = production - cfg.gamma * y[i]
            
            return dydt
        
        solution = solve_ivp(threshold_odes, t_span, y0, t_eval=t_eval, method='RK45')
        
        t = solution.t
        y = solution.y
        
        metrics = {
            "num_genes": n,
            "final_expression": y[:, -1].tolist(),
            "mean_expression": float(np.mean(y[:, -1])),
            "model": "threshold",
        }
        
        return {
            "metrics": metrics,
            "logs": ["Threshold model simulation completed"],
            "time": t.tolist(),
            "expression": y.T.tolist(),
        }
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []
        
        # Network has reasonable structure
        if metrics.get("num_edges", 0) > 0:
            factors.append(0.3)
        
        # Attractor found or steady state reached
        if "attractor_type" in metrics:
            factors.append(0.3)
        elif "final_expression" in metrics:
            factors.append(0.3)
        
        # Expression in reasonable range
        mean_expr = metrics.get("mean_expression", 0.5)
        if 0 < mean_expr < 10:
            factors.append(0.2)
        
        # Model-specific checks
        if self.config.model == GRNModel.BOOLEAN:
            if metrics.get("attractor_type") == "fixed_point":
                factors.append(0.2)
        
        return min(0.95, sum(factors))
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        n = params.get("num_genes", 5)
        
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + n * n * 1e-5,
            "gpu_required": False,
            "estimated_time_seconds": 1 + n / 10,
        }
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get pattern metadata"""
        return {
            "id": cls.id,
            "name": cls.name,
            "category": cls.category,
            "description": cls.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "default": p.default,
                    "min": p.min,
                    "max": p.max,
                    "options": p.options,
                    "description": p.description,
                }
                for p in cls.parameters
            ],
            "references": [
                "Thomas, R. (1973). Boolean formalization of genetic control circuits",
                "Glass, L. & Kauffman, S.A. (1973). The logical analysis of continuous",
                "Sanchez, L. et al. (2001). Modeling the segmentation clock",
            ],
        }
