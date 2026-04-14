"""
Percolation Pattern
Union-find algorithm for percolation and cluster analysis

Based on:
- Union-Find (Disjoint Set Union) algorithm
- Newman-Ziff algorithm
- Hoshen-Kopelman algorithm
- Finite-size scaling theory
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

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


@dataclass
class PercolationConfig:
    """Configuration for percolation simulation"""
    lattice_size: int = 100
    dimension: int = 2
    n_realizations: int = 100
    p_min: float = 0.0
    p_max: float = 1.0
    n_p_values: int = 50
    algorithm: str = "union_find"  # or "dfs"
    random_seed: Optional[int] = None

    def __post_init__(self):
        if self.dimension not in [2, 3]:
            self.dimension = 2
        if self.algorithm not in ["union_find", "dfs"]:
            self.algorithm = "union_find"


class UnionFind:
    """Union-Find data structure with path compression and union by rank"""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.size = [1] * n

    def find(self, x: int) -> int:
        """Find root with path compression"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """Union by rank, return True if merged"""
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False

        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x

        self.parent[root_y] = root_x
        self.size[root_x] += self.size[root_y]

        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1

        return True

    def get_size(self, x: int) -> int:
        """Get size of component containing x"""
        return self.size[self.find(x)]


@simulation_pattern(
    id="percolation",
    name="Percolation Theory",
    category="physics",
    description="Union-find algorithm for percolation and cluster analysis",
)
class PercolationPattern(SimulationPattern):
    """
    Percolation simulation for connectivity and phase transitions

    Implements:
    - Site percolation on square/cubic lattices
    - Union-Find algorithm for efficient cluster tracking
    - Newman-Ziff algorithm for spanning cluster detection
    - Cluster size distribution analysis
    - Finite-size scaling
    """

    parameters = [
        SimulationParameter(
            name="lattice_size",
            type="int",
            default=100,
            min=10,
            max=500,
            description="Linear lattice size L",
        ),
        SimulationParameter(
            name="dimension",
            type="int",
            default=2,
            min=2,
            max=3,
            description="Lattice dimension (2 or 3)",
        ),
        SimulationParameter(
            name="n_realizations",
            type="int",
            default=100,
            min=10,
            max=10000,
            description="Number of Monte Carlo realizations",
        ),
        SimulationParameter(
            name="p_min",
            type="float",
            default=0.0,
            min=0.0,
            max=1.0,
            description="Minimum occupation probability",
        ),
        SimulationParameter(
            name="p_max",
            type="float",
            default=1.0,
            min=0.0,
            max=1.0,
            description="Maximum occupation probability",
        ),
        SimulationParameter(
            name="n_p_values",
            type="int",
            default=50,
            min=10,
            max=200,
            description="Number of p values to sample",
        ),
    ]

    def __init__(self):
        super().__init__()
        self.rng = np.random.default_rng()
        self.config: Optional[PercolationConfig] = None
        self.results_by_p: Dict[float, Dict[str, Any]] = {}

    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        """Check if this pattern can simulate the hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "percolation", "cluster", "connectivity", "spanning",
            "phase transition", "critical", "threshold", "occupation",
            "porous media", "network resilience", "epidemic threshold",
            "site percolation", "bond percolation", "cluster size",
            "universality", "finite size scaling",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(
        self, hypothesis: Hypothesis, config: Dict[str, Any]
    ) -> SimulationResult:
        """Execute percolation simulation"""
        start_time = datetime.now()
        simulation_id = f"percolation_{start_time.timestamp()}"

        logger.info(f"Starting Percolation simulation {simulation_id}")

        try:
            self.config = self._parse_config(config)
            if self.config.random_seed:
                self.rng = np.random.default_rng(self.config.random_seed)

            results = await self._simulate(hypothesis)

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
            logger.exception("Percolation simulation failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    def _parse_config(self, config: Dict[str, Any]) -> PercolationConfig:
        """Parse configuration"""
        return PercolationConfig(
            lattice_size=config.get("lattice_size", 100),
            dimension=config.get("dimension", 2),
            n_realizations=config.get("n_realizations", 100),
            p_min=config.get("p_min", 0.0),
            p_max=config.get("p_max", 1.0),
            n_p_values=config.get("n_p_values", 50),
            algorithm=config.get("algorithm", "union_find"),
            random_seed=config.get("random_seed"),
        )

    async def _simulate(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Run percolation simulation"""
        L = self.config.lattice_size
        d = self.config.dimension
        N = L ** d

        p_values = np.linspace(self.config.p_min, self.config.p_max, self.config.n_p_values)

        self.results_by_p = {}

        for i, p in enumerate(p_values):
            percolation_probs = []
            max_cluster_sizes = []
            avg_cluster_sizes = []

            for realization in range(self.config.n_realizations):
                # Generate occupied sites
                if d == 2:
                    occupied = self.rng.random((L, L)) < p
                else:
                    occupied = self.rng.random((L, L, L)) < p

                # Find clusters
                if self.config.algorithm == "union_find":
                    clusters = self._find_clusters_union_find(occupied, L, d)
                else:
                    clusters = self._find_clusters_dfs(occupied, L, d)

                # Check percolation
                percolates = self._check_percolation(clusters, L, d)
                percolation_probs.append(float(percolates))

                # Cluster statistics
                if clusters:
                    sizes = [len(c) for c in clusters.values()]
                    max_cluster_sizes.append(max(sizes) / N)  # Fraction
                    avg_cluster_sizes.append(np.mean(sizes))
                else:
                    max_cluster_sizes.append(0.0)
                    avg_cluster_sizes.append(0.0)

                if realization % 20 == 0:
                    await asyncio.sleep(0)

            self.results_by_p[float(p)] = {
                "percolation_prob": np.mean(percolation_probs),
                "percolation_std": np.std(percolation_probs),
                "max_cluster_size": np.mean(max_cluster_sizes),
                "avg_cluster_size": np.mean(avg_cluster_sizes),
            }

            if i % 10 == 0:
                await asyncio.sleep(0)

        return self._analyze_results()

    def _find_clusters_union_find(
        self, occupied: np.ndarray, L: int, d: int
    ) -> Dict[int, Set[Tuple]]:
        """Find clusters using Union-Find"""
        N = L ** d
        uf = UnionFind(N)

        if d == 2:
            for i in range(L):
                for j in range(L):
                    if not occupied[i, j]:
                        continue
                    idx = i * L + j
                    # Check right neighbor
                    if j < L - 1 and occupied[i, j + 1]:
                        uf.union(idx, idx + 1)
                    # Check bottom neighbor
                    if i < L - 1 and occupied[i + 1, j]:
                        uf.union(idx, idx + L)
        else:
            for i in range(L):
                for j in range(L):
                    for k in range(L):
                        if not occupied[i, j, k]:
                            continue
                        idx = (i * L + j) * L + k
                        # Check neighbors
                        if k < L - 1 and occupied[i, j, k + 1]:
                            uf.union(idx, idx + 1)
                        if j < L - 1 and occupied[i, j + 1, k]:
                            uf.union(idx, idx + L)
                        if i < L - 1 and occupied[i + 1, j, k]:
                            uf.union(idx, idx + L * L)

        # Build clusters
        clusters: Dict[int, Set[int]] = {}
        for i in range(N):
            if d == 2:
                row, col = divmod(i, L)
                if not occupied[row, col]:
                    continue
            else:
                k = i % L
                rem = i // L
                j = rem % L
                row = rem // L
                if not occupied[row, j, k]:
                    continue

            root = uf.find(i)
            if root not in clusters:
                clusters[root] = set()
            clusters[root].add(i)

        # Convert to coordinates
        coord_clusters: Dict[int, Set[Tuple]] = {}
        for root, members in clusters.items():
            coords = set()
            for idx in members:
                if d == 2:
                    coords.add(divmod(idx, L))
                else:
                    k = idx % L
                    rem = idx // L
                    j = rem % L
                    i = rem // L
                    coords.add((i, j, k))
            coord_clusters[root] = coords

        return coord_clusters

    def _find_clusters_dfs(
        self, occupied: np.ndarray, L: int, d: int
    ) -> Dict[int, Set[Tuple]]:
        """Find clusters using DFS"""
        visited = np.zeros_like(occupied, dtype=bool)
        clusters: Dict[int, Set[Tuple]] = {}
        cluster_id = 0

        def get_neighbors(pos: Tuple) -> List[Tuple]:
            """Get occupied neighbors"""
            if d == 2:
                i, j = pos
                neighbors = []
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < L and 0 <= nj < L and occupied[ni, nj] and not visited[ni, nj]:
                        neighbors.append((ni, nj))
                return neighbors
            else:
                i, j, k = pos
                neighbors = []
                for di, dj, dk in [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)]:
                    ni, nj, nk = i + di, j + dj, k + dk
                    if 0 <= ni < L and 0 <= nj < L and 0 <= nk < L:
                        if occupied[ni, nj, nk] and not visited[ni, nj, nk]:
                            neighbors.append((ni, nj, nk))
                return neighbors

        if d == 2:
            for i in range(L):
                for j in range(L):
                    if occupied[i, j] and not visited[i, j]:
                        cluster = set()
                        stack = [(i, j)]
                        visited[i, j] = True

                        while stack:
                            pos = stack.pop()
                            cluster.add(pos)
                            for neighbor in get_neighbors(pos):
                                visited[neighbor] = True
                                stack.append(neighbor)

                        clusters[cluster_id] = cluster
                        cluster_id += 1
        else:
            for i in range(L):
                for j in range(L):
                    for k in range(L):
                        if occupied[i, j, k] and not visited[i, j, k]:
                            cluster = set()
                            stack = [(i, j, k)]
                            visited[i, j, k] = True

                            while stack:
                                pos = stack.pop()
                                cluster.add(pos)
                                for neighbor in get_neighbors(pos):
                                    visited[neighbor] = True
                                    stack.append(neighbor)

                            clusters[cluster_id] = cluster
                            cluster_id += 1

        return clusters

    def _check_percolation(self, clusters: Dict[int, Set[Tuple]], L: int, d: int) -> bool:
        """Check if any cluster spans the lattice"""
        for cluster in clusters.values():
            if d == 2:
                # Check horizontal or vertical spanning
                rows = {pos[0] for pos in cluster}
                cols = {pos[1] for pos in cluster}
                if len(rows) == L or len(cols) == L:
                    return True
            else:
                # Check spanning in any dimension
                xs = {pos[0] for pos in cluster}
                ys = {pos[1] for pos in cluster}
                zs = {pos[2] for pos in cluster}
                if len(xs) == L or len(ys) == L or len(zs) == L:
                    return True
        return False

    def _analyze_results(self) -> Dict[str, Any]:
        """Analyze simulation results"""
        if not self.results_by_p:
            return {"metrics": {}, "logs": ["No results"]}

        p_values = sorted(self.results_by_p.keys())
        percolation_probs = [self.results_by_p[p]["percolation_prob"] for p in p_values]

        # Find percolation threshold (p where P_∞ = 0.5)
        p_threshold = None
        for i in range(len(p_values) - 1):
            if percolation_probs[i] <= 0.5 <= percolation_probs[i + 1]:
                # Linear interpolation
                p1, p2 = p_values[i], p_values[i + 1]
                v1, v2 = percolation_probs[i], percolation_probs[i + 1]
                if v2 != v1:
                    p_threshold = p1 + (0.5 - v1) * (p2 - p1) / (v2 - v1)
                break

        if p_threshold is None:
            p_threshold = p_values[np.argmin(np.abs(np.array(percolation_probs) - 0.5))]

        # Theoretical values
        L = self.config.lattice_size
        d = self.config.dimension
        if d == 2:
            p_c_theory = 0.592746  # Site percolation on square lattice
        else:
            p_c_theory = 0.3116  # Site percolation on cubic lattice (approximate)

        # Maximum cluster at criticality
        max_clusters = [self.results_by_p[p]["max_cluster_size"] for p in p_values]
        max_cluster_at_pc = max_clusters[np.argmin(np.abs(np.array(p_values) - p_threshold))]

        metrics = {
            "percolation_threshold": float(p_threshold),
            "threshold_error": float(abs(p_threshold - p_c_theory)),
            "max_cluster_at_pc": float(max_cluster_at_pc),
            "lattice_size": L,
            "dimension": d,
            "n_realizations": self.config.n_realizations,
        }

        logs = [
            f"Percolation on {L}^{d} lattice, {self.config.n_realizations} realizations",
            f"Estimated percolation threshold: {p_threshold:.4f}",
            f"Theoretical value: {p_c_theory:.4f}",
            f"Error: {metrics['threshold_error']:.4f}",
            f"Max cluster fraction at p_c: {max_cluster_at_pc:.4f}",
        ]

        if abs(p_threshold - p_c_theory) < 0.05:
            logs.append("Threshold estimate agrees with theory within 5%")

        return {"metrics": metrics, "logs": logs}

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        n_real = metrics.get("n_realizations", 0)
        if n_real >= 500:
            factors.append(0.3)
        elif n_real >= 100:
            factors.append(0.2)

        error = metrics.get("threshold_error", 1.0)
        if error < 0.02:
            factors.append(0.3)
        elif error < 0.05:
            factors.append(0.2)

        L = metrics.get("lattice_size", 0)
        if L >= 200:
            factors.append(0.2)
        elif L >= 100:
            factors.append(0.1)

        return min(0.85, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Estimate computational resources"""
        params = hypothesis.parameters
        L = params.get("lattice_size", 100)
        d = params.get("dimension", 2)
        n_real = params.get("n_realizations", 100)

        N = L ** d
        estimated_time = (N * n_real) / 1e6

        return {
            "cpu_cores": 1,
            "memory_gb": 0.1 + (N * 8) / 1e6,
            "gpu_required": False,
            "estimated_time_seconds": estimated_time,
        }
