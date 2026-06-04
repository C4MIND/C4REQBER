"""
Benchmark runner: Execute all Reqber benchmarks.

Usage:
    python -m src.benchmarks
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from .falsification_benchmark import run_falsification_benchmark
from .isomorphism_benchmark import run_isomorphism_benchmark
from .novelty_benchmark import run_novelty_benchmark
from .triz_benchmark import run_triz_benchmark


def run_all() -> dict[str, dict]:
    """Run all benchmarks and return aggregated results."""
    return {
        "triz": run_triz_benchmark(),
        "novelty": run_novelty_benchmark(),
        "falsification": run_falsification_benchmark(),
        "isomorphism": run_isomorphism_benchmark(),
    }


def main() -> int:
    """CLI entry point."""
    print("=" * 60)
    print("Reqber Benchmark Suite v5.0-alpha")
    print("=" * 60)
    print()

    results = run_all()

    out_dir = Path("benchmark_results")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"all_benchmarks_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(results, indent=2))

    for name, result in results.items():
        print(f"\n{name.upper()} BENCHMARK")
        print("-" * 40)
        agg = result["aggregate"]
        for key, value in agg.items():
            print(f"  {key}: {value}")

    print(f"\nAll results written to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
