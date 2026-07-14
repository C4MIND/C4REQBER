"""c4reqber — AI Meta-Solver for Scientific Discovery.

Supports: python -m c4reqber

BLAST CLI — 4-Mode System:
  blast solve       → Problem solving (UniversalSolvePipeline)
  blast turbo       → Research proposals (HILDiscoveryPipeline)
  blast flash       → Quick answers
  blast turbofactory → Parallel paradigm factory
"""
from __future__ import annotations

from src.cli.blast_app import app


if __name__ == "__main__":
    app()
