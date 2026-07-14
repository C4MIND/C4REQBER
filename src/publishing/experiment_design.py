# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Experimental Protocol Generator — design real-world experiments for hypotheses.

Generates structured experimental protocols with:
- Materials & Methods (equipment, reagents, organisms)
- Sample size calculation (power analysis: α=0.05, β=0.20)
- Statistical test selection based on hypothesis type
- Expected effect size estimation
- Timeline and cost breakdown
- Required ethical approvals checklist

Output: inline section in dissertation OR standalone appendix file.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ExperimentalProtocol:
    """ExperimentalProtocol."""
    hypothesis_id: str
    domain: str  # "biology" | "chemistry" | "physics" | "cs" | "social"

    # Design
    design_type: str  # "RCT" | "cohort" | "case-control" | "in-silico" | "in-vitro" | "in-vivo" | "field"
    sample_size: int
    control_groups: int
    treatment_groups: int

    # Methods
    materials: list[str]
    equipment: list[str]
    procedure: list[str]  # step-by-step

    # Statistics
    statistical_test: str  # "t-test" | "ANOVA" | "χ²" | "regression" | "survival" | "Bayesian"
    effect_size_expected: float  # Cohen's d or equivalent
    power: float  # 0.0-1.0

    # Logistics
    estimated_duration_days: int
    estimated_cost_usd: float
    significance_level: float = 0.05
    ethical_approvals: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """To markdown."""
        lines = [
            "\n## Experimental Validation Protocol",
            "",
            f"**Design:** {self.design_type.upper()} | **Domain:** {self.domain}",
            f"**Sample:** n={self.sample_size} ({self.treatment_groups} treatment + {self.control_groups} control)",
            "",
            "### Materials & Equipment",
        ]
        for m in self.materials[:8]:
            lines.append(f"- {m}")
        for e in self.equipment[:6]:
            lines.append(f"- {e}")

        lines += [
            "",
            "### Procedure",
        ]
        for i, step in enumerate(self.procedure[:10], 1):
            lines.append(f"{i}. {step}")

        lines += [
            "",
            "### Statistical Analysis",
            f"- **Test:** {self.statistical_test}",
            f"- **Expected effect size:** {self.effect_size_expected} (Cohen's d)",
            f"- **Power:** {self.power:.0%} at α={self.significance_level}",
            f"- **Sample justification:** n={self.sample_size} provides {self.power:.0%} power to detect d≥{self.effect_size_expected}",
            "",
            "### Logistics",
            f"- **Estimated duration:** {self.estimated_duration_days} days",
            f"- **Estimated cost:** ${self.estimated_cost_usd:,.0f}",
        ]
        if self.ethical_approvals:
            lines.append(f"- **Required approvals:** {', '.join(self.ethical_approvals)}")

        return "\n".join(lines)


DOMAIN_PROTOCOLS: dict[str, dict] = {
    "biology": {
        "design_types": ["in-vitro", "in-vivo", "RCT", "cohort", "case-control"],
        "materials_templates": [
            "Cell culture media (DMEM/RPMI-1640)",
            "Fetal bovine serum (FBS) 10%",
            "Penicillin-streptomycin 1%",
            "Lipofectamine 3000 transfection reagent",
            "qPCR primers for target gene",
            "Western blot antibodies (primary + HRP-secondary)",
            "siRNA/shRNA for gene knockdown",
            "CRISPR-Cas9 RNP complex",
            "Flow cytometry antibodies",
            "ELISA kit",
        ],
        "equipment_templates": [
            "CO₂ incubator (37°C, 5% CO₂)",
            "Biosafety cabinet Class II",
            "qPCR thermocycler",
            "Western blot transfer system",
            "Flow cytometer",
            "Confocal microscope",
            "Plate reader (absorbance/fluorescence)",
            "Electrophoresis system",
        ],
        "approvals": ["IRB approval", "IACUC approval (if animal)", "Biosafety protocol"],
    },
    "chemistry": {
        "design_types": ["synthesis", "characterization", "assay", "combinatorial"],
        "materials_templates": [
            "Starting reagents (ACS grade)",
            "Solvents (anhydrous, HPLC grade)",
            "Catalyst (specified loading mol%)",
            "TLC plates (silica gel 60 F254)",
            "Column chromatography silica",
            "NMR tubes (5mm, 500 MHz)",
        ],
        "equipment_templates": [
            "Schlenk line / glovebox",
            "NMR spectrometer (500 MHz)",
            "HPLC-MS system",
            "X-ray diffractometer",
            "FTIR spectrometer",
            "Rotary evaporator",
        ],
        "approvals": ["Chemical safety protocol", "Waste disposal plan"],
    },
    "physics": {
        "design_types": ["controlled experiment", "observational", "simulation", "calibration"],
        "materials_templates": [
            "Optical table with vibration isolation",
            "Laser source (specified wavelength/power)",
            "Detector array (specified sensitivity)",
            "Cryostat / vacuum chamber",
            "Calibration standards (NIST-traceable)",
        ],
        "equipment_templates": [
            "Oscilloscope (specified bandwidth)",
            "Spectrum analyzer",
            "Lock-in amplifier",
            "Temperature controller (±0.01K)",
            "Data acquisition system",
        ],
        "approvals": ["Laser safety protocol", "Radiation safety (if applicable)"],
    },
}


def generate_protocol(hypothesis: str, domain: str, effect_size: float = 0.5) -> ExperimentalProtocol:
    """Generate an experimental protocol based on domain templates."""
    templates = DOMAIN_PROTOCOLS.get(domain, DOMAIN_PROTOCOLS["biology"])
    design = templates["design_types"][0]

    # Sample size: power analysis for t-test (Cohen, 1988)
    # n ≈ 2 * (z_α + z_β)² / d²  for independent t-test, α=0.025 (two-tailed), β=0.20
    import math
    z_alpha = 1.96
    z_beta = 0.84
    n_per_group = math.ceil(2 * (z_alpha + z_beta) ** 2 / max(effect_size, 0.1) ** 2)

    # Heuristic cost: $500/day for wet lab, $200/day for computational
    cost_per_day = {"biology": 500, "chemistry": 400, "physics": 300}.get(domain, 300)
    estimated_days = 14 if domain == "biology" else 10

    return ExperimentalProtocol(
        hypothesis_id=f"EXP-{hash(hypothesis) % 10000:04d}",
        domain=domain,
        design_type=design,
        sample_size=n_per_group * 3,  # 1 control + 2 treatment
        control_groups=1,
        treatment_groups=2,
        materials=templates["materials_templates"][:6],
        equipment=templates["equipment_templates"][:5],
        procedure=_generate_procedure(domain, hypothesis),
        statistical_test=_select_test(hypothesis),
        effect_size_expected=effect_size,
        power=0.80,
        significance_level=0.05,
        estimated_duration_days=estimated_days,
        estimated_cost_usd=cost_per_day * estimated_days,
        ethical_approvals=templates["approvals"],
    )


def _generate_procedure(domain: str, hypothesis: str) -> list[str]:
    if domain == "biology":
        return [
            f"Prepare cell cultures: seed {domain}-relevant cell lines at appropriate density",
            "Allow cells to adhere and reach 70-80% confluence (24-48h)",
            "Apply experimental treatment vs. vehicle control (n per group calculated above)",
            "Incubate for specified duration under standard conditions",
            "Harvest cells and extract RNA/protein for downstream analysis",
            "Perform qPCR for target gene expression (ΔΔCt method, housekeeping gene normalization)",
            "Validate by Western blot (protein level) and/or immunofluorescence (localization)",
            "Repeat experiment in 3 independent biological replicates",
            "Statistical analysis: compare groups using appropriate test (see Statistical Analysis section)",
        ]
    elif domain == "chemistry":
        return [
            "Prepare starting materials under inert atmosphere (N₂/Ar)",
            "Add reagents in specified stoichiometric ratios",
            "Monitor reaction progress by TLC/GC-MS at regular intervals",
            "Quench reaction and extract product with appropriate solvent",
            "Purify by column chromatography / recrystallization",
            "Characterize product: ¹H NMR, ¹³C NMR, HRMS, IR",
            "Determine yield and assess purity (>95% by HPLC)",
            "Repeat synthesis 3 times for reproducibility",
        ]
    return [f"Design controlled experiment to test: {hypothesis[:100]}",
            "Collect data under standardized conditions",
            "Apply appropriate statistical test",
            "Report effect size with confidence intervals",
            "Replicate in independent setting"]


def _select_test(hypothesis: str) -> str:
    lower = hypothesis.lower()
    if any(w in lower for w in ["survival", "lifespan", "mortality", "time to"]):
        return "survival analysis (log-rank + Cox proportional hazards)"
    if any(w in lower for w in ["correlat", "associat", "relates to", "linked"]):
        return "Pearson/Spearman correlation + multiple regression"
    if any(w in lower for w in ["difference", "changes", "affects", "increases", "decreases"]):
        return "t-test / ANOVA with post-hoc Tukey HSD"
    if any(w in lower for w in ["interact", "synergy", "modulat"]):
        return "two-way ANOVA with interaction term"
    return "appropriate parametric/non-parametric test based on data distribution"
