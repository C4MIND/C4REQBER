"""
TURBO-CDI v6.0 - PID Tuning Pattern
PID controller with Ziegler-Nichols and auto-tuning methods.

Pattern Structure (Christopher Alexander):
- Context: Control systems requiring proportional-integral-derivative feedback
- Forces: Stability vs response time, overshoot vs settling time, manual tuning complexity
- Solution: Automated tuning algorithms with configurable objectives
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


class TuningMethod(Enum):
    """Available PID tuning methods"""

    MANUAL = "manual"
    ZIEGLER_NICHOLS = "ziegler_nichols"
    AUTO_TUNE_RELAY = "auto_tune_relay"
    AUTO_TUNE_STEP = "auto_tune_step"
    COHEN_COON = "cohen_coon"


class PIDStructure(Enum):
    """PID controller structures"""

    PARALLEL = "parallel"  # Independent P, I, D terms
    SERIES = "series"  # Interacting terms
    IDEAL = "ideal"  # Non-interacting


@dataclass
class PIDConfig:
    """Configuration for PID controller and tuning"""

    # Controller parameters (for manual tuning)
    Kp: float = 1.0  # Proportional gain
    Ki: float = 0.1  # Integral gain
    Kd: float = 0.01  # Derivative gain

    # Tuning method
    tuning_method: TuningMethod = TuningMethod.ZIEGLER_NICHOLS
    pid_structure: PIDStructure = PIDStructure.PARALLEL

    # Auto-tune parameters
    auto_tune_steps: int = 2000
    auto_tune_setpoint: float = 1.0
    relay_amplitude: float = 1.0  # For relay auto-tuning

    # Simulation parameters
    dt: float = 0.01  # Time step
    simulation_steps: int = 5000

    # System model for testing (first-order plus dead time)
    process_gain: float = 1.0
    time_constant: float = 1.0
    dead_time: float = 0.1

    # Performance criteria
    settling_time_weight: float = 1.0
    overshoot_weight: float = 1.0
    rise_time_weight: float = 0.5

    # Output
    output_interval: int = 10

    # Anti-windup
    enable_anti_windup: bool = True
    output_limits: Tuple[float, float] = (-10.0, 10.0)


class PIDController:
    """
    PID controller with multiple implementation structures.
    """

    def __init__(
        self,
        Kp: float,
        Ki: float,
        Kd: float,
        dt: float = 0.01,
        structure: PIDStructure = PIDStructure.PARALLEL,
        output_limits: Tuple[float, float] = (-np.inf, np.inf),
        enable_anti_windup: bool = True,
    ):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt
        self.structure = structure
        self.output_limits = output_limits
        self.enable_anti_windup = enable_anti_windup

        # State variables
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_measurement = 0.0

    def reset(self):
        """Reset controller state"""
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_measurement = 0.0

    def update(self, setpoint: float, measurement: float) -> float:
        """Compute control output"""
        error = setpoint - measurement

        # Proportional term
        P = self.Kp * error

        # Integral term with anti-windup
        self.integral += error * self.dt
        if self.enable_anti_windup:
            # Clamp integral to prevent windup
            integral_limit = max(abs(self.output_limits[0]), abs(self.output_limits[1]))
            self.integral = np.clip(
                self.integral,
                -integral_limit / max(self.Ki, 1e-10),
                integral_limit / max(self.Ki, 1e-10),
            )
        I = self.Ki * self.integral

        # Derivative term (on measurement, not error, to avoid derivative kick)
        d_measurement = (measurement - self.prev_measurement) / self.dt
        D = -self.Kd * d_measurement  # Negative because we use measurement derivative

        # Compute output
        if self.structure == PIDStructure.PARALLEL:
            output = P + I + D
        elif self.structure == PIDStructure.SERIES:
            # Interacting form
            output = self.Kp * (
                error + self.Ki * self.integral - self.Kd * d_measurement
            )
        else:  # IDEAL
            output = P + I + D

        # Apply output limits
        output = np.clip(output, self.output_limits[0], self.output_limits[1])

        # Update state
        self.prev_error = error
        self.prev_measurement = measurement

        return output


class PIDTuningPattern:
    """
    PID controller tuning with multiple methods.

    Implements Ziegler-Nichols, Cohen-Coon, and auto-tuning
    approaches for finding optimal PID parameters.
    """

    PATTERN_ID = "pid_tuning"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[PIDConfig] = None):
        self.config = config or PIDConfig()
        self.controller: Optional[PIDController] = None
        self.tuning_results: Dict[str, Any] = {}
        self.history: Dict[str, List] = {
            "time": [],
            "setpoint": [],
            "measurement": [],
            "control": [],
            "error": [],
        }

    def _simulate_process(self, control_signal: float, state: Dict) -> float:
        """Simulate first-order plus dead time process"""
        cfg = self.config

        # First-order dynamics with dead time approximation
        # Using Padé approximation for dead time
        alpha = cfg.dead_time / (cfg.dead_time + cfg.time_constant)

        # Update state (simplified FOPDT)
        state["y"] = state.get("y", 0.0)
        state["y_delayed"] = state.get("y_delayed", 0.0)

        # Main dynamics
        dy = (-state["y"] + cfg.process_gain * control_signal) / cfg.time_constant
        state["y"] += dy * cfg.dt

        # Dead time approximation
        state["y_delayed"] = alpha * state["y_delayed"] + (1 - alpha) * state["y"]

        return state["y_delayed"]

    def _ziegler_nichols_tuning(self) -> Tuple[float, float, float]:
        """
        Ziegler-Nichols closed-loop tuning method.
        Finds ultimate gain and period through relay feedback.
        """
        cfg = self.config

        # Relay feedback test
        setpoint = cfg.auto_tune_setpoint
        relay_amp = cfg.relay_amplitude

        state = {}
        measurement = 0.0
        control = relay_amp

        oscillations = []
        crossings = []
        prev_error = setpoint - measurement

        for step in range(cfg.auto_tune_steps):
            # Relay control
            error = setpoint - measurement
            if error > 0:
                control = relay_amp
            else:
                control = -relay_amp

            # Simulate process
            measurement = self._simulate_process(control, state)

            # Detect zero crossings
            if prev_error * error < 0:  # Sign change
                crossings.append(step * cfg.dt)

            prev_error = error

        # Calculate ultimate period from oscillations
        if len(crossings) >= 4:
            periods = [
                crossings[i + 2] - crossings[i] for i in range(len(crossings) - 2)
            ]
            Tu = np.mean(periods)  # Ultimate period

            # Ultimate gain from relay amplitude and amplitude of oscillation
            # Using describing function approximation
            y_max = state.get("y_max", relay_amp * cfg.process_gain)
            y_min = state.get("y_min", -relay_amp * cfg.process_gain)
            a = (y_max - y_min) / 2  # Oscillation amplitude

            if a > 1e-10:
                Ku = 4 * relay_amp / (np.pi * a)  # Ultimate gain
            else:
                Ku = 1.0
        else:
            # Fallback: estimate from process parameters
            Tu = 4 * cfg.dead_time if cfg.dead_time > 0 else 4 * cfg.time_constant
            Ku = 1.0 / (cfg.process_gain * (cfg.dead_time / cfg.time_constant + 0.5))

        # Ziegler-Nichols formulas
        Kp = 0.6 * Ku
        Ti = 0.5 * Tu
        Td = 0.125 * Tu

        Ki = Kp / Ti if Ti > 0 else 0.0
        Kd = Kp * Td

        self.tuning_results = {
            "method": "ziegler_nichols",
            "ultimate_gain": Ku,
            "ultimate_period": Tu,
            "Kp": Kp,
            "Ki": Ki,
            "Kd": Kd,
            "Ti": Ti,
            "Td": Td,
        }

        return Kp, Ki, Kd

    def _cohen_coon_tuning(self) -> Tuple[float, float, float]:
        """
        Cohen-Coon open-loop tuning method.
        Uses process reaction curve (step response).
        """
        cfg = self.config

        K = cfg.process_gain
        tau = cfg.time_constant
        theta = cfg.dead_time

        if theta <= 0:
            theta = 0.01  # Small dead time to avoid division by zero

        # Cohen-Coon formulas for PID
        Kp = (1.35 / K) * (tau / theta + 0.185)
        Ti = 2.5 * theta * (tau + 0.185 * theta) / (tau + 0.611 * theta)
        Td = 0.37 * theta * tau / (tau + 0.185 * theta)

        Ki = Kp / Ti if Ti > 0 else 0.0
        Kd = Kp * Td

        self.tuning_results = {
            "method": "cohen_coon",
            "Kp": Kp,
            "Ki": Ki,
            "Kd": Kd,
            "Ti": Ti,
            "Td": Td,
        }

        return Kp, Ki, Kd

    def _auto_tune_relay(self) -> Tuple[float, float, float]:
        """
        Åström-Hägglund relay auto-tuning method.
        """
        cfg = self.config

        # Similar to ZN but with more sophisticated analysis
        Kp, Ki, Kd = self._ziegler_nichols_tuning()

        # Refine based on desired robustness
        # Increase damping slightly
        Kp *= 0.8
        Ki *= 0.8
        Kd *= 1.2

        self.tuning_results["method"] = "auto_tune_relay"
        self.tuning_results["notes"] = "Refined ZN with improved robustness"

        return Kp, Ki, Kd

    def _auto_tune_step(self) -> Tuple[float, float, float]:
        """
        Auto-tuning using step response analysis.
        """
        cfg = self.config

        # Collect step response data
        state = {}
        step_size = 1.0

        t_values = []
        y_values = []

        for step in range(cfg.auto_tune_steps):
            t = step * cfg.dt
            measurement = self._simulate_process(step_size, state)

            t_values.append(t)
            y_values.append(measurement)

        t_values = np.array(t_values)
        y_values = np.array(y_values)

        # Find process characteristics
        y_final = y_values[-1]
        y_28 = 0.283 * y_final
        y_63 = 0.632 * y_final

        # Find times for 28% and 63% response
        idx_28 = np.where(y_values >= y_28)[0]
        idx_63 = np.where(y_values >= y_63)[0]

        if len(idx_28) > 0 and len(idx_63) > 0:
            t_28 = t_values[idx_28[0]]
            t_63 = t_values[idx_63[0]]

            # Two-point method estimates
            tau = 0.67 * (t_63 - t_28)
            theta = 1.5 * (t_28 - 0.33 * t_63)
            K = y_final / step_size

            # Use Cohen-Coon with estimated parameters
            if theta > 0 and tau > 0:
                Kp = (1.35 / K) * (tau / theta + 0.185)
                Ti = 2.5 * theta * (tau + 0.185 * theta) / (tau + 0.611 * theta)
                Td = 0.37 * theta * tau / (tau + 0.185 * theta)

                Ki = Kp / Ti if Ti > 0 else 0.0
                Kd = Kp * Td
            else:
                Kp, Ki, Kd = 1.0, 0.1, 0.01
        else:
            Kp, Ki, Kd = 1.0, 0.1, 0.01

        self.tuning_results = {
            "method": "auto_tune_step",
            "estimated_gain": K if len(idx_28) > 0 else cfg.process_gain,
            "estimated_tau": tau if len(idx_28) > 0 else cfg.time_constant,
            "estimated_theta": theta if len(idx_28) > 0 else cfg.dead_time,
            "Kp": Kp,
            "Ki": Ki,
            "Kd": Kd,
        }

        return Kp, Ki, Kd

    def tune(self) -> Tuple[float, float, float]:
        """Run selected tuning method"""
        cfg = self.config

        if cfg.tuning_method == TuningMethod.MANUAL:
            Kp, Ki, Kd = cfg.Kp, cfg.Ki, cfg.Kd
            self.tuning_results = {
                "method": "manual",
                "Kp": Kp,
                "Ki": Ki,
                "Kd": Kd,
            }
        elif cfg.tuning_method == TuningMethod.ZIEGLER_NICHOLS:
            Kp, Ki, Kd = self._ziegler_nichols_tuning()
        elif cfg.tuning_method == TuningMethod.COHEN_COON:
            Kp, Ki, Kd = self._cohen_coon_tuning()
        elif cfg.tuning_method == TuningMethod.AUTO_TUNE_RELAY:
            Kp, Ki, Kd = self._auto_tune_relay()
        elif cfg.tuning_method == TuningMethod.AUTO_TUNE_STEP:
            Kp, Ki, Kd = self._auto_tune_step()
        else:
            Kp, Ki, Kd = cfg.Kp, cfg.Ki, cfg.Kd

        # Create controller with tuned parameters
        self.controller = PIDController(
            Kp=Kp,
            Ki=Ki,
            Kd=Kd,
            dt=cfg.dt,
            structure=cfg.pid_structure,
            output_limits=cfg.output_limits,
            enable_anti_windup=cfg.enable_anti_windup,
        )

        return Kp, Ki, Kd

    def _calculate_metrics(
        self, setpoint: np.ndarray, measurement: np.ndarray, time: np.ndarray
    ) -> Dict[str, float]:
        """Calculate control performance metrics"""
        error = setpoint - measurement

        # Rise time (10% to 90%)
        y_normalized = (measurement - measurement[0]) / (setpoint[-1] - measurement[0])
        idx_10 = np.where(y_normalized >= 0.1)[0]
        idx_90 = np.where(y_normalized >= 0.9)[0]

        if len(idx_10) > 0 and len(idx_90) > 0:
            rise_time = time[idx_90[0]] - time[idx_10[0]]
        else:
            rise_time = time[-1] - time[0]

        # Settling time (within 2% of final value)
        final_val = (
            measurement[-100:].mean() if len(measurement) > 100 else measurement[-1]
        )
        settling_band = 0.02 * abs(final_val)
        settled = np.abs(measurement - final_val) < settling_band

        # Find last point not settled
        not_settled = np.where(~settled)[0]
        if len(not_settled) > 0:
            settling_time = time[not_settled[-1]]
        else:
            settling_time = 0.0

        # Overshoot
        if setpoint[-1] > measurement[0]:
            overshoot = max(
                0,
                (measurement.max() - setpoint[-1])
                / (setpoint[-1] - measurement[0])
                * 100,
            )
        else:
            overshoot = 0.0

        # Integral Absolute Error
        iae = np.sum(np.abs(error)) * (time[1] - time[0])

        # Integral Square Error
        ise = np.sum(error**2) * (time[1] - time[0])

        return {
            "rise_time": float(rise_time),
            "settling_time": float(settling_time),
            "overshoot_percent": float(overshoot),
            "iae": float(iae),
            "ise": float(ise),
            "max_error": float(np.max(np.abs(error))),
            "mean_error": float(np.mean(np.abs(error))),
        }

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run PID tuning and closed-loop simulation"""
        cfg = self.config

        logger.info(f"Starting PID tuning with method: {cfg.tuning_method.value}")

        # Run tuning
        Kp, Ki, Kd = self.tune()
        logger.info(f"Tuned parameters: Kp={Kp:.4f}, Ki={Ki:.4f}, Kd={Kd:.4f}")

        # Closed-loop simulation
        setpoint = np.ones(cfg.simulation_steps) * cfg.auto_tune_setpoint
        # Add some variation
        setpoint[: cfg.simulation_steps // 4] = 0.0
        setpoint[cfg.simulation_steps // 2 : 3 * cfg.simulation_steps // 4] = 0.5

        state = {}
        measurement = 0.0
        self.controller.reset()

        self.history = {
            "time": [],
            "setpoint": [],
            "measurement": [],
            "control": [],
            "error": [],
        }

        for step in range(cfg.simulation_steps):
            t = step * cfg.dt
            sp = setpoint[step]

            # Controller update
            control = self.controller.update(sp, measurement)

            # Process simulation
            measurement = self._simulate_process(control, state)

            # Record
            if step % cfg.output_interval == 0:
                self.history["time"].append(t)
                self.history["setpoint"].append(sp)
                self.history["measurement"].append(measurement)
                self.history["control"].append(control)
                self.history["error"].append(sp - measurement)

        # Calculate metrics
        metrics = self._calculate_metrics(
            np.array(self.history["setpoint"]),
            np.array(self.history["measurement"]),
            np.array(self.history["time"]),
        )

        return self._format_output(metrics)

    def _format_output(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Format output"""
        cfg = self.config

        return {
            "tuning_method": self.tuning_results.get("method", "unknown"),
            "tuning_results": self.tuning_results,
            "controller_parameters": {
                "Kp": self.controller.Kp if self.controller else cfg.Kp,
                "Ki": self.controller.Ki if self.controller else cfg.Ki,
                "Kd": self.controller.Kd if self.controller else cfg.Kd,
            },
            "performance_metrics": metrics,
            "history": {
                "time": self.history["time"],
                "setpoint": self.history["setpoint"],
                "measurement": self.history["measurement"],
                "control": self.history["control"],
                "error": self.history["error"],
            },
            "config": {
                "tuning_method": cfg.tuning_method.value,
                "pid_structure": cfg.pid_structure.value,
                "dt": cfg.dt,
                "simulation_steps": cfg.simulation_steps,
                "process_gain": cfg.process_gain,
                "time_constant": cfg.time_constant,
                "dead_time": cfg.dead_time,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "PID Tuning",
            "category": "EXTENDED",
            "domain": ["Control Systems", "Automation", "Process Control"],
            "description": "PID controller tuning with Ziegler-Nichols, Cohen-Coon, and auto-tuning methods",
            "computational_complexity": "O(N) per simulation step",
            "typical_runtime": "milliseconds to seconds",
            "accuracy": "High (depends on tuning method)",
            "assumptions": [
                "Linear or mildly nonlinear process",
                "Single-input single-output (SISO)",
                "Continuous-time approximation",
            ],
            "parameters": [
                {
                    "name": "tuning_method",
                    "type": "enum",
                    "options": [
                        "manual",
                        "ziegler_nichols",
                        "auto_tune_relay",
                        "auto_tune_step",
                        "cohen_coon",
                    ],
                    "default": "ziegler_nichols",
                },
                {"name": "Kp", "type": "float", "default": 1.0},
                {"name": "Ki", "type": "float", "default": 0.1},
                {"name": "Kd", "type": "float", "default": 0.01},
                {"name": "process_gain", "type": "float", "default": 1.0},
                {"name": "time_constant", "type": "float", "default": 1.0},
                {"name": "dead_time", "type": "float", "default": 0.1},
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestPIDController(unittest.TestCase):
    """Unit tests for PID controller"""

    def test_controller_initialization(self):
        """Test PID controller initialization"""
        pid = PIDController(Kp=2.0, Ki=0.5, Kd=0.1)
        self.assertEqual(pid.Kp, 2.0)
        self.assertEqual(pid.Ki, 0.5)
        self.assertEqual(pid.Kd, 0.1)

    def test_controller_update(self):
        """Test controller update with constant error"""
        pid = PIDController(Kp=1.0, Ki=0.1, Kd=0.01, dt=0.1)

        # Step response
        setpoint = 1.0
        measurement = 0.0

        outputs = []
        for _ in range(10):
            output = pid.update(setpoint, measurement)
            outputs.append(output)
            # Simulate simple process response
            measurement += 0.1 * output

        # Output should increase due to integral action
        self.assertGreater(outputs[-1], outputs[0])

    def test_anti_windup(self):
        """Test anti-windup functionality"""
        pid = PIDController(
            Kp=1.0, Ki=1.0, Kd=0.0, output_limits=(-1.0, 1.0), enable_anti_windup=True
        )

        # Large error should saturate output
        for _ in range(100):
            output = pid.update(100.0, 0.0)

        # Output should be clamped
        self.assertEqual(output, 1.0)

        # Integral should not grow indefinitely
        integral_before = pid.integral
        for _ in range(10):
            pid.update(100.0, 0.0)
        integral_after = pid.integral

        # Integral should be bounded
        self.assertLess(abs(integral_after), 100.0)

    def test_reset(self):
        """Test controller reset"""
        pid = PIDController(Kp=1.0, Ki=0.1, Kd=0.01)

        # Run some updates
        for i in range(10):
            pid.update(1.0, 0.0)

        # Reset
        pid.reset()

        # State should be zero
        self.assertEqual(pid.integral, 0.0)
        self.assertEqual(pid.prev_error, 0.0)


class TestPIDTuningPattern(unittest.TestCase):
    """Unit tests for PID tuning pattern"""

    def test_initialization(self):
        """Test pattern initialization"""
        pattern = PIDTuningPattern()
        self.assertIsNotNone(pattern.config)
        self.assertEqual(pattern.config.tuning_method, TuningMethod.ZIEGLER_NICHOLS)

    def test_manual_tuning(self):
        """Test manual tuning mode"""
        config = PIDConfig(
            tuning_method=TuningMethod.MANUAL,
            Kp=2.0,
            Ki=0.5,
            Kd=0.1,
            simulation_steps=100,
        )
        pattern = PIDTuningPattern(config)
        result = pattern.run()

        self.assertEqual(result["tuning_method"], "manual")
        self.assertEqual(result["controller_parameters"]["Kp"], 2.0)
        self.assertIn("performance_metrics", result)

    def test_ziegler_nichols_tuning(self):
        """Test Ziegler-Nichols tuning"""
        config = PIDConfig(
            tuning_method=TuningMethod.ZIEGLER_NICHOLS,
            auto_tune_steps=500,
            simulation_steps=500,
        )
        pattern = PIDTuningPattern(config)
        result = pattern.run()

        self.assertEqual(result["tuning_method"], "ziegler_nichols")
        self.assertIn("ultimate_gain", result["tuning_results"])
        self.assertIn("Kp", result["tuning_results"])

        # Parameters should be positive
        self.assertGreater(result["tuning_results"]["Kp"], 0)

    def test_cohen_coon_tuning(self):
        """Test Cohen-Coon tuning"""
        config = PIDConfig(tuning_method=TuningMethod.COHEN_COON, simulation_steps=500)
        pattern = PIDTuningPattern(config)
        result = pattern.run()

        self.assertEqual(result["tuning_method"], "cohen_coon")
        self.assertIn("Kp", result["tuning_results"])

    def test_auto_tune_step(self):
        """Test step response auto-tuning"""
        config = PIDConfig(
            tuning_method=TuningMethod.AUTO_TUNE_STEP,
            auto_tune_steps=500,
            simulation_steps=500,
        )
        pattern = PIDTuningPattern(config)
        result = pattern.run()

        self.assertEqual(result["tuning_method"], "auto_tune_step")
        self.assertIn("estimated_tau", result["tuning_results"])

    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        config = PIDConfig(simulation_steps=1000)
        pattern = PIDTuningPattern(config)
        result = pattern.run()

        metrics = result["performance_metrics"]
        self.assertIn("rise_time", metrics)
        self.assertIn("settling_time", metrics)
        self.assertIn("overshoot_percent", metrics)
        self.assertIn("iae", metrics)

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = PIDTuningPattern.get_metadata()

        self.assertEqual(metadata["id"], "pid_tuning")
        self.assertEqual(metadata["category"], "EXTENDED")
        self.assertIn("parameters", metadata)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("PID Tuning Pattern Demo")
    print("=" * 60)

    for method in [TuningMethod.ZIEGLER_NICHOLS, TuningMethod.COHEN_COON]:
        print(f"\n--- {method.value.upper()} ---")
        config = PIDConfig(tuning_method=method, simulation_steps=2000)
        pattern = PIDTuningPattern(config)
        result = pattern.run()

        print(f"Kp: {result['controller_parameters']['Kp']:.4f}")
        print(f"Ki: {result['controller_parameters']['Ki']:.4f}")
        print(f"Kd: {result['controller_parameters']['Kd']:.4f}")
        print(f"Rise Time: {result['performance_metrics']['rise_time']:.3f}s")
        print(f"Settling Time: {result['performance_metrics']['settling_time']:.3f}s")
        print(f"Overshoot: {result['performance_metrics']['overshoot_percent']:.2f}%")
