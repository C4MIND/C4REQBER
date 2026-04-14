"""
Evolution Engine
Genetic algorithms for hypothesis evolution (von Neumann cellular automata concept)

Implements:
- Genetic algorithm with custom mutation/crossover
- Novelty search for exploration
- Multi-objective optimization (Pareto frontier)
- Fitness from simulation results
"""

import asyncio
import random
import numpy as np
from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from copy import deepcopy

from ..core import Hypothesis, SimulationResult, MetaSimulationEngine

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """A hypothesis individual in the population"""

    hypothesis: Hypothesis
    fitness: float = 0.0
    novelty: float = 0.0  # For novelty search
    objectives: Dict[str, float] = field(default_factory=dict)
    dominated_count: int = 0  # For NSGA-II
    dominating: List[int] = field(default_factory=list)
    crowding_distance: float = 0.0
    rank: int = 0


@dataclass
class EvolutionConfig:
    """Configuration for evolution run"""

    population_size: int = 100
    generations: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 5
    tournament_size: int = 3

    # Novelty search parameters
    use_novelty_search: bool = True
    novelty_k: int = 15  # K nearest neighbors for novelty
    novelty_threshold: float = 0.3

    # Multi-objective
    objectives: List[str] = field(default_factory=lambda: ["fitness", "novelty"])

    # Convergence
    convergence_threshold: float = 0.01
    stagnation_limit: int = 10


class EvolutionEngine:
    """
    Genetic algorithm engine for evolving hypotheses

    Based on John von Neumann's cellular automata concept:
    - Each hypothesis is a "cell" that can reproduce
    - Environment (simulation results) determines fitness
    - Evolution produces emergent solutions

    Implements NSGA-II for multi-objective optimization.
    """

    def __init__(self, simulation_engine: MetaSimulationEngine):
        self.sim_engine = simulation_engine
        self.population: List[Individual] = []
        self.generation = 0
        self.archive: List[Individual] = []  # Novelty archive
        self.behavior_archive: List[np.ndarray] = []  # For novelty calculation

    async def evolve(
        self,
        seed_hypotheses: List[Hypothesis],
        config: EvolutionConfig,
        progress_callback: Optional[Callable[[int, List[Individual]], None]] = None,
    ) -> List[Hypothesis]:
        """
        Run evolution from seed hypotheses

        Args:
            seed_hypotheses: Initial population seeds
            config: Evolution parameters
            progress_callback: Called each generation with (generation, population)

        Returns:
            List of evolved hypotheses (Pareto frontier)
        """
        logger.info(f"Starting evolution with {len(seed_hypotheses)} seeds")
        logger.info(
            f"Target: {config.generations} generations, "
            f"pop_size={config.population_size}"
        )

        # Initialize population
        await self._initialize_population(seed_hypotheses, config)

        # Evolution loop
        stagnation_count = 0
        prev_best_fitness = -float("inf")

        for generation in range(config.generations):
            self.generation = generation

            logger.info(f"Generation {generation + 1}/{config.generations}")

            # Evaluate population (run simulations)
            await self._evaluate_population(config)

            # Calculate novelty (if enabled)
            if config.use_novelty_search:
                self._calculate_novelty(config)

            # Non-dominated sorting (NSGA-II)
            fronts = self._non_dominated_sort()

            # Calculate crowding distance
            self._calculate_crowding_distance(fronts)

            # Create next generation
            offspring = await self._create_offspring(config)

            # Environmental selection
            self._environmental_selection(offspring, config)

            # Check convergence
            best_fitness = max(ind.fitness for ind in self.population)
            fitness_improvement = (
                (best_fitness - prev_best_fitness) / abs(prev_best_fitness)
                if prev_best_fitness != 0
                else 1.0
            )

            if fitness_improvement < config.convergence_threshold:
                stagnation_count += 1
                if stagnation_count >= config.stagnation_limit:
                    logger.info(f"Converged after {generation + 1} generations")
                    break
            else:
                stagnation_count = 0
                prev_best_fitness = best_fitness

            # Progress callback
            if progress_callback:
                progress_callback(generation, self.population)

            logger.info(
                f"  Best fitness: {best_fitness:.4f}, "
                f"Avg: {np.mean([ind.fitness for ind in self.population]):.4f}"
            )

        # Return Pareto frontier
        pareto_front = [ind.hypothesis for ind in self.population if ind.rank == 0]
        logger.info(
            f"Evolution complete. Pareto frontier: {len(pareto_front)} solutions"
        )

        return pareto_front

    async def _initialize_population(
        self, seed_hypotheses: List[Hypothesis], config: EvolutionConfig
    ) -> None:
        """Initialize population from seeds with random variations"""
        self.population = []

        # Add seeds
        for hypothesis in seed_hypotheses:
            ind = Individual(hypothesis=deepcopy(hypothesis))
            self.population.append(ind)

        # Fill remaining with mutations of seeds
        while len(self.population) < config.population_size:
            seed = random.choice(seed_hypotheses)
            mutated = self._mutate_hypothesis(deepcopy(seed), config.mutation_rate * 2)
            ind = Individual(hypothesis=mutated)
            self.population.append(ind)

    async def _evaluate_population(self, config: EvolutionConfig) -> None:
        """Run simulations to evaluate fitness"""
        # Run simulations in parallel batches
        batch_size = 4  # Adjust based on CPU cores

        for i in range(0, len(self.population), batch_size):
            batch = self.population[i : i + batch_size]

            tasks = [self._evaluate_individual(ind) for ind in batch]

            await asyncio.gather(*tasks)

    async def _evaluate_individual(self, individual: Individual) -> None:
        """Evaluate single individual via simulation"""
        try:
            result = await self.sim_engine.simulate(
                individual.hypothesis, timeout_seconds=60
            )

            if result.status.value == "COMPLETED":
                # Fitness is confidence score from simulation
                individual.fitness = result.confidence_score

                # Store behavior characterization for novelty
                behavior = self._extract_behavior(result)
                individual.hypothesis.parameters["_behavior"] = behavior.tolist()
            else:
                individual.fitness = 0.0

        except Exception as e:
            logger.warning(f"Evaluation failed: {e}")
            individual.fitness = 0.0

    def _extract_behavior(self, result: SimulationResult) -> np.ndarray:
        """Extract behavior vector from simulation result"""
        # Use key metrics as behavior characterization
        metrics = result.metrics
        behavior = [
            metrics.get("mean", 0),
            metrics.get("std", 0),
            metrics.get("ci_lower", 0),
            metrics.get("ci_upper", 0),
        ]
        return np.array(behavior)

    def _calculate_novelty(self, config: EvolutionConfig) -> None:
        """
        Calculate novelty score for each individual

        Novelty is average distance to k nearest neighbors in behavior space.
        """
        behaviors = []
        for ind in self.population:
            behavior = ind.hypothesis.parameters.get("_behavior", [0, 0, 0, 0])
            behaviors.append(np.array(behavior))

        # Include archive behaviors
        all_behaviors = behaviors + self.behavior_archive

        for i, ind in enumerate(self.population):
            if len(all_behaviors) <= config.novelty_k:
                ind.novelty = 1.0  # Max novelty if no neighbors
                continue

            # Calculate distances to all other behaviors
            distances = [
                np.linalg.norm(behaviors[i] - b)
                for j, b in enumerate(all_behaviors)
                if i != j or j >= len(behaviors)  # Exclude self
            ]

            # Average distance to k nearest
            distances.sort()
            k_distances = distances[: config.novelty_k]
            ind.novelty = np.mean(k_distances)

        # Update archive with novel individuals
        for ind in self.population:
            if ind.novelty > config.novelty_threshold:
                behavior = ind.hypothesis.parameters.get("_behavior", [0, 0, 0, 0])
                self.behavior_archive.append(np.array(behavior))
                self.archive.append(ind)

    def _non_dominated_sort(self) -> List[List[int]]:
        """
        NSGA-II non-dominated sorting

        Returns list of fronts, where each front is list of indices
        """
        n = len(self.population)

        # Reset
        for ind in self.population:
            ind.dominated_count = 0
            ind.dominating = []
            ind.rank = 0

        fronts = [[]]

        for i in range(n):
            for j in range(i + 1, n):
                ind_i = self.population[i]
                ind_j = self.population[j]

                if self._dominates(ind_i, ind_j):
                    ind_i.dominating.append(j)
                    ind_j.dominated_count += 1
                elif self._dominates(ind_j, ind_i):
                    ind_j.dominating.append(i)
                    ind_i.dominated_count += 1

            if self.population[i].dominated_count == 0:
                self.population[i].rank = 0
                fronts[0].append(i)

        # Build subsequent fronts
        i = 0
        while len(fronts[i]) > 0:
            next_front = []
            for p_idx in fronts[i]:
                p = self.population[p_idx]
                for q_idx in p.dominating:
                    q = self.population[q_idx]
                    q.dominated_count -= 1
                    if q.dominated_count == 0:
                        q.rank = i + 1
                        next_front.append(q_idx)

            i += 1
            fronts.append(next_front)

        return fronts[:-1]  # Remove empty last front

    def _dominates(self, ind1: Individual, ind2: Individual) -> bool:
        """
        Check if ind1 dominates ind2 (Pareto dominance)

        ind1 dominates ind2 if:
        - ind1 is no worse than ind2 in all objectives
        - ind1 is strictly better than ind2 in at least one objective
        """
        obj1 = {"fitness": ind1.fitness, "novelty": ind1.novelty}
        obj2 = {"fitness": ind2.fitness, "novelty": ind2.novelty}

        better_in_one = False

        for key in obj1:
            if obj1[key] < obj2[key]:
                return False  # Worse in this objective
            if obj1[key] > obj2[key]:
                better_in_one = True

        return better_in_one

    def _calculate_crowding_distance(self, fronts: List[List[int]]) -> None:
        """Calculate crowding distance for diversity preservation"""
        for front in fronts:
            if len(front) <= 2:
                for idx in front:
                    self.population[idx].crowding_distance = float("inf")
                continue

            for idx in front:
                self.population[idx].crowding_distance = 0

            objectives = ["fitness", "novelty"]

            for obj in objectives:
                # Sort by objective
                front_sorted = sorted(
                    front, key=lambda i: getattr(self.population[i], obj)
                )

                # Boundary points have infinite distance
                self.population[front_sorted[0]].crowding_distance = float("inf")
                self.population[front_sorted[-1]].crowding_distance = float("inf")

                # Calculate distances
                obj_min = getattr(self.population[front_sorted[0]], obj)
                obj_max = getattr(self.population[front_sorted[-1]], obj)

                if obj_max - obj_min > 0:
                    for i in range(1, len(front_sorted) - 1):
                        prev_obj = getattr(self.population[front_sorted[i - 1]], obj)
                        next_obj = getattr(self.population[front_sorted[i + 1]], obj)

                        self.population[front_sorted[i]].crowding_distance += (
                            next_obj - prev_obj
                        ) / (obj_max - obj_min)

    async def _create_offspring(self, config: EvolutionConfig) -> List[Individual]:
        """Create offspring through selection, crossover, mutation"""
        offspring = []

        # Elitism: Keep best individuals
        sorted_pop = sorted(
            self.population, key=lambda x: (x.rank, -x.crowding_distance)
        )
        elites = [deepcopy(sorted_pop[i]) for i in range(config.elite_size)]
        offspring.extend(elites)

        # Create rest through crossover
        while len(offspring) < config.population_size:
            # Tournament selection
            parent1 = self._tournament_selection(config.tournament_size)
            parent2 = self._tournament_selection(config.tournament_size)

            # Crossover
            if random.random() < config.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = deepcopy(parent1), deepcopy(parent2)

            # Mutation
            child1.hypothesis = self._mutate_hypothesis(
                child1.hypothesis, config.mutation_rate
            )
            child2.hypothesis = self._mutate_hypothesis(
                child2.hypothesis, config.mutation_rate
            )

            # Reset fitness (will be re-evaluated)
            child1.fitness = 0.0
            child2.fitness = 0.0

            offspring.append(child1)
            if len(offspring) < config.population_size:
                offspring.append(child2)

        return offspring

    def _tournament_selection(self, tournament_size: int) -> Individual:
        """Select individual using tournament selection"""
        tournament = random.sample(
            self.population, min(tournament_size, len(self.population))
        )
        return min(tournament, key=lambda x: (x.rank, -x.crowding_distance))

    def _crossover(
        self, parent1: Individual, parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """
        Crossover two hypotheses

        Implements parameter-level crossover
        """
        child1 = deepcopy(parent1)
        child2 = deepcopy(parent2)

        params1 = child1.hypothesis.parameters
        params2 = child2.hypothesis.parameters

        # Uniform crossover on parameters
        for key in params1:
            if key in params2 and key != "_behavior":
                if random.random() < 0.5:
                    params1[key], params2[key] = params2[key], params1[key]

        # Increment generation
        child1.hypothesis.generation += 1
        child2.hypothesis.generation += 1

        # Track parentage
        child1.hypothesis.parent_ids = [parent1.hypothesis.id, parent2.hypothesis.id]
        child2.hypothesis.parent_ids = [parent1.hypothesis.id, parent2.hypothesis.id]

        return child1, child2

    def _mutate_hypothesis(
        self, hypothesis: Hypothesis, mutation_rate: float
    ) -> Hypothesis:
        """
        Mutate hypothesis parameters

        Implements Gaussian mutation for numeric parameters
        """
        mutated = deepcopy(hypothesis)

        for key, value in mutated.parameters.items():
            if key.startswith("_"):  # Skip internal params
                continue

            if random.random() < mutation_rate:
                if isinstance(value, (int, float)):
                    # Gaussian mutation
                    noise = np.random.normal(0, abs(value) * 0.1 if value != 0 else 0.1)
                    mutated.parameters[key] = value + noise

                    # Ensure non-negative for most params
                    if key in ["size", "count", "samples"]:
                        mutated.parameters[key] = max(1, mutated.parameters[key])

        return mutated

    def _environmental_selection(
        self, offspring: List[Individual], config: EvolutionConfig
    ) -> None:
        """Select next generation from combined population + offspring"""
        combined = self.population + offspring

        # Non-dominated sort
        self.population = combined  # Temporary for sorting
        fronts = self._non_dominated_sort()

        # Select by rank and crowding distance
        new_population = []
        for front in fronts:
            if len(new_population) + len(front) <= config.population_size:
                new_population.extend([self.population[i] for i in front])
            else:
                # Sort by crowding distance and take best
                front_sorted = sorted(
                    front, key=lambda i: -self.population[i].crowding_distance
                )
                remaining = config.population_size - len(new_population)
                new_population.extend(
                    [self.population[i] for i in front_sorted[:remaining]]
                )
                break

        self.population = new_population
