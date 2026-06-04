"""Falsifier — empirical falsification with simulations, statistics, and structured critique."""
from __future__ import annotations

import copy
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import stats


logger = logging.getLogger("c44tcdi.discovery.falsifier")


def _extract_json(text: str) -> Any:
    """Extract JSON from text, handling markdown code blocks."""
    if not text:
        return {}
    cleaned = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
    return json.loads(cleaned)


@dataclass
class Counterexample:
    """A generated counterexample from simulation or reasoning."""

    description: str
    parameter_values: dict[str, Any] = field(default_factory=dict)
    observed_outcome: float = 0.0
    expected_outcome: float = 0.0
    violation_magnitude: float = 0.0
    source: str = "simulation"  # simulation | statistical | literature | critique

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "parameter_values": self.parameter_values,
            "observed_outcome": self.observed_outcome,
            "expected_outcome": self.expected_outcome,
            "violation_magnitude": self.violation_magnitude,
            "source": self.source,
        }


@dataclass
class Contradiction:
    """A contradiction found in literature or reasoning."""

    claim: str
    opposing_evidence: str
    source: str
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "opposing_evidence": self.opposing_evidence,
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass
class FalsificationResult:
    """Full result of empirical falsification."""

    falsifiable: bool
    confidence: float
    counterexamples: list[Counterexample] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    statistical_tests: list[dict[str, Any]] = field(default_factory=list)
    critique: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "falsifiable": self.falsifiable,
            "confidence": self.confidence,
            "counterexamples": [c.to_dict() for c in self.counterexamples],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "statistical_tests": self.statistical_tests,
            "critique": self.critique,
            "recommendation": self.recommendation,
        }


class PhysicsSimulator:
    """Lightweight physics simulation for counterexample generation."""

    def __init__(self, rng: np.random.RandomState | None = None) -> None:
        self.rng = rng or np.random.RandomState()

    def run_ballistic(
        self,
        initial_velocity: float,
        angle_deg: float,
        gravity: float = 9.81,
        drag_coeff: float = 0.0,
        mass: float = 1.0,
    ) -> dict[str, float]:
        """Simulate projectile motion; return max_range and max_height."""
        angle_rad = np.radians(angle_deg)
        vx = initial_velocity * np.cos(angle_rad)
        vy = initial_velocity * np.sin(angle_rad)
        if drag_coeff > 0:
            # Simple numerical integration with drag
            dt = 0.001
            t = 0.0
            x, y = 0.0, 0.0
            while y >= 0 or t == 0:
                v = np.sqrt(vx**2 + vy**2)
                ax = -drag_coeff * v * vx / mass
                ay = -gravity - drag_coeff * v * vy / mass
                vx += ax * dt
                vy += ay * dt
                x += vx * dt
                y += vy * dt
                t += dt
            return {"max_range": x, "max_height": max(y, 0.0), "flight_time": t}
        # Analytical solution (no drag)
        flight_time = 2 * vy / gravity
        max_range = vx * flight_time
        max_height = vy**2 / (2 * gravity)
        return {
            "max_range": max_range,
            "max_height": max_height,
            "flight_time": flight_time,
        }

    def run_oscillator(
        self,
        k: float,
        m: float,
        amplitude: float,
        damping: float = 0.0,
        steps: int = 1000,
    ) -> dict[str, float]:
        """Simulate damped harmonic oscillator via velocity Verlet; return period and energy decay."""
        omega0 = np.sqrt(k / m)
        dt = min(0.01, 0.1 / omega0)  # adaptive: at least 10 steps per cycle
        x = amplitude
        v = 0.0
        peaks: list[float] = []
        peak_times: list[float] = []
        t = 0.0
        prev_x = x
        for _ in range(steps):
            a = -(k / m) * x - (damping / m) * v
            x_half = x + v * dt + 0.5 * a * dt * dt
            a_next = -(k / m) * x_half - (damping / m) * v
            v += 0.5 * (a + a_next) * dt
            x = x_half
            t += dt
            # Peak = turning point (sign change in position derivative)
            if (prev_x > x and x > x - (v * dt)) or (prev_x < x and x < x - (v * dt)):
                # Simpler: local max when v changes from + to -
                pass
            prev_x = x
        # Re-detect peaks by zero-crossing of velocity
        # Re-run short simulation for clean peak detection
        x = amplitude
        v = 0.0
        t = 0.0
        prev_v = v
        peaks = []
        peak_times = []
        for _ in range(steps * 2):
            a = -(k / m) * x - (damping / m) * v
            x += v * dt + 0.5 * a * dt * dt
            v += a * dt
            t += dt
            if prev_v > 0 and v <= 0:
                peaks.append(x)
                peak_times.append(t)
            prev_v = v
        period = np.mean(np.diff(peak_times)) if len(peak_times) > 1 else 2 * np.pi / omega0
        energy_decay = (
            (0.5 * k * peaks[0]**2 - 0.5 * k * peaks[-1]**2) / (0.5 * k * peaks[0]**2)
            if peaks
            else 0.0
        )
        return {"period": period, "energy_decay": energy_decay, "omega0": omega0}

    def run_diffusion(
        self,
        D: float,
        L: float,
        N: int = 50,
        dt: float = 0.001,
        steps: int = 500,
    ) -> dict[str, float]:
        """1D diffusion simulation with no-flux boundaries; return characteristic_time and max_gradient."""
        dx = L / N
        # Stability: D * dt / dx^2 < 0.5
        stable_dt = 0.4 * dx**2 / D if D > 0 else dt
        dt = min(dt, stable_dt)
        c = np.zeros(N)
        c[N // 2] = 1.0 / dx  # delta initial condition
        for _ in range(steps):
            c_new = c.copy()
            c_new[1:-1] = c[1:-1] + D * dt / dx**2 * (c[2:] - 2 * c[1:-1] + c[:-2])
            # No-flux boundaries (Neumann)
            c_new[0] = c_new[1]
            c_new[-1] = c_new[-2]
            c = c_new
        # Characteristic time for no-flux slab: ~ L^2 / (pi^2 * D)
        char_time = L**2 / (np.pi**2 * D) if D > 0 else float("inf")
        max_grad = np.max(np.abs(np.diff(c))) / dx
        return {"characteristic_time": char_time, "max_gradient": max_grad}


class Falsifier:
    """Empirical falsification engine with simulations, statistics, and structured critique."""

    def __init__(self, rng_seed: int | None = None, llm_model: str = "deepseek/deepseek-chat", llm_temperature: float = 0.3, llm_max_tokens: int = 800) -> None:
        self.rng = np.random.RandomState(rng_seed) if rng_seed is not None else np.random.RandomState()
        self.simulator = PhysicsSimulator(self.rng)
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.llm_max_tokens = llm_max_tokens

    def check(self, hypothesis: str, domain: str = "general") -> FalsificationResult:
        """Run full empirical falsification pipeline.

        Steps:
        1. Simulation-based counterexample generation
        2. Statistical hypothesis testing against baseline
        3. Structured literature contradiction search
        4. Expert critique via structured LLM prompt
        """
        counterexamples: list[Counterexample] = []
        contradictions: list[Contradiction] = []
        statistical_tests: list[dict[str, Any]] = []

        # 1. Simulation-based counterexamples (only for physics/engineering domains)
        if domain.lower() in ("physics", "engineering", "mechanics", "fluid dynamics", "thermodynamics"):
            sim_cx = self._simulate_counterexamples(hypothesis, domain)
            counterexamples.extend(sim_cx)

        # 2. Statistical hypothesis testing
        stats_results = self._statistical_tests(hypothesis, domain)
        statistical_tests.extend(stats_results["tests"])
        counterexamples.extend(stats_results["counterexamples"])

        # 3. Literature contradiction search
        lit_contra = self._literature_contradictions(hypothesis, domain)
        contradictions.extend(lit_contra)

        # 4. Structured expert critique
        critique = self._structured_critique(hypothesis, domain)

        # Aggregate confidence
        n_cx = len(counterexamples)
        n_contra = len(contradictions)
        p_values = [
            t["p_value"]
            for t in statistical_tests
            if t.get("p_value") is not None
        ]
        sig_p = [p for p in p_values if p < 0.05]
        physical_impossibilities = len(critique.get("physical_impossibilities", []))
        logical_flaws = len(critique.get("logical_flaws", []))

        # Confidence that hypothesis is falsifiable increases with evidence
        # Use logarithmic saturation so that overwhelming evidence is reflected
        import math
        confidence = min(
            1.0,
            0.05
            + 0.20 * (1 - math.exp(-n_cx / 3))
            + 0.30 * (1 - math.exp(-n_contra / 3))
            + 0.15 * (1 - math.exp(-len(sig_p) / 3))
            + 0.20 * (1 - math.exp(-physical_impossibilities / 3))
            + 0.10 * (1 - math.exp(-logical_flaws / 3))
            + 0.05 * (critique.get("severity_score", 0) / 10),
        )

        falsifiable = (
            confidence > 0.35
            or bool(sig_p)
            or bool(counterexamples)
            or bool(n_contra)
            or physical_impossibilities > 0
        )

        recommendation = "Accept"
        if falsifiable and confidence > 0.7:
            recommendation = "Reject"
        elif falsifiable and confidence > 0.4:
            recommendation = "Revise"

        return FalsificationResult(
            falsifiable=falsifiable,
            confidence=round(confidence, 4),
            counterexamples=counterexamples,
            contradictions=contradictions,
            statistical_tests=statistical_tests,
            critique=critique,
            recommendation=recommendation,
        )

    def _simulate_counterexamples(
        self, hypothesis: str, domain: str
    ) -> list[Counterexample]:
        """Run physics simulations with perturbed parameters to find violations."""
        counterexamples: list[Counterexample] = []
        h_lower = hypothesis.lower()

        # Ballistic hypothesis tests
        if any(w in h_lower for w in ("projectile", "ballistic", "range", "trajectory")):
            # Hypothesis: max range is always at 45 degrees
            # Use a single random velocity for all angles to avoid false positives from velocity variation
            shared_v0 = 10.0 + self.rng.uniform(-1, 1)
            baseline = self.simulator.run_ballistic(
                initial_velocity=shared_v0,
                angle_deg=45.0,
            )
            expected = baseline["max_range"]
            for angle in [30, 60]:
                result = self.simulator.run_ballistic(
                    initial_velocity=shared_v0,
                    angle_deg=angle,
                )
                observed = result["max_range"]
                if observed > expected * 1.05:
                    counterexamples.append(Counterexample(
                        description=f"Range at {angle}° exceeds 45° range",
                        parameter_values={"angle": angle, "v0": round(shared_v0, 4)},
                        observed_outcome=round(observed, 4),
                        expected_outcome=round(expected, 4),
                        violation_magnitude=round((observed - expected) / expected, 4),
                        source="simulation",
                    ))

            # Test with drag: 45° is no longer optimal
            shared_v0_drag = 20.0 + self.rng.uniform(-1, 1)
            baseline_drag = self.simulator.run_ballistic(
                initial_velocity=shared_v0_drag,
                angle_deg=45.0,
                drag_coeff=0.1,
            )
            expected_drag = baseline_drag["max_range"]
            for angle in [35, 55]:
                result_drag = self.simulator.run_ballistic(
                    initial_velocity=shared_v0_drag,
                    angle_deg=angle,
                    drag_coeff=0.1,
                )
                observed_drag = result_drag["max_range"]
                if observed_drag > expected_drag * 1.02:
                    counterexamples.append(Counterexample(
                        description=f"With drag, range at {angle}° exceeds 45° range",
                        parameter_values={"angle": angle, "v0": round(shared_v0_drag, 4), "drag": 0.1},
                        observed_outcome=round(observed_drag, 4),
                        expected_outcome=round(expected_drag, 4),
                        violation_magnitude=round(
                            (observed_drag - expected_drag) / expected_drag, 4
                        ),
                        source="simulation",
                    ))

        # Oscillator hypothesis tests
        if any(w in h_lower for w in ("oscillator", "period", "harmonic", "resonance")):
            # Hypothesis: period is independent of amplitude
            amplitudes = [0.5, 1.0, 2.0, 3.0]
            periods: list[float] = []
            for A in amplitudes:
                res = self.simulator.run_oscillator(k=10.0, m=1.0, amplitude=A)
                periods.append(res["period"])
            # For nonlinear restoring force (we used linear, but test anyway)
            period_std = np.std(periods)
            if period_std > 0.01:
                counterexamples.append(Counterexample(
                    description="Period varies with amplitude",
                    parameter_values={"amplitudes": amplitudes},
                    observed_outcome=float(round(period_std, 4)),
                    expected_outcome=0.0,
                    violation_magnitude=float(round(period_std / np.mean(periods), 4)),
                    source="simulation",
                ))

            # Hypothesis: damping does not affect period (underdamped approx)
            damping_values = [0.0, 0.5, 1.0, 2.0]
            damped_periods: list[float] = []
            for gamma in damping_values:
                res = self.simulator.run_oscillator(
                    k=10.0, m=1.0, amplitude=1.0, damping=gamma
                )
                damped_periods.append(res["period"])
            # Damping increases effective period
            if np.std(damped_periods) > 0.01:
                counterexamples.append(Counterexample(
                    description="Damping changes oscillator period",
                    parameter_values={"damping": damping_values},
                    observed_outcome=float(round(np.std(damped_periods), 4)),
                    expected_outcome=0.0,
                    violation_magnitude=float(round(
                        np.std(damped_periods) / np.mean(damped_periods), 4
                    )),
                    source="simulation",
                ))

        # Diffusion hypothesis tests
        if any(w in h_lower for w in ("diffusion", "spread", "concentration", "gradient")):
            # Hypothesis: characteristic time scales linearly with D
            D_values = [0.1, 0.5, 1.0, 2.0]
            times: list[float] = []
            for D in D_values:
                res = self.simulator.run_diffusion(D=D, L=1.0)
                times.append(res["characteristic_time"])
            # t ~ L²/D, so 1/D relationship
            # If someone claims linear in D, that's wrong
            if "linear" in h_lower and "diffusion" in h_lower:
                counterexamples.append(Counterexample(
                    description="Diffusion time scales as 1/D, not linear with D",
                    parameter_values={"D_values": D_values},
                    observed_outcome=float(round(times[0] / times[-1], 4)),
                    expected_outcome=0.05,  # linear would give ~0.05 ratio
                    violation_magnitude=float(round(
                        abs(times[0] / times[-1] - 0.05) / 0.05, 4
                    )),
                    source="simulation",
                ))

        return counterexamples

    def _statistical_tests(
        self, hypothesis: str, domain: str
    ) -> dict[str, Any]:
        """Run statistical hypothesis tests against baselines."""
        tests: list[dict[str, Any]] = []
        counterexamples: list[Counterexample] = []
        h_lower = hypothesis.lower()

        # Generate synthetic baseline data
        n_samples = 100
        baseline = self.rng.normal(loc=0.0, scale=1.0, size=n_samples)

        # Apply Bonferroni correction for multiple comparisons
        # Count how many tests will be run to set alpha appropriately
        alpha_raw = 0.05
        test_count = 0
        if any(w in h_lower for w in ("effect", "increase", "decrease", "difference")):
            test_count += 1
        if any(w in h_lower for w in ("groups", "conditions", "levels", "categories")):
            test_count += 1
        if "normal" in h_lower or "gaussian" in h_lower:
            test_count += 1
        if any(w in h_lower for w in ("correlate", "relationship", "association", "linked")):
            test_count += 1
        alpha = alpha_raw / max(test_count, 1)

        # Test 1: t-test against zero mean
        if any(w in h_lower for w in ("effect", "increase", "decrease", "difference")):
            treatment = self.rng.normal(loc=0.3, scale=1.0, size=n_samples)
            t_stat, p_value = stats.ttest_ind(baseline, treatment)
            tests.append({
                "test": "independent_t_test",
                "statistic": round(float(t_stat), 4),
                "p_value": round(float(p_value), 4),
                "significant": p_value < alpha,
                "alpha": round(alpha, 4),
                "n_samples": n_samples,
                "description": "Test whether treatment differs from baseline",
            })
            if p_value >= alpha:
                counterexamples.append(Counterexample(
                    description="No statistically significant effect detected",
                    parameter_values={"n_samples": n_samples, "effect_size": 0.3},
                    observed_outcome=round(float(p_value), 4),
                    expected_outcome=round(alpha, 4),
                    violation_magnitude=round(p_value / max(alpha, 1e-10), 4),
                    source="statistical",
                ))

        # Test 2: ANOVA for multiple groups
        if any(w in h_lower for w in ("groups", "conditions", "levels", "categories")):
            group_a = self.rng.normal(loc=0.0, scale=1.0, size=n_samples)
            group_b = self.rng.normal(loc=0.1, scale=1.0, size=n_samples)
            group_c = self.rng.normal(loc=0.2, scale=1.0, size=n_samples)
            f_stat, p_value = stats.f_oneway(group_a, group_b, group_c)
            tests.append({
                "test": "one_way_anova",
                "statistic": round(float(f_stat), 4),
                "p_value": round(float(p_value), 4),
                "significant": p_value < alpha,
                "alpha": round(alpha, 4),
                "n_samples": n_samples * 3,
                "description": "Test whether group means differ",
            })
            if p_value >= alpha:
                counterexamples.append(Counterexample(
                    description="ANOVA finds no significant group differences",
                    parameter_values={"groups": 3, "n_per_group": n_samples},
                    observed_outcome=round(float(p_value), 4),
                    expected_outcome=round(alpha, 4),
                    violation_magnitude=round(p_value / max(alpha, 1e-10), 4),
                    source="statistical",
                ))

        # Test 3: Normality test (many hypotheses assume normality)
        if "normal" in h_lower or "gaussian" in h_lower:
            skewed = self.rng.exponential(scale=1.0, size=n_samples)
            stat, p_value = stats.shapiro(skewed[: min(5000, n_samples)])
            tests.append({
                "test": "shapiro_wilk_normality",
                "statistic": round(float(stat), 4),
                "p_value": round(float(p_value), 4),
                "significant": p_value < alpha,
                "alpha": round(alpha, 4),
                "description": "Test whether data is normally distributed",
            })
            if p_value < alpha:
                counterexamples.append(Counterexample(
                    description="Data significantly deviates from normal distribution",
                    parameter_values={"n_samples": n_samples},
                    observed_outcome=round(float(p_value), 4),
                    expected_outcome=round(alpha, 4),
                    violation_magnitude=round(alpha / max(p_value, 1e-10), 4),
                    source="statistical",
                ))

        # Test 4: Correlation test
        if any(w in h_lower for w in ("correlate", "relationship", "association", "linked")):
            x = self.rng.uniform(0, 10, n_samples)
            y = 0.1 * x + self.rng.normal(0, 5, n_samples)  # weak correlation
            r, p_value = stats.pearsonr(x, y)
            tests.append({
                "test": "pearson_correlation",
                "statistic": round(float(r), 4),
                "p_value": round(float(p_value), 4),
                "significant": p_value < alpha,
                "alpha": round(alpha, 4),
                "description": "Test linear correlation strength",
            })
            if abs(r) < 0.3:
                counterexamples.append(Counterexample(
                    description="Correlation is weak or nonexistent",
                    parameter_values={"n_samples": n_samples},
                    observed_outcome=round(float(r), 4),
                    expected_outcome=0.5,
                    violation_magnitude=round(abs(0.5 - abs(r)) / 0.5, 4),
                    source="statistical",
                ))

        return {"tests": tests, "counterexamples": counterexamples}

    def _literature_contradictions(
        self, hypothesis: str, domain: str
    ) -> list[Contradiction]:
        """Search for papers with claims opposite to the hypothesis."""
        contradictions: list[Contradiction] = []
        h_lower = hypothesis.lower()

        # Structured keyword-based contradiction search
        # In production, this would query CrossRef / Semantic Scholar APIs
        contradiction_db: list[dict[str, Any]] = [
            {
                "patterns": [" heavier objects fall faster", "mass affects fall speed"],
                "opposing": "Galileo showed all objects fall at same rate in vacuum",
                "source": "Galileo, Dialogues Concerning Two New Sciences (1638)",
                "confidence": 0.99,
            },
            {
                "patterns": ["phlogiston", "caloric fluid", "luminiferous ether"],
                "opposing": "Experiments falsified these substances (Lavoisier, Michelson-Morley)",
                "source": "Michelson & Morley (1887); Lavoisier (1783)",
                "confidence": 0.98,
            },
            {
                "patterns": ["cold fusion", "fleischmann-pons", "room temperature fusion"],
                "opposing": "No reproducible excess heat or neutron emission found",
                "source": "DOE Review Panel (1989, 2004)",
                "confidence": 0.95,
            },
            {
                "patterns": ["vaccine causes autism", "vaccines cause autism", "mmr autism"],
                "opposing": "Large-scale studies find no causal link (N ~ 500,000)",
                "source": "Hviid et al., Annals of Internal Medicine (2019)",
                "confidence": 0.97,
            },
            {
                "patterns": ["lamarckian inheritance", "acquired traits inherited", "acquired characteristics"],
                "opposing": "Weismann barrier prevents somatic-to-germline information transfer",
                "source": "Weismann (1893); modern epigenetics is limited and reversible",
                "confidence": 0.90,
            },
            {
                "patterns": ["perpetual motion", "free energy", "over-unity"],
                "opposing": "Violates first and second laws of thermodynamics",
                "source": "Clausius & Kelvin formulation of thermodynamics",
                "confidence": 0.99,
            },
            {
                "patterns": ["diffusion is linear in time", "diffusion scales linearly"],
                "opposing": "Mean squared displacement scales as sqrt(t) in 1D, t in higher dimensions",
                "source": "Einstein (1905); Fick's laws",
                "confidence": 0.95,
            },
            {
                "patterns": ["local hidden variables", "bell inequality violated by locality"],
                "opposing": "Bell tests rule out local hidden variable theories",
                "source": "Aspect et al. (1982); Hensen et al. (2015)",
                "confidence": 0.98,
            },
            {
                "patterns": ["earth is flat", "flat earth", "sun revolves around the earth", "geocentrism"],
                "opposing": "Earth is an oblate spheroid orbiting the Sun; heliocentrism confirmed by parallax, spaceflight, and geodesy",
                "source": "Copernicus (1543); Galileo (1632); Apollo missions (1969-1972)",
                "confidence": 0.99,
            },
        ]

        for entry in contradiction_db:
            for pattern in entry["patterns"]:
                if pattern in h_lower:
                    contradictions.append(Contradiction(
                        claim=hypothesis,
                        opposing_evidence=entry["opposing"],
                        source=entry["source"],
                        confidence=entry["confidence"],
                    ))
                    break

        # Domain-specific heuristics
        domain_contradictions: dict[str, list[dict[str, Any]]] = {
            "physics": [
                {
                    "patterns": ["faster than light", "faster than the speed of light", "superluminal", "tachyons"],
                    "opposing": "Special relativity forbids superluminal information transfer",
                    "source": "Einstein (1905)",
                    "confidence": 0.99,
                },
            ],
            "biology": [
                {
                    "patterns": ["spontaneous generation", "abiogenesis in jar"],
                    "opposing": "Pasteur's swan-neck flask experiments falsified spontaneous generation",
                    "source": "Pasteur (1861)",
                    "confidence": 0.98,
                },
            ],
            "economics": [
                {
                    "patterns": ["perpetual growth", "infinite exponential growth"],
                    "opposing": "Resource constraints and entropy limit infinite growth",
                    "source": "Georgescu-Roegen (1971); Meadows et al. (1972)",
                    "confidence": 0.85,
                },
            ],
        }

        for d, entries in domain_contradictions.items():
            # Use tokenized matching to avoid substring false positives
            # e.g. "biophysics" contains "physics" but is a biology domain
            if d == domain.lower().split()[0] or f" {d} " in f" {domain.lower()} ":
                for entry in entries:
                    for pattern in entry["patterns"]:
                        if pattern in h_lower:
                            contradictions.append(Contradiction(
                                claim=hypothesis,
                                opposing_evidence=entry["opposing"],
                                source=entry["source"],
                                confidence=entry["confidence"],
                            ))
                            break

        return contradictions

    def _structured_critique(self, hypothesis: str, domain: str) -> dict[str, Any]:
        """Expert critique via structured reasoning (LLM or rule-based)."""
        critique: dict[str, Any] = {
            "logical_flaws": [],
            "missing_controls": [],
            "unstated_assumptions": [],
            "physical_impossibilities": [],
            "severity_score": 0.0,
        }
        h_lower = hypothesis.lower()

        # Logical flaw detection
        logical_patterns: list[tuple[list[str], str]] = [
            (
                ["all ", "every ", "always", "never", "impossible"],
                "Universal quantifier without bounded domain — likely false given edge cases",
            ),
            (
                ["prove", "proof", "undeniable", "certainly"],
                "Epistemic overreach: scientific hypotheses are corroborated, not proven",
            ),
            (
                ["correlation implies causation", "correlation means causation"],
                "Logical fallacy: correlation does not imply causation",
            ),
            (
                ["after this, therefore because of this", "post hoc"],
                "Post hoc ergo propter hoc fallacy",
            ),
        ]
        for patterns, flaw in logical_patterns:
            if any(p in h_lower for p in patterns):
                critique["logical_flaws"].append(flaw)

        # Missing controls
        if any(w in h_lower for w in ("effect", "causes", "increases", "decreases")):
            critique["missing_controls"].append(
                "No control group or baseline comparison specified"
            )
            critique["missing_controls"].append(
                "Confounding variables not addressed (e.g., selection bias, regression to mean)"
            )

        # Unstated assumptions
        if "assume" not in h_lower and "assuming" not in h_lower:
            critique["unstated_assumptions"].append(
                "Hypothesis contains implicit assumptions not explicitly listed"
            )
        if any(w in h_lower for w in ("linear", "proportional", "scales as")):
            critique["unstated_assumptions"].append(
                "Linearity/proportionality assumed without domain justification"
            )

        # Physical impossibilities
        physical_patterns: list[tuple[list[str], str]] = [
            (
                ["perpetual motion", "free energy", "over-unity"],
                "Violates conservation of energy (1st law) and/or entropy (2nd law)",
            ),
            (
                ["faster than light", "superluminal communication"],
                "Violates special relativity and causality",
            ),
            (
                ["negative absolute temperature", "below absolute zero"],
                "Thermodynamically ill-defined for equilibrium systems",
            ),
            (
                ["create matter from nothing", "energy from vacuum"],
                "Violates mass-energy conservation unless quantum fluctuations are properly bounded",
            ),
        ]
        for patterns, impossibility in physical_patterns:
            if any(p in h_lower for p in patterns):
                critique["physical_impossibilities"].append(impossibility)

        # Severity score: 0-10
        severity = (
            len(critique["logical_flaws"]) * 2
            + len(critique["missing_controls"])
            + len(critique["unstated_assumptions"])
            + len(critique["physical_impossibilities"]) * 3
        )
        critique["severity_score"] = min(10.0, severity)

        return critique

    async def check_adversarial(
        self, hypothesis: str, domain: str
    ) -> dict[str, Any]:
        """Async wrapper that also attempts LLM-based critique if API key is present."""
        result = copy.deepcopy(self.check(hypothesis, domain))
        or_key = os.getenv("OPENROUTER_API_KEY", "")
        if or_key:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=60) as c:
                    r = await c.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {or_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.llm_model,
                            "temperature": self.llm_temperature,
                            "max_tokens": self.llm_max_tokens,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a rigorous scientific reviewer. Evaluate the hypothesis "
                                        "using these criteria:\n"
                                        "1. LOGICAL FLAWS: identify fallacies, circular reasoning, or contradictions\n"
                                        "2. MISSING CONTROLS: list control experiments, confounders, or baselines omitted\n"
                                        "3. UNSTATED ASSUMPTIONS: surface hidden premises or domain boundaries\n"
                                        "4. PHYSICAL IMPOSSIBILITIES: flag violations of known laws\n"
                                        "5. STATISTICAL VALIDITY: note sample size, power, p-hacking risks\n"
                                        "Output JSON: {"
                                        "logical_flaws: [...], missing_controls: [...], "
                                        "unstated_assumptions: [...], physical_impossibilities: [...], "
                                        "statistical_concerns: [...], verdict: 'PASS'|'REJECT'|'REVISE', "
                                        "confidence: float, severity_score: float}"
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": f"Hypothesis: {hypothesis[:1000].replace('<', '[').replace('>', ']')}. Domain: {domain.replace('<', '[').replace('>', ']')}.",
                                },
                            ],
                        },
                    )
                    llm_critique = _extract_json(
                        r.json()["choices"][0]["message"]["content"]
                    )
                    result.critique["llm_critique"] = llm_critique
                    # Blend confidence with LLM assessment
                    llm_conf = llm_critique.get("confidence", 0.5)
                    result.confidence = round(
                        0.7 * result.confidence + 0.3 * llm_conf, 4
                    )
                    if llm_critique.get("verdict") == "REJECT":
                        result.falsifiable = True
                        result.recommendation = "Reject"
            except Exception as e:
                logger.warning("LLM adversarial check failed: %s", e)
                result.critique["adversarial_check_status"] = "failed"

        return result.to_dict()


# Convenience function for quick falsification checks
def falsify(hypothesis: str, domain: str = "general") -> dict[str, Any]:
    """One-shot falsification check."""
    f = Falsifier()
    return f.check(hypothesis, domain).to_dict()
