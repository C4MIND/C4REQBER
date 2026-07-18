from __future__ import annotations

import json
import os
import sys
import time
from typing import Any


def _configure_warp_cache() -> None:
    cache = os.environ.get("WARP_CACHE_DIR") or os.environ.get("WARP_CACHE_PATH")
    if not cache:
        # Prefer project-local cache when running from repo
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(here, "..", ".."))
        cache = os.path.join(root, ".cache", "warp")
    os.makedirs(cache, exist_ok=True)
    os.environ.setdefault("WARP_CACHE_DIR", cache)
    os.environ.setdefault("WARP_CACHE_PATH", cache)


def _run_newton_physics(config: dict[str, Any], start_time: float) -> dict[str, Any]:
    """Real newton.ModelBuilder + SolverXPBD step loop."""
    _configure_warp_cache()
    import logging as _logging

    _logging.getLogger("warp").setLevel(_logging.ERROR)
    import newton
    import warp as wp

    # Quiet Warp banner noise so subprocess stdout stays JSON-parseable
    try:
        wp.config.verbose = False
    except Exception:
        pass

    device = str(config.get("device") or "cpu")
    if device.startswith("cuda") and not getattr(wp, "is_cuda_available", lambda: False)():
        device = "cpu"
    wp.set_device(device)

    sim_type = str(config.get("type", "rigid_body")).lower()
    dt = float(config.get("dt", 1.0 / 60.0))
    num_steps = int(config.get("num_steps", 60))
    height = float(config.get("height", config.get("z0", 2.0)))
    radius = float(config.get("radius", 0.5))

    builder = newton.ModelBuilder()
    if config.get("ground", True) and sim_type in {
        "rigid_body",
        "sphere",
        "drop",
        "cfd",
        "continuum",
    }:
        # Rigid drop is the wired real path; CFD/continuum refuse empty completed.
        if sim_type not in {"rigid_body", "sphere", "drop", "n_body"}:
            return {
                "status": "unavailable",
                "backend": "newton_physics",
                "engine_truth": "newton_physics",
                "executed": False,
                "stub": True,
                "error": f"type={sim_type!r} not wired to Newton solvers yet (use rigid_body/drop/n_body)",
                "execution_time": time.perf_counter() - start_time,
                "data": {},
                "metrics": {"type": sim_type},
            }
        builder.add_ground_plane()

    if sim_type == "n_body":
        # Approximate N free spheres under gravity (not astrophysical N-body)
        n = min(int(config.get("num_particles", 4)), 16)
        for i in range(n):
            x = (i % 4) * 0.6 - 0.9
            y = (i // 4) * 0.6
            body = builder.add_body(
                xform=wp.transform((x, y, height + i * 0.05), wp.quat_identity())
            )
            builder.add_shape_sphere(body, radius=max(0.1, radius * 0.4))
    else:
        body = builder.add_body(xform=wp.transform((0.0, 0.0, height), wp.quat_identity()))
        builder.add_shape_sphere(body, radius=radius)

    model = builder.finalize(device=device)
    solver = newton.solvers.SolverXPBD(model, iterations=int(config.get("iterations", 5)))
    state_0 = model.state()
    state_1 = model.state()
    control = model.control()
    contacts = model.contacts()

    z0 = float(state_0.body_q.numpy()[0][2])
    for _ in range(num_steps):
        state_0.clear_forces()
        model.collide(state_0, contacts)
        solver.step(state_0, state_1, control, contacts, dt)
        state_0, state_1 = state_1, state_0

    body_q = state_0.body_q.numpy()
    positions = [[float(p[0]), float(p[1]), float(p[2])] for p in body_q]
    z1 = positions[0][2]

    return {
        "status": "success",
        "backend": "newton_physics",
        "engine_truth": "newton_physics",
        "executed": True,
        "stub": False,
        "data": {
            "positions": positions[:16],
            "z0": z0,
            "z_final": z1,
            "fell": z1 < z0 - 1e-4,
            "body_count": int(model.body_count),
            "device": device,
            "type": sim_type if sim_type != "n_body" else "multi_sphere_drop",
        },
        "metrics": {
            "num_steps": num_steps,
            "dt": dt,
            "body_count": int(model.body_count),
            "backend": "newton_physics",
        },
        "execution_time": time.perf_counter() - start_time,
        "note": "Newton SolverXPBD real step loop",
    }


def run_newton_simulation(config: dict[str, Any]) -> dict[str, Any]:
    """Run simulation: prefer real newton; NumPy n-body only if forced or import fails."""
    start_time = time.perf_counter()
    sim_type = str(config.get("type", "rigid_body")).lower()
    prefer_numpy = bool(config.get("force_numpy_fallback"))

    if not prefer_numpy:
        try:
            return _run_newton_physics(config, start_time)
        except ImportError as e:
            if sim_type not in {"n_body", "rigid_body", "sphere", "drop"}:
                return {
                    "status": "unavailable",
                    "backend": "missing",
                    "engine_truth": "not_newton_physics",
                    "executed": False,
                    "stub": True,
                    "error": f"newton not importable: {e}",
                    "execution_time": time.perf_counter() - start_time,
                    "data": {},
                    "metrics": {},
                }
            # fall through to numpy n_body only
        except Exception as e:
            return {
                "status": "error",
                "backend": "newton_physics",
                "engine_truth": "newton_physics",
                "executed": False,
                "stub": True,
                "error": str(e),
                "execution_time": time.perf_counter() - start_time,
                "data": {},
                "metrics": {},
            }

    # Honest NumPy gravitational N-body only (never for CFD/etc.)
    if sim_type != "n_body":
        return {
            "status": "unavailable",
            "backend": "numpy_fallback",
            "engine_truth": "not_newton_physics",
            "executed": False,
            "stub": True,
            "error": (
                f"No Newton path for type={sim_type!r} "
                "(numpy fallback is n_body-only; refusing empty completed)"
            ),
            "execution_time": time.perf_counter() - start_time,
            "data": {},
            "metrics": {},
        }

    try:
        import numpy as np

        dt = float(config.get("dt", 1e-3))
        num_steps = int(config.get("num_steps", 100))
        num_particles = int(config.get("num_particles", 100))
        positions = np.random.rand(num_particles, 3) * 10 - 5
        velocities = np.random.randn(num_particles, 3) * 0.1
        steps_run = min(num_steps, 20)

        for _ in range(steps_run):
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

        return {
            "status": "partial",
            "backend": "numpy_fallback",
            "engine_truth": "not_newton_physics",
            "executed": True,
            "stub": False,
            "data": {
                "positions": positions.tolist()[:10],
                "velocities": velocities.tolist()[:10],
            },
            "metrics": {"num_particles": num_particles, "steps": steps_run},
            "execution_time": time.perf_counter() - start_time,
            "note": "NumPy n-body — not newton.ModelBuilder",
        }
    except Exception as e:
        return {
            "status": "error",
            "backend": "error",
            "engine_truth": "not_newton_physics",
            "executed": False,
            "stub": True,
            "error": str(e),
            "execution_time": time.perf_counter() - start_time,
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Also accept --config path for Vast remote runner
        if "--config" in sys.argv:
            idx = sys.argv.index("--config")
            with open(sys.argv[idx + 1], encoding="utf-8") as f:
                config = json.load(f)
        else:
            print(json.dumps({"status": "error", "error": "No config provided"}))
            sys.exit(1)
    else:
        arg = sys.argv[1]
        if arg == "--config":
            with open(sys.argv[2], encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = json.loads(arg)
    result = run_newton_simulation(config)
    print(json.dumps(result))
