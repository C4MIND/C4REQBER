"""
TURBO-CDI v6.0 Engine - Main Integration Module
Production-grade meta-simulation system

Usage:
    from v6.engine import TURBOCDIEngine, Hypothesis

    engine = TURBOCDIEngine()

    hypothesis = Hypothesis(
        title="Novel battery electrode",
        description="Gradient porosity for ion transport",
        parameters={"base_value": 1.0, "noise_scale": 0.1}
    )

    # Single simulation
    result = await engine.simulate(hypothesis)

    # Full validation hierarchy
    report = await engine.validate(hypothesis)

    # Evolution
    evolved = await engine.evolve([hypothesis], generations=50)
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Core components
from .core import (
    MetaSimulationEngine,
    PatternRegistry,
    Hypothesis,
    SimulationResult,
    ValidationLevel,
    simulation_pattern,
)

# Patterns
from .patterns.monte_carlo import MonteCarloPattern
from .patterns.agent_based import AgentBasedPattern
from .patterns.system_dynamics import SystemDynamicsPattern
from .patterns.circuit_simulation import CircuitSimulationPattern

# Evolution
from .evolution.engine import EvolutionEngine, EvolutionConfig

# Validation
from .validation.hierarchy import ValidationEngine, ValidationReport

logger = logging.getLogger(__name__)


@dataclass
class EngineConfig:
    """Configuration for TURBO-CDI Engine"""

    # Validation
    default_validation_level: ValidationLevel = ValidationLevel.MONTE_CARLO
    validation_timeout: float = 300  # seconds
    target_confidence: float = 0.85

    # Evolution
    evolution_population_size: int = 100
    evolution_generations: int = 50
    evolution_mutation_rate: float = 0.1

    # Resources
    max_parallel_simulations: int = 4
    simulation_timeout: float = 3600

    # Backends
    enable_docker: bool = False
    enable_kubernetes: bool = False
    backend_endpoint: Optional[str] = None


class TURBOCDIEngine:
    """
    Main TURBO-CDI v6.0 Engine

    Integrates:
    - Meta-simulation engine with pattern library
    - Validation hierarchy (5 levels)
    - Evolution engine (genetic algorithms)
    - Canvas visualization (via external module)

    This is the primary interface for the entire v6.0 system.
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()

        # Initialize core engine
        self.sim_engine = MetaSimulationEngine()

        # Initialize validation engine
        self.validation_engine = ValidationEngine(self.sim_engine)

        # Initialize evolution engine
        self.evolution_engine = EvolutionEngine(self.sim_engine)

        # Register built-in patterns
        self._register_builtin_patterns()

        logger.info("TURBO-CDI v6.0 Engine initialized")
        logger.info(
            f"Available patterns: {len(self.sim_engine.registry.list_patterns())}"
        )

    def _register_builtin_patterns(self) -> None:
        """Register all built-in simulation patterns"""
        # Patterns are auto-registered via @simulation_pattern decorator
        # when their modules are imported
        # Just need to ensure they're imported
        from .patterns import (
            MonteCarloPattern,
            AgentBasedPattern,
            SystemDynamicsPattern,
            CircuitSimulationPattern,
        )
        logger.info(f"Registered {len(self.sim_engine.registry.list_patterns())} patterns")

    async def simulate(
        self,
        hypothesis: Hypothesis,
        pattern: Optional[str] = None,
        validation_level: Optional[ValidationLevel] = None,
        timeout: Optional[float] = None,
    ) -> SimulationResult:
        """
        Run simulation for a hypothesis

        Args:
            hypothesis: The hypothesis to simulate
            pattern: Specific pattern to use (auto-selected if None)
            validation_level: Target validation level
            timeout: Maximum runtime in seconds

        Returns:
            SimulationResult with metrics and confidence score

        Example:
            result = await engine.simulate(hypothesis)
            print(f"Confidence: {result.confidence_score:.2f}")
            print(f"Metrics: {result.metrics}")
        """
        timeout = timeout or self.config.simulation_timeout
        level = validation_level or self.config.default_validation_level

        logger.info(f"Starting simulation for hypothesis: {hypothesis.id}")
        logger.info(f"Title: {hypothesis.title}")

        # If specific pattern requested
        if pattern:
            return await self.sim_engine.simulate(
                hypothesis,
                pattern_ids=[pattern],
                validation_level=level,
                timeout_seconds=timeout,
            )

        # Auto-select pattern
        return await self.sim_engine.simulate(
            hypothesis, validation_level=level, timeout_seconds=timeout
        )

    async def validate(
        self,
        hypothesis: Hypothesis,
        target_confidence: Optional[float] = None,
        max_level: Optional[ValidationLevel] = None,
        timeout_per_level: Optional[float] = None,
    ) -> ValidationReport:
        """
        Run full validation hierarchy for hypothesis

        Attempts validation at all levels from highest to max_level,
        stopping when target confidence is reached.

        Args:
            hypothesis: Hypothesis to validate
            target_confidence: Stop when this confidence reached
            max_level: Maximum validation level to attempt
            timeout_per_level: Timeout for each level

        Returns:
            ValidationReport with complete results and recommendations

        Example:
            report = await engine.validate(hypothesis)
            print(f"Final confidence: {report.confidence:.2f}")
            print(f"Achieved at level: {report.final_level.name}")
            for rec in report.recommendations:
                print(f"Recommendation: {rec}")
        """
        target = target_confidence or self.config.target_confidence
        max_lvl = max_level or ValidationLevel.EMPIRICAL
        timeout = timeout_per_level or self.config.validation_timeout

        logger.info(f"Starting validation for hypothesis: {hypothesis.id}")
        logger.info(f"Target confidence: {target}")

        return await self.validation_engine.validate(
            hypothesis,
            target_confidence=target,
            max_level=max_lvl,
            timeout_per_level=timeout,
        )

    async def evolve(
        self,
        seed_hypotheses: List[Hypothesis],
        generations: Optional[int] = None,
        population_size: Optional[int] = None,
        progress_callback: Optional[Any] = None,
    ) -> List[Hypothesis]:
        """
        Evolve hypotheses using genetic algorithm

        Runs multi-objective optimization (fitness + novelty) to
        evolve seed hypotheses into optimized solutions.

        Args:
            seed_hypotheses: Initial population seeds
            generations: Number of generations to run
            population_size: Size of population
            progress_callback: Called each generation

        Returns:
            List of evolved hypotheses (Pareto frontier)

        Example:
            seeds = [hypothesis1, hypothesis2]
            evolved = await engine.evolve(seeds, generations=50)
            print(f"Evolved {len(evolved)} solutions")
        """
        config = EvolutionConfig(
            population_size=population_size or self.config.evolution_population_size,
            generations=generations or self.config.evolution_generations,
            mutation_rate=self.config.evolution_mutation_rate,
        )

        logger.info(f"Starting evolution with {len(seed_hypotheses)} seeds")
        logger.info(f"Generations: {config.generations}")
        logger.info(f"Population: {config.population_size}")

        return await self.evolution_engine.evolve(
            seed_hypotheses, config, progress_callback
        )

    async def full_pipeline(
        self,
        hypothesis: Hypothesis,
        run_evolution: bool = True,
        evolution_generations: int = 30,
    ) -> Dict[str, Any]:
        """
        Run complete TURBO-CDI pipeline

        1. Generate initial simulation
        2. Run validation hierarchy
        3. If confidence low, run evolution
        4. Validate evolved solutions

        Args:
            hypothesis: Initial hypothesis
            run_evolution: Whether to run evolution if needed
            evolution_generations: Number of evolution generations

        Returns:
            Complete results including all stages
        """
        results = {
            "hypothesis": hypothesis,
            "initial_simulation": None,
            "validation_report": None,
            "evolved_hypotheses": None,
            "final_recommendations": [],
        }

        # Initial simulation
        logger.info("=== STAGE 1: Initial Simulation ===")
        sim_result = await self.simulate(hypothesis)
        results["initial_simulation"] = sim_result

        # Validation hierarchy
        logger.info("=== STAGE 2: Validation Hierarchy ===")
        val_report = await self.validate(hypothesis)
        results["validation_report"] = val_report

        # Check if evolution needed
        if run_evolution and val_report.confidence < self.config.target_confidence:
            logger.info("=== STAGE 3: Evolution ===")
            evolved = await self.evolve([hypothesis], generations=evolution_generations)
            results["evolved_hypotheses"] = evolved

            # Validate best evolved hypothesis
            if evolved:
                logger.info("=== STAGE 4: Validation of Evolved Solution ===")
                best = evolved[0]
                evolved_report = await self.validate(best)
                results["evolved_validation"] = evolved_report

        # Generate recommendations
        results["final_recommendations"] = self._generate_pipeline_recommendations(
            results
        )

        return results

    def _generate_pipeline_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate final recommendations based on pipeline results"""
        recommendations = []

        val_report = results.get("validation_report")
        if val_report:
            recommendations.extend(val_report.recommendations)

        evolved = results.get("evolved_hypotheses")
        if evolved:
            recommendations.append(
                f"Evolution produced {len(evolved)} optimized variants. "
                "Review Pareto frontier for trade-off analysis."
            )

        return recommendations

    def get_pattern_library(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get organized library of available simulation patterns

        Returns:
            Dictionary organized by category with pattern details
        """
        return self.sim_engine.get_pattern_library()

    def get_status(self) -> Dict[str, Any]:
        """Get engine status and capabilities"""
        return {
            "version": "6.0.0",
            "patterns_registered": len(self.sim_engine.registry.list_patterns()),
            "validation_levels": [level.name for level in ValidationLevel],
            "evolution_available": True,
            "docker_enabled": self.config.enable_docker,
            "kubernetes_enabled": self.config.enable_kubernetes,
            "max_parallel": self.config.max_parallel_simulations,
        }


# Export main classes (API imported separately to avoid circular imports)
__all__ = [
    "TURBOCDIEngine",
    "EngineConfig",
    "Hypothesis",
    "SimulationResult",
    "ValidationReport",
    "ValidationLevel",
    "EvolutionConfig",
    "simulation_pattern",
    "PatternRegistry",
    # Patterns
    "MonteCarloPattern",
    "AgentBasedPattern",
    "SystemDynamicsPattern",
    "CircuitSimulationPattern",
]
