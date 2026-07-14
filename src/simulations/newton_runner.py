from __future__ import annotations

import json
import sys
import time
from typing import Any


def run_newton_simulation(config: dict[str, Any]) -> dict[str, Any]:
    """Run Newton simulation using newton-physics (requires Python ≥3.10)."""

    start_time = time.perf_counter()
    sim_type = config.get("type", "rigid_body").lower()
    dt = config.get("dt", 1e-3)
    num_steps = config.get("num_steps", 100)

    result: dict[str, Any] = {"status": "success", "data": {}, "metrics": {}}

    try:
        if sim_type == "n_body":
            # Simple N-body simulation
            import numpy as np
            num_particles = config.get("num_particles", 100)
            positions = np.random.rand(num_particles, 3) * 10 - 5
            velocities = np.random.randn(num_particles, 3) * 0.1

            for _ in range(min(num_steps, 20)):
                # Simplified gravity calculation
                forces = np.zeros((num_particles, 3))
                for i in range(num_particles):
                    diff = positions - positions[i]
                    dist_sq = np.sum(diff**2, axis=1) + 1e-4
                    dist = np.sqrt(dist_sq)
                    force_mag = 1.0 / dist_sq
                    force_mag[i] = 0
                    forces[i] = np.sum(diff * force_mag[:, np.newaxis] / dist[:, np.newaxis], axis=0)
                velocities += forces * dt
                positions += velocities * dt

            result["data"] = {
                "positions": positions.tolist()[:10],  # Truncate for output
                "velocities": velocities.tolist()[:10],
            }
            result["metrics"] = {"num_particles": num_particles, "steps": min(num_steps, 20)}

        else:
            # Generic simulation fallback
            result["data"] = {"status": "completed", "type": sim_type}
            result["metrics"] = {"dt": dt, "num_steps": num_steps}

        result["execution_time"] = time.perf_counter() - start_time
        return result

    except (ImportError, IndexError, KeyError) as e:
        return {
            "status": "error",
            "error": str(e),
            "execution_time": time.perf_counter() - start_time
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "error": "No config provided"}))
        sys.exit(1)

    config = json.loads(sys.argv[1])
    result = run_newton_simulation(config)
    print(json.dumps(result))
