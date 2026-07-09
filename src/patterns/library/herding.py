"""
Pattern 62: Herding and Opinion Dynamics
Implements Ising-like opinion formation models, information cascades,
and social learning dynamics.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class HerdingConfig:
    """Configuration for herding and opinion dynamics model."""
    n_agents: int = 100
    n_states: int = 2           # Number of opinion states
    temperature: float = 1.0    # Noise parameter (inverse of coupling strength)
    J: float = 1.0              # Interaction strength
    external_field: float = 0.0 # External influence
    network_type: str = "complete"  # "complete", "lattice", "small_world"
    initial_opinion: str = "random"  # "random", "uniform", "polarized"
    learning_rate: float = 0.1
    convergence_threshold: float = 0.95
    max_iterations: int = 1000
    random_seed: int = 42


class HerdingModel:
    """
    Opinion dynamics and herding behavior model.

    Implements:
    - Ising-like opinion formation
    - Information cascade models
    - Social learning dynamics
    """

    def __init__(self, config: HerdingConfig = None) -> None:  # type: ignore[assignment]
        self.config = config or HerdingConfig()
        np.random.seed(self.config.random_seed)
        self.opinions: np.ndarray = None  # type: ignore[assignment]
        self.network: np.ndarray = None  # type: ignore[assignment]
        self.history: list[dict] = []
        self._initialize()

    def _initialize(self) -> None:
        """Initialize agent opinions and network."""
        cfg = self.config
        n = cfg.n_agents

        # Initialize opinions
        if cfg.initial_opinion == "random":
            self.opinions = np.random.choice([-1, 1], n)
        elif cfg.initial_opinion == "uniform":
            self.opinions = np.ones(n)
        elif cfg.initial_opinion == "polarized":
            self.opinions = np.concatenate([np.ones(n//2), -np.ones(n - n//2)])
        else:
            self.opinions = np.random.choice([-1, 1], n)

        # Create network
        self.network = self._create_network()

    def _create_network(self) -> np.ndarray:
        """Create interaction network."""
        cfg = self.config
        n = cfg.n_agents

        if cfg.network_type == "complete":
            # Everyone connected to everyone
            network = np.ones((n, n)) - np.eye(n)
        elif cfg.network_type == "lattice":
            # 1D lattice with nearest neighbors
            network = np.zeros((n, n))
            for i in range(n):
                network[i, (i-1) % n] = 1
                network[i, (i+1) % n] = 1
        elif cfg.network_type == "small_world":
            # Small-world network (Watts-Strogatz)
            network = np.zeros((n, n))
            k = 4  # Each node connected to k nearest neighbors

            # Regular ring lattice
            for i in range(n):
                for j in range(1, k//2 + 1):
                    network[i, (i-j) % n] = 1
                    network[i, (i+j) % n] = 1

            # Rewire with probability p
            p_rewire = 0.1
            for i in range(n):
                for j in range(i+1, n):
                    if network[i, j] == 1 and np.random.random() < p_rewire:
                        network[i, j] = 0
                        network[j, i] = 0
                        new_j = np.random.randint(0, n)
                        if new_j != i:
                            network[i, new_j] = 1
                            network[new_j, i] = 1
        else:
            network = np.ones((n, n)) - np.eye(n)

        return network

    def local_field(self, agent: int) -> float:
        """Calculate local field (social influence) for an agent."""
        cfg = self.config
        neighbors = self.network[agent] > 0
        field = cfg.J * np.sum(self.opinions[neighbors])
        field += cfg.external_field
        return field  # type: ignore[no-any-return]

    def update_opinion_ising(self, agent: int) -> int:
        """
        Update opinion using Ising/Glauber dynamics.

        Args:
            agent: Agent index

        Returns:
            New opinion
        """
        cfg = self.config
        field = self.local_field(agent)

        # Glauber dynamics: probability of spin up
        prob_up = 1 / (1 + np.exp(-2 * field / cfg.temperature))

        if np.random.random() < prob_up:
            return 1
        else:
            return -1

    def update_opinion_majority(self, agent: int) -> int:
        """
        Update opinion using majority rule.

        Args:
            agent: Agent index

        Returns:
            New opinion
        """
        neighbors = self.network[agent] > 0
        neighbor_opinions = self.opinions[neighbors]

        if len(neighbor_opinions) == 0:
            return self.opinions[agent]  # type: ignore[no-any-return]

        majority = np.sign(np.sum(neighbor_opinions))

        if majority == 0:
            return self.opinions[agent]  # type: ignore[no-any-return]

        # Add some noise
        if np.random.random() < self.config.temperature:
            return -majority  # type: ignore[no-any-return]

        return int(majority)

    def update_opinion_voter(self, agent: int) -> int:
        """
        Update opinion using voter model.

        Args:
            agent: Agent index

        Returns:
            New opinion
        """
        neighbors = self.network[agent] > 0
        neighbor_opinions = self.opinions[neighbors]

        if len(neighbor_opinions) == 0:
            return self.opinions[agent]  # type: ignore[no-any-return]

        # Copy random neighbor
        return int(np.random.choice(neighbor_opinions))

    def simulate(self, update_rule: str = "ising") -> dict[str, Any]:
        """
        Run opinion dynamics simulation.

        Args:
            update_rule: "ising", "majority", or "voter"

        Returns:
            Dict with simulation results
        """
        cfg = self.config

        if update_rule == "ising":
            update_fn = self.update_opinion_ising
        elif update_rule == "majority":
            update_fn = self.update_opinion_majority
        elif update_rule == "voter":
            update_fn = self.update_opinion_voter
        else:
            update_fn = self.update_opinion_ising

        # History tracking
        opinion_history = []
        magnetization_history = []

        for _ in range(cfg.max_iterations):
            # Random sequential update
            order = np.random.permutation(cfg.n_agents)

            for agent in order:
                self.opinions[agent] = update_fn(agent)

            # Record state
            opinion_history.append(self.opinions.copy())
            magnetization = np.mean(self.opinions)
            magnetization_history.append(magnetization)

            # Check convergence
            if abs(magnetization) >= cfg.convergence_threshold:
                break

        # Final statistics
        final_magnetization = np.mean(self.opinions)
        consensus_reached = abs(final_magnetization) >= cfg.convergence_threshold

        # Cluster analysis
        clusters = self._analyze_clusters()

        return {
            "final_opinions": self.opinions.tolist(),
            "final_magnetization": float(final_magnetization),
            "consensus_reached": bool(consensus_reached),
            "iterations": cfg.max_iterations,
            "magnetization_history": magnetization_history,
            "clusters": clusters,
            "update_rule": update_rule
        }

    def _analyze_clusters(self) -> dict[str, Any]:
        """Analyze opinion clusters."""
        # Simple cluster counting
        n_positive = np.sum(self.opinions > 0)
        n_negative = np.sum(self.opinions < 0)

        # Largest connected component of each opinion
        set(np.where(self.opinions > 0)[0])
        set(np.where(self.opinions < 0)[0])

        return {
            "n_positive": int(n_positive),
            "n_negative": int(n_negative),
            "fraction_positive": float(n_positive / len(self.opinions)),
            "fraction_negative": float(n_negative / len(self.opinions))
        }

    def information_cascade(self, private_signals: list[float] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """
        Simulate information cascade (Banerjee model).

        Args:
            private_signals: Private signals for each agent

        Returns:
            Dict with cascade dynamics
        """
        cfg = self.config
        n = cfg.n_agents

        if private_signals is None:
            # True state is +1, agents get noisy signals
            true_state = 1  # type: ignore[unreachable]
            private_signals = [true_state + np.random.normal(0, 1) for _ in range(n)]

        # Decisions
        decisions = np.zeros(n)
        public_belief = 0  # Difference between +1 and -1 decisions

        decision_history = []
        cascade_start = None

        for i in range(n):
            # Agent observes previous decisions
            if i == 0:
                # First agent follows private signal
                decisions[i] = 1 if private_signals[i] > 0 else -1
            else:
                # Weight between private signal and public belief
                if abs(public_belief) > 2:  # Cascade condition
                    if cascade_start is None:
                        cascade_start = i
                    decisions[i] = np.sign(public_belief)
                else:
                    # Use both signals
                    combined = private_signals[i] + 0.5 * public_belief
                    decisions[i] = 1 if combined > 0 else -1

            # Update public belief
            public_belief += decisions[i]
            decision_history.append({
                "agent": i,
                "decision": int(decisions[i]),
                "private_signal": float(private_signals[i]),
                "public_belief": float(public_belief)
            })

        # Check if correct cascade
        correct_cascade = decisions[-1] == 1

        return {
            "decisions": decisions.tolist(),
            "decision_history": decision_history,
            "cascade_started": cascade_start is not None,
            "cascade_start_point": cascade_start,
            "correct_cascade": bool(correct_cascade),
            "final_consensus": int(decisions[-1])
        }

    def social_learning(self, true_value: float = 0.5) -> dict[str, Any]:
        """
        Simulate DeGroot social learning model.

        Args:
            true_value: True value agents are learning

        Returns:
            Dict with learning dynamics
        """
        cfg = self.config
        n = cfg.n_agents

        # Initial beliefs (noisy observations of true value)
        beliefs = np.array([true_value + np.random.normal(0, 0.2) for _ in range(n)])

        # Normalize network to get weights
        weights = self.network.copy()
        row_sums = weights.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        weights = weights / row_sums

        # Learning dynamics
        belief_history = [beliefs.copy()]

        for _ in range(cfg.max_iterations):
            # Update beliefs: b_i(t+1) = sum_j W_ij * b_j(t)
            new_beliefs = weights @ beliefs

            # Add some private signals occasionally
            if np.random.random() < 0.1:
                new_beliefs += cfg.learning_rate * np.random.normal(0, 0.1, n)

            beliefs = new_beliefs
            belief_history.append(beliefs.copy())

            # Check convergence
            if np.std(beliefs) < 0.01:
                break

        # Learning accuracy
        final_error = np.mean(np.abs(beliefs - true_value))
        consensus_reached = np.std(beliefs) < 0.05

        return {
            "true_value": float(true_value),
            "final_beliefs": beliefs.tolist(),
            "mean_belief": float(np.mean(beliefs)),
            "belief_variance": float(np.var(beliefs)),
            "final_error": float(final_error),
            "consensus_reached": bool(consensus_reached),
            "belief_history": [b[:10].tolist() for b in belief_history[::10]]  # Sample
        }

    def phase_transition_analysis(self) -> dict[str, Any]:
        """
        Analyze phase transition behavior.

        Returns:
            Dict with phase transition results
        """
        temperatures = np.linspace(0.1, 3.0, 20)
        magnetizations = []

        for T in temperatures:
            self.config.temperature = T
            result = self.simulate(update_rule="ising")
            magnetizations.append(abs(result["final_magnetization"]))
            # Reset opinions
            self.opinions = np.random.choice([-1, 1], self.config.n_agents)

        # Find critical temperature (approximate)
        critical_idx = np.argmin(np.abs(np.array(magnetizations) - 0.5))
        critical_temp = temperatures[critical_idx]

        return {
            "temperatures": temperatures.tolist(),
            "magnetizations": magnetizations,
            "critical_temperature": float(critical_temp),
            "ordered_phase": float(critical_temp) < 1.0
        }

    def run(self) -> dict[str, Any]:
        """Execute complete herding analysis."""
        cfg = self.config

        # Opinion dynamics with different rules
        ising_result = self.simulate(update_rule="ising")

        # Reset for majority
        self.opinions = np.random.choice([-1, 1], cfg.n_agents)
        majority_result = self.simulate(update_rule="majority")

        # Reset for voter
        self.opinions = np.random.choice([-1, 1], cfg.n_agents)
        voter_result = self.simulate(update_rule="voter")

        # Information cascade
        cascade = self.information_cascade()

        # Social learning
        learning = self.social_learning()

        # Phase transition (for Ising)
        self.opinions = np.random.choice([-1, 1], cfg.n_agents)
        phase = self.phase_transition_analysis()

        return {
            "opinion_dynamics": {
                "ising": ising_result,
                "majority": majority_result,
                "voter": voter_result
            },
            "information_cascade": cascade,
            "social_learning": learning,
            "phase_transition": phase,
            "network_properties": {
                "type": cfg.network_type,
                "n_agents": cfg.n_agents,
                "avg_degree": float(np.mean(np.sum(self.network, axis=1)))
            },
            "model_type": "herding_opinion_dynamics"
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """Return pattern metadata."""
        return {
            "pattern_id": 62,
            "name": "Herding and Opinion Dynamics",
            "category": "Behavioral Economics",
            "description": "Ising-like opinion formation and information cascades",
            "author": "Banerjee, Bikhchandani, Welch, Ising",
            "year": 1992,
            "parameters": ["n_agents", "temperature", "J", "network_type"],
            "outputs": ["consensus", "magnetization", "cascade_dynamics"],
            "applications": ["financial_bubbles", "social_networks", "adoption_dynamics"]
        }


# Unit Tests
import unittest


class TestHerdingModel(unittest.TestCase):

    """TestHerdingModel."""
    def test_initialization(self) -> None:
        """Test model initialization."""
        config = HerdingConfig(n_agents=50)
        model = HerdingModel(config)

        self.assertEqual(len(model.opinions), 50)
        self.assertEqual(model.network.shape, (50, 50))
        self.assertTrue(np.all(np.abs(model.opinions) == 1))

    def test_local_field(self) -> None:
        """Test local field calculation."""
        config = HerdingConfig(n_agents=10, network_type="complete")
        model = HerdingModel(config)

        # All agents have opinion 1
        model.opinions = np.ones(10)
        field = model.local_field(0)

        # Field should be positive and proportional to J
        self.assertGreater(field, 0)
        self.assertAlmostEqual(field, config.J * 9, delta=0.1)

    def test_ising_update(self) -> None:
        """Test Ising update rule."""
        config = HerdingConfig(n_agents=10, temperature=0.1)
        model = HerdingModel(config)

        model.opinions = np.ones(10)
        model.opinions[0] = -1

        # With strong positive field, agent should likely switch to +1
        model.config.external_field = 5.0
        new_opinion = model.update_opinion_ising(0)

        # High probability of switching due to strong field
        self.assertEqual(new_opinion, 1)

    def test_majority_update(self) -> None:
        """Test majority rule update."""
        config = HerdingConfig(n_agents=5, network_type="complete")
        model = HerdingModel(config)

        # 4 positive, 1 negative
        model.opinions = np.array([1, 1, 1, 1, -1])

        # Negative agent should switch (at low temperature)
        model.config.temperature = 0.01
        new_opinion = model.update_opinion_majority(4)

        self.assertEqual(new_opinion, 1)

    def test_simulation_convergence(self) -> None:
        """Test simulation reaches some outcome."""
        config = HerdingConfig(n_agents=20, max_iterations=100)
        model = HerdingModel(config)

        result = model.simulate(update_rule="majority")

        self.assertIn("final_magnetization", result)
        self.assertIn("cfg.max_iterationss", result)
        self.assertLessEqual(result["cfg.max_iterationss"], 100)

    def test_information_cascade(self) -> None:
        """Test information cascade simulation."""
        config = HerdingConfig(n_agents=20)
        model = HerdingModel(config)

        cascade = model.information_cascade()

        self.assertIn("decisions", cascade)
        self.assertIn("cascade_started", cascade)
        self.assertEqual(len(cascade["decisions"]), 20)

    def test_social_learning(self) -> None:
        """Test social learning convergence."""
        config = HerdingConfig(n_agents=20, max_iterations=200)
        model = HerdingModel(config)

        learning = model.social_learning(true_value=0.5)

        self.assertIn("final_beliefs", learning)
        self.assertIn("final_error", learning)

        # Should converge close to true value
        self.assertLess(learning["final_error"], 0.2)

    def test_network_types(self) -> None:
        """Test different network types."""
        for net_type in ["complete", "lattice", "small_world"]:
            config = HerdingConfig(n_agents=20, network_type=net_type)
            model = HerdingModel(config)

            # Check network is valid
            self.assertEqual(model.network.shape, (20, 20))
            self.assertTrue(np.all(model.network >= 0))


if __name__ == "__main__":
    # Run demonstration
    config = HerdingConfig(n_agents=50, temperature=0.5)
    model = HerdingModel(config)
    result = model.run()

    print("=" * 60)
    print("HERDING AND OPINION DYNAMICS MODEL")
    print("=" * 60)
    print("\nOpinion Dynamics (Ising):")
    print(f"  Final Magnetization: {result['opinion_dynamics']['ising']['final_magnetization']:.4f}")
    print(f"  Consensus Reached: {result['opinion_dynamics']['ising']['consensus_reached']}")
    print(f"  Iterations: {result['opinion_dynamics']['ising']['cfg.max_iterationss']}")

    print("\nInformation Cascade:")
    print(f"  Cascade Started: {result['information_cascade']['cascade_started']}")
    if result['information_cascade']['cascade_start_point']:
        print(f"  Cascade Start: Agent {result['information_cascade']['cascade_start_point']}")
    print(f"  Correct Cascade: {result['information_cascade']['correct_cascade']}")

    print("\nSocial Learning:")
    print(f"  Mean Belief: {result['social_learning']['mean_belief']:.4f}")
    print(f"  Consensus Reached: {result['social_learning']['consensus_reached']}")
    print(f"  Final Error: {result['social_learning']['final_error']:.4f}")

    print("\nPhase Transition:")
    print(f"  Critical Temperature: {result['phase_transition']['critical_temperature']:.4f}")

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)


# Alias for C4REQBER compatibility
HerdingPattern = HerdingModel
