"""
Novelty Benchmark: Known Duplicate Pairs vs Genuinely Novel Pairs

Evaluates Reqber's novelty detection by testing if it can distinguish:
- Known duplicates (same idea, different wording)
- Genuinely novel pairs (different ideas)

Usage:
    python -m src.benchmarks.novelty_benchmark

Results are written to `benchmark_results/novelty_<timestamp>.json`.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NoveltyPair:
    """A pair of scientific claims with known ground-truth novelty."""

    id: str
    claim_a: str
    claim_b: str
    is_novel: bool  # True if claim_b is genuinely novel relative to claim_a
    domain: str
    justification: str


NOVELTY_PAIRS: list[NoveltyPair] = [
    # === DUPLICATES (is_novel=False) ===
    NoveltyPair(
        id="N001",
        claim_a="Memory consolidation occurs during slow-wave sleep",
        claim_b="Slow-wave sleep is critical for memory consolidation",
        is_novel=False,
        domain="neuroscience",
        justification="Same claim, reversed word order",
    ),
    NoveltyPair(
        id="N002",
        claim_a="CRISPR-Cas9 can be used to edit mammalian genomes",
        claim_b="Gene editing in mammals is possible using CRISPR technology",
        is_novel=False,
        domain="biotech",
        justification="Paraphrase of the same established result",
    ),
    NoveltyPair(
        id="N003",
        claim_a="Transformer architectures use self-attention mechanisms",
        claim_b="Self-attention is the core mechanism in transformer models",
        is_novel=False,
        domain="ml",
        justification="Same concept from Vaswani et al. 2017",
    ),
    NoveltyPair(
        id="N004",
        claim_a="The Higgs boson gives mass to other particles via the Higgs field",
        claim_b="Particle masses arise from interactions with the Higgs field",
        is_novel=False,
        domain="physics",
        justification="Same Standard Model mechanism",
    ),
    NoveltyPair(
        id="N005",
        claim_a="Photosynthesis converts light energy into chemical energy",
        claim_b="Plants transform sunlight into chemical bonds through photosynthesis",
        is_novel=False,
        domain="biology",
        justification="Same well-known process",
    ),
    NoveltyPair(
        id="N006",
        claim_a="Entanglement allows instantaneous correlation between distant particles",
        claim_b="Quantum entangled particles share correlated states regardless of distance",
        is_novel=False,
        domain="physics",
        justification="Same quantum mechanics principle",
    ),
    NoveltyPair(
        id="N007",
        claim_a="Backpropagation computes gradients via the chain rule",
        claim_b="Neural network training uses the chain rule to calculate derivatives",
        is_novel=False,
        domain="ml",
        justification="Same algorithm, different wording",
    ),
    NoveltyPair(
        id="N008",
        claim_a="Dark matter interacts gravitationally but not electromagnetically",
        claim_b="Dark matter exerts gravity but does not emit or absorb light",
        is_novel=False,
        domain="astrophysics",
        justification="Same astrophysical property",
    ),
    NoveltyPair(
        id="N009",
        claim_a="The citric acid cycle produces NADH and FADH2 for the electron transport chain",
        claim_b="Krebs cycle generates electron carriers that feed oxidative phosphorylation",
        is_novel=False,
        domain="biology",
        justification="Same metabolic pathway",
    ),
    NoveltyPair(
        id="N010",
        claim_a="Convolutional layers detect spatial hierarchies in images",
        claim_b="CNNs learn spatial feature hierarchies through convolution operations",
        is_novel=False,
        domain="ml",
        justification="Same architectural concept",
    ),
    NoveltyPair(
        id="N011",
        claim_a="mRNA vaccines deliver genetic instructions to produce antigens",
        claim_b="Messenger RNA-based vaccines instruct cells to synthesize target proteins",
        is_novel=False,
        domain="medicine",
        justification="Same vaccine mechanism",
    ),
    NoveltyPair(
        id="N012",
        claim_a="Superconductors exhibit zero electrical resistance below a critical temperature",
        claim_b="Below Tc, superconducting materials conduct electricity without resistance",
        is_novel=False,
        domain="physics",
        justification="Same definition",
    ),
    NoveltyPair(
        id="N013",
        claim_a="Reinforcement learning optimizes policies through reward feedback",
        claim_b="RL agents learn optimal behavior by maximizing cumulative rewards",
        is_novel=False,
        domain="ml",
        justification="Same paradigm",
    ),
    NoveltyPair(
        id="N014",
        claim_a="The ribosome translates mRNA into proteins using tRNA adapters",
        claim_b="Protein synthesis occurs when ribosomes decode mRNA with tRNA help",
        is_novel=False,
        domain="biology",
        justification="Same central dogma",
    ),
    NoveltyPair(
        id="N015",
        claim_a="Black holes have an event horizon from which nothing escapes",
        claim_b="The event horizon of a black hole marks the point of no return",
        is_novel=False,
        domain="astrophysics",
        justification="Same concept",
    ),
    NoveltyPair(
        id="N016",
        claim_a="Gradient boosting combines weak learners sequentially to correct errors",
        claim_b="AdaBoost and XGBoost build ensembles by iteratively fitting residuals",
        is_novel=False,
        domain="ml",
        justification="Same ensemble principle",
    ),
    NoveltyPair(
        id="N017",
        claim_a="Neurons communicate via action potentials traveling along axons",
        claim_b="Electrical signals called action potentials propagate down neuronal axons",
        is_novel=False,
        domain="neuroscience",
        justification="Same physiology",
    ),
    NoveltyPair(
        id="N018",
        claim_a="The uncertainty principle limits simultaneous knowledge of position and momentum",
        claim_b="Heisenberg's principle states position and momentum cannot both be known precisely",
        is_novel=False,
        domain="physics",
        justification="Same principle",
    ),
    NoveltyPair(
        id="N019",
        claim_a="Ozone absorbs UV radiation in the stratosphere",
        claim_b="The ozone layer blocks ultraviolet light from reaching Earth's surface",
        is_novel=False,
        domain="earth_science",
        justification="Same atmospheric chemistry",
    ),
    NoveltyPair(
        id="N020",
        claim_a="Graph neural networks propagate information along graph edges",
        claim_b="GNNs update node representations via message passing over edges",
        is_novel=False,
        domain="ml",
        justification="Same architecture",
    ),
    NoveltyPair(
        id="N021",
        claim_a="Antibiotics target bacterial cell wall synthesis or protein production",
        claim_b="Antimicrobial agents kill bacteria by disrupting cell walls or ribosomes",
        is_novel=False,
        domain="medicine",
        justification="Same mechanism class",
    ),
    NoveltyPair(
        id="N022",
        claim_a="Plate tectonics explains continental drift and seismic activity",
        claim_b="Earth's lithospheric plates move, causing earthquakes and mountain formation",
        is_novel=False,
        domain="earth_science",
        justification="Same geological theory",
    ),
    NoveltyPair(
        id="N023",
        claim_a="Attention mechanisms weight input tokens by relevance",
        claim_b="Neural attention computes importance scores for each input element",
        is_novel=False,
        domain="ml",
        justification="Same mechanism",
    ),
    NoveltyPair(
        id="N024",
        claim_a="Telomeres shorten with each cell division, limiting replication",
        claim_b="Cellular senescence is caused by progressive telomere attrition",
        is_novel=False,
        domain="biology",
        justification="Same Hayflick limit concept",
    ),
    NoveltyPair(
        id="N025",
        claim_a="The double helix structure of DNA was discovered by Watson and Crick",
        claim_b="DNA has a twisted ladder structure with complementary base pairing",
        is_novel=False,
        domain="biology",
        justification="Same historical fact",
    ),
    # === GENUINELY NOVEL (is_novel=True) ===
    NoveltyPair(
        id="N026",
        claim_a="Sleep consolidates declarative memory through hippocampal replay",
        claim_b="Glia actively participate in memory consolidation via calcium waves during sleep",
        is_novel=True,
        domain="neuroscience",
        justification="Second claim introduces glial mechanism, not in the first",
    ),
    NoveltyPair(
        id="N027",
        claim_a="CRISPR-Cas9 edits DNA by creating double-strand breaks",
        claim_b="Base editing with CRISPR converts C→T without double-strand breaks",
        is_novel=True,
        domain="biotech",
        justification="Base editing is a distinct technology from standard CRISPR",
    ),
    NoveltyPair(
        id="N028",
        claim_a="Transformers use self-attention for sequence modeling",
        claim_b="Mamba architectures replace attention with state space models for linear complexity",
        is_novel=True,
        domain="ml",
        justification="Mamba is a distinct architecture from transformers",
    ),
    NoveltyPair(
        id="N029",
        claim_a="The Higgs mechanism explains electroweak symmetry breaking",
        claim_b="Axions could explain both dark matter and the strong CP problem",
        is_novel=True,
        domain="physics",
        justification="Axions are a distinct hypothetical particle with different physics",
    ),
    NoveltyPair(
        id="N030",
        claim_a="Photosynthesis uses chlorophyll to capture light",
        claim_b="Some bacteria use rhodopsin instead of chlorophyll for phototrophy",
        is_novel=True,
        domain="biology",
        justification="Rhodopsin-based photosynthesis is a distinct mechanism",
    ),
    NoveltyPair(
        id="N031",
        claim_a="Quantum entanglement enables Bell inequality violations",
        claim_b="Entanglement can be used for quantum error correction in topological codes",
        is_novel=True,
        domain="physics",
        justification="Topological quantum error correction is a distinct application",
    ),
    NoveltyPair(
        id="N032",
        claim_a="Backpropagation trains deep networks via gradient descent",
        claim_b="Forward-mode automatic differentiation can train networks without storing activations",
        is_novel=True,
        domain="ml",
        justification="Forward-mode training is a distinct algorithm from backprop",
    ),
    NoveltyPair(
        id="N033",
        claim_a="Dark matter is detected through gravitational lensing",
        claim_b="Self-interacting dark matter could explain galactic core density profiles",
        is_novel=True,
        domain="astrophysics",
        justification="Self-interacting dark matter is a specific hypothesis not implied by lensing",
    ),
    NoveltyPair(
        id="N034",
        claim_a="The citric acid cycle produces energy in mitochondria",
        claim_b="Some cancer cells rewire metabolism to rely on glutaminolysis instead",
        is_novel=True,
        domain="biology",
        justification="Warburg effect / glutaminolysis is a distinct metabolic pathway",
    ),
    NoveltyPair(
        id="N035",
        claim_a="CNNs detect local features in images",
        claim_b="Vision transformers partition images into patches and apply self-attention",
        is_novel=True,
        domain="ml",
        justification="ViTs are a distinct architecture from CNNs",
    ),
    NoveltyPair(
        id="N036",
        claim_a="mRNA vaccines were used for COVID-19",
        claim_b="Self-amplifying RNA vaccines encode both antigen and replicase machinery",
        is_novel=True,
        domain="medicine",
        justification="saRNA is a distinct vaccine platform from standard mRNA",
    ),
    NoveltyPair(
        id="N037",
        claim_a="Superconductors have zero resistance",
        claim_b="Room-temperature superconductivity in hydrides has been reported under high pressure",
        is_novel=True,
        domain="physics",
        justification="Room-temperature superconductivity is a distinct (controversial) claim",
    ),
    NoveltyPair(
        id="N038",
        claim_a="Reinforcement learning requires reward design",
        claim_b="Inverse RL infers reward functions from expert demonstrations",
        is_novel=True,
        domain="ml",
        justification="Inverse RL is a distinct paradigm from standard RL",
    ),
    NoveltyPair(
        id="N039",
        claim_a="Ribosomes synthesize proteins in the cytoplasm",
        claim_b="Some antibiotics target mitochondrial ribosomes, which differ from bacterial ones",
        is_novel=True,
        domain="biology",
        justification="Mitochondrial ribosome specificity is a distinct pharmacological insight",
    ),
    NoveltyPair(
        id="N040",
        claim_a="Black holes emit Hawking radiation",
        claim_b="Information may be preserved in black hole evaporation via soft hair",
        is_novel=True,
        domain="astrophysics",
        justification="Soft hair conjecture is a distinct theoretical proposal",
    ),
    NoveltyPair(
        id="N041",
        claim_a="Gradient boosting uses decision trees as weak learners",
        claim_b="Neural additive models combine gradient boosting with neural network smoothers",
        is_novel=True,
        domain="ml",
        justification="NAMs are a distinct model class from standard GBDT",
    ),
    NoveltyPair(
        id="N042",
        claim_a="Action potentials are all-or-nothing electrical events",
        claim_b="Dendritic spikes are graded, localized depolarizations that boost synaptic input",
        is_novel=True,
        domain="neuroscience",
        justification="Dendritic spikes are a distinct phenomenon from axonal action potentials",
    ),
    NoveltyPair(
        id="N043",
        claim_a="The uncertainty principle is a fundamental limit of quantum mechanics",
        claim_b="Quantum weak measurements can extract partial information without full disturbance",
        is_novel=True,
        domain="physics",
        justification="Weak measurements are a distinct technique from standard measurement",
    ),
    NoveltyPair(
        id="N044",
        claim_a="Ozone depletion was caused by CFCs",
        claim_b="New industrial compounds like HFCs deplete ozone less but are potent greenhouse gases",
        is_novel=True,
        domain="earth_science",
        justification="HFC climate impact is a distinct environmental concern",
    ),
    NoveltyPair(
        id="N045",
        claim_a="GNNs learn on graph-structured data",
        claim_b="Graph diffusion networks simulate continuous diffusion processes on graphs",
        is_novel=True,
        domain="ml",
        justification="Graph diffusion networks are a distinct model class",
    ),
    NoveltyPair(
        id="N046",
        claim_a="Antibiotics kill bacteria",
        claim_b="Bacteriophage therapy uses viruses to target specific bacterial strains",
        is_novel=True,
        domain="medicine",
        justification="Phage therapy is a distinct treatment modality",
    ),
    NoveltyPair(
        id="N047",
        claim_a="Plate tectonics drives volcanic arcs at subduction zones",
        claim_b="Mantle plumes create intraplate volcanism independent of plate boundaries",
        is_novel=True,
        domain="earth_science",
        justification="Mantle plumes are a distinct volcanism mechanism",
    ),
    NoveltyPair(
        id="N048",
        claim_a="Attention computes query-key-value interactions",
        claim_b="Linear attention kernels approximate softmax attention in O(n) time",
        is_novel=True,
        domain="ml",
        justification="Linear attention is a distinct algorithmic approximation",
    ),
    NoveltyPair(
        id="N049",
        claim_a="Telomeres limit cellular lifespan",
        claim_b="Telomerase reactivation can immortalize cells but increases cancer risk",
        is_novel=True,
        domain="biology",
        justification="Telomerase-cancer link is a distinct clinical insight",
    ),
    NoveltyPair(
        id="N050",
        claim_a="DNA is the molecule of heredity",
        claim_b="Prions are infectious proteins that transmit conformational information without nucleic acids",
        is_novel=True,
        domain="biology",
        justification="Prions are a distinct (non-DNA) inheritance mechanism",
    ),
]

BENCHMARK_META = {
    "total_pairs": 50,
    "duplicates": 25,
    "genuinely_novel": 25,
    "domains": sorted({p.domain for p in NOVELTY_PAIRS}),
}


def run_novelty_benchmark(
    detector: Any | None = None,
) -> dict[str, Any]:
    """Run novelty benchmark.

    Args:
        detector: Callable that takes (claim_a, claim_b) and returns float in [0,1]
                  where higher = more novel. If None, uses random baseline.

    Returns:
        Dictionary with ROC-AUC, accuracy, and per-pair results.
    """
    import random

    if detector is None:

        def detector(claim_a: str, claim_b: str) -> float:  # noqa: ARG001
            return random.random()

    results: list[dict[str, Any]] = []
    start = time.perf_counter()

    for pair in NOVELTY_PAIRS:
        t0 = time.perf_counter()
        score = detector(pair.claim_a, pair.claim_b)
        latency = (time.perf_counter() - t0) * 1000

        results.append(
            {
                "pair_id": pair.id,
                "score": round(score, 4),
                "ground_truth_novel": pair.is_novel,
                "domain": pair.domain,
                "latency_ms": round(latency, 2),
            }
        )

    # Compute ROC-AUC
    try:
        from sklearn.metrics import roc_auc_score

        y_true = [1 if r["ground_truth_novel"] else 0 for r in results]
        y_scores = [r["score"] for r in results]
        roc_auc = roc_auc_score(y_true, y_scores)
    except ImportError:
        roc_auc = None

    # Accuracy at threshold 0.5
    correct = sum(
        1
        for r in results
        if (r["score"] >= 0.5 and r["ground_truth_novel"])
        or (r["score"] < 0.5 and not r["ground_truth_novel"])
    )
    accuracy = correct / len(results) if results else 0.0

    total_time = (time.perf_counter() - start) * 1000
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0.0

    summary = {
        "benchmark": "novelty",
        "version": "v5.0-alpha",
        "timestamp": datetime.utcnow().isoformat(),
        "meta": BENCHMARK_META,
        "aggregate": {
            "pairs_tested": len(NOVELTY_PAIRS),
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
    summary = run_novelty_benchmark()

    out_dir = Path("benchmark_results")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"novelty_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(summary, indent=2))

    print("Novelty Benchmark v5.0-alpha")
    print(f"Pairs tested: {summary['aggregate']['pairs_tested']}")
    print(f"Accuracy@0.5: {summary['aggregate']['accuracy_at_0.5']:.2%}")
    if summary["aggregate"]["roc_auc"] is not None:
        print(f"ROC-AUC:      {summary['aggregate']['roc_auc']:.4f}")
    print(f"Avg Latency:  {summary['aggregate']['avg_latency_ms']:.1f}ms")
    print(f"Results written to: {out_file}")


if __name__ == "__main__":
    main()
