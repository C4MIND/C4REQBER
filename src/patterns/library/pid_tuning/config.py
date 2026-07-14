"""
C4REQBER v6.0 - PID Tuning Pattern[str] - Configuration
Enums and PIDConfig dataclass for PID controller configuration.
"""

from dataclasses import dataclass
from enum import Enum


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
    output_limits: tuple[float, float] = (-10.0, 10.0)
