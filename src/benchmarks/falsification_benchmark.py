"""
Falsification Benchmark: Known True/False Hypotheses

Evaluates Reqber's falsifiability generation and hypothesis evaluation
against hypotheses with established ground-truth status.

Usage:
    python -m src.benchmarks.falsification_benchmark

Results are written to `benchmark_results/falsification_<timestamp>.json`.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FalsificationCase:
    """A hypothesis with known truth value and established falsification criteria."""

    id: str
    hypothesis: str
    is_true: bool  # Ground truth
    domain: str
    known_falsification: str  # How this hypothesis was / could be falsified
    source: str  # e.g., "Popper 1934", "Historical experiment"


FALSIFICATION_CASES: list[FalsificationCase] = [
    # === TRUE HYPOTHESES ===
    FalsificationCase(
        id="F001",
        hypothesis="Water expands when it freezes below 4°C",
        is_true=True,
        domain="physics",
        known_falsification="Measure density of water at 0°C vs 4°C; if density increases, hypothesis is false",
        source="Historical experiment",
    ),
    FalsificationCase(
        id="F002",
        hypothesis="DNA is a double helix with complementary base pairing",
        is_true=True,
        domain="biology",
        known_falsification="X-ray crystallography showing non-helical structure or non-complementary bases",
        source="Watson & Crick 1953",
    ),
    FalsificationCase(
        id="F003",
        hypothesis="Accelerating charges emit electromagnetic radiation",
        is_true=True,
        domain="physics",
        known_falsification="Observe an accelerating charge in a vacuum; if no radiation detected, hypothesis is false",
        source="Maxwell's equations",
    ),
    FalsificationCase(
        id="F004",
        hypothesis="All living cells arise from pre-existing cells",
        is_true=True,
        domain="biology",
        known_falsification="Observe spontaneous generation of life from non-living matter under sterile conditions",
        source="Pasteur 1859",
    ),
    FalsificationCase(
        id="F005",
        hypothesis="The speed of light in vacuum is constant for all observers",
        is_true=True,
        domain="physics",
        known_falsification="Measure speed of light in vacuum from different inertial frames; if values differ, hypothesis is false",
        source="Einstein 1905",
    ),
    FalsificationCase(
        id="F006",
        hypothesis="Increasing model capacity reduces training error given sufficient data",
        is_true=True,
        domain="ml",
        known_falsification="Train a larger model with sufficient data; if training error does not decrease, hypothesis is false",
        source="Universal approximation theory",
    ),
    FalsificationCase(
        id="F007",
        hypothesis="Antibiotics kill bacteria by inhibiting cell wall synthesis or protein synthesis",
        is_true=True,
        domain="medicine",
        known_falsification="Treat bacteria with antibiotics; if cell walls and proteins remain intact, hypothesis is false",
        source="Fleming 1928 / Mechanistic studies",
    ),
    FalsificationCase(
        id="F008",
        hypothesis="The Earth orbits the Sun in an elliptical path",
        is_true=True,
        domain="astrophysics",
        known_falsification="Measure planetary positions over years; if they do not fit elliptical orbits, hypothesis is false",
        source="Kepler 1609",
    ),
    FalsificationCase(
        id="F009",
        hypothesis="Neural networks with one hidden layer can approximate any continuous function",
        is_true=True,
        domain="ml",
        known_falsification="Construct a continuous function that no single-hidden-layer network can approximate within epsilon",
        source="Cybenko 1989",
    ),
    FalsificationCase(
        id="F010",
        hypothesis="Vaccination induces adaptive immunity via antibody production",
        is_true=True,
        domain="medicine",
        known_falsification="Vaccinate subjects and measure antibody titers; if no antibodies produced, hypothesis is false",
        source="Jenner 1796 / Modern immunology",
    ),
    FalsificationCase(
        id="F011",
        hypothesis="Natural selection drives adaptive evolution in populations",
        is_true=True,
        domain="biology",
        known_falsification="Track allele frequencies over generations; if no correlation with fitness, hypothesis is false",
        source="Darwin 1859",
    ),
    FalsificationCase(
        id="F012",
        hypothesis="Neutrinos have non-zero mass",
        is_true=True,
        domain="physics",
        known_falsification="Measure neutrino oscillations; if no oscillation observed, hypothesis is false",
        source="Super-Kamiokande 1998",
    ),
    FalsificationCase(
        id="F013",
        hypothesis="Regularization reduces overfitting in high-capacity models",
        is_true=True,
        domain="ml",
        known_falsification="Train identical models with/without regularization; if test error is equal or worse with regularization, hypothesis is false",
        source="Statistical learning theory",
    ),
    FalsificationCase(
        id="F014",
        hypothesis="HIV causes AIDS",
        is_true=True,
        domain="medicine",
        known_falsification="Identify AIDS patients without HIV infection; if such patients exist in significant numbers, hypothesis is false",
        source="Gallo & Montagnier 1983",
    ),
    FalsificationCase(
        id="F015",
        hypothesis="The universe is expanding",
        is_true=True,
        domain="astrophysics",
        known_falsification="Measure redshift of distant galaxies; if blueshift dominates, hypothesis is false",
        source="Hubble 1929",
    ),
    # === FALSE HYPOTHESES (historically falsified) ===
    FalsificationCase(
        id="F016",
        hypothesis="The Sun revolves around the Earth",
        is_true=False,
        domain="astrophysics",
        known_falsification="Measure stellar parallax and planetary retrograde motion; geocentric model fails to predict these",
        source="Galileo 1632",
    ),
    FalsificationCase(
        id="F017",
        hypothesis="Phlogiston is released during combustion",
        is_true=False,
        domain="chemistry",
        known_falsification="Measure mass before and after combustion; if mass increases, phlogiston theory is false",
        source="Lavoisier 1783",
    ),
    FalsificationCase(
        id="F018",
        hypothesis="Spontaneous generation produces life from non-life",
        is_true=False,
        domain="biology",
        known_falsification="Use sterilized broth in sealed flask; if no microbial growth occurs, hypothesis is false",
        source="Pasteur 1859",
    ),
    FalsificationCase(
        id="F019",
        hypothesis="The luminiferous aether carries light waves",
        is_true=False,
        domain="physics",
        known_falsification="Measure speed of light perpendicular vs parallel to Earth's motion; if no difference (Michelson-Morley), hypothesis is false",
        source="Michelson & Morley 1887",
    ),
    FalsificationCase(
        id="F020",
        hypothesis="Lamarckian inheritance of acquired traits drives evolution",
        is_true=False,
        domain="biology",
        known_falsification="Cut tails off mice for multiple generations; if offspring are born with normal tails, hypothesis is false",
        source="Weismann 1889",
    ),
    FalsificationCase(
        id="F021",
        hypothesis="Cold fusion occurs at room temperature in palladium deuteride",
        is_true=False,
        domain="physics",
        known_falsification="Measure neutron emission and excess heat under claimed conditions; if neither detected, hypothesis is false",
        source="Fleischmann & Pons 1989 (failed replication)",
    ),
    FalsificationCase(
        id="F022",
        hypothesis="N-rays exist and can be refracted by aluminum prisms",
        is_true=False,
        domain="physics",
        known_falsification="Use blinded observers; if N-ray effects disappear under blinding, hypothesis is false",
        source="Wood 1904",
    ),
    FalsificationCase(
        id="F023",
        hypothesis="The MMR vaccine causes autism",
        is_true=False,
        domain="medicine",
        known_falsification="Large epidemiological studies (n>500,000) show no correlation between MMR and autism",
        source="Wakefield 1998 (retracted) / Multiple refutations",
    ),
    FalsificationCase(
        id="F024",
        hypothesis="Perpetual motion machines of the first kind are possible",
        is_true=False,
        domain="physics",
        known_falsification="Construct claimed machine; if it produces more energy than input, hypothesis would be true — none have passed",
        source="Thermodynamics (1st Law)",
    ),
    FalsificationCase(
        id="F025",
        hypothesis="Piltdown Man is a missing link between apes and humans",
        is_true=False,
        domain="anthropology",
        known_falsification="Fluorine dating showed the jaw was from a modern orangutan and the skull was medieval human",
        source="Dawson 1912 / Oakley 1953",
    ),
    FalsificationCase(
        id="F026",
        hypothesis="The expanding Earth explains continental drift without plate tectonics",
        is_true=False,
        domain="earth_science",
        known_falsification="Measure Earth's radius over time via satellite; if no expansion detected, hypothesis is false",
        source="Carey 1958 / Modern geodesy",
    ),
    FalsificationCase(
        id="F027",
        hypothesis="Polywater is a stable polymerized form of water with altered properties",
        is_true=False,
        domain="chemistry",
        known_falsification="Show that observed properties were due to contamination (silicates, sweat); pure water does not form polywater",
        source="Deryagin 1961 / Franks 1970",
    ),
    FalsificationCase(
        id="F028",
        hypothesis="Homeopathic dilutions beyond Avogadro's limit retain therapeutic effect",
        is_true=False,
        domain="medicine",
        known_falsification="Double-blind RCTs at 12C+ dilutions show no difference from placebo",
        source="Multiple meta-analyses (Shang et al. 2005)",
    ),
    FalsificationCase(
        id="F029",
        hypothesis="The steady-state model explains cosmic expansion without a beginning",
        is_true=False,
        domain="astrophysics",
        known_falsification="Measure cosmic microwave background; if blackbody spectrum detected, steady-state is false",
        source="Penzias & Wilson 1965",
    ),
    FalsificationCase(
        id="F030",
        hypothesis="Facilitated communication allows non-verbal autistic individuals to communicate",
        is_true=False,
        domain="psychology",
        known_falsification="Use double-blind tests where facilitator cannot see the stimulus; if accuracy drops to chance, hypothesis is false",
        source="Multiple controlled studies 1990s",
    ),
]

BENCHMARK_META = {
    "total_cases": 30,
    "true_hypotheses": 15,
    "false_hypotheses": 15,
    "domains": sorted({c.domain for c in FALSIFICATION_CASES}),
}


def run_falsification_benchmark(
    evaluator: Any | None = None,
) -> dict[str, Any]:
    """Run falsification benchmark.

    Args:
        evaluator: Callable that takes a hypothesis string and returns dict with:
            - "falsifiable": bool
            - "criteria": list[str]  # falsification criteria generated
            - "verdict": str  # "true", "false", or "uncertain"
        If None, uses random baseline.

    Returns:
        Dictionary with accuracy, precision, recall, and per-case results.
    """
    import random

    if evaluator is None:

        def evaluator(hypothesis: str) -> dict[str, Any]:  # noqa: ARG001
            return {
                "falsifiable": random.choice([True, False]),
                "criteria": ["criterion_1", "criterion_2"],
                "verdict": random.choice(["true", "false", "uncertain"]),
            }

    results: list[dict[str, Any]] = []
    start = time.perf_counter()

    for case in FALSIFICATION_CASES:
        t0 = time.perf_counter()
        prediction = evaluator(case.hypothesis)
        latency = (time.perf_counter() - t0) * 1000

        # Map verdict to boolean
        pred_true = prediction.get("verdict") == "true"
        correct = pred_true == case.is_true

        results.append(
            {
                "case_id": case.id,
                "predicted_verdict": prediction.get("verdict"),
                "ground_truth": "true" if case.is_true else "false",
                "correct": correct,
                "falsifiable": prediction.get("falsifiable"),
                "criteria_count": len(prediction.get("criteria", [])),
                "domain": case.domain,
                "latency_ms": round(latency, 2),
            }
        )

    total = len(results)
    correct_count = sum(1 for r in results if r["correct"])
    accuracy = correct_count / total if total else 0.0

    true_cases = [r for r in results if r["ground_truth"] == "true"]
    false_cases = [r for r in results if r["ground_truth"] == "false"]

    true_positive = sum(1 for r in true_cases if r["predicted_verdict"] == "true")
    false_positive = sum(1 for r in false_cases if r["predicted_verdict"] == "true")
    false_negative = sum(1 for r in true_cases if r["predicted_verdict"] != "true")

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0.0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0.0

    total_time = (time.perf_counter() - start) * 1000
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0.0

    summary = {
        "benchmark": "falsification",
        "version": "v5.0-alpha",
        "timestamp": datetime.utcnow().isoformat(),
        "meta": BENCHMARK_META,
        "aggregate": {
            "cases_tested": len(FALSIFICATION_CASES),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "total_time_ms": round(total_time, 2),
        },
        "results": results,
    }

    return summary


def main() -> None:
    """CLI entry point."""
    summary = run_falsification_benchmark()

    out_dir = Path("benchmark_results")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"falsification_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(summary, indent=2))

    print("Falsification Benchmark v5.0-alpha")
    print(f"Cases tested: {summary['aggregate']['cases_tested']}")
    print(f"Accuracy:     {summary['aggregate']['accuracy']:.2%}")
    print(f"Precision:    {summary['aggregate']['precision']:.2%}")
    print(f"Recall:       {summary['aggregate']['recall']:.2%}")
    print(f"Avg Latency:  {summary['aggregate']['avg_latency_ms']:.1f}ms")
    print(f"Results written to: {out_file}")


if __name__ == "__main__":
    main()
