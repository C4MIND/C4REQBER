"""
Isomorphism Benchmark: Known Valid/Invalid Analogies

Evaluates Reqber's cross-domain transfer by testing if it can distinguish
structurally valid analogies from invalid ones.

Usage:
    python -m src.benchmarks.isomorphism_benchmark

Results are written to `benchmark_results/isomorphism_<timestamp>.json`.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IsomorphismCase:
    """A cross-domain analogy with known validity."""

    id: str
    source_domain: str
    source_problem: str
    target_domain: str
    target_problem: str
    is_valid: bool  # True if a meaningful structural analogy exists
    mapping_description: str  # What maps to what
    justification: str


ISOMORPHISM_CASES: list[IsomorphismCase] = [
    # === VALID ANALOGIES (is_valid=True) ===
    IsomorphismCase(
        id="I001",
        source_domain="biology",
        source_problem="Cells use vesicles to transport molecules between organelles",
        target_domain="logistics",
        target_problem="Companies use trucks to transport goods between warehouses",
        is_valid=True,
        mapping_description="vesicle → truck, organelle → warehouse, molecule → goods",
        justification="Well-established analogy in systems biology and operations research",
    ),
    IsomorphismCase(
        id="I002",
        source_domain="physics",
        source_problem="Water flows from high pressure to low pressure through a pipe",
        target_domain="electronics",
        target_problem="Current flows from high voltage to low voltage through a wire",
        is_valid=True,
        mapping_description="pressure → voltage, flow rate → current, pipe → wire",
        justification="Direct analogy used in hydraulic-electric analogies",
    ),
    IsomorphismCase(
        id="I003",
        source_domain="neuroscience",
        source_problem="Neurons fire when input exceeds a threshold",
        target_domain="ml",
        target_problem="Perceptron activates when weighted sum exceeds bias",
        is_valid=True,
        mapping_description="neuron → perceptron, synaptic weight → weight, threshold → bias",
        justification="Perceptron was explicitly modeled after neurons (Rosenblatt 1958)",
    ),
    IsomorphismCase(
        id="I004",
        source_domain="ecology",
        source_problem="Predator-prey dynamics regulate population sizes",
        target_domain="economics",
        target_problem="Supply and demand regulate market prices",
        is_valid=True,
        mapping_description="predator → buyer, prey → seller, population → price",
        justification="Lotka-Volterra models have been applied to market dynamics",
    ),
    IsomorphismCase(
        id="I005",
        source_domain="immunology",
        source_problem="Antibodies bind to specific antigens to neutralize pathogens",
        target_domain="computer_security",
        target_problem="Antivirus signatures match specific malware patterns to neutralize threats",
        is_valid=True,
        mapping_description="antibody → signature, antigen → malware, pathogen → threat",
        justification="Well-known analogy in biological computing",
    ),
    IsomorphismCase(
        id="I006",
        source_domain="thermodynamics",
        source_problem="Heat spreads from hot to cold until thermal equilibrium",
        target_domain="sociology",
        target_problem="Information spreads from informed to uninformed until consensus",
        is_valid=True,
        mapping_description="temperature → knowledge, heat flow → information flow, equilibrium → consensus",
        justification="Social physics models (e.g., Helbing) use thermodynamic analogies",
    ),
    IsomorphismCase(
        id="I007",
        source_domain="botany",
        source_problem="Plants grow toward light sources (phototropism)",
        target_domain="robotics",
        target_problem="Robots navigate toward beacons using light sensors",
        is_valid=True,
        mapping_description="plant → robot, light source → beacon, photoreceptor → light sensor",
        justification="Direct biomimicry analogy",
    ),
    IsomorphismCase(
        id="I008",
        source_domain="linguistics",
        source_problem="Words with similar meanings cluster in semantic space",
        target_domain="ml",
        target_problem="Word embeddings cluster similar words in vector space",
        is_valid=True,
        mapping_description="word meaning → vector, semantic similarity → cosine distance",
        justification="Word2Vec and similar models operationalize this analogy",
    ),
    IsomorphismCase(
        id="I009",
        source_domain="geology",
        source_problem="Sedimentary layers record historical environmental conditions",
        target_domain="computing",
        target_problem="Log files record historical system states",
        is_valid=True,
        mapping_description="sediment layer → log entry, time → timestamp, environment → system state",
        justification="Both are temporal record-keeping systems",
    ),
    IsomorphismCase(
        id="I010",
        source_domain="chemistry",
        source_problem="Catalysts lower activation energy without being consumed",
        target_domain="economics",
        target_problem="Intermediaries reduce transaction costs without consuming the product",
        is_valid=True,
        mapping_description="catalyst → intermediary, activation energy → transaction cost, reaction → trade",
        justification="Chemical reaction economics uses this analogy",
    ),
    IsomorphismCase(
        id="I011",
        source_domain="music",
        source_problem="Harmony emerges from frequency ratios between notes",
        target_domain="physics",
        target_problem="Stability emerges from energy level ratios in atoms",
        is_valid=True,
        mapping_description="note frequency → energy level, harmony → stability, ratio → quantum number",
        justification="Both involve resonant frequency relationships",
    ),
    IsomorphismCase(
        id="I012",
        source_domain="epidemiology",
        source_problem="Diseases spread through contact networks with super-spreader nodes",
        target_domain="social_media",
        target_problem="Viral content spreads through follower networks with influencer nodes",
        is_valid=True,
        mapping_description="disease → content, infection → share, super-spreader → influencer",
        justification="SIR models are directly applied to information spread",
    ),
    IsomorphismCase(
        id="I013",
        source_domain="aviation",
        source_problem="Wing vortices reduce lift and increase drag",
        target_domain="swimming",
        target_problem="Hand entry vortices reduce propulsion and increase drag",
        is_valid=True,
        mapping_description="wing → hand, lift → propulsion, vortex → eddy",
        justification="Fluid dynamics is the same in both domains",
    ),
    IsomorphismCase(
        id="I014",
        source_domain="architecture",
        source_problem="Arches distribute load through compressive forces",
        target_domain="biology",
        target_problem="Bone trabeculae distribute load along lines of stress",
        is_valid=True,
        mapping_description="arch → trabecula, load → mechanical stress, compression → bone remodeling",
        justification="Wolff's law directly mirrors structural engineering principles",
    ),
    IsomorphismCase(
        id="I015",
        source_domain="astronomy",
        source_problem="Planetary orbits are stable due to gravitational balance",
        target_domain="chemistry",
        target_problem="Electron orbitals are stable due to electrostatic balance",
        is_valid=True,
        mapping_description="planet → electron, gravity → Coulomb force, orbit → orbital",
        justification="Bohr model explicitly used this analogy",
    ),
    IsomorphismCase(
        id="I016",
        source_domain="neuroscience",
        source_problem="Long-term potentiation strengthens synapses through repeated activation",
        target_domain="ml",
        target_problem="Gradient descent strengthens weights through repeated training iterations",
        is_valid=True,
        mapping_description="synapse → weight, LTP → parameter update, repeated activation → epoch",
        justification="Hebbian learning directly inspired neural network training",
    ),
    IsomorphismCase(
        id="I017",
        source_domain="mycology",
        source_problem="Fungal mycelium distributes nutrients across a network",
        target_domain="internet",
        target_problem="Packet-switched networks route data across nodes",
        is_valid=True,
        mapping_description="mycelium → fiber optic, nutrient → packet, hypha → link",
        justification="Both are adaptive resource distribution networks",
    ),
    IsomorphismCase(
        id="I018",
        source_domain="immunology",
        source_problem="Immune tolerance prevents attack on self-cells",
        target_domain="ml",
        target_problem="Regularization prevents overfitting to training data",
        is_valid=True,
        mapping_description="immune system → model, self-cell → training distribution, attack → overfitting",
        justification="Both are negative feedback mechanisms for system stability",
    ),
    IsomorphismCase(
        id="I019",
        source_domain="materials",
        source_problem="Dislocations allow metals to deform plastically",
        target_domain="urban_planning",
        target_problem="Alternative routes allow traffic to flow around congestion",
        is_valid=True,
        mapping_description="dislocation → detour, crystal lattice → road network, slip → traffic flow",
        justification="Both involve defect-mediated flow in constrained networks",
    ),
    IsomorphismCase(
        id="I020",
        source_domain="genetics",
        source_problem="Crossing over shuffles alleles during meiosis",
        target_domain="optimization",
        target_problem="Genetic algorithms use crossover to combine solutions",
        is_valid=True,
        mapping_description="chromosome → solution, allele → parameter, meiosis → generation",
        justification="Genetic algorithms are explicitly modeled on genetics",
    ),
    # === INVALID ANALOGIES (is_valid=False) ===
    IsomorphismCase(
        id="I021",
        source_domain="physics",
        source_problem="Quantum superposition allows particles to exist in multiple states",
        target_domain="psychology",
        target_problem="Ambivalence allows people to hold multiple opinions",
        is_valid=False,
        mapping_description="superposition → ambivalence",
        justification="Superposition is a physical state, not a psychological one; no mathematical isomorphism",
    ),
    IsomorphismCase(
        id="I022",
        source_domain="biology",
        source_problem="Photosynthesis converts light to chemical energy",
        target_domain="economics",
        target_problem="Banking converts deposits to loans",
        is_valid=False,
        mapping_description="light → deposit, chemical energy → loan",
        justification="No structural similarity; banking is intermediation, not energy conversion",
    ),
    IsomorphismCase(
        id="I023",
        source_domain="astronomy",
        source_problem="Black holes have event horizons from which nothing escapes",
        target_domain="sociology",
        target_problem="Totalitarian regimes have borders from which nothing escapes",
        is_valid=False,
        mapping_description="event horizon → border",
        justification="Metaphorical similarity only; no shared mathematical structure",
    ),
    IsomorphismCase(
        id="I024",
        source_domain="chemistry",
        source_problem="Radioactive decay follows exponential kinetics",
        target_domain="linguistics",
        target_problem="Language change follows exponential diffusion",
        is_valid=False,
        mapping_description="decay → language change, half-life → adoption rate",
        justification="Both may be exponential but the underlying mechanisms are unrelated",
    ),
    IsomorphismCase(
        id="I025",
        source_domain="neuroscience",
        source_problem="Action potentials are all-or-nothing electrical spikes",
        target_domain="digital_logic",
        target_problem="Logic gates output binary signals",
        is_valid=False,
        mapping_description="action potential → logic gate output",
        justification="Neurons are analog-digital hybrid; logic gates are purely digital; no deep structural match",
    ),
    IsomorphismCase(
        id="I026",
        source_domain="ecology",
        source_problem="Keystone species maintain ecosystem structure",
        target_domain="business",
        target_problem="Key employees maintain company structure",
        is_valid=False,
        mapping_description="keystone species → key employee",
        justification="Loose metaphor; no formal network-theoretic isomorphism has been established",
    ),
    IsomorphismCase(
        id="I027",
        source_domain="thermodynamics",
        source_problem="Entropy always increases in closed systems",
        target_domain="information_theory",
        target_problem="Information entropy always increases in closed systems",
        is_valid=False,
        mapping_description="thermodynamic entropy → information entropy",
        justification="Shannon entropy does not always increase; the Second Law does not apply directly",
    ),
    IsomorphismCase(
        id="I028",
        source_domain="physics",
        source_problem="Wave-particle duality means light is both wave and particle",
        target_domain="philosophy",
        target_problem="Mind-body dualism means humans are both mind and body",
        is_valid=False,
        mapping_description="wave-particle → mind-body",
        justification="Deep philosophical differences; quantum duality is experimentally verified, mind-body is not",
    ),
    IsomorphismCase(
        id="I029",
        source_domain="biology",
        source_problem="Natural selection optimizes fitness in populations",
        target_domain="engineering",
        target_problem="Evolutionary algorithms optimize objective functions",
        is_valid=False,
        mapping_description="natural selection → evolutionary algorithm",
        justification="EAs are inspired by but do not perfectly mirror natural selection (no genetic drift, no neutral theory)",
    ),
    IsomorphismCase(
        id="I030",
        source_domain="medicine",
        source_problem="Vaccines prime the immune system against future infections",
        target_domain="computer_security",
        target_problem="Antivirus software primes the system against future malware",
        is_valid=False,
        mapping_description="vaccine → antivirus",
        justification="Antivirus is reactive/signature-based, not adaptive like immune memory; poor structural match",
    ),
    IsomorphismCase(
        id="I031",
        source_domain="geology",
        source_problem="Tectonic plates float on the asthenosphere",
        target_domain="biology",
        target_problem="Cells float in extracellular fluid",
        is_valid=False,
        mapping_description="plate → cell, asthenosphere → extracellular fluid",
        justification="No shared dynamics; plates are rigid solids, cells are soft matter with active processes",
    ),
    IsomorphismCase(
        id="I032",
        source_domain="music",
        source_problem="Dissonance creates tension that resolves into consonance",
        target_domain="narrative",
        target_problem="Conflict creates tension that resolves into denouement",
        is_valid=False,
        mapping_description="dissonance → conflict, consonance → resolution",
        justification="Metaphorical only; no formal tension-resolution theory bridges both domains",
    ),
    IsomorphismCase(
        id="I033",
        source_domain="chemistry",
        source_problem="Chemical bonds form to minimize potential energy",
        target_domain="sociology",
        target_problem="Social bonds form to minimize social tension",
        is_valid=False,
        mapping_description="chemical bond → social bond, energy → tension",
        justification="Metaphor only; no shared Hamiltonian or optimization framework",
    ),
    IsomorphismCase(
        id="I034",
        source_domain="physics",
        source_problem="Relativity shows space and time are unified",
        target_domain="cognitive_science",
        target_problem="Perception shows space and time are unified",
        is_valid=False,
        mapping_description="spacetime → perceptual space-time",
        justification="Perceptual space-time is psychological, not Minkowskian; no formal unification",
    ),
    IsomorphismCase(
        id="I035",
        source_domain="botany",
        source_problem="Roots grow downward toward water and nutrients",
        target_domain="economics",
        target_problem="Investments flow toward profitable markets",
        is_valid=False,
        mapping_description="roots → investments, water → profit",
        justification="Loose directional analogy; no shared growth/network model",
    ),
    IsomorphismCase(
        id="I036",
        source_domain="linguistics",
        source_problem="Syntax governs sentence structure",
        target_domain="architecture",
        target_problem="Structure governs building form",
        is_valid=False,
        mapping_description="syntax → structure, sentence → building",
        justification="Both involve structure but no formal grammar maps to architecture",
    ),
    IsomorphismCase(
        id="I037",
        source_domain="astronomy",
        source_problem="Stars fuse hydrogen into helium",
        target_domain="cooking",
        target_problem="Ovens transform raw ingredients into cooked food",
        is_valid=False,
        mapping_description="star → oven, hydrogen → raw ingredients",
        justification="Both are transformation processes but no structural analogy (nuclear vs chemical)",
    ),
    IsomorphismCase(
        id="I038",
        source_domain="immunology",
        source_problem="The immune system distinguishes self from non-self",
        target_domain="politics",
        target_problem="Immigration policy distinguishes citizens from non-citizens",
        is_valid=False,
        mapping_description="self → citizen, non-self → non-citizen",
        justification="Metaphorical only; no shared pattern recognition or tolerance mechanism",
    ),
    IsomorphismCase(
        id="I039",
        source_domain="genetics",
        source_problem="DNA mutations introduce genetic variation",
        target_domain="software",
        target_problem="Code changes introduce software variation",
        is_valid=False,
        mapping_description="mutation → code change",
        justification="Both introduce variation but selection mechanisms and heredity are entirely different",
    ),
    IsomorphismCase(
        id="I040",
        source_domain="materials",
        source_problem="Grain boundaries strengthen polycrystalline materials",
        target_domain="sociology",
        target_problem="Cultural boundaries strengthen multicultural societies",
        is_valid=False,
        mapping_description="grain boundary → cultural boundary",
        justification="Metaphor only; Hall-Petch relation has no social analog",
    ),
]

BENCHMARK_META = {
    "total_pairs": 40,
    "valid_analogies": 20,
    "invalid_analogies": 20,
    "domains": sorted({c.source_domain for c in ISOMORPHISM_CASES} | {c.target_domain for c in ISOMORPHISM_CASES}),
}


def run_isomorphism_benchmark(
    detector: Any | None = None,
) -> dict[str, Any]:
    """Run isomorphism benchmark.

    Args:
        detector: Callable that takes (source_problem, target_problem) and returns
                  float in [0,1] where higher = more likely valid.
                  If None, uses random baseline.

    Returns:
        Dictionary with ROC-AUC, accuracy, and per-pair results.
    """
    import random

    if detector is None:

        def detector(source: str, target: str) -> float:  # noqa: ARG001
            return random.random()

    results: list[dict[str, Any]] = []
    start = time.perf_counter()

    for case in ISOMORPHISM_CASES:
        t0 = time.perf_counter()
        score = detector(case.source_problem, case.target_problem)
        latency = (time.perf_counter() - t0) * 1000

        results.append(
            {
                "case_id": case.id,
                "score": round(score, 4),
                "ground_truth_valid": case.is_valid,
                "source_domain": case.source_domain,
                "target_domain": case.target_domain,
                "latency_ms": round(latency, 2),
            }
        )

    try:
        from sklearn.metrics import roc_auc_score

        y_true = [1 if r["ground_truth_valid"] else 0 for r in results]
        y_scores = [r["score"] for r in results]
        roc_auc = roc_auc_score(y_true, y_scores)
    except ImportError:
        roc_auc = None

    correct = sum(
        1
        for r in results
        if (r["score"] >= 0.5 and r["ground_truth_valid"])
        or (r["score"] < 0.5 and not r["ground_truth_valid"])
    )
    accuracy = correct / len(results) if results else 0.0

    total_time = (time.perf_counter() - start) * 1000
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0.0

    summary = {
        "benchmark": "isomorphism",
        "version": "v5.0-alpha",
        "timestamp": datetime.utcnow().isoformat(),
        "meta": BENCHMARK_META,
        "aggregate": {
            "cases_tested": len(ISOMORPHISM_CASES),
            "accuracy_at_0.5": round(accuracy, 4),
            "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
            "avg_latency_ms": round(avg_latency, 2),
            "total_time_ms": round(total_time, 2),
        },
        "results": results,
    }

    return summary


def main() -> None:
    """CLI entry point."""
    summary = run_isomorphism_benchmark()

    out_dir = Path("benchmark_results")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"isomorphism_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(summary, indent=2))

    print("Isomorphism Benchmark v5.0-alpha")
    print(f"Cases tested: {summary['aggregate']['cases_tested']}")
    print(f"Accuracy@0.5: {summary['aggregate']['accuracy_at_0.5']:.2%}")
    if summary["aggregate"]["roc_auc"] is not None:
        print(f"ROC-AUC:      {summary['aggregate']['roc_auc']:.4f}")
    print(f"Avg Latency:  {summary['aggregate']['avg_latency_ms']:.1f}ms")
    print(f"Results written to: {out_file}")


if __name__ == "__main__":
    main()
