"""
C4REQBER v6.0 - PID Tuning Pattern[str] - Core
Tuning algorithms and main PIDTuningPattern class.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .config import PIDConfig, TuningMethod
from .utils import PIDController


logger = logging.getLogger(__name__)

class PIDTuningPattern:
    """
    PID controller tuning with multiple methods.

    Implements Ziegler-Nichols, Cohen-Coon, and auto-tuning
    approaches for finding optimal PID parameters.
    """

    PATTERN_ID = "pid_tuning"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: PIDConfig | None = None) -> None:
        self.config = config or PIDConfig()
        self.controller: PIDController | None = None
        self.tuning_results: dict[str, Any] = {}
        self.history: dict[str, list[Any]] = {
            "time": [],
            "setpoint": [],
            "measurement": [],
            "control": [],
            "error": [],
        }

    def _simulate_process(self, control_signal: float, state: dict[str, Any]) -> float:
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

        return float(state["y_delayed"])

    def _ziegler_nichols_tuning(self) -> tuple[float, float, float]:
        """
        Ziegler-Nichols closed-loop tuning method.
        Finds ultimate gain and period through relay feedback.
        """
        cfg = self.config

        # Relay feedback test
        setpoint = cfg.auto_tune_setpoint
        relay_amp = cfg.relay_amplitude

        state: dict[str, Any] = {}
        measurement = 0.0
        control = relay_amp

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
            Tu = 4 * cfg.dead_time if cfg.dead_time > 0 else 4 * cfg.time_constant  # type: ignore[assignment]
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

    def _cohen_coon_tuning(self) -> tuple[float, float, float]:
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

    def _auto_tune_relay(self) -> tuple[float, float, float]:
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

    def _auto_tune_step(self) -> tuple[float, float, float]:
        """
        Auto-tuning using step response analysis.
        """
        cfg = self.config

        # Collect step response data
        state: dict[str, Any] = {}
        step_size = 1.0

        t_values = []
        y_values = []

        for step in range(cfg.auto_tune_steps):
            t = step * cfg.dt
            measurement = self._simulate_process(step_size, state)

            t_values.append(t)
            y_values.append(measurement)

        t_values = np.array(t_values)  # type: ignore[assignment]
        y_values = np.array(y_values)  # type: ignore[assignment]

        # Find process characteristics
        y_final = y_values[-1]
        y_28 = 0.283 * y_final
        y_63 = 0.632 * y_final

        # Find times for 28% and 63% response
        idx_28 = np.where(y_values >= y_28)[0]  # type: ignore[operator]
        idx_63 = np.where(y_values >= y_63)[0]  # type: ignore[operator]

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

    def tune(self) -> tuple[float, float, float]:
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

            Kp, Ki, Kd = cfg.Kp, cfg.Ki, cfg.Kd  # type: ignore[unreachable]

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
    ) -> dict[str, float]:
        """Calculate control performance metrics"""
        error = setpoint - measurement

        # Handle single-point arrays
        if len(time) < 2:
            return {
                "rise_time": 0.0,
                "settling_time": 0.0,
                "overshoot_percent": 0.0,
                "iae": float(np.sum(np.abs(error))),
                "ise": float(np.sum(error**2)),
                "max_error": float(np.max(np.abs(error))) if len(error) > 0 else 0.0,
                "mean_error": float(np.mean(np.abs(error))) if len(error) > 0 else 0.0,
            }

        # Rise time (10% to 90%)
        denom = setpoint[-1] - measurement[0]
        if abs(denom) > 1e-12:
            y_normalized = (measurement - measurement[0]) / denom
        else:
            y_normalized = np.zeros_like(measurement)
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

        dt = time[1] - time[0] if len(time) > 1 else 1.0
        # Integral Absolute Error
        iae = np.sum(np.abs(error)) * dt

        # Integral Square Error
        ise = np.sum(error**2) * dt

        return {
            "rise_time": float(rise_time),
            "settling_time": float(settling_time),
            "overshoot_percent": float(overshoot),
            "iae": float(iae),
            "ise": float(ise),
            "max_error": float(np.max(np.abs(error))),
            "mean_error": float(np.mean(np.abs(error))),
        }

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
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

        state: Any = {}
        measurement = 0.0
        self.controller.reset()  # type: ignore[union-attr]

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
            control = self.controller.update(sp, measurement)  # type: ignore[union-attr]

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

    def _format_output(self, metrics: dict[str, float]) -> dict[str, Any]:
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
    def get_metadata(cls) -> dict[str, Any]:
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
