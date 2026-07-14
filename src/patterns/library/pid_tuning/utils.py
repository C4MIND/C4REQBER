"""
C4REQBER v6.0 - PID Tuning Pattern[str] - Utilities
Helper functions and the PIDController class.
"""


import numpy as np

from .config import PIDStructure


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
        output_limits: tuple[float, float] = (-np.inf, np.inf),
        enable_anti_windup: bool = True,
    ) -> None:
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

    def reset(self) -> None:
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
        if self.dt > 0:
            d_measurement = (measurement - self.prev_measurement) / self.dt
        else:
            d_measurement = 0.0
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

        # Apply output limits (handle reversed limits gracefully)
        lo, hi = self.output_limits
        if lo > hi:
            lo, hi = hi, lo
        output = np.clip(output, lo, hi)

        # Update state
        self.prev_error = error
        self.prev_measurement = measurement

        return float(output)
