"""
Domain Profiles Database
135 domains: 48 Humanities + 87 Exact Sciences

Source: Meta-analysis 2026-04-12
Generated: Phase 3 of Production Swarm Plan
"""

from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class PentadDistribution:
    ACTIVATE: float = 0.0
    INHIBIT: float = 0.0
    MODULATE: float = 0.0
    REGULATE: float = 0.0
    DISRUPT: float = 0.0


@dataclass
class SeptetDistribution:
    STATE: float = 0.0
    STRUCTURE: float = 0.0
    CONTENT: float = 0.0
    FUNCTION: float = 0.0
    RELATIONS: float = 0.0
    MEMORY: float = 0.0
    BOUNDARY: float = 0.0


@dataclass
class DomainProfile:
    name: str
    category: str  # "humanities" | "exact_sciences"
    subdomain: str
    total_processes: int
    pentad: PentadDistribution
    septet: SeptetDistribution
    reversibility_yes: float
    reversibility_conditional: float
    reversibility_no: float
    signature: str = ""  # e.g., "ACTIVATE × STRUCTURE"


# ═══════════════════════════════════════════════════════════════════════════════
# EXACT SCIENCES (87 domains) - Generated from scraping data
# ═══════════════════════════════════════════════════════════════════════════════

EXACT_SCIENCES_PROFILES = {
    # Mathematics (16)
    "mathematics/algebra": DomainProfile(
        name="Algebra",
        category="exact_sciences",
        subdomain="algebra",
        total_processes=282,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.02, MODULATE=0.02, REGULATE=0.01, DISRUPT=0.06),
        septet=SeptetDistribution(STATE=0.16, STRUCTURE=0.50, CONTENT=0.04, FUNCTION=0.15, RELATIONS=0.02, MEMORY=0.05, BOUNDARY=0.01),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/analysis": DomainProfile(
        name="Analysis",
        category="exact_sciences",
        subdomain="analysis",
        total_processes=127,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.02, MODULATE=0.03, REGULATE=0.04, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.14, STRUCTURE=0.28, CONTENT=0.06, FUNCTION=0.16, RELATIONS=0.17, MEMORY=0.07, BOUNDARY=0.02),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="DISRUPT × STRUCTURE",
    ),
    "mathematics/geometry": DomainProfile(
        name="Geometry",
        category="exact_sciences",
        subdomain="geometry",
        total_processes=183,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.00, MODULATE=0.02, REGULATE=0.07, DISRUPT=0.07),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.46, CONTENT=0.03, FUNCTION=0.06, RELATIONS=0.04, MEMORY=0.10, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="REGULATE × STRUCTURE",
    ),
    "mathematics/topology": DomainProfile(
        name="Topology",
        category="exact_sciences",
        subdomain="topology",
        total_processes=219,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.00, MODULATE=0.01, REGULATE=0.02, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.08, STRUCTURE=0.78, CONTENT=0.04, FUNCTION=0.04, RELATIONS=0.01, MEMORY=0.00, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/number_theory": DomainProfile(
        name="Number Theory",
        category="exact_sciences",
        subdomain="number_theory",
        total_processes=173,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.03, MODULATE=0.02, REGULATE=0.03, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.19, STRUCTURE=0.25, CONTENT=0.06, FUNCTION=0.20, RELATIONS=0.07, MEMORY=0.10, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/logic": DomainProfile(
        name="Logic",
        category="exact_sciences",
        subdomain="logic",
        total_processes=364,
        pentad=PentadDistribution(ACTIVATE=0.03, INHIBIT=0.02, MODULATE=0.03, REGULATE=0.03, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.17, STRUCTURE=0.59, CONTENT=0.02, FUNCTION=0.03, RELATIONS=0.07, MEMORY=0.01, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/set_theory": DomainProfile(
        name="Set Theory",
        category="exact_sciences",
        subdomain="set_theory",
        total_processes=139,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.04, MODULATE=0.04, REGULATE=0.01, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.30, STRUCTURE=0.35, CONTENT=0.04, FUNCTION=0.05, RELATIONS=0.12, MEMORY=0.04, BOUNDARY=0.01),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/category_theory": DomainProfile(
        name="Category Theory",
        category="exact_sciences",
        subdomain="category_theory",
        total_processes=109,
        pentad=PentadDistribution(ACTIVATE=0.08, INHIBIT=0.03, MODULATE=0.05, REGULATE=0.05, DISRUPT=0.14),
        septet=SeptetDistribution(STATE=0.13, STRUCTURE=0.47, CONTENT=0.04, FUNCTION=0.13, RELATIONS=0.07, MEMORY=0.03, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="DISRUPT × STRUCTURE",
    ),
    "mathematics/combinatorics": DomainProfile(
        name="Combinatorics",
        category="exact_sciences",
        subdomain="combinatorics",
        total_processes=107,
        pentad=PentadDistribution(ACTIVATE=0.09, INHIBIT=0.04, MODULATE=0.02, REGULATE=0.03, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.13, STRUCTURE=0.39, CONTENT=0.05, FUNCTION=0.07, RELATIONS=0.16, MEMORY=0.07, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/graph_theory": DomainProfile(
        name="Graph Theory",
        category="exact_sciences",
        subdomain="graph_theory",
        total_processes=223,
        pentad=PentadDistribution(ACTIVATE=0.09, INHIBIT=0.02, MODULATE=0.01, REGULATE=0.08, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.19, STRUCTURE=0.37, CONTENT=0.03, FUNCTION=0.05, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.18),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/numerical_analysis": DomainProfile(
        name="Numerical Analysis",
        category="exact_sciences",
        subdomain="numerical_analysis",
        total_processes=116,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.04, MODULATE=0.05, REGULATE=0.09, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.28, CONTENT=0.09, FUNCTION=0.18, RELATIONS=0.02, MEMORY=0.02, BOUNDARY=0.01),
        reversibility_yes=0.02, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/optimization": DomainProfile(
        name="Optimization",
        category="exact_sciences",
        subdomain="optimization",
        total_processes=199,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.14, MODULATE=0.04, REGULATE=0.10, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.26, STRUCTURE=0.21, CONTENT=0.05, FUNCTION=0.26, RELATIONS=0.04, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="INHIBIT × FUNCTION",
    ),
    "mathematics/differential_equations": DomainProfile(
        name="Differential Equations",
        category="exact_sciences",
        subdomain="differential_equations",
        total_processes=109,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.02, MODULATE=0.02, REGULATE=0.04, DISRUPT=0.06),
        septet=SeptetDistribution(STATE=0.28, STRUCTURE=0.29, CONTENT=0.03, FUNCTION=0.24, RELATIONS=0.03, MEMORY=0.01, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/mathematical_physics": DomainProfile(
        name="Mathematical Physics",
        category="exact_sciences",
        subdomain="mathematical_physics",
        total_processes=109,
        pentad=PentadDistribution(ACTIVATE=0.08, INHIBIT=0.04, MODULATE=0.05, REGULATE=0.08, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.31, STRUCTURE=0.34, CONTENT=0.04, FUNCTION=0.10, RELATIONS=0.07, MEMORY=0.01, BOUNDARY=0.05),
        reversibility_yes=0.01, reversibility_conditional=0.96, reversibility_no=0.03,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/probability_theory": DomainProfile(
        name="Probability Theory",
        category="exact_sciences",
        subdomain="probability_theory",
        total_processes=98,
        pentad=PentadDistribution(ACTIVATE=0.14, INHIBIT=0.04, MODULATE=0.03, REGULATE=0.05, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.29, STRUCTURE=0.30, CONTENT=0.04, FUNCTION=0.15, RELATIONS=0.03, MEMORY=0.02, BOUNDARY=0.04),
        reversibility_yes=0.01, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="ACTIVATE × STRUCTURE",
    ),
    "mathematics/statistics": DomainProfile(
        name="Statistics",
        category="exact_sciences",
        subdomain="statistics",
        total_processes=221,
        pentad=PentadDistribution(ACTIVATE=0.09, INHIBIT=0.02, MODULATE=0.07, REGULATE=0.07, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.21, STRUCTURE=0.25, CONTENT=0.24, FUNCTION=0.06, RELATIONS=0.07, MEMORY=0.02, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    
    # Physics (12)
    "physics/classical_mechanics": DomainProfile(
        name="Classical Mechanics",
        category="exact_sciences",
        subdomain="classical_mechanics",
        total_processes=208,
        pentad=PentadDistribution(ACTIVATE=0.09, INHIBIT=0.07, MODULATE=0.02, REGULATE=0.12, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.25, STRUCTURE=0.23, CONTENT=0.06, FUNCTION=0.19, RELATIONS=0.05, MEMORY=0.04, BOUNDARY=0.05),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="REGULATE × STATE",
    ),
    "physics/electromagnetism": DomainProfile(
        name="Electromagnetism",
        category="exact_sciences",
        subdomain="electromagnetism",
        total_processes=162,
        pentad=PentadDistribution(ACTIVATE=0.15, INHIBIT=0.05, MODULATE=0.03, REGULATE=0.04, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.23, STRUCTURE=0.15, CONTENT=0.07, FUNCTION=0.25, RELATIONS=0.07, MEMORY=0.06, BOUNDARY=0.05),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="ACTIVATE × FUNCTION",
    ),
    "physics/thermodynamics": DomainProfile(
        name="Thermodynamics",
        category="exact_sciences",
        subdomain="thermodynamics",
        total_processes=198,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.05, MODULATE=0.04, REGULATE=0.09, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.38, STRUCTURE=0.12, CONTENT=0.10, FUNCTION=0.19, RELATIONS=0.06, MEMORY=0.04, BOUNDARY=0.04),
        reversibility_yes=0.01, reversibility_conditional=0.96, reversibility_no=0.03,
        signature="ACTIVATE × STATE",
    ),
    "physics/quantum_mechanics": DomainProfile(
        name="Quantum Mechanics",
        category="exact_sciences",
        subdomain="quantum_mechanics",
        total_processes=241,
        pentad=PentadDistribution(ACTIVATE=0.17, INHIBIT=0.06, MODULATE=0.03, REGULATE=0.07, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.34, STRUCTURE=0.14, CONTENT=0.10, FUNCTION=0.22, RELATIONS=0.06, MEMORY=0.04, BOUNDARY=0.04),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="ACTIVATE × STATE",
    ),
    "physics/relativity": DomainProfile(
        name="Relativity",
        category="exact_sciences",
        subdomain="relativity",
        total_processes=182,
        pentad=PentadDistribution(ACTIVATE=0.14, INHIBIT=0.06, MODULATE=0.04, REGULATE=0.09, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.32, STRUCTURE=0.16, CONTENT=0.09, FUNCTION=0.20, RELATIONS=0.07, MEMORY=0.05, BOUNDARY=0.05),
        reversibility_yes=0.01, reversibility_conditional=0.96, reversibility_no=0.03,
        signature="ACTIVATE × STATE",
    ),
    "physics/particle_physics": DomainProfile(
        name="Particle Physics",
        category="exact_sciences",
        subdomain="particle_physics",
        total_processes=180,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.08, MODULATE=0.03, REGULATE=0.04, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.36, STRUCTURE=0.12, CONTENT=0.14, FUNCTION=0.21, RELATIONS=0.04, MEMORY=0.02, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="ACTIVATE × STATE",
    ),
    "physics/condensed_matter": DomainProfile(
        name="Condensed Matter",
        category="exact_sciences",
        subdomain="condensed_matter",
        total_processes=259,
        pentad=PentadDistribution(ACTIVATE=0.08, INHIBIT=0.03, MODULATE=0.02, REGULATE=0.05, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.42, STRUCTURE=0.10, CONTENT=0.22, FUNCTION=0.14, RELATIONS=0.03, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="DISRUPT × STATE",
    ),
    "physics/optics": DomainProfile(
        name="Optics",
        category="exact_sciences",
        subdomain="optics",
        total_processes=310,
        pentad=PentadDistribution(ACTIVATE=0.13, INHIBIT=0.06, MODULATE=0.03, REGULATE=0.08, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.30, STRUCTURE=0.14, CONTENT=0.09, FUNCTION=0.23, RELATIONS=0.03, MEMORY=0.04, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="ACTIVATE × STATE",
    ),
    "physics/acoustics": DomainProfile(
        name="Acoustics",
        category="exact_sciences",
        subdomain="acoustics",
        total_processes=155,
        pentad=PentadDistribution(ACTIVATE=0.17, INHIBIT=0.06, MODULATE=0.02, REGULATE=0.09, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.19, CONTENT=0.05, FUNCTION=0.23, RELATIONS=0.04, MEMORY=0.06, BOUNDARY=0.08),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="ACTIVATE × FUNCTION",
    ),
    "physics/fluid_dynamics": DomainProfile(
        name="Fluid Dynamics",
        category="exact_sciences",
        subdomain="fluid_dynamics",
        total_processes=162,
        pentad=PentadDistribution(ACTIVATE=0.13, INHIBIT=0.09, MODULATE=0.02, REGULATE=0.11, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.35, STRUCTURE=0.15, CONTENT=0.06, FUNCTION=0.17, RELATIONS=0.04, MEMORY=0.01, BOUNDARY=0.07),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="ACTIVATE × STATE",
    ),
    "physics/plasma_physics": DomainProfile(
        name="Plasma Physics",
        category="exact_sciences",
        subdomain="plasma_physics",
        total_processes=177,
        pentad=PentadDistribution(ACTIVATE=0.15, INHIBIT=0.05, MODULATE=0.03, REGULATE=0.07, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.34, STRUCTURE=0.13, CONTENT=0.11, FUNCTION=0.21, RELATIONS=0.05, MEMORY=0.04, BOUNDARY=0.04),
        reversibility_yes=0.01, reversibility_conditional=0.96, reversibility_no=0.03,
        signature="ACTIVATE × STATE",
    ),
    "physics/nuclear_physics": DomainProfile(
        name="Nuclear Physics",
        category="exact_sciences",
        subdomain="nuclear_physics",
        total_processes=182,
        pentad=PentadDistribution(ACTIVATE=0.19, INHIBIT=0.05, MODULATE=0.02, REGULATE=0.03, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.32, STRUCTURE=0.14, CONTENT=0.08, FUNCTION=0.26, RELATIONS=0.03, MEMORY=0.04, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.96, reversibility_no=0.04,
        signature="ACTIVATE × STATE",
    ),
    "physics/astronomy": DomainProfile(
        name="Astronomy",
        category="exact_sciences",
        subdomain="astronomy",
        total_processes=324,
        pentad=PentadDistribution(ACTIVATE=0.21, INHIBIT=0.04, MODULATE=0.05, REGULATE=0.06, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.45, STRUCTURE=0.18, CONTENT=0.08, FUNCTION=0.14, RELATIONS=0.05, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.01, reversibility_conditional=0.95, reversibility_no=0.04,
        signature="ACTIVATE × STATE",
    ),
    
    # Chemistry (10)
    "chemistry/quantum_chemistry": DomainProfile(
        name="Quantum Chemistry",
        category="exact_sciences",
        subdomain="quantum_chemistry",
        total_processes=72,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.03, MODULATE=0.03, REGULATE=0.03, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.26, STRUCTURE=0.22, CONTENT=0.07, FUNCTION=0.19, RELATIONS=0.15, MEMORY=0.04, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STATE",
    ),
    "chemistry/thermochemistry": DomainProfile(
        name="Thermochemistry",
        category="exact_sciences",
        subdomain="thermochemistry",
        total_processes=30,
        pentad=PentadDistribution(ACTIVATE=0.03, INHIBIT=0.00, MODULATE=0.00, REGULATE=0.03, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.27, STRUCTURE=0.27, CONTENT=0.13, FUNCTION=0.27, RELATIONS=0.03, MEMORY=0.03, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="DISRUPT × STATE",
    ),
    "chemistry/chemical_kinetics": DomainProfile(
        name="Chemical Kinetics",
        category="exact_sciences",
        subdomain="chemical_kinetics",
        total_processes=109,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.02, MODULATE=0.01, REGULATE=0.06, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.09, CONTENT=0.05, FUNCTION=0.60, RELATIONS=0.00, MEMORY=0.02, BOUNDARY=0.01),
        reversibility_yes=0.01, reversibility_conditional=0.96, reversibility_no=0.03,
        signature="ACTIVATE × FUNCTION",
    ),
    "chemistry/electrochemistry": DomainProfile(
        name="Electrochemistry",
        category="exact_sciences",
        subdomain="electrochemistry",
        total_processes=152,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.07, MODULATE=0.01, REGULATE=0.05, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.17, STRUCTURE=0.19, CONTENT=0.08, FUNCTION=0.38, RELATIONS=0.04, MEMORY=0.03, BOUNDARY=0.01),
        reversibility_yes=0.01, reversibility_conditional=0.95, reversibility_no=0.03,
        signature="ACTIVATE × FUNCTION",
    ),
    "chemistry/spectroscopy": DomainProfile(
        name="Spectroscopy",
        category="exact_sciences",
        subdomain="spectroscopy",
        total_processes=133,
        pentad=PentadDistribution(ACTIVATE=0.08, INHIBIT=0.03, MODULATE=0.02, REGULATE=0.02, DISRUPT=0.06),
        septet=SeptetDistribution(STATE=0.26, STRUCTURE=0.23, CONTENT=0.26, FUNCTION=0.11, RELATIONS=0.05, MEMORY=0.01, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × CONTENT",
    ),
    "chemistry/organic_chemistry": DomainProfile(
        name="Organic Chemistry",
        category="exact_sciences",
        subdomain="organic_chemistry",
        total_processes=125,
        pentad=PentadDistribution(ACTIVATE=0.13, INHIBIT=0.02, MODULATE=0.02, REGULATE=0.03, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.06, STRUCTURE=0.29, CONTENT=0.12, FUNCTION=0.27, RELATIONS=0.11, MEMORY=0.05, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="ACTIVATE × STRUCTURE",
    ),
    "chemistry/inorganic_chemistry": DomainProfile(
        name="Inorganic Chemistry",
        category="exact_sciences",
        subdomain="inorganic_chemistry",
        total_processes=72,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.00, MODULATE=0.04, REGULATE=0.08, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.17, STRUCTURE=0.21, CONTENT=0.08, FUNCTION=0.29, RELATIONS=0.17, MEMORY=0.03, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="REGULATE × FUNCTION",
    ),
    "chemistry/analytical_chemistry": DomainProfile(
        name="Analytical Chemistry",
        category="exact_sciences",
        subdomain="analytical_chemistry",
        total_processes=80,
        pentad=PentadDistribution(ACTIVATE=0.09, INHIBIT=0.03, MODULATE=0.01, REGULATE=0.07, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.24, CONTENT=0.25, FUNCTION=0.11, RELATIONS=0.04, MEMORY=0.04, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × CONTENT",
    ),
    "chemistry/biochemistry": DomainProfile(
        name="Biochemistry",
        category="exact_sciences",
        subdomain="biochemistry",
        total_processes=142,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.01, MODULATE=0.04, REGULATE=0.04, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.09, STRUCTURE=0.43, CONTENT=0.05, FUNCTION=0.22, RELATIONS=0.07, MEMORY=0.04, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "chemistry/materials_chemistry": DomainProfile(
        name="Materials Chemistry",
        category="exact_sciences",
        subdomain="materials_chemistry",
        total_processes=250,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.02, MODULATE=0.03, REGULATE=0.02, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.08, STRUCTURE=0.25, CONTENT=0.54, FUNCTION=0.06, RELATIONS=0.02, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × CONTENT",
    ),
    
    # Biology (9)
    "biology/genetics": DomainProfile(
        name="Genetics",
        category="exact_sciences",
        subdomain="genetics",
        total_processes=188,
        pentad=PentadDistribution(ACTIVATE=0.15, INHIBIT=0.05, MODULATE=0.04, REGULATE=0.05, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.10, STRUCTURE=0.35, CONTENT=0.05, FUNCTION=0.22, RELATIONS=0.09, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "biology/molecular_biology": DomainProfile(
        name="Molecular Biology",
        category="exact_sciences",
        subdomain="molecular_biology",
        total_processes=88,
        pentad=PentadDistribution(ACTIVATE=0.08, INHIBIT=0.05, MODULATE=0.06, REGULATE=0.06, DISRUPT=0.09),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.32, CONTENT=0.08, FUNCTION=0.23, RELATIONS=0.02, MEMORY=0.03, BOUNDARY=0.00),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="DISRUPT × STRUCTURE",
    ),
    "biology/biochemistry": DomainProfile(
        name="Biochemistry",
        category="exact_sciences",
        subdomain="biochemistry",
        total_processes=142,
        pentad=PentadDistribution(ACTIVATE=0.12, INHIBIT=0.01, MODULATE=0.04, REGULATE=0.04, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.09, STRUCTURE=0.43, CONTENT=0.05, FUNCTION=0.22, RELATIONS=0.07, MEMORY=0.04, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "biology/cell_biology": DomainProfile(
        name="Cell Biology",
        category="exact_sciences",
        subdomain="cell_biology",
        total_processes=26,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.08, MODULATE=0.12, REGULATE=0.00, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.23, STRUCTURE=0.23, CONTENT=0.15, FUNCTION=0.19, RELATIONS=0.04, MEMORY=0.04, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.96, reversibility_no=0.04,
        signature="MODULATE × STRUCTURE",
    ),
    "biology/evolutionary_biology": DomainProfile(
        name="Evolutionary Biology",
        category="exact_sciences",
        subdomain="evolutionary_biology",
        total_processes=30,
        pentad=PentadDistribution(ACTIVATE=0.13, INHIBIT=0.00, MODULATE=0.10, REGULATE=0.07, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.27, STRUCTURE=0.23, CONTENT=0.00, FUNCTION=0.30, RELATIONS=0.03, MEMORY=0.03, BOUNDARY=0.00),
        reversibility_yes=0.03, reversibility_conditional=0.93, reversibility_no=0.03,
        signature="ACTIVATE × FUNCTION",
    ),
    "biology/ecology": DomainProfile(
        name="Ecology",
        category="exact_sciences",
        subdomain="ecology",
        total_processes=246,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.03, MODULATE=0.14, REGULATE=0.10, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.16, STRUCTURE=0.22, CONTENT=0.06, FUNCTION=0.21, RELATIONS=0.11, MEMORY=0.07, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.99, reversibility_no=0.00,
        signature="MODULATE × STRUCTURE",
    ),
    "biology/systems_biology": DomainProfile(
        name="Systems Biology",
        category="exact_sciences",
        subdomain="systems_biology",
        total_processes=229,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.04, MODULATE=0.02, REGULATE=0.09, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.45, STRUCTURE=0.11, CONTENT=0.09, FUNCTION=0.21, RELATIONS=0.06, MEMORY=0.01, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=1.00, reversibility_no=0.00,
        signature="REGULATE × STATE",
    ),
    "biology/bioinformatics": DomainProfile(
        name="Bioinformatics",
        category="exact_sciences",
        subdomain="bioinformatics",
        total_processes=243,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.00, MODULATE=0.03, REGULATE=0.05, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.11, STRUCTURE=0.53, CONTENT=0.17, FUNCTION=0.13, RELATIONS=0.02, MEMORY=0.01, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=1.00, reversibility_no=0.00,
        signature="ACTIVATE × STRUCTURE",
    ),
    "biology/neurobiology": DomainProfile(
        name="Neurobiology",
        category="exact_sciences",
        subdomain="neurobiology",
        total_processes=173,
        pentad=PentadDistribution(ACTIVATE=0.08, INHIBIT=0.01, MODULATE=0.05, REGULATE=0.06, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.19, STRUCTURE=0.25, CONTENT=0.03, FUNCTION=0.29, RELATIONS=0.03, MEMORY=0.10, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × FUNCTION",
    ),
    
    # Computer Science (12)
    "computer_science/algorithms": DomainProfile(
        name="Algorithms",
        category="exact_sciences",
        subdomain="algorithms",
        total_processes=238,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.05, MODULATE=0.02, REGULATE=0.07, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.24, STRUCTURE=0.37, CONTENT=0.05, FUNCTION=0.14, RELATIONS=0.01, MEMORY=0.08, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="REGULATE × STRUCTURE",
    ),
    "computer_science/complexity_theory": DomainProfile(
        name="Complexity Theory",
        category="exact_sciences",
        subdomain="complexity_theory",
        total_processes=199,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.06, MODULATE=0.03, REGULATE=0.06, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.36, STRUCTURE=0.31, CONTENT=0.04, FUNCTION=0.15, RELATIONS=0.02, MEMORY=0.02, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="REGULATE × STATE",
    ),
    "computer_science/automata_theory": DomainProfile(
        name="Automata Theory",
        category="exact_sciences",
        subdomain="automata_theory",
        total_processes=205,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.05, MODULATE=0.02, REGULATE=0.05, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.40, STRUCTURE=0.35, CONTENT=0.05, FUNCTION=0.08, RELATIONS=0.01, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="ACTIVATE × STATE",
    ),
    "computer_science/formal_languages": DomainProfile(
        name="Formal Languages",
        category="exact_sciences",
        subdomain="formal_languages",
        total_processes=207,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.04, MODULATE=0.01, REGULATE=0.05, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.19, STRUCTURE=0.58, CONTENT=0.04, FUNCTION=0.08, RELATIONS=0.00, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "computer_science/cryptography": DomainProfile(
        name="Cryptography",
        category="exact_sciences",
        subdomain="cryptography",
        total_processes=313,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.11, MODULATE=0.02, REGULATE=0.12, DISRUPT=0.09),
        septet=SeptetDistribution(STATE=0.24, STRUCTURE=0.25, CONTENT=0.11, FUNCTION=0.10, RELATIONS=0.01, MEMORY=0.03, BOUNDARY=0.04),
        reversibility_yes=0.04, reversibility_conditional=0.95, reversibility_no=0.02,
        signature="REGULATE × STRUCTURE",
    ),
    "computer_science/logic_in_cs": DomainProfile(
        name="Logic In Cs",
        category="exact_sciences",
        subdomain="logic_in_cs",
        total_processes=108,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.04, MODULATE=0.02, REGULATE=0.08, DISRUPT=0.06),
        septet=SeptetDistribution(STATE=0.32, STRUCTURE=0.40, CONTENT=0.06, FUNCTION=0.07, RELATIONS=0.00, MEMORY=0.03, BOUNDARY=0.04),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="REGULATE × STRUCTURE",
    ),
    "computer_science/programming_languages": DomainProfile(
        name="Programming Languages",
        category="exact_sciences",
        subdomain="programming_languages",
        total_processes=259,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.07, MODULATE=0.03, REGULATE=0.08, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.19, STRUCTURE=0.38, CONTENT=0.09, FUNCTION=0.15, RELATIONS=0.01, MEMORY=0.03, BOUNDARY=0.04),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="REGULATE × STRUCTURE",
    ),
    "computer_science/operating_systems": DomainProfile(
        name="Operating Systems",
        category="exact_sciences",
        subdomain="operating_systems",
        total_processes=341,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.09, MODULATE=0.03, REGULATE=0.15, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.21, STRUCTURE=0.25, CONTENT=0.07, FUNCTION=0.21, RELATIONS=0.01, MEMORY=0.09, BOUNDARY=0.06),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="REGULATE × STRUCTURE",
    ),
    "computer_science/computer_architecture": DomainProfile(
        name="Computer Architecture",
        category="exact_sciences",
        subdomain="computer_architecture",
        total_processes=224,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.05, MODULATE=0.02, REGULATE=0.08, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.48, CONTENT=0.06, FUNCTION=0.13, RELATIONS=0.00, MEMORY=0.02, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="REGULATE × STRUCTURE",
    ),
    "computer_science/distributed_systems": DomainProfile(
        name="Distributed Systems",
        category="exact_sciences",
        subdomain="distributed_systems",
        total_processes=267,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.04, MODULATE=0.02, REGULATE=0.09, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.25, STRUCTURE=0.36, CONTENT=0.06, FUNCTION=0.15, RELATIONS=0.02, MEMORY=0.04, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="REGULATE × STRUCTURE",
    ),
    "computer_science/databases": DomainProfile(
        name="Databases",
        category="exact_sciences",
        subdomain="databases",
        total_processes=484,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.02, MODULATE=0.02, REGULATE=0.13, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.23, STRUCTURE=0.24, CONTENT=0.39, FUNCTION=0.05, RELATIONS=0.02, MEMORY=0.04, BOUNDARY=0.01),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="REGULATE × CONTENT",
    ),
    "computer_science/networks": DomainProfile(
        name="Networks",
        category="exact_sciences",
        subdomain="networks",
        total_processes=114,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.04, MODULATE=0.02, REGULATE=0.10, DISRUPT=0.06),
        septet=SeptetDistribution(STATE=0.32, STRUCTURE=0.39, CONTENT=0.09, FUNCTION=0.07, RELATIONS=0.01, MEMORY=0.03, BOUNDARY=0.04),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="REGULATE × STRUCTURE",
    ),
    
    # Engineering (12)
    "engineering/mechanics": DomainProfile(
        name="Mechanics",
        category="exact_sciences",
        subdomain="mechanics",
        total_processes=54,
        pentad=PentadDistribution(ACTIVATE=0.11, INHIBIT=0.07, MODULATE=0.09, REGULATE=0.04, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.37, STRUCTURE=0.19, CONTENT=0.04, FUNCTION=0.11, RELATIONS=0.02, MEMORY=0.15, BOUNDARY=0.04),
        reversibility_yes=0.00, reversibility_conditional=0.96, reversibility_no=0.04,
        signature="ACTIVATE × STATE",
    ),
    "engineering/thermodynamics": DomainProfile(
        name="Thermodynamics",
        category="exact_sciences",
        subdomain="thermodynamics",
        total_processes=112,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.06, MODULATE=0.03, REGULATE=0.03, DISRUPT=0.03),
        septet=SeptetDistribution(STATE=0.43, STRUCTURE=0.10, CONTENT=0.12, FUNCTION=0.15, RELATIONS=0.07, MEMORY=0.04, BOUNDARY=0.04),
        reversibility_yes=0.03, reversibility_conditional=0.91, reversibility_no=0.06,
        signature="INHIBIT × STATE",
    ),
    "engineering/fluid_mechanics": DomainProfile(
        name="Fluid Mechanics",
        category="exact_sciences",
        subdomain="fluid_mechanics",
        total_processes=41,
        pentad=PentadDistribution(ACTIVATE=0.02, INHIBIT=0.00, MODULATE=0.05, REGULATE=0.17, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.24, CONTENT=0.22, FUNCTION=0.05, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.07),
        reversibility_yes=0.00, reversibility_conditional=0.95, reversibility_no=0.05,
        signature="REGULATE × STRUCTURE",
    ),
    "engineering/materials": DomainProfile(
        name="Materials",
        category="exact_sciences",
        subdomain="materials",
        total_processes=36,
        pentad=PentadDistribution(ACTIVATE=0.11, INHIBIT=0.00, MODULATE=0.00, REGULATE=0.03, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.03, STRUCTURE=0.28, CONTENT=0.67, FUNCTION=0.03, RELATIONS=0.00, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="ACTIVATE × CONTENT",
    ),
    "engineering/circuits": DomainProfile(
        name="Circuits",
        category="exact_sciences",
        subdomain="circuits",
        total_processes=9,
        pentad=PentadDistribution(ACTIVATE=0.11, INHIBIT=0.00, MODULATE=0.00, REGULATE=0.44, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.11, STRUCTURE=0.33, CONTENT=0.33, FUNCTION=0.11, RELATIONS=0.11, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.89, reversibility_no=0.11,
        signature="REGULATE × CONTENT",
    ),
    "engineering/signal_processing": DomainProfile(
        name="Signal Processing",
        category="exact_sciences",
        subdomain="signal_processing",
        total_processes=82,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.00, MODULATE=0.09, REGULATE=0.05, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.10, STRUCTURE=0.10, CONTENT=0.09, FUNCTION=0.67, RELATIONS=0.00, MEMORY=0.01, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.98, reversibility_no=0.02,
        signature="MODULATE × FUNCTION",
    ),
    "engineering/control_systems": DomainProfile(
        name="Control Systems",
        category="exact_sciences",
        subdomain="control_systems",
        total_processes=69,
        pentad=PentadDistribution(ACTIVATE=0.09, INHIBIT=0.00, MODULATE=0.06, REGULATE=0.77, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.10, STRUCTURE=0.12, CONTENT=0.04, FUNCTION=0.28, RELATIONS=0.01, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.97, reversibility_no=0.03,
        signature="REGULATE × FUNCTION",
    ),
    "engineering/power": DomainProfile(
        name="Power",
        category="exact_sciences",
        subdomain="power",
        total_processes=9,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.00, MODULATE=0.11, REGULATE=0.11, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.22, CONTENT=0.22, FUNCTION=0.11, RELATIONS=0.11, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.89, reversibility_no=0.11,
        signature="ACTIVATE × CONTENT",
    ),
    "engineering/software_design": DomainProfile(
        name="Software Design",
        category="exact_sciences",
        subdomain="software_design",
        total_processes=85,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.04, MODULATE=0.05, REGULATE=0.12, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.31, STRUCTURE=0.28, CONTENT=0.05, FUNCTION=0.22, RELATIONS=0.01, MEMORY=0.00, BOUNDARY=0.04),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="REGULATE × STATE",
    ),
    "engineering/testing": DomainProfile(
        name="Testing",
        category="exact_sciences",
        subdomain="testing",
        total_processes=6,
        pentad=PentadDistribution(ACTIVATE=0.17, INHIBIT=0.00, MODULATE=0.00, REGULATE=0.17, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.33, STRUCTURE=0.17, CONTENT=0.33, FUNCTION=0.00, RELATIONS=0.17, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.83, reversibility_no=0.17,
        signature="ACTIVATE × CONTENT",
    ),
    "engineering/deployment": DomainProfile(
        name="Deployment",
        category="exact_sciences",
        subdomain="deployment",
        total_processes=6,
        pentad=PentadDistribution(ACTIVATE=0.17, INHIBIT=0.00, MODULATE=0.00, REGULATE=0.17, DISRUPT=0.17),
        septet=SeptetDistribution(STATE=0.33, STRUCTURE=0.17, CONTENT=0.33, FUNCTION=0.00, RELATIONS=0.17, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.83, reversibility_no=0.17,
        signature="ACTIVATE × CONTENT",
    ),
    "engineering/maintenance": DomainProfile(
        name="Maintenance",
        category="exact_sciences",
        subdomain="maintenance",
        total_processes=90,
        pentad=PentadDistribution(ACTIVATE=0.02, INHIBIT=0.21, MODULATE=0.06, REGULATE=0.13, DISRUPT=0.06),
        septet=SeptetDistribution(STATE=0.31, STRUCTURE=0.19, CONTENT=0.09, FUNCTION=0.19, RELATIONS=0.00, MEMORY=0.01, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="INHIBIT × STATE",
    ),
    
    # Logic (8)
    "logic/propositional_logic": DomainProfile(
        name="Propositional Logic",
        category="exact_sciences",
        subdomain="propositional_logic",
        total_processes=181,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.01, MODULATE=0.04, REGULATE=0.03, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.34, STRUCTURE=0.45, CONTENT=0.02, FUNCTION=0.07, RELATIONS=0.02, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.01, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × STRUCTURE",
    ),
    "logic/predicate_logic": DomainProfile(
        name="Predicate Logic",
        category="exact_sciences",
        subdomain="predicate_logic",
        total_processes=303,
        pentad=PentadDistribution(ACTIVATE=0.01, INHIBIT=0.07, MODULATE=0.03, REGULATE=0.00, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.17, STRUCTURE=0.54, CONTENT=0.01, FUNCTION=0.15, RELATIONS=0.06, MEMORY=0.00, BOUNDARY=0.03),
        reversibility_yes=0.00, reversibility_conditional=1.00, reversibility_no=0.00,
        signature="INHIBIT × STRUCTURE",
    ),
    "logic/modal_logic": DomainProfile(
        name="Modal Logic",
        category="exact_sciences",
        subdomain="modal_logic",
        total_processes=144,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.02, MODULATE=0.01, REGULATE=0.03, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.32, STRUCTURE=0.33, CONTENT=0.08, FUNCTION=0.03, RELATIONS=0.12, MEMORY=0.04, BOUNDARY=0.02),
        reversibility_yes=0.02, reversibility_conditional=0.96, reversibility_no=0.02,
        signature="ACTIVATE × STRUCTURE",
    ),
    "logic/temporal_logic": DomainProfile(
        name="Temporal Logic",
        category="exact_sciences",
        subdomain="temporal_logic",
        total_processes=63,
        pentad=PentadDistribution(ACTIVATE=0.08, INHIBIT=0.06, MODULATE=0.05, REGULATE=0.00, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.43, STRUCTURE=0.32, CONTENT=0.05, FUNCTION=0.06, RELATIONS=0.08, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.02, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="ACTIVATE × STATE",
    ),
    "logic/automated_reasoning": DomainProfile(
        name="Automated Reasoning",
        category="exact_sciences",
        subdomain="automated_reasoning",
        total_processes=27,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.15, MODULATE=0.00, REGULATE=0.00, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.19, STRUCTURE=0.30, CONTENT=0.07, FUNCTION=0.44, RELATIONS=0.00, MEMORY=0.00, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=1.00, reversibility_no=0.00,
        signature="ACTIVATE × FUNCTION",
    ),
    "logic/theorem_proving": DomainProfile(
        name="Theorem Proving",
        category="exact_sciences",
        subdomain="theorem_proving",
        total_processes=60,
        pentad=PentadDistribution(ACTIVATE=0.07, INHIBIT=0.05, MODULATE=0.03, REGULATE=0.07, DISRUPT=0.00),
        septet=SeptetDistribution(STATE=0.17, STRUCTURE=0.25, CONTENT=0.08, FUNCTION=0.47, RELATIONS=0.00, MEMORY=0.03, BOUNDARY=0.00),
        reversibility_yes=0.03, reversibility_conditional=0.97, reversibility_no=0.00,
        signature="ACTIVATE × FUNCTION",
    ),
    "logic/type_theory": DomainProfile(
        name="Type Theory",
        category="exact_sciences",
        subdomain="type_theory",
        total_processes=123,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.04, MODULATE=0.02, REGULATE=0.04, DISRUPT=0.01),
        septet=SeptetDistribution(STATE=0.11, STRUCTURE=0.24, CONTENT=0.03, FUNCTION=0.45, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.00),
        reversibility_yes=0.00, reversibility_conditional=0.99, reversibility_no=0.01,
        signature="ACTIVATE × FUNCTION",
    ),
    "logic/proof_theory": DomainProfile(
        name="Proof Theory",
        category="exact_sciences",
        subdomain="proof_theory",
        total_processes=156,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.08, MODULATE=0.02, REGULATE=0.03, DISRUPT=0.02),
        septet=SeptetDistribution(STATE=0.15, STRUCTURE=0.55, CONTENT=0.02, FUNCTION=0.18, RELATIONS=0.03, MEMORY=0.01, BOUNDARY=0.02),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="INHIBIT × STRUCTURE",
    ),
    
    # Statistics (7)
    "statistics/probability_theory": DomainProfile(
        name="Probability Theory",
        category="exact_sciences",
        subdomain="probability_theory",
        total_processes=156,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.13, MODULATE=0.04, REGULATE=0.06, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.48, STRUCTURE=0.14, CONTENT=0.12, FUNCTION=0.10, RELATIONS=0.04, MEMORY=0.01, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="INHIBIT × STATE",
    ),
    "statistics/statistical_inference": DomainProfile(
        name="Statistical Inference",
        category="exact_sciences",
        subdomain="statistical_inference",
        total_processes=179,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.12, MODULATE=0.04, REGULATE=0.08, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.45, STRUCTURE=0.16, CONTENT=0.14, FUNCTION=0.12, RELATIONS=0.03, MEMORY=0.01, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="INHIBIT × STATE",
    ),
    "statistics/bayesian_statistics": DomainProfile(
        name="Bayesian Statistics",
        category="exact_sciences",
        subdomain="bayesian_statistics",
        total_processes=147,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.14, MODULATE=0.05, REGULATE=0.06, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.46, STRUCTURE=0.13, CONTENT=0.13, FUNCTION=0.11, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.04),
        reversibility_yes=0.01, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="INHIBIT × STATE",
    ),
    "statistics/regression_analysis": DomainProfile(
        name="Regression Analysis",
        category="exact_sciences",
        subdomain="regression_analysis",
        total_processes=168,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.11, MODULATE=0.04, REGULATE=0.09, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.44, STRUCTURE=0.17, CONTENT=0.15, FUNCTION=0.11, RELATIONS=0.03, MEMORY=0.01, BOUNDARY=0.03),
        reversibility_yes=0.01, reversibility_conditional=0.98, reversibility_no=0.01,
        signature="INHIBIT × STATE",
    ),
    "statistics/experimental_design": DomainProfile(
        name="Experimental Design",
        category="exact_sciences",
        subdomain="experimental_design",
        total_processes=134,
        pentad=PentadDistribution(ACTIVATE=0.05, INHIBIT=0.10, MODULATE=0.06, REGULATE=0.10, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.38, STRUCTURE=0.21, CONTENT=0.18, FUNCTION=0.12, RELATIONS=0.04, MEMORY=0.02, BOUNDARY=0.03),
        reversibility_yes=0.02, reversibility_conditional=0.95, reversibility_no=0.03,
        signature="INHIBIT × STATE",
    ),
    "statistics/multivariate_analysis": DomainProfile(
        name="Multivariate Analysis",
        category="exact_sciences",
        subdomain="multivariate_analysis",
        total_processes=145,
        pentad=PentadDistribution(ACTIVATE=0.04, INHIBIT=0.12, MODULATE=0.05, REGULATE=0.07, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.42, STRUCTURE=0.18, CONTENT=0.14, FUNCTION=0.10, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.04),
        reversibility_yes=0.01, reversibility_conditional=0.97, reversibility_no=0.02,
        signature="INHIBIT × STATE",
    ),
    "statistics/stochastic_processes": DomainProfile(
        name="Stochastic Processes",
        category="exact_sciences",
        subdomain="stochastic_processes",
        total_processes=112,
        pentad=PentadDistribution(ACTIVATE=0.06, INHIBIT=0.09, MODULATE=0.05, REGULATE=0.07, DISRUPT=0.04),
        septet=SeptetDistribution(STATE=0.50, STRUCTURE=0.15, CONTENT=0.11, FUNCTION=0.13, RELATIONS=0.04, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.01, reversibility_conditional=0.96, reversibility_no=0.03,
        signature="INHIBIT × STATE",
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# HUMANITIES (48 domains) - Generated from domain patterns
# ═══════════════════════════════════════════════════════════════════════════════

HUMANITIES_PROFILES = {
    # Social Sciences (16)
    "psychology": DomainProfile(
        name="Psychology",
        category="humanities",
        subdomain="cognitive",
        total_processes=2500,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.18, MODULATE=0.25, REGULATE=0.20, DISRUPT=0.15),
        septet=SeptetDistribution(STATE=0.25, STRUCTURE=0.20, CONTENT=0.30, FUNCTION=0.15, RELATIONS=0.05, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.15, reversibility_conditional=0.60, reversibility_no=0.25,
        signature="MODULATE × CONTENT",
    ),
    "neuroscience": DomainProfile(
        name="Neuroscience",
        category="humanities",
        subdomain="biological",
        total_processes=1800,
        pentad=PentadDistribution(ACTIVATE=0.35, INHIBIT=0.20, MODULATE=0.15, REGULATE=0.18, DISRUPT=0.12),
        septet=SeptetDistribution(STATE=0.30, STRUCTURE=0.25, CONTENT=0.15, FUNCTION=0.20, RELATIONS=0.05, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.08, reversibility_conditional=0.72, reversibility_no=0.20,
        signature="ACTIVATE × STATE",
    ),
    "sociology": DomainProfile(
        name="Sociology",
        category="humanities",
        subdomain="social",
        total_processes=1200,
        pentad=PentadDistribution(ACTIVATE=0.18, INHIBIT=0.12, MODULATE=0.28, REGULATE=0.22, DISRUPT=0.20),
        septet=SeptetDistribution(STATE=0.15, STRUCTURE=0.35, CONTENT=0.25, FUNCTION=0.10, RELATIONS=0.12, MEMORY=0.02, BOUNDARY=0.01),
        reversibility_yes=0.12, reversibility_conditional=0.68, reversibility_no=0.20,
        signature="MODULATE × STRUCTURE",
    ),
    "economics": DomainProfile(
        name="Economics",
        category="humanities",
        subdomain="behavioral",
        total_processes=1500,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.15, MODULATE=0.22, REGULATE=0.30, DISRUPT=0.13),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.30, CONTENT=0.25, FUNCTION=0.15, RELATIONS=0.07, MEMORY=0.02, BOUNDARY=0.01),
        reversibility_yes=0.10, reversibility_conditional=0.55, reversibility_no=0.35,
        signature="REGULATE × STRUCTURE",
    ),
    "business": DomainProfile(
        name="Business",
        category="humanities",
        subdomain="applied",
        total_processes=2000,
        pentad=PentadDistribution(ACTIVATE=0.25, INHIBIT=0.10, MODULATE=0.20, REGULATE=0.30, DISRUPT=0.15),
        septet=SeptetDistribution(STATE=0.15, STRUCTURE=0.35, CONTENT=0.20, FUNCTION=0.20, RELATIONS=0.07, MEMORY=0.02, BOUNDARY=0.01),
        reversibility_yes=0.20, reversibility_conditional=0.60, reversibility_no=0.20,
        signature="REGULATE × STRUCTURE",
    ),
    "anthropology": DomainProfile(
        name="Anthropology",
        category="humanities",
        subdomain="cultural",
        total_processes=1100,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.15, MODULATE=0.30, REGULATE=0.18, DISRUPT=0.17),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.25, CONTENT=0.35, FUNCTION=0.12, RELATIONS=0.07, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.10, reversibility_conditional=0.70, reversibility_no=0.20,
        signature="MODULATE × CONTENT",
    ),
    "political_science": DomainProfile(
        name="Political Science",
        category="humanities",
        subdomain="systems",
        total_processes=1400,
        pentad=PentadDistribution(ACTIVATE=0.18, INHIBIT=0.14, MODULATE=0.24, REGULATE=0.28, DISRUPT=0.16),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.32, CONTENT=0.22, FUNCTION=0.14, RELATIONS=0.08, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.65, reversibility_no=0.23,
        signature="REGULATE × STRUCTURE",
    ),
    "linguistics": DomainProfile(
        name="Linguistics",
        category="humanities",
        subdomain="cognitive",
        total_processes=1300,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.16, MODULATE=0.26, REGULATE=0.21, DISRUPT=0.15),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.28, CONTENT=0.32, FUNCTION=0.12, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.14, reversibility_conditional=0.68, reversibility_no=0.18,
        signature="MODULATE × CONTENT",
    ),
    "education": DomainProfile(
        name="Education",
        category="humanities",
        subdomain="applied",
        total_processes=1600,
        pentad=PentadDistribution(ACTIVATE=0.28, INHIBIT=0.12, MODULATE=0.24, REGULATE=0.26, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.30, CONTENT=0.28, FUNCTION=0.16, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.18, reversibility_conditional=0.62, reversibility_no=0.20,
        signature="REGULATE × CONTENT",
    ),
    "law": DomainProfile(
        name="Law",
        category="humanities",
        subdomain="systems",
        total_processes=1700,
        pentad=PentadDistribution(ACTIVATE=0.15, INHIBIT=0.22, MODULATE=0.20, REGULATE=0.35, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.25, STRUCTURE=0.38, CONTENT=0.20, FUNCTION=0.10, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.08, reversibility_conditional=0.72, reversibility_no=0.20,
        signature="REGULATE × STRUCTURE",
    ),
    "international_relations": DomainProfile(
        name="International Relations",
        category="humanities",
        subdomain="systems",
        total_processes=1200,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.15, MODULATE=0.28, REGULATE=0.22, DISRUPT=0.15),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.28, CONTENT=0.25, FUNCTION=0.12, RELATIONS=0.15, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.10, reversibility_conditional=0.68, reversibility_no=0.22,
        signature="MODULATE × RELATIONS",
    ),
    "urban_studies": DomainProfile(
        name="Urban Studies",
        category="humanities",
        subdomain="applied",
        total_processes=900,
        pentad=PentadDistribution(ACTIVATE=0.24, INHIBIT=0.12, MODULATE=0.22, REGULATE=0.30, DISRUPT=0.12),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.35, CONTENT=0.20, FUNCTION=0.15, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.15, reversibility_conditional=0.65, reversibility_no=0.20,
        signature="REGULATE × STRUCTURE",
    ),
    "communication": DomainProfile(
        name="Communication",
        category="humanities",
        subdomain="applied",
        total_processes=1100,
        pentad=PentadDistribution(ACTIVATE=0.25, INHIBIT=0.14, MODULATE=0.30, REGULATE=0.20, DISRUPT=0.11),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.25, CONTENT=0.35, FUNCTION=0.14, RELATIONS=0.05, MEMORY=0.01, BOUNDARY=0.02),
        reversibility_yes=0.18, reversibility_conditional=0.60, reversibility_no=0.22,
        signature="MODULATE × CONTENT",
    ),
    "social_work": DomainProfile(
        name="Social Work",
        category="humanities",
        subdomain="applied",
        total_processes=800,
        pentad=PentadDistribution(ACTIVATE=0.30, INHIBIT=0.12, MODULATE=0.25, REGULATE=0.22, DISRUPT=0.11),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.28, CONTENT=0.22, FUNCTION=0.22, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.20, reversibility_conditional=0.58, reversibility_no=0.22,
        signature="ACTIVATE × FUNCTION",
    ),
    "criminology": DomainProfile(
        name="Criminology",
        category="humanities",
        subdomain="behavioral",
        total_processes=950,
        pentad=PentadDistribution(ACTIVATE=0.15, INHIBIT=0.35, MODULATE=0.20, REGULATE=0.22, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.25, STRUCTURE=0.30, CONTENT=0.20, FUNCTION=0.12, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.10),
        reversibility_yes=0.08, reversibility_conditional=0.70, reversibility_no=0.22,
        signature="INHIBIT × BOUNDARY",
    ),
    "demography": DomainProfile(
        name="Demography",
        category="humanities",
        subdomain="systems",
        total_processes=850,
        pentad=PentadDistribution(ACTIVATE=0.35, INHIBIT=0.15, MODULATE=0.20, REGULATE=0.20, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.35, STRUCTURE=0.28, CONTENT=0.18, FUNCTION=0.12, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.68, reversibility_no=0.20,
        signature="ACTIVATE × STATE",
    ),
    
    # Humanities proper (16)
    "philosophy": DomainProfile(
        name="Philosophy",
        category="humanities",
        subdomain="theoretical",
        total_processes=1400,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.18, MODULATE=0.28, REGULATE=0.22, DISRUPT=0.12),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.22, CONTENT=0.35, FUNCTION=0.15, RELATIONS=0.07, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.14, reversibility_conditional=0.65, reversibility_no=0.21,
        signature="MODULATE × CONTENT",
    ),
    "history": DomainProfile(
        name="History",
        category="humanities",
        subdomain="descriptive",
        total_processes=1600,
        pentad=PentadDistribution(ACTIVATE=0.35, INHIBIT=0.15, MODULATE=0.20, REGULATE=0.18, DISRUPT=0.12),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.25, CONTENT=0.20, FUNCTION=0.10, RELATIONS=0.05, MEMORY=0.30, BOUNDARY=0.02),
        reversibility_yes=0.05, reversibility_conditional=0.75, reversibility_no=0.20,
        signature="ACTIVATE × MEMORY",
    ),
    "literature": DomainProfile(
        name="Literature",
        category="humanities",
        subdomain="creative",
        total_processes=1300,
        pentad=PentadDistribution(ACTIVATE=0.25, INHIBIT=0.15, MODULATE=0.32, REGULATE=0.18, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.20, CONTENT=0.38, FUNCTION=0.14, RELATIONS=0.07, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.15, reversibility_conditional=0.62, reversibility_no=0.23,
        signature="MODULATE × CONTENT",
    ),
    "art_history": DomainProfile(
        name="Art History",
        category="humanities",
        subdomain="descriptive",
        total_processes=1100,
        pentad=PentadDistribution(ACTIVATE=0.28, INHIBIT=0.14, MODULATE=0.30, REGULATE=0.18, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.22, CONTENT=0.36, FUNCTION=0.12, RELATIONS=0.06, MEMORY=0.06, BOUNDARY=0.02),
        reversibility_yes=0.10, reversibility_conditional=0.70, reversibility_no=0.20,
        signature="MODULATE × CONTENT",
    ),
    "music_theory": DomainProfile(
        name="Music Theory",
        category="humanities",
        subdomain="formal",
        total_processes=900,
        pentad=PentadDistribution(ACTIVATE=0.18, INHIBIT=0.16, MODULATE=0.24, REGULATE=0.32, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.35, CONTENT=0.25, FUNCTION=0.15, RELATIONS=0.04, MEMORY=0.01, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.68, reversibility_no=0.20,
        signature="REGULATE × STRUCTURE",
    ),
    "theology": DomainProfile(
        name="Theology",
        category="humanities",
        subdomain="metaphysical",
        total_processes=1000,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.18, MODULATE=0.26, REGULATE=0.24, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.28, CONTENT=0.32, FUNCTION=0.12, RELATIONS=0.04, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.08, reversibility_conditional=0.72, reversibility_no=0.20,
        signature="REGULATE × CONTENT",
    ),
    "classics": DomainProfile(
        name="Classics",
        category="humanities",
        subdomain="descriptive",
        total_processes=800,
        pentad=PentadDistribution(ACTIVATE=0.32, INHIBIT=0.14, MODULATE=0.22, REGULATE=0.18, DISRUPT=0.14),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.24, CONTENT=0.22, FUNCTION=0.08, RELATIONS=0.04, MEMORY=0.28, BOUNDARY=0.02),
        reversibility_yes=0.05, reversibility_conditional=0.75, reversibility_no=0.20,
        signature="ACTIVATE × MEMORY",
    ),
    "archaeology": DomainProfile(
        name="Archaeology",
        category="humanities",
        subdomain="empirical",
        total_processes=950,
        pentad=PentadDistribution(ACTIVATE=0.30, INHIBIT=0.16, MODULATE=0.22, REGULATE=0.20, DISRUPT=0.12),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.35, CONTENT=0.18, FUNCTION=0.15, RELATIONS=0.06, MEMORY=0.04, BOUNDARY=0.02),
        reversibility_yes=0.08, reversibility_conditional=0.72, reversibility_no=0.20,
        signature="ACTIVATE × STRUCTURE",
    ),
    "cultural_studies": DomainProfile(
        name="Cultural Studies",
        category="humanities",
        subdomain="critical",
        total_processes=1000,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.15, MODULATE=0.25, REGULATE=0.18, DISRUPT=0.22),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.28, CONTENT=0.35, FUNCTION=0.12, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.65, reversibility_no=0.23,
        signature="DISRUPT × CONTENT",
    ),
    "media_studies": DomainProfile(
        name="Media Studies",
        category="humanities",
        subdomain="applied",
        total_processes=900,
        pentad=PentadDistribution(ACTIVATE=0.25, INHIBIT=0.14, MODULATE=0.30, REGULATE=0.20, DISRUPT=0.11),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.24, CONTENT=0.36, FUNCTION=0.14, RELATIONS=0.05, MEMORY=0.01, BOUNDARY=0.02),
        reversibility_yes=0.15, reversibility_conditional=0.62, reversibility_no=0.23,
        signature="MODULATE × CONTENT",
    ),
    "gender_studies": DomainProfile(
        name="Gender Studies",
        category="humanities",
        subdomain="critical",
        total_processes=850,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.16, MODULATE=0.26, REGULATE=0.18, DISRUPT=0.18),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.35, CONTENT=0.28, FUNCTION=0.12, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.65, reversibility_no=0.23,
        signature="DISRUPT × STRUCTURE",
    ),
    "ethics": DomainProfile(
        name="Ethics",
        category="humanities",
        subdomain="normative",
        total_processes=1100,
        pentad=PentadDistribution(ACTIVATE=0.18, INHIBIT=0.20, MODULATE=0.25, REGULATE=0.32, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.30, CONTENT=0.28, FUNCTION=0.12, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.08),
        reversibility_yes=0.10, reversibility_conditional=0.70, reversibility_no=0.20,
        signature="REGULATE × BOUNDARY",
    ),
    "aesthetics": DomainProfile(
        name="Aesthetics",
        category="humanities",
        subdomain="philosophical",
        total_processes=950,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.16, MODULATE=0.30, REGULATE=0.22, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.22, CONTENT=0.35, FUNCTION=0.15, RELATIONS=0.07, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.14, reversibility_conditional=0.64, reversibility_no=0.22,
        signature="MODULATE × CONTENT",
    ),
    "religious_studies": DomainProfile(
        name="Religious Studies",
        category="humanities",
        subdomain="descriptive",
        total_processes=1000,
        pentad=PentadDistribution(ACTIVATE=0.25, INHIBIT=0.15, MODULATE=0.28, REGULATE=0.22, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.26, CONTENT=0.32, FUNCTION=0.13, RELATIONS=0.06, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.10, reversibility_conditional=0.68, reversibility_no=0.22,
        signature="MODULATE × CONTENT",
    ),
    "folklore": DomainProfile(
        name="Folklore",
        category="humanities",
        subdomain="descriptive",
        total_processes=700,
        pentad=PentadDistribution(ACTIVATE=0.35, INHIBIT=0.12, MODULATE=0.22, REGULATE=0.18, DISRUPT=0.13),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.24, CONTENT=0.22, FUNCTION=0.10, RELATIONS=0.04, MEMORY=0.28, BOUNDARY=0.02),
        reversibility_yes=0.06, reversibility_conditional=0.74, reversibility_no=0.20,
        signature="ACTIVATE × MEMORY",
    ),
    "mythology": DomainProfile(
        name="Mythology",
        category="humanities",
        subdomain="descriptive",
        total_processes=800,
        pentad=PentadDistribution(ACTIVATE=0.28, INHIBIT=0.14, MODULATE=0.30, REGULATE=0.18, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.22, CONTENT=0.35, FUNCTION=0.12, RELATIONS=0.07, MEMORY=0.06, BOUNDARY=0.02),
        reversibility_yes=0.08, reversibility_conditional=0.70, reversibility_no=0.22,
        signature="MODULATE × CONTENT",
    ),
    
    # Interdisciplinary (16)
    "cognitive_science": DomainProfile(
        name="Cognitive Science",
        category="humanities",
        subdomain="interdisciplinary",
        total_processes=1200,
        pentad=PentadDistribution(ACTIVATE=0.35, INHIBIT=0.15, MODULATE=0.20, REGULATE=0.20, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.28, STRUCTURE=0.35, CONTENT=0.18, FUNCTION=0.15, RELATIONS=0.04, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.10, reversibility_conditional=0.70, reversibility_no=0.20,
        signature="ACTIVATE × STRUCTURE",
    ),
    "science_technology_studies": DomainProfile(
        name="Science Technology Studies",
        category="humanities",
        subdomain="critical",
        total_processes=900,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.15, MODULATE=0.25, REGULATE=0.18, DISRUPT=0.22),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.35, CONTENT=0.25, FUNCTION=0.13, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.65, reversibility_no=0.23,
        signature="DISRUPT × STRUCTURE",
    ),
    "environmental_studies": DomainProfile(
        name="Environmental Studies",
        category="humanities",
        subdomain="applied",
        total_processes=1000,
        pentad=PentadDistribution(ACTIVATE=0.28, INHIBIT=0.18, MODULATE=0.22, REGULATE=0.24, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.35, STRUCTURE=0.28, CONTENT=0.18, FUNCTION=0.15, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.10, reversibility_conditional=0.68, reversibility_no=0.22,
        signature="REGULATE × STATE",
    ),
    "public_health": DomainProfile(
        name="Public Health",
        category="humanities",
        subdomain="applied",
        total_processes=1400,
        pentad=PentadDistribution(ACTIVATE=0.30, INHIBIT=0.15, MODULATE=0.20, REGULATE=0.28, DISRUPT=0.07),
        septet=SeptetDistribution(STATE=0.38, STRUCTURE=0.25, CONTENT=0.18, FUNCTION=0.15, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.66, reversibility_no=0.22,
        signature="REGULATE × STATE",
    ),
    "library_science": DomainProfile(
        name="Library Science",
        category="humanities",
        subdomain="applied",
        total_processes=800,
        pentad=PentadDistribution(ACTIVATE=0.18, INHIBIT=0.15, MODULATE=0.22, REGULATE=0.35, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.35, CONTENT=0.28, FUNCTION=0.10, RELATIONS=0.04, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.15, reversibility_conditional=0.65, reversibility_no=0.20,
        signature="REGULATE × CONTENT",
    ),
    "museum_studies": DomainProfile(
        name="Museum Studies",
        category="humanities",
        subdomain="applied",
        total_processes=700,
        pentad=PentadDistribution(ACTIVATE=0.25, INHIBIT=0.14, MODULATE=0.28, REGULATE=0.23, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.28, CONTENT=0.32, FUNCTION=0.13, RELATIONS=0.05, MEMORY=0.04, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.66, reversibility_no=0.22,
        signature="MODULATE × CONTENT",
    ),
    "digital_humanities": DomainProfile(
        name="Digital Humanities",
        category="humanities",
        subdomain="applied",
        total_processes=850,
        pentad=PentadDistribution(ACTIVATE=0.35, INHIBIT=0.12, MODULATE=0.18, REGULATE=0.25, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.25, STRUCTURE=0.38, CONTENT=0.20, FUNCTION=0.12, RELATIONS=0.04, MEMORY=0.03, BOUNDARY=0.02),
        reversibility_yes=0.14, reversibility_conditional=0.66, reversibility_no=0.20,
        signature="ACTIVATE × STRUCTURE",
    ),
    "area_studies": DomainProfile(
        name="Area Studies",
        category="humanities",
        subdomain="descriptive",
        total_processes=900,
        pentad=PentadDistribution(ACTIVATE=0.28, INHIBIT=0.14, MODULATE=0.28, REGULATE=0.20, DISRUPT=0.10),
        septet=SeptetDistribution(STATE=0.18, STRUCTURE=0.26, CONTENT=0.35, FUNCTION=0.12, RELATIONS=0.07, MEMORY=0.04, BOUNDARY=0.02),
        reversibility_yes=0.08, reversibility_conditional=0.70, reversibility_no=0.22,
        signature="MODULATE × CONTENT",
    ),
    "peace_studies": DomainProfile(
        name="Peace Studies",
        category="humanities",
        subdomain="normative",
        total_processes=700,
        pentad=PentadDistribution(ACTIVATE=0.25, INHIBIT=0.18, MODULATE=0.22, REGULATE=0.28, DISRUPT=0.07),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.28, CONTENT=0.22, FUNCTION=0.15, RELATIONS=0.14, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.68, reversibility_no=0.20,
        signature="REGULATE × RELATIONS",
    ),
    "development_studies": DomainProfile(
        name="Development Studies",
        category="humanities",
        subdomain="applied",
        total_processes=800,
        pentad=PentadDistribution(ACTIVATE=0.35, INHIBIT=0.15, MODULATE=0.20, REGULATE=0.22, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.28, CONTENT=0.18, FUNCTION=0.25, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.15, reversibility_conditional=0.62, reversibility_no=0.23,
        signature="ACTIVATE × FUNCTION",
    ),
    "security_studies": DomainProfile(
        name="Security Studies",
        category="humanities",
        subdomain="applied",
        total_processes=750,
        pentad=PentadDistribution(ACTIVATE=0.18, INHIBIT=0.35, MODULATE=0.20, REGULATE=0.22, DISRUPT=0.05),
        septet=SeptetDistribution(STATE=0.25, STRUCTURE=0.30, CONTENT=0.18, FUNCTION=0.12, RELATIONS=0.06, MEMORY=0.02, BOUNDARY=0.12),
        reversibility_yes=0.08, reversibility_conditional=0.70, reversibility_no=0.22,
        signature="INHIBIT × BOUNDARY",
    ),
    "information_science": DomainProfile(
        name="Information Science",
        category="humanities",
        subdomain="applied",
        total_processes=1000,
        pentad=PentadDistribution(ACTIVATE=0.22, INHIBIT=0.15, MODULATE=0.20, REGULATE=0.35, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.38, CONTENT=0.25, FUNCTION=0.10, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.14, reversibility_conditional=0.66, reversibility_no=0.20,
        signature="REGULATE × STRUCTURE",
    ),
    "knowledge_management": DomainProfile(
        name="Knowledge Management",
        category="humanities",
        subdomain="applied",
        total_processes=900,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.15, MODULATE=0.22, REGULATE=0.35, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.30, CONTENT=0.22, FUNCTION=0.12, RELATIONS=0.06, MEMORY=0.28, BOUNDARY=0.02),
        reversibility_yes=0.15, reversibility_conditional=0.65, reversibility_no=0.20,
        signature="REGULATE × MEMORY",
    ),
    "futures_studies": DomainProfile(
        name="Futures Studies",
        category="humanities",
        subdomain="speculative",
        total_processes=650,
        pentad=PentadDistribution(ACTIVATE=0.38, INHIBIT=0.12, MODULATE=0.22, REGULATE=0.20, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.35, STRUCTURE=0.25, CONTENT=0.20, FUNCTION=0.15, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.18, reversibility_conditional=0.58, reversibility_no=0.24,
        signature="ACTIVATE × STATE",
    ),
    "science_communication": DomainProfile(
        name="Science Communication",
        category="humanities",
        subdomain="applied",
        total_processes=800,
        pentad=PentadDistribution(ACTIVATE=0.28, INHIBIT=0.14, MODULATE=0.30, REGULATE=0.20, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.20, STRUCTURE=0.25, CONTENT=0.35, FUNCTION=0.15, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.16, reversibility_conditional=0.62, reversibility_no=0.22,
        signature="MODULATE × CONTENT",
    ),
    "technology_assessment": DomainProfile(
        name="Technology Assessment",
        category="humanities",
        subdomain="applied",
        total_processes=750,
        pentad=PentadDistribution(ACTIVATE=0.20, INHIBIT=0.18, MODULATE=0.22, REGULATE=0.32, DISRUPT=0.08),
        septet=SeptetDistribution(STATE=0.22, STRUCTURE=0.30, CONTENT=0.18, FUNCTION=0.25, RELATIONS=0.05, MEMORY=0.02, BOUNDARY=0.02),
        reversibility_yes=0.12, reversibility_conditional=0.66, reversibility_no=0.22,
        signature="REGULATE × FUNCTION",
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED DATABASE (135 domains total)
# ═══════════════════════════════════════════════════════════════════════════════

ALL_DOMAINS = {**HUMANITIES_PROFILES, **EXACT_SCIENCES_PROFILES}

# Quick lookup by category
HUMANITIES_NAMES = [k for k, v in ALL_DOMAINS.items() if v.category == "humanities"]
EXACT_SCIENCES_NAMES = [k for k, v in ALL_DOMAINS.items() if v.category == "exact_sciences"]

# Boundary disciplines (The Bridge)
BOUNDARY_DISCIPLINES = ["logic", "statistics", "computer_science"]


def get_profile(domain_name: str) -> DomainProfile:
    """Get domain profile by name"""
    return ALL_DOMAINS.get(domain_name)


def get_similar_domains(domain_name: str, n: int = 3) -> List[str]:
    """
    Find structurally similar domains (homomorphism detection)
    """
    target = get_profile(domain_name)
    if not target:
        return []

    similarities = []
    for name, profile in ALL_DOMAINS.items():
        if name == domain_name:
            continue

        # Calculate similarity (Euclidean distance in Pentad×Septet space)
        pentad_sim = sum([
            (target.pentad.ACTIVATE - profile.pentad.ACTIVATE) ** 2,
            (target.pentad.INHIBIT - profile.pentad.INHIBIT) ** 2,
            (target.pentad.MODULATE - profile.pentad.MODULATE) ** 2,
            (target.pentad.REGULATE - profile.pentad.REGULATE) ** 2,
            (target.pentad.DISRUPT - profile.pentad.DISRUPT) ** 2,
        ])

        septet_sim = sum([
            (target.septet.STATE - profile.septet.STATE) ** 2,
            (target.septet.STRUCTURE - profile.septet.STRUCTURE) ** 2,
            (target.septet.CONTENT - profile.septet.CONTENT) ** 2,
        ])

        total_dist = (pentad_sim + septet_sim) ** 0.5
        similarities.append((name, total_dist))

    # Return n most similar
    similarities.sort(key=lambda x: x[1])
    return [name for name, _ in similarities[:n]]


def find_bridge_domains() -> Dict[str, List[str]]:
    """
    Find domains that bridge humanities and exact sciences
    """
    bridges = {}

    for boundary in BOUNDARY_DISCIPLINES:
        profile = get_profile(boundary)
        if not profile:
            continue

        # Find closest humanities and exact science domains
        humanities_close = []
        exact_close = []

        for name, other in ALL_DOMAINS.items():
            if name == boundary:
                continue

            # Simple distance metric
            dist = abs(profile.pentad.MODULATE - other.pentad.MODULATE)

            if other.category == "humanities":
                humanities_close.append((name, dist))
            else:
                exact_close.append((name, dist))

        humanities_close.sort(key=lambda x: x[1])
        exact_close.sort(key=lambda x: x[1])

        bridges[boundary] = {
            "humanities_neighbors": [n for n, _ in humanities_close[:3]],
            "exact_neighbors": [n for n, _ in exact_close[:3]],
        }

    return bridges


# Export for use
__all__ = [
    "ALL_DOMAINS",
    "HUMANITIES_PROFILES",
    "EXACT_SCIENCES_PROFILES",
    "get_profile",
    "get_similar_domains",
    "find_bridge_domains",
    "BOUNDARY_DISCIPLINES",
]


if __name__ == "__main__":
    # Validation
    print(f"Total domains: {len(ALL_DOMAINS)}")
    print(f"  - Humanities: {len(HUMANITIES_PROFILES)}")
    print(f"  - Exact Sciences: {len(EXACT_SCIENCES_PROFILES)}")
    print(f"\nValidation: {'PASS' if len(ALL_DOMAINS) == 135 else 'FAIL'}")
