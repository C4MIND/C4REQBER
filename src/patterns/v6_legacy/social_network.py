"""
Social Network Pattern
Diffusion and influence propagation in social networks

Based on:
- Network effects
- Diffusion models (SIR-like for ideas)
- Centrality measures
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..core import (
    SimulationPattern, SimulationResult, SimulationStatus,
    Hypothesis, SimulationParameter, ValidationLevel, simulation_pattern
)

logger = logging.getLogger(__name__)


@simulation_pattern(
    id="social_network",
    name="Social Network Diffusion",
    category="social",
    description="Information and influence diffusion in social networks",
)
class SocialNetworkPattern(SimulationPattern):
    """
    Social network simulation for diffusion analysis
    
    Implements:
    - Network generation (small-world, scale-free)
    - Diffusion models
    - Centrality measures
    - Cascade effects
    """
    
    parameters = [
        SimulationParameter(
            name="num_nodes",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Number of network nodes",
        ),
        SimulationParameter(
            name="network_type",
            type="select",
            default="small_world",
            options=["small_world", "scale_free", "random"],
            description="Network topology",
        ),
        SimulationParameter(
            name="diffusion_model",
            type="select",
            default="independent_cascade",
            options=["independent_cascade", "linear_threshold"],
            description="Diffusion model",
        ),
        SimulationParameter(
            name="adoption_rate",
            type="float",
            default=0.1,
            min=0.01,
            max=1.0,
            description="Probability of adoption",
        ),
    ]
    
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "social network", "diffusion", "viral", "cascade",
            "influence", "adoption", "information spread",
            "network effect", "centrality",
        ]
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> SimulationResult:
        start_time = datetime.now()
        simulation_id = f"sn_{start_time.timestamp()}"
        
        try:
            results = await self._simulate_network(hypothesis, config)
            
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=datetime.now(),
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )
        except Exception as e:
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    async def _simulate_network(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        N = config.get("num_nodes", 100)
        network_type = config.get("network_type", "small_world")
        diffusion_model = config.get("diffusion_model", "independent_cascade")
        p_adopt = config.get("adoption_rate", 0.1)
        
        # Create network
        if network_type == "small_world":
            adjacency = self._create_small_world(N, k=4, p=0.3)
        elif network_type == "scale_free":
            adjacency = self._create_scale_free(N, m=2)
        else:
            adjacency = self._create_random(N, p=0.1)
        
        # Calculate centrality (degree)
        degrees = np.sum(adjacency, axis=1)
        avg_degree = float(np.mean(degrees))
        max_degree = int(np.max(degrees))
        
        # Simulate diffusion
        # Independent cascade model
        initial_adopters = set(np.random.choice(N, size=max(1, N//20), replace=False))
        adopters = initial_adopters.copy()
        
        changed = True
        iterations = 0
        
        while changed and iterations < 100:
            changed = False
            new_adopters = set()
            
            for node in range(N):
                if node in adopters:
                    continue
                
                # Check neighbors
                neighbors = np.where(adjacency[node])[0]
                adopting_neighbors = sum(1 for n in neighbors if n in adopters)
                
                if diffusion_model == "independent_cascade":
                    # Each adopting neighbor has p_adopt chance to influence
                    for n in neighbors:
                        if n in adopters and np.random.random() < p_adopt:
                            new_adopters.add(node)
                            break
                else:  # Linear threshold
                    threshold = degrees[node] * 0.5
                    if adopting_neighbors >= threshold:
                        new_adopters.add(node)
            
            if new_adopters:
                adopters.update(new_adopters)
                changed = True
            
            iterations += 1
            
            if iterations % 10 == 0:
                await asyncio.sleep(0)
        
        adoption_rate = len(adopters) / N
        
        metrics = {
            "num_nodes": N,
            "num_edges": int(np.sum(adjacency) / 2),
            "avg_degree": avg_degree,
            "max_degree": max_degree,
            "clustering_coefficient": self._calculate_clustering(adjacency),
            "final_adoption_rate": float(adoption_rate),
            "adopters": len(adopters),
            "diffusion_iterations": iterations,
        }
        
        logs = [
            f"Social network: {N} nodes, {metrics['num_edges']} edges",
            f"Network type: {network_type}",
            f"Average degree: {avg_degree:.2f}",
            f"Final adoption rate: {adoption_rate:.1%}",
            f"Diffusion iterations: {iterations}",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    def _create_small_world(self, N: int, k: int, p: float) -> np.ndarray:
        """Watts-Strogatz small-world network"""
        adj = np.zeros((N, N))
        
        # Ring lattice
        for i in range(N):
            for j in range(1, k//2 + 1):
                adj[i, (i+j) % N] = 1
                adj[i, (i-j) % N] = 1
        
        # Rewire
        for i in range(N):
            for j in range(i+1, N):
                if adj[i, j] and np.random.random() < p:
                    # Rewire
                    adj[i, j] = 0
                    adj[j, i] = 0
                    new_target = np.random.randint(0, N)
                    if new_target != i:
                        adj[i, new_target] = 1
                        adj[new_target, i] = 1
        
        return adj
    
    def _create_scale_free(self, N: int, m: int) -> np.ndarray:
        """Barabasi-Albert scale-free network"""
        adj = np.zeros((N, N))
        
        # Start with m nodes
        for i in range(m):
            for j in range(i+1, m):
                adj[i, j] = 1
                adj[j, i] = 1
        
        # Preferential attachment
        for i in range(m, N):
            degrees = np.sum(adj, axis=1)
            probs = degrees / np.sum(degrees)
            
            targets = np.random.choice(i, size=min(m, i), replace=False, p=probs[:i])
            for t in targets:
                adj[i, t] = 1
                adj[t, i] = 1
        
        return adj
    
    def _create_random(self, N: int, p: float) -> np.ndarray:
        """Erdos-Renyi random network"""
        adj = np.random.random((N, N)) < p
        adj = np.triu(adj, 1)  # Upper triangle
        adj = adj + adj.T  # Symmetric
        return adj.astype(int)
    
    def _calculate_clustering(self, adj: np.ndarray) -> float:
        """Calculate average clustering coefficient"""
        N = len(adj)
        coeffs = []
        
        for i in range(N):
            neighbors = np.where(adj[i])[0]
            if len(neighbors) < 2:
                continue
            
            # Count triangles
            triangles = 0
            for j in neighbors:
                for k in neighbors:
                    if j < k and adj[j, k]:
                        triangles += 1
            
            possible = len(neighbors) * (len(neighbors) - 1) / 2
            if possible > 0:
                coeffs.append(triangles / possible)
        
        return float(np.mean(coeffs)) if coeffs else 0.0
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        metrics = results["metrics"]
        factors = []
        
        if 0 < metrics.get("avg_degree", 0) < 20:
            factors.append(0.3)
        
        if 0 < metrics.get("final_adoption_rate", 0) <= 1:
            factors.append(0.3)
        
        return min(0.9, sum(factors) + 0.3)
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        N = hypothesis.parameters.get("num_nodes", 100)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + N**2 * 1e-6,
            "gpu_required": False,
            "estimated_time_seconds": N / 100,
        }
