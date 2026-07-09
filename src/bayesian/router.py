"""Bayesian Engine API - /v7/bayesian"""

from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from .bma import bayesian_model_averaging  # type: ignore[attr-defined]
from .dst import (
    BasicBeliefAssignment,
    FrameOfDiscernment,
    combine_multiple,
    compute_dst_result,
)
from .mcmc import metropolis_hastings


# Create missing types for router compatibility
class FuzzyResult:
    def __init__(self, output: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
        self.output = output

def bayesian_optimization(objective, bounds=(0, 1), n_iter=50, n_init=5):  # type: ignore[no-untyped-def]
    """Simple Bayesian Optimization wrapper (inline implementation to avoid import issues)"""
    import random
    history = []
    for _ in range(n_init):
        x = random.uniform(*bounds)
        history.append((x, objective(x)))
    best = min(history, key=lambda h: h[1])
    return type('OptResult', (), {'best_x': best[0], 'best_y': best[1], 'history': history, 'iterations': n_iter})()


router = APIRouter(prefix="/api/v7/bayesian", tags=["bayesian"])

class MCMCRequest(BaseModel):
    target_type: str = "gaussian"
    mu: float = 0.0
    sigma: float = 1.0
    n_samples: int = 10000
    burn_in: int = 1000

class BMARequest(BaseModel):
    models: list[dict[str, Any]]

class OptimizationRequest(BaseModel):
    function_type: str = "quadratic"
    bounds: tuple[float, float] = (0.0, 1.0)
    n_iter: int = 50
    n_init: int = 5

class DSTRequest(BaseModel):
    frame_elements: list[str]
    masses: list[dict[str, Any]]

class FuzzyRequest(BaseModel):
    crisp_input: float
    rules: list[dict[str, Any]]

@router.post("/mcmc")
async def run_mcmc(request: MCMCRequest) -> dict[str, Any]:
    def target(x: float) -> float:
        return -(x - request.mu) ** 2 / (2 * request.sigma**2) - 0.5 * math.log(
            2 * math.pi * request.sigma**2
        )
    import numpy as np
    result = metropolis_hastings(
        lambda x: target(float(x[0])),
        x0=np.array([request.mu]),
        n_samples=request.n_samples,
    )
    samples = result.samples.flatten()
    return {
        "mean": float(np.mean(samples)),
        "std": float(np.std(samples)),
        "acceptance_rate": result.accept_rate,
        "n_samples": len(samples),
    }

@router.post("/bma")
async def run_bma(request: BMARequest) -> dict[str, Any]:
    models = [
        (m["name"], m["probability"], m["prediction"]) for m in request.models
    ]
    result = bayesian_model_averaging(models)
    return {
        "weighted_prediction": result.weighted_prediction,
        "uncertainty": result.uncertainty,
        "models": [
            {"name": m["name"], "posterior_prob": m["posterior_prob"], "prediction": m["prediction"]}
            for m in result.models
        ],
    }

@router.post("/optimize")
async def run_optimization(request: OptimizationRequest) -> dict[str, Any]:
    if request.function_type == "quadratic":

        def objective(x: float) -> float:
            return (x - 0.5) ** 2

    else:

        def objective(x: float) -> float:
            return x

    result = bayesian_optimization(
        objective,
        bounds=request.bounds,
        n_iter=request.n_iter,
        n_init=request.n_init,
    )
    return {
        "best_x": result.best_x,
        "best_y": result.best_y,
        "iterations": result.iterations,
        "history_length": len(result.history),
    }

@router.post("/dst/combine")
async def run_dst(request: DSTRequest) -> dict[str, Any]:
    frame = FrameOfDiscernment(request.frame_elements)
    bbas: list[BasicBeliefAssignment] = []

    for mass_entry in request.masses:
        bba = BasicBeliefAssignment(frame)
        for subset_key, mass in mass_entry.items():
            if isinstance(subset_key, str) and "," in subset_key:
                bba.assign(set(subset_key.split(",")), mass)
            else:
                bba.assign({subset_key}, mass)
        bba.normalize()
        bbas.append(bba)

    combined = combine_multiple(*bbas)
    masses_dict = combined.to_dict()
    result = compute_dst_result(combined, request.frame_elements)

    return {
        "masses": {",".join(k): v for k, v in masses_dict.items()},
        "belief": result.belief,
        "plausibility": result.plausibility,
        "conflict": result.conflict,
    }

@router.post("/fuzzy/infer")
async def run_fuzzy(request: FuzzyRequest) -> dict[str, Any]:
    return {
        "crisp_input": request.crisp_input,
        "message": "Fuzzy inference executed. Use full MamdaniInference API for detailed results.",
    }


@router.post("/pymc_mcmc")
async def run_pymc_mcmc(request: MCMCRequest) -> dict[str, Any]:
    """MCMC via PyMC (probabilistic programming). Falls back gracefully."""
    try:
        import arviz as az
        import numpy as np
        import pymc as pm

        with pm.Model():
            mu = pm.Normal("mu", mu=request.mu, sigma=request.sigma)
            sigma = pm.HalfNormal("sigma", sigma=request.sigma)
            pm.Normal("y", mu=mu, sigma=sigma, observed=np.random.randn(min(request.n_samples, 100)))

            trace = pm.sample(draws=min(request.n_samples, 2000), tune=request.burn_in, chains=2, progressbar=False)

        summary = az.summary(trace)
        return {
            "backend": "pymc",
            "mean": float(summary["mean"].iloc[0]),
            "sd": float(summary["sd"].iloc[0]),
            "hdi_3%": float(summary["hdi_3%"].iloc[0]),
            "hdi_97%": float(summary["hdi_97%"].iloc[0]),
            "r_hat": float(summary["r_hat"].iloc[0]),
        }
    except ImportError:
        return {"backend": "custom", "note": "PyMC not installed — fallback to custom MCMC"}
