#!/usr/bin/env python3
"""Replace broad 'except Exception' with specific exceptions systematically."""
import os
import re
import sys


# Mapping of files todo - I'll process them in batches
replacements = [
    # patterns/library files
    ("src/patterns/library/percolation.py", 211, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/metapopulation.py", 261, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/optimization.py", 153, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/open_quantum.py", 231, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/maxwell_fdtd.py", 225, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/__init__.py", 27, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/__init__.py", 263, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/monte_carlo.py", 212, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/fractal_mandelbrot.py", 146, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/supply_chain.py", 136, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/gene_regulatory.py", 246, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/epidemic_seir.py", 197, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/poisson_solver.py", 221, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/plasma_pic/pattern.py", 277, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/forest_gap.py", 240, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/discrete_event.py", 203, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/neural_network.py", 160, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/ising_model.py", 190, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/cellular_automata.py", 144, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/lotka_volterra.py", 193, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/loader.py", 513, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/reaction_diffusion.py", 169, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/spring_mass.py", 146, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/circuit_simulation/pattern.py", 191, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/circuit_simulation/core.py", 255, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/circuit_simulation/core.py", 434, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/signal_transduction/pattern.py", 228, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/fractal_julia.py", 147, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/wave_optics.py", 247, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/dsge.py", 155, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/monte_carlo_pi.py", 123, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/phase_field.py", 169, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/projectile_motion.py", 149, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/state_space.py", 210, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/state_space.py", 239, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/enzyme_kinetics/pattern.py", 211, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/protein_folding.py", 248, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/synaptic_plasticity.py", 276, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/qft_lattice.py", 202, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/runner.py", 232, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/runner.py", 288, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/runner.py", 297, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/system_dynamics/core.py", 204, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/bootstrap.py", 131, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/pharmacokinetics.py", 166, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/dft.py", 210, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/thermal.py", 215, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/quantum_harmonic_oscillator.py", 137, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/hodgkin_huxley.py", 202, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/neural_mass.py", 248, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/population_genetics.py", 155, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/spatial_ecology.py", 191, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/fisheries.py", 264, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/epidemic_sir.py", 149, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/agent_based.py", 258, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/markov_chain.py", 134, "(ImportError, AttributeError, RuntimeError)"),
    ("src/patterns/library/percolation.py", 211, "(ImportError, AttributeError, RuntimeError)"),
]

fixed = 0
failed = 0

for filepath, line_num, exception_type in replacements:
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        failed += 1
        continue
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if line_num < 1 or line_num > len(lines):
        print(f"Line {line_num} out of range for {filepath}")
        failed += 1
        continue
    
    # Line numbers are 1-based, list indices are 0-based
    idx = line_num - 1
    old_line = lines[idx]
    
    # Check if the line contains 'except Exception'
    if 'except Exception' not in old_line:
        print(f"Line {line_num} doesn't contain 'except Exception' in {filepath}")
        failed += 1
        continue
    
    # Replace 'except Exception' with specific exception
    new_line = old_line.replace('except Exception', f'except {exception_type} as e:')
    
    if new_line == old_line:
        print(f"No change needed for {filepath} line {line_num}")
        continue
    
    lines[idx] = new_line
    
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print(f"Fixed: {filepath} line {line_num}")
    fixed += 1

print(f"\nSummary: {fixed} fixed, {failed} failed")
