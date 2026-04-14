"""
TURBO-CDI v6.0 - State Space Pattern
Linear Quadratic Regulator (LQR) and Linear Quadratic Gaussian (LQG) control.

Pattern Structure (Christopher Alexander):
- Context: Multi-input multi-output (MIMO) control systems
- Forces: State coupling, optimal performance, noise rejection
- Solution: State-space representation with optimal control
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


class ControlMethod(Enum):
    """Available control methods"""

    LQR = "lqr"  # Linear Quadratic Regulator
    LQG = "lqg"  # Linear Quadratic Gaussian
    POLE_PLACEMENT = "pole_placement"
    DEADBEAT = "deadbeat"


class SystemType(Enum):
    """Predefined system types for testing"""

    DOUBLE_INTEGRATOR = "double_integrator"
    INVERTED_PENDULUM = "inverted_pendulum"
    DC_MOTOR = "dc_motor"
    MASS_SPRING_DAMPER = "mass_spring_damper"
    CUSTOM = "custom"


@dataclass
class StateSpaceConfig:
    """Configuration for state-space control"""

    # System definition
    system_type: SystemType = SystemType.DOUBLE_INTEGRATOR
    A: Optional[np.ndarray] = None  # State matrix
    B: Optional[np.ndarray] = None  # Input matrix
    C: Optional[np.ndarray] = None  # Output matrix
    D: Optional[np.ndarray] = None  # Feedthrough matrix

    # LQR weights
    Q: Optional[np.ndarray] = None  # State cost matrix
    R: Optional[np.ndarray] = None  # Control cost matrix

    # LQG noise covariances
    W: Optional[np.ndarray] = None  # Process noise covariance
    V: Optional[np.ndarray] = None  # Measurement noise covariance

    # Control method
    control_method: ControlMethod = ControlMethod.LQR

    # Pole placement (if used)
    desired_poles: Optional[List[complex]] = None

    # Simulation parameters
    dt: float = 0.01
    simulation_steps: int = 2000
    initial_state: Optional[np.ndarray] = None

    # Reference trajectory
    reference_type: str = "constant"  # constant, sinusoid, ramp
    reference_value: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0]))

    # Output
    output_interval: int = 10

    def __post_init__(self):
        """Initialize default matrices if not provided"""
        if self.system_type == SystemType.DOUBLE_INTEGRATOR:
            self.A = np.array([[0.0, 1.0], [0.0, 0.0]])
            self.B = np.array([[0.0], [1.0]])
            self.C = np.array([[1.0, 0.0]])
            self.D = np.array([[0.0]])

        elif self.system_type == SystemType.INVERTED_PENDULUM:
            # Linearized inverted pendulum: [theta, theta_dot]
            g, L = 9.81, 1.0
            self.A = np.array([[0.0, 1.0], [g / L, 0.0]])
            self.B = np.array([[0.0], [1.0 / L]])
            self.C = np.array([[1.0, 0.0]])
            self.D = np.array([[0.0]])

        elif self.system_type == SystemType.DC_MOTOR:
            # DC motor: [omega, current]
            J, b, K, R, L = 0.01, 0.1, 0.01, 1.0, 0.5
            self.A = np.array([[-b / J, K / J], [-K / L, -R / L]])
            self.B = np.array([[0.0], [1.0 / L]])
            self.C = np.array([[1.0, 0.0]])
            self.D = np.array([[0.0]])

        elif self.system_type == SystemType.MASS_SPRING_DAMPER:
            # [position, velocity]
            m, c, k = 1.0, 0.5, 2.0
            self.A = np.array([[0.0, 1.0], [-k / m, -c / m]])
            self.B = np.array([[0.0], [1.0 / m]])
            self.C = np.array([[1.0, 0.0]])
            self.D = np.array([[0.0]])

        n_states = self.A.shape[0]
        n_inputs = self.B.shape[1]
        n_outputs = self.C.shape[0]

        # Default LQR weights
        if self.Q is None:
            self.Q = np.eye(n_states)
        if self.R is None:
            self.R = np.eye(n_inputs)

        # Default noise covariances
        if self.W is None:
            self.W = 0.01 * np.eye(n_states)
        if self.V is None:
            self.V = 0.01 * np.eye(n_outputs)

        # Default initial state
        if self.initial_state is None:
            self.initial_state = np.zeros(n_states)


class StateSpaceController:
    """
    State-space controller with LQR/LQG design.
    """

    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        dt: float = 0.01,
    ):
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self.dt = dt

        self.n_states = A.shape[0]
        self.n_inputs = B.shape[1]
        self.n_outputs = C.shape[0]

        # Controller and observer gains
        self.K: Optional[np.ndarray] = None  # State feedback gain
        self.L: Optional[np.ndarray] = None  # Observer gain

        # State estimate (for LQG)
        self.x_hat = np.zeros(self.n_states)

        # Control history
        self.control_history = []

    def discretize(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Discretize continuous-time system using zero-order hold.
        """
        # Approximate: A_d ≈ I + A*dt, B_d ≈ B*dt
        # More accurate: matrix exponential
        from scipy.linalg import expm

        # Build augmented matrix for expm
        n = self.n_states
        m = self.n_inputs

        M = np.zeros((n + m, n + m))
        M[:n, :n] = self.A
        M[:n, n:] = self.B

        Md = expm(M * self.dt)

        A_d = Md[:n, :n]
        B_d = Md[:n, n:]

        return A_d, B_d

    def solve_lqr(self, Q: np.ndarray, R: np.ndarray) -> np.ndarray:
        """
        Solve discrete-time LQR problem.
        Returns optimal feedback gain K.
        """
        A_d, B_d = self.discretize()

        # Solve discrete-time algebraic Riccati equation
        # P = A'PA - A'PB(R + B'PB)^(-1)B'PA + Q
        from scipy.linalg import solve_discrete_are, inv

        try:
            P = solve_discrete_are(A_d, B_d, Q, R)

            # K = (R + B'PB)^(-1) B'PA
            K = inv(R + B_d.T @ P @ B_d) @ B_d.T @ P @ A_d

            self.K = K
            return K

        except Exception as e:
            logger.warning(f"LQR solve failed: {e}, using pole placement fallback")
            # Fallback: place poles at stable locations
            poles = [0.5 + 0.1j * i for i in range(self.n_states)]
            return self.place_poles(poles)

    def place_poles(self, poles: List[complex]) -> np.ndarray:
        """
        Pole placement using Ackermann's formula.
        """
        A_d, B_d = self.discretize()

        # Check controllability
        from scipy.linalg import ctrb

        Co = ctrb(A_d, B_d)

        if np.linalg.matrix_rank(Co) < self.n_states:
            logger.warning("System not controllable, using LQR fallback")
            # Return some stabilizing gain
            return -np.ones((self.n_inputs, self.n_states)) * 0.1

        # Use scipy's place_poles if available
        try:
            from scipy.signal import place_poles

            result = place_poles(A_d, B_d, poles)
            self.K = result.gain_matrix
            return self.K
        except Exception as e:
            logger.warning(f"Pole placement failed: {e}")
            # Simple fallback
            self.K = -np.ones((self.n_inputs, self.n_states)) * 0.5
            return self.K

    def design_observer(self, W: np.ndarray, V: np.ndarray) -> np.ndarray:
        """
        Design Kalman filter (observer) for LQG.
        Returns observer gain L.
        """
        A_d, B_d = self.discretize()

        # Solve for observer using duality
        # Observer problem is LQR for (A', C') with weights (W, V)
        from scipy.linalg import solve_discrete_are, inv

        try:
            P = solve_discrete_are(A_d.T, self.C.T, W, V)

            # L = P C^T (V + C P C^T)^(-1)
            self.L = P @ self.C.T @ inv(V + self.C @ P @ self.C.T)

            return self.L

        except Exception as e:
            logger.warning(f"Observer design failed: {e}, using fallback")
            # Simple observer gain
            self.L = np.ones((self.n_states, self.n_outputs)) * 0.1
            return self.L

    def update_observer(self, y: np.ndarray, u: np.ndarray):
        """
        Update state estimate using observer dynamics.
        """
        if self.L is None:
            return

        A_d, B_d = self.discretize()

        # x_hat[k+1] = A x_hat[k] + B u[k] + L (y[k] - C x_hat[k])
        y_pred = self.C @ self.x_hat
        innovation = y - y_pred

        self.x_hat = A_d @ self.x_hat + B_d @ u + self.L @ innovation

    def compute_control(
        self, x: np.ndarray, x_ref: np.ndarray = None, use_observer: bool = False
    ) -> np.ndarray:
        """
        Compute control input using state feedback.
        """
        if self.K is None:
            raise RuntimeError(
                "Controller gain not computed. Call solve_lqr() or place_poles() first."
            )

        # Use state estimate if observer is enabled
        if use_observer:
            x_eff = self.x_hat
        else:
            x_eff = x

        # Reference tracking
        if x_ref is not None:
            x_eff = x_eff - x_ref

        # u = -K x
        u = -self.K @ x_eff

        self.control_history.append(u.copy())

        return u


class StateSpacePattern:
    """
    State-space control pattern with LQR/LQG.

    Implements optimal control for linear systems using
    state-space representation.
    """

    PATTERN_ID = "state_space"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[StateSpaceConfig] = None):
        self.config = config or StateSpaceConfig()
        self.controller: Optional[StateSpaceController] = None
        self.history: Dict[str, List] = {
            "time": [],
            "state": [],
            "output": [],
            "control": [],
            "reference": [],
            "state_estimate": [],
        }

    def _initialize_controller(self):
        """Initialize state-space controller"""
        cfg = self.config

        self.controller = StateSpaceController(cfg.A, cfg.B, cfg.C, cfg.D, cfg.dt)

        # Design controller
        if cfg.control_method == ControlMethod.LQR:
            self.controller.solve_lqr(cfg.Q, cfg.R)
            logger.info("LQR controller designed")

        elif cfg.control_method == ControlMethod.POLE_PLACEMENT:
            if cfg.desired_poles is None:
                # Default stable poles
                cfg.desired_poles = [0.5 + 0.1j * i for i in range(cfg.A.shape[0])]
            self.controller.place_poles(cfg.desired_poles)
            logger.info("Pole placement controller designed")

        elif cfg.control_method == ControlMethod.DEADBEAT:
            # All poles at origin
            poles = [0.0] * cfg.A.shape[0]
            self.controller.place_poles(poles)
            logger.info("Deadbeat controller designed")

        # Design observer for LQG
        if cfg.control_method == ControlMethod.LQG:
            self.controller.solve_lqr(cfg.Q, cfg.R)
            self.controller.design_observer(cfg.W, cfg.V)
            logger.info("LQG controller and observer designed")

    def _get_reference(self, t: float) -> np.ndarray:
        """Get reference signal at time t"""
        cfg = self.config

        if cfg.reference_type == "constant":
            return cfg.reference_value
        elif cfg.reference_type == "sinusoid":
            freq = 0.5
            return cfg.reference_value * np.sin(2 * np.pi * freq * t)
        elif cfg.reference_type == "ramp":
            slope = 0.1
            return cfg.reference_value * slope * t
        else:
            return cfg.reference_value

    def _simulate_step(
        self, x: np.ndarray, u: np.ndarray, use_observer: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Simulate one time step"""
        cfg = self.config

        # Discrete dynamics
        A_d, B_d = self.controller.discretize()

        # Add process noise
        if cfg.control_method == ControlMethod.LQG:
            w = np.random.multivariate_normal(np.zeros(cfg.A.shape[0]), cfg.W)
        else:
            w = np.zeros(cfg.A.shape[0])

        # State update: x[k+1] = A x[k] + B u[k] + w[k]
        x_next = A_d @ x + B_d @ u + w

        # Measurement with noise
        if cfg.control_method == ControlMethod.LQG:
            v = np.random.multivariate_normal(np.zeros(cfg.C.shape[0]), cfg.V)
        else:
            v = np.zeros(cfg.C.shape[0])

        y = cfg.C @ x_next + cfg.D @ u + v

        # Update observer
        if use_observer:
            self.controller.update_observer(y, u)

        return x_next, y

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run state-space control simulation"""
        cfg = self.config

        logger.info(f"Starting state-space control: {cfg.control_method.value}")

        self._initialize_controller()

        use_observer = cfg.control_method == ControlMethod.LQG

        # Initialize state
        x = cfg.initial_state.copy()

        # Simulation loop
        for step in range(cfg.simulation_steps):
            t = step * cfg.dt

            # Get reference
            x_ref = self._get_reference(t)

            # Compute control
            u = self.controller.compute_control(x, x_ref, use_observer)

            # Simulate
            x, y = self._simulate_step(x, u, use_observer)

            # Record
            if step % cfg.output_interval == 0:
                self.history["time"].append(t)
                self.history["state"].append(x.copy())
                self.history["output"].append(y.copy())
                self.history["control"].append(u.copy())
                self.history["reference"].append(x_ref.copy())
                if use_observer:
                    self.history["state_estimate"].append(self.controller.x_hat.copy())

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        states = np.array(self.history["state"])
        controls = np.array(self.history["control"])
        outputs = np.array(self.history["output"])

        # Calculate performance metrics
        state_error = states - np.array(self.history["reference"])

        metrics = {
            "mean_state_error": float(np.mean(np.abs(state_error))),
            "max_state_error": float(np.max(np.abs(state_error))),
            "control_effort": float(np.sum(controls**2) * cfg.dt),
            "final_output": outputs[-1].tolist(),
            "final_state": states[-1].tolist(),
        }

        # Check stability
        A_d, _ = self.controller.discretize()
        A_cl = (
            A_d - self.controller.B @ self.controller.K
            if self.controller.K is not None
            else A_d
        )
        eigenvalues = np.linalg.eigvals(A_cl)

        return {
            "control_method": cfg.control_method.value,
            "system_type": cfg.system_type.value,
            "controller_gain": self.controller.K.tolist()
            if self.controller.K is not None
            else None,
            "observer_gain": self.controller.L.tolist()
            if self.controller.L is not None
            else None,
            "closed_loop_eigenvalues": eigenvalues.tolist(),
            "stability": "stable" if all(np.abs(eigenvalues) < 1) else "unstable",
            "performance_metrics": metrics,
            "history": {
                "time": self.history["time"],
                "state": [s.tolist() for s in self.history["state"]],
                "output": [o.tolist() for o in self.history["output"]],
                "control": [c.tolist() for c in self.history["control"]],
                "reference": [r.tolist() for r in self.history["reference"]],
            },
            "system_matrices": {
                "A": cfg.A.tolist(),
                "B": cfg.B.tolist(),
                "C": cfg.C.tolist(),
                "D": cfg.D.tolist(),
            },
            "lqr_weights": {
                "Q": cfg.Q.tolist(),
                "R": cfg.R.tolist(),
            },
            "config": {
                "dt": cfg.dt,
                "simulation_steps": cfg.simulation_steps,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "State Space Control",
            "category": "EXTENDED",
            "domain": ["Control Systems", "Robotics", "Aerospace"],
            "description": "LQR/LQG optimal control using state-space representation",
            "computational_complexity": "O(N³) for Riccati solve, O(N²) per step",
            "typical_runtime": "milliseconds to seconds",
            "accuracy": "High (optimal control)",
            "assumptions": [
                "Linear time-invariant (LTI) system",
                "Full state measurement or observable",
                "Gaussian noise for LQG",
            ],
            "parameters": [
                {
                    "name": "system_type",
                    "type": "enum",
                    "options": [
                        "double_integrator",
                        "inverted_pendulum",
                        "dc_motor",
                        "mass_spring_damper",
                    ],
                    "default": "double_integrator",
                },
                {
                    "name": "control_method",
                    "type": "enum",
                    "options": ["lqr", "lqg", "pole_placement", "deadbeat"],
                    "default": "lqr",
                },
                {"name": "dt", "type": "float", "default": 0.01},
                {"name": "simulation_steps", "type": "int", "default": 2000},
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestStateSpaceController(unittest.TestCase):
    """Unit tests for state-space controller"""

    def test_controller_initialization(self):
        """Test controller initialization"""
        A = np.array([[0, 1], [0, 0]])
        B = np.array([[0], [1]])
        C = np.array([[1, 0]])
        D = np.array([[0]])

        ctrl = StateSpaceController(A, B, C, D)
        self.assertEqual(ctrl.n_states, 2)
        self.assertEqual(ctrl.n_inputs, 1)

    def test_discretization(self):
        """Test system discretization"""
        A = np.array([[0, 1], [0, -1]])
        B = np.array([[0], [1]])
        C = np.array([[1, 0]])
        D = np.array([[0]])

        ctrl = StateSpaceController(A, B, C, D, dt=0.1)
        A_d, B_d = ctrl.discretize()

        # Check dimensions
        self.assertEqual(A_d.shape, A.shape)
        self.assertEqual(B_d.shape, B.shape)

        # Check that eigenvalues are preserved (approximately)
        eigs_c = np.linalg.eigvals(A)
        eigs_d = np.linalg.eigvals(A_d)
        # For small dt: z ≈ 1 + s*dt
        self.assertTrue(np.allclose(eigs_d, np.exp(eigs_c * 0.1), rtol=0.1))

    def test_lqr_design(self):
        """Test LQR controller design"""
        config = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR, control_method=ControlMethod.LQR
        )
        pattern = StateSpacePattern(config)
        pattern._initialize_controller()

        self.assertIsNotNone(pattern.controller.K)
        self.assertEqual(pattern.controller.K.shape, (1, 2))

    def test_pole_placement(self):
        """Test pole placement design"""
        config = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.POLE_PLACEMENT,
            desired_poles=[0.5, 0.6],
        )
        pattern = StateSpacePattern(config)
        pattern._initialize_controller()

        self.assertIsNotNone(pattern.controller.K)

    def test_observer_design(self):
        """Test observer/Kalman filter design"""
        config = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR, control_method=ControlMethod.LQG
        )
        pattern = StateSpacePattern(config)
        pattern._initialize_controller()

        self.assertIsNotNone(pattern.controller.K)
        self.assertIsNotNone(pattern.controller.L)

    def test_control_computation(self):
        """Test control computation"""
        config = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.LQR,
            simulation_steps=10,
        )
        pattern = StateSpacePattern(config)
        pattern._initialize_controller()

        x = np.array([1.0, 0.0])
        u = pattern.controller.compute_control(x)

        self.assertEqual(u.shape, (1,))

    def test_full_simulation_lqr(self):
        """Test complete LQR simulation"""
        config = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.LQR,
            simulation_steps=500,
            dt=0.01,
        )
        pattern = StateSpacePattern(config)
        result = pattern.run()

        self.assertEqual(result["control_method"], "lqr")
        self.assertIn("performance_metrics", result)
        self.assertIn("stability", result)

        # System should be stabilized
        final_state = result["performance_metrics"]["final_state"]
        self.assertLess(abs(final_state[0]), 2.0)  # Position bounded

    def test_full_simulation_lqg(self):
        """Test complete LQG simulation"""
        config = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=ControlMethod.LQG,
            simulation_steps=500,
        )
        pattern = StateSpacePattern(config)
        result = pattern.run()

        self.assertEqual(result["control_method"], "lqg")
        self.assertIsNotNone(result["observer_gain"])

    def test_inverted_pendulum(self):
        """Test inverted pendulum stabilization"""
        config = StateSpaceConfig(
            system_type=SystemType.INVERTED_PENDULUM,
            control_method=ControlMethod.LQR,
            simulation_steps=500,
            dt=0.01,
        )
        pattern = StateSpacePattern(config)
        result = pattern.run()

        self.assertEqual(result["system_type"], "inverted_pendulum")
        self.assertEqual(result["stability"], "stable")

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = StateSpacePattern.get_metadata()

        self.assertEqual(metadata["id"], "state_space")
        self.assertEqual(metadata["category"], "EXTENDED")
        self.assertIn("parameters", metadata)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("State Space Control Pattern Demo")
    print("=" * 60)

    for method in [ControlMethod.LQR, ControlMethod.LQG]:
        print(f"\n--- {method.value.upper()} Control ---")
        config = StateSpaceConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            control_method=method,
            simulation_steps=1000,
        )
        pattern = StateSpacePattern(config)
        result = pattern.run()

        print(f"Controller Gain K: {result['controller_gain']}")
        print(f"Stability: {result['stability']}")
        print(
            f"Mean State Error: {result['performance_metrics']['mean_state_error']:.4f}"
        )
        print(f"Control Effort: {result['performance_metrics']['control_effort']:.2f}")
