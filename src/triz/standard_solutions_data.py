# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StandardSolution:
    """A single TRIZ Standard Solution."""

    id: str
    name: str
    description: str
    applicability: str  # Human-readable predicate description
    c4_trajectory: list[tuple[int, int, int]]
    examples: list[str] = field(default_factory=list)
    related_principles: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "applicability": self.applicability,
            "c4_trajectory": self.c4_trajectory,
            "examples": self.examples,
            "related_principles": self.related_principles,
        }


# =============================================================================
# CLASS 1: Establish or Modify Su-Fields (13 solutions)
# =============================================================================

CLASS_1_SOLUTIONS: list[StandardSolution] = [
    StandardSolution(
        id="1.1.1",
        name="Complete an Incomplete Su-Field",
        description=(
            "If a technical system contains an incomplete Su-Field (missing S2 or F), "
            "complete it by introducing the missing element. This is the most fundamental "
            "innovation pattern: identify what is absent and add it."
        ),
        applicability="Su-Field has S1 only; both S2 and F are missing.",
        c4_trajectory=[(1, 0, 0), (2, 0, 0), (2, 1, 0)],
        examples=[
            "Add a cutting tool (S2) and mechanical force (F) to process a raw material (S1).",
            "Introduce an electrode (S2) and electric field (F) to plate a metal surface (S1).",
        ],
        related_principles=[24, 28],
    ),
    StandardSolution(
        id="1.1.2",
        name="Add a Field to an Existing S1-S2 Pair",
        description=(
            "If S1 and S2 exist but are not coupled by a field, introduce a field "
            "to create a functional Su-Field. Choose the field type based on the desired interaction."
        ),
        applicability="S1 and S2 exist but no field couples them.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        examples=[
            "Ultrasonic welding: two plastic parts (S1, S2) joined by ultrasonic vibration (F).",
            "Magnetic particle inspection: ferromagnetic part (S1) + magnetizing coil (S2) + magnetic field (F).",
        ],
        related_principles=[28, 18],
    ),
    StandardSolution(
        id="1.1.3",
        name="Add a Tool S2 for an Existing Field",
        description=(
            "If S1 and a field exist but there is no tool to direct or modulate the field, "
            "introduce S2 to channel the field energy onto S1 effectively."
        ),
        applicability="S1 and F exist; S2 is missing.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (2, 1, 0)],
        examples=[
            "Lens (S2) focuses sunlight (F) onto a solar cell (S1).",
            "Reflector (S2) directs radar waves (F) onto a target (S1).",
        ],
        related_principles=[24, 19],
    ),
    StandardSolution(
        id="1.1.4",
        name="Add Ferromagnetic Particles and Magnetic Field",
        description=(
            "Introduce ferromagnetic particles into S1 or S2, then apply a magnetic field "
            "to gain precise control over the interaction. This enables remote, contactless actuation."
        ),
        applicability="System requires precise, remote, or contactless control of interaction.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Magnetic abrasive finishing: ferromagnetic abrasive particles + magnetic field polish metal.",
            "Ferrofluid seals: magnetic particles in carrier fluid form tight seal under magnetic field.",
        ],
        related_principles=[28, 29, 35],
    ),
    StandardSolution(
        id="1.1.5",
        name="Add Ferromagnetic Particles with External Field Source",
        description=(
            "Use an external source (e.g., electromagnet, permanent magnet) to generate "
            "the magnetic field for ferromagnetic particle systems. Allows switching and control."
        ),
        applicability="System already has ferromagnetic particles; needs external field control.",
        c4_trajectory=[(1, 0, 1), (1, 1, 1), (2, 1, 2)],
        examples=[
            "Magnetic drug delivery: ferromagnetic nanoparticles guided by external electromagnet.",
            "Magnetic separation: ferromagnetic contaminants removed by applying external magnetic field.",
        ],
        related_principles=[23, 28],
    ),
    StandardSolution(
        id="1.1.6",
        name="Use Ferromagnetic Particles with Capillary Structure",
        description=(
            "Combine ferromagnetic particles with a porous or capillary structure to "
            "create complex, field-responsive materials with multifunctional properties."
        ),
        applicability="System requires field-responsive material with internal structure.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0), (1, 2, 1)],
        examples=[
            "Magnetorheological fluids in porous dampers: stiffness tuned by magnetic field.",
            "Self-healing composites: magnetic particles in capillary network for crack closing.",
        ],
        related_principles=[30, 31, 35],
    ),
    StandardSolution(
        id="1.1.7",
        name="Natural Ferromagnetic Particles",
        description=(
            "If the object (S1) is naturally ferromagnetic, use its own magnetic properties "
            "without adding external particles. Exploit inherent material properties."
        ),
        applicability="S1 is naturally ferromagnetic (iron, nickel, cobalt, certain alloys).",
        c4_trajectory=[(1, 0, 0), (1, 0, 2), (1, 1, 2)],
        examples=[
            "Electromagnetic forming: use workpiece's own ferromagnetism for shaping.",
            "Magnetic levitation of naturally ferromagnetic objects without additives.",
        ],
        related_principles=[27, 33],
    ),
    StandardSolution(
        id="1.1.8",
        name="Introduce Additive with Magnetic Properties",
        description=(
            "If S1 is non-ferromagnetic, add a ferromagnetic coating, layer, or particle "
            "to enable magnetic field interaction."
        ),
        applicability="S1 is non-ferromagnetic but magnetic interaction is desired.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "Magnetic ink: non-magnetic paper + ferromagnetic pigment for MICR encoding.",
            "Magnetic targeting: non-magnetic drug encapsulated in ferromagnetic carrier.",
        ],
        related_principles=[24, 35],
    ),
    StandardSolution(
        id="1.2.1",
        name="Introduce S3 Between S1 and S2",
        description=(
            "Add a third substance (S3) between S1 and S2 to modify the field interaction. "
            "S3 can amplify, filter, or redirect the field."
        ),
        applicability="Existing S1-S2-F Su-Field needs modification of interaction.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Thermal barrier coating (S3) between turbine blade (S1) and hot gas (S2).",
            "Buffer solution (S3) between electrode (S2) and sample (S1) in electrochemistry.",
        ],
        related_principles=[24, 1],
    ),
    StandardSolution(
        id="1.2.2",
        name="Introduce S3 Derived from S1 or S2",
        description=(
            "Instead of an external S3, use a modified or extracted portion of S1 or S2 "
            "as the intermediate substance. Reduces system complexity."
        ),
        applicability="External S3 is undesirable; system should be self-contained.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 2)],
        examples=[
            "Oxide layer (S3 from S1) on aluminum as natural protective coating.",
            "Passive film on stainless steel: chromium from alloy forms protective layer.",
        ],
        related_principles=[25, 33],
    ),
    StandardSolution(
        id="1.2.3",
        name="Introduce Environmental Substance as S3",
        description=(
            "Use an ambient substance (air, water, surrounding medium) as S3. "
            "Leverages what is already present in the environment."
        ),
        applicability="External S3 should be avoided; environment can provide the mediator.",
        c4_trajectory=[(1, 0, 0), (0, 0, 1), (0, 1, 1)],
        examples=[
            "Air cooling: ambient air (S3) carries heat away from CPU (S1).",
            "Underwater welding: surrounding water (S3) cools the weld zone.",
        ],
        related_principles=[22, 25],
    ),
    StandardSolution(
        id="1.2.4",
        name="Use Void or Gas as S3",
        description=(
            "Use a void, vacuum, or gas bubble as S3. This avoids introducing any "
            "solid or liquid material into the system."
        ),
        applicability="System must avoid contamination or added material.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Air bearings: thin air film (S3) separates shaft (S1) from housing (S2).",
            "Vacuum insulation: void (S3) prevents heat transfer between walls.",
        ],
        related_principles=[29, 30],
    ),
    StandardSolution(
        id="1.2.5",
        name="Use Field Instead of S3",
        description=(
            "Replace a physical intermediate substance (S3) with a field. "
            "Achieves contactless mediation with no material contamination."
        ),
        applicability="S3 causes contamination, wear, or material compatibility issues.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        examples=[
            "Magnetic bearings replace mechanical bearings (S3) with magnetic field.",
            "Electrostatic precipitator replaces filter (S3) with electric field to remove particles.",
        ],
        related_principles=[28, 29],
    ),
]


# =============================================================================
# CLASS 2: Remove Harmful Effects (23 solutions)
# =============================================================================

CLASS_2_SOLUTIONS: list[StandardSolution] = [
    StandardSolution(
        id="2.1.1",
        name="Introduce S3 to Protect S1 from Harmful Field",
        description=(
            "Add a protective substance (S3) between S1 and the harmful field source. "
            "S3 absorbs, reflects, or diverts the harmful effect."
        ),
        applicability="S1 is exposed to a harmful field from S2.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Radiation shield (S3) protects astronauts (S1) from cosmic rays (S2+F).",
            "Heat shield tiles (S3) protect space shuttle (S1) from atmospheric friction heat (F).",
        ],
        related_principles=[1, 24, 30],
    ),
    StandardSolution(
        id="2.1.2",
        name="Modify S1 to Resist Harmful Field",
        description=(
            "Change the properties of S1 itself so that it becomes resistant to "
            "the harmful field, eliminating the need for external protection."
        ),
        applicability="S1 can be modified without losing its primary function.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Doped silicon becomes radiation-hard for space electronics.",
            "Alloyed steel becomes corrosion-resistant in acidic environments.",
        ],
        related_principles=[35, 33, 3],
    ),
    StandardSolution(
        id="2.1.3",
        name="Modify or Replace the Harmful Field",
        description=(
            "Change the field type or its parameters (intensity, frequency, direction) "
            "so that it no longer causes harm while still achieving the useful function."
        ),
        applicability="The field itself can be altered without losing usefulness.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (2, 1, 0)],
        examples=[
            "Switch from continuous-wave to pulsed laser to reduce thermal damage.",
            "Use low-frequency ultrasound instead of high-frequency to avoid cavitation damage.",
        ],
        related_principles=[19, 28, 35],
    ),
    StandardSolution(
        id="2.2.1",
        name="Eliminate Harmful Field by Counter-Field",
        description=(
            "Introduce a counteracting field that neutralizes the harmful effect. "
            "The two fields superpose to cancel the harm."
        ),
        applicability="Harmful field can be precisely measured and countered.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        examples=[
            "Noise-canceling headphones generate anti-noise to cancel ambient sound.",
            "Active vibration control: counter-shaker cancels machine vibration.",
        ],
        related_principles=[22, 23],
    ),
    StandardSolution(
        id="2.2.2",
        name="Introduce S3 to Absorb Harmful Field",
        description=(
            "Add a substance that absorbs the harmful field energy and converts it "
            "to a benign form (heat dissipation, re-radiation, etc.)."
        ),
        applicability="Absorbing material can be added without affecting S1 function.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "EMI ferrite cores absorb high-frequency electromagnetic interference.",
            "Acoustic foam absorbs sound reflections in recording studios.",
        ],
        related_principles=[1, 24],
    ),
    StandardSolution(
        id="2.2.3",
        name="Use Field-Activated Substance to Control Harmful Effect",
        description=(
            "Introduce a substance that changes properties under the field, "
            "thereby dynamically controlling the harmful effect."
        ),
        applicability="Dynamic, adaptive protection is needed.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (2, 0, 1)],
        examples=[
            "Photochromic glass darkens under UV to protect from intense light.",
            "Magnetorheological damper stiffens under magnetic field to suppress shock.",
        ],
        related_principles=[23, 32, 35],
    ),
    StandardSolution(
        id="2.3.1",
        name="Switch to a Different Field Type",
        description=(
            "Replace the harmful field with a different field type that achieves "
            "the same useful effect but without the harmful side effects."
        ),
        applicability="Alternative field types exist for the same function.",
        c4_trajectory=[(1, 0, 0), (2, 0, 0), (2, 1, 0)],
        examples=[
            "Replace mechanical cutting (wear, heat) with laser cutting (clean, precise).",
            "Replace thermal sterilization with UV light sterilization.",
        ],
        related_principles=[28, 35],
    ),
    StandardSolution(
        id="2.3.2",
        name="Switch from Thermal to Optical Field",
        description=(
            "Specific case: replace thermal processes with optical (laser, UV, IR) "
            "processes to reduce heat-affected zones and thermal damage."
        ),
        applicability="Thermal field causes excessive heat damage to S1.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (2, 1, 0)],
        examples=[
            "Laser welding replaces arc welding to minimize heat-affected zone.",
            "UV curing replaces thermal curing for heat-sensitive substrates.",
        ],
        related_principles=[28, 35],
    ),
    StandardSolution(
        id="2.3.3",
        name="Switch from Mechanical to Electrical/Magnetic Field",
        description=(
            "Replace mechanical contact and force with non-contact electromagnetic "
            "interaction to eliminate friction, wear, and mechanical fatigue."
        ),
        applicability="Mechanical contact causes wear, friction, or fatigue.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (2, 0, 1)],
        examples=[
            "Magnetic levitation replaces wheel bearings in high-speed trains.",
            "Induction heating replaces flame heating for clean, contactless processing.",
        ],
        related_principles=[28, 29],
    ),
    StandardSolution(
        id="2.4.1",
        name="Use Ferromagnetic Particles with Magnetic Field for Protection",
        description=(
            "Apply ferromagnetic particles and a controlled magnetic field to create "
            "an adaptive shield against harmful fields or particles."
        ),
        applicability="Harmful effect is from particles or fields that can be magnetically controlled.",
        c4_trajectory=[(1, 0, 0), (1, 0, 2), (1, 1, 2)],
        examples=[
            "Magnetic fluid seals prevent dust and contaminants from entering precision instruments.",
            "Magnetic filters capture ferromagnetic wear debris from lubricating oil.",
        ],
        related_principles=[28, 30],
    ),
    StandardSolution(
        id="2.4.2",
        name="Use Ferromagnetic Particles in Capillary Structure for Protection",
        description=(
            "Embed ferromagnetic particles in a porous matrix; apply magnetic field "
            "to dynamically seal, filter, or dampen harmful effects."
        ),
        applicability="System requires controllable, reversible protection mechanism.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 1)],
        examples=[
            "Magnetorheological elastomers: stiffness changes with field to absorb shocks.",
            "Smart porous membranes: magnetic field controls pore size for selective filtration.",
        ],
        related_principles=[30, 31, 35],
    ),
    StandardSolution(
        id="2.4.3",
        name="Use Environmental Ferromagnetic Particles",
        description=(
            "If the environment naturally contains ferromagnetic material, exploit it "
            "for protection or control without adding new substances."
        ),
        applicability="Environment has natural ferromagnetic components.",
        c4_trajectory=[(1, 0, 0), (0, 0, 1), (0, 1, 1)],
        examples=[
            "Using soil's natural iron content for magnetic ground stabilization.",
            "Magnetic separation of natural magnetite from ore slurry.",
        ],
        related_principles=[22, 33],
    ),
    StandardSolution(
        id="2.5.1",
        name="Transform Harmful Field into Useful One",
        description=(
            "Reframe the harmful effect as a resource. Modify the system so that "
            "what was harmful now performs a useful function."
        ),
        applicability="The harmful effect carries energy or information that can be harvested.",
        c4_trajectory=[(1, 0, 0), (1, 1, 1), (1, 2, 2)],
        examples=[
            "Waste heat recovery: exhaust heat (harmful) generates electricity (useful).",
            "Regenerative braking: kinetic energy (heat when braked) charges battery.",
        ],
        related_principles=[22, 25],
    ),
    StandardSolution(
        id="2.5.2",
        name="Amplify Harmful Field Until It Becomes Harmless",
        description=(
            "Increase the harmful effect to such an extreme that its nature changes "
            "and it no longer causes the original harm."
        ),
        applicability="The harmful effect has a threshold beyond which harm is eliminated.",
        c4_trajectory=[(1, 0, 0), (2, 0, 0), (2, 1, 2)],
        examples=[
            "Controlled burns: small fires prevent large destructive wildfires.",
            "Vaccination: weakened pathogen builds immunity without causing disease.",
        ],
        related_principles=[22, 21],
    ),
    StandardSolution(
        id="2.5.3",
        name="Combine Multiple Harmful Effects to Neutralize",
        description=(
            "Add a second harmful effect that counteracts the first. The two effects "
            "cancel or dominate each other, resulting in net safety."
        ),
        applicability="A second, controllable harmful effect can be introduced.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 2)],
        examples=[
            "Counter-rotating propellers cancel torque on aircraft.",
            "Chemical neutralization: acid + base = harmless salt water.",
        ],
        related_principles=[22, 1],
    ),
    StandardSolution(
        id="2.6.1",
        name="Remove Harmful Source from System",
        description=(
            "Eliminate the source of the harmful field rather than trying to protect "
            "against it. If S2 is harmful, remove or replace S2."
        ),
        applicability="S2 is not essential; another tool can perform the same function.",
        c4_trajectory=[(1, 0, 0), (0, 0, 0), (0, 1, 0)],
        examples=[
            "Replace solvent-based paint (harmful VOCs) with water-based paint.",
            "Remove asbestos insulation and replace with mineral wool.",
        ],
        related_principles=[2, 27],
    ),
    StandardSolution(
        id="2.6.2",
        name="Segment S1 to Isolate Harmful Zones",
        description=(
            "Divide S1 into segments so that harmful effects are localized to "
            "sacrificial or non-critical parts."
        ),
        applicability="Harmful effect is localized; segmentation is feasible.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "Fuse: thin segment melts to protect entire circuit.",
            "Crumple zones in cars absorb impact, protecting passenger compartment.",
        ],
        related_principles=[1, 11],
    ),
    StandardSolution(
        id="2.6.3",
        name="Make S1 Self-Protecting",
        description=(
            "Design S1 so that it automatically generates its own protective layer, "
            "field, or structure when exposed to the harmful effect."
        ),
        applicability="S1 can react to the harmful field by forming a protective response.",
        c4_trajectory=[(1, 0, 0), (1, 0, 2), (1, 1, 2)],
        examples=[
            "Passivation: stainless steel forms protective oxide film when exposed to oxygen.",
            "Self-healing concrete: cracks trigger internal repair via bacterial capsules.",
        ],
        related_principles=[25, 23],
    ),
    StandardSolution(
        id="2.7.1",
        name="Use Porous Material to Distribute Harmful Effect",
        description=(
            "Replace dense S1 with porous material so that harmful effects (heat, "
            "stress, chemicals) are distributed rather than concentrated."
        ),
        applicability="Harmful effect is concentrated; distribution reduces peak damage.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Porous burner distributes flame for even, low-NOx combustion.",
            "Foam padding distributes impact force to reduce peak pressure on body.",
        ],
        related_principles=[31, 30],
    ),
    StandardSolution(
        id="2.7.2",
        name="Use Flexible Shell or Film to Isolate",
        description=(
            "Cover S1 with a thin, flexible film or shell that isolates it from "
            "the harmful field while maintaining function."
        ),
        applicability="Thin barrier is sufficient to block or redirect the harmful effect.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "Gore-Tex membrane: thin film keeps water out while letting vapor escape.",
            "Conformal coating on PCBs protects from moisture and corrosion.",
        ],
        related_principles=[30, 1],
    ),
    StandardSolution(
        id="2.7.3",
        name="Use Capillary Structure for Controlled Release",
        description=(
            "Embed the harmful substance or energy source in a capillary structure "
            "that releases it slowly and controllably."
        ),
        applicability="Harmful effect is from uncontrolled release of energy or substance.",
        c4_trajectory=[(1, 0, 0), (1, 1, 1), (1, 2, 1)],
        examples=[
            "Drug-eluting stent: capillary polymer coating releases drug over months.",
            "Slow-release fertilizer: porous granules release nutrients gradually.",
        ],
        related_principles=[31, 19],
    ),
    StandardSolution(
        id="2.1.4",
        name="Introduce Protective Atmosphere or Vacuum",
        description=(
            "Replace the normal environment around S1 with an inert gas, protective "
            "atmosphere, or vacuum to eliminate harmful chemical or physical interactions."
        ),
        applicability="Harmful effect comes from environmental gases, moisture, or particles.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Nitrogen atmosphere prevents oxidation during high-temperature processing.",
            "Vacuum packaging removes oxygen to prevent food spoilage.",
        ],
        related_principles=[29, 39],
    ),
    StandardSolution(
        id="2.4.4",
        name="Use Electric Field for Particle Deflection",
        description=(
            "Apply an electric field to deflect or trap charged harmful particles before "
            "they reach S1, preventing contamination or damage."
        ),
        applicability="Harmful particles are charged or can be ionized.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (2, 0, 1)],
        examples=[
            "Electrostatic precipitator removes dust from industrial exhaust gases.",
            "Ion thruster: electric field accelerates ions for propulsion while shielding spacecraft.",
        ],
        related_principles=[28, 30],
    ),
]


# =============================================================================
# CLASS 3: System Transition (6 solutions)
# =============================================================================

CLASS_3_SOLUTIONS: list[StandardSolution] = [
    StandardSolution(
        id="3.1.1",
        name="Transition to Bi-System",
        description=(
            "Combine two similar systems into a dual (bi-) system to enhance "
            "performance or add functionality."
        ),
        applicability="Single system is at performance limit; two can cooperate.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Dual-core processor: two CPUs share workload.",
            "Binocular vision: two eyes provide depth perception.",
        ],
        related_principles=[5, 6],
    ),
    StandardSolution(
        id="3.1.2",
        name="Transition to Poly-System",
        description=(
            "Extend the bi-system idea to multiple (poly-) systems. Many identical "
            "or complementary systems work in parallel or series."
        ),
        applicability="Bi-system is insufficient; many units provide scalability.",
        c4_trajectory=[(1, 0, 0), (1, 1, 1), (1, 2, 2)],
        examples=[
            "Multi-core CPU with 64+ cores for massive parallelism.",
            "Swarm robotics: hundreds of simple robots perform complex tasks collectively.",
        ],
        related_principles=[5, 1],
    ),
    StandardSolution(
        id="3.2.1",
        name="Transition from Homogeneous to Heterogeneous System",
        description=(
            "Replace identical subsystems with differentiated ones, each optimized "
            "for a specific sub-function."
        ),
        applicability="Homogeneous system has inefficiencies; specialization helps.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Heterogeneous computing: CPU + GPU + FPGA each handle suitable workloads.",
            "Specialized worker teams in manufacturing: each station optimized for one operation.",
        ],
        related_principles=[3, 40],
    ),
    StandardSolution(
        id="3.2.2",
        name="Combine Opposite Systems",
        description=(
            "Integrate two systems with opposite properties into one hybrid system "
            "that exhibits both properties as needed."
        ),
        applicability="System needs contradictory properties that pure systems cannot provide.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 2)],
        examples=[
            "Amphibious vehicle: combines car (land) and boat (water) systems.",
            "Hybrid car: combines electric motor (efficiency) and combustion engine (range).",
        ],
        related_principles=[6, 40],
    ),
    StandardSolution(
        id="3.3.1",
        name="Transition to Super-System",
        description=(
            "Merge the current system with adjacent systems to form a super-system "
            "that provides new capabilities at a higher level."
        ),
        applicability="System is isolated; integration with environment creates new value.",
        c4_trajectory=[(1, 0, 0), (1, 1, 1), (1, 2, 2)],
        examples=[
            "Smart grid: merges generation, transmission, and consumption into unified system.",
            "Smart city: integrates transport, energy, water, and communication infrastructure.",
        ],
        related_principles=[5, 6],
    ),
    StandardSolution(
        id="3.3.2",
        name="Transition to Micro-Level",
        description=(
            "Move the critical function from the macro-level to the micro- or nano-level. "
            "Use particles, molecules, or atoms as the new working elements."
        ),
        applicability="Macro-level approach hits physical limits; micro-level offers new control.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Nanoparticle drug delivery: drugs transported by nanoparticles to target cells.",
            "Molecular electronics: single molecules as switches and wires.",
        ],
        related_principles=[1, 27, 35],
    ),
]


# =============================================================================
# CLASS 4: Detection and Measurement (17 solutions)
# =============================================================================

CLASS_4_SOLUTIONS: list[StandardSolution] = [
    StandardSolution(
        id="4.1.1",
        name="Indirect Measurement via Copy",
        description=(
            "Instead of measuring the object directly, create a copy or image and "
            "measure that. Protects the original and enables non-contact sensing."
        ),
        applicability="Direct measurement is impossible, dangerous, or destructive.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "X-ray imaging measures internal bone structure without surgery.",
            "Satellite imagery measures terrain without ground survey.",
        ],
        related_principles=[26, 28],
    ),
    StandardSolution(
        id="4.1.2",
        name="Measure Change in an Intermediate Object",
        description=(
            "Introduce an intermediate object that changes measurably when exposed "
            "to the property being studied. Measure the intermediate, not the target."
        ),
        applicability="Target property cannot be measured directly.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Mercury thermometer: mercury expands (intermediate change) indicating temperature.",
            "Strain gauge: resistance change measures mechanical deformation.",
        ],
        related_principles=[24, 28],
    ),
    StandardSolution(
        id="4.1.3",
        name="Measure Multiple Properties and Calculate Target",
        description=(
            "Measure several accessible properties and compute the desired property "
            "through a known physical relationship."
        ),
        applicability="Target property is functionally related to measurable ones.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Calculate density from separately measured mass and volume.",
            "Calculate viscosity from pressure drop and flow rate in a capillary.",
        ],
        related_principles=[6, 23],
    ),
    StandardSolution(
        id="4.2.1",
        name="Create Artificial Measurement Field",
        description=(
            "If the natural field is too weak or absent, introduce an artificial field "
            "and measure how the system responds to it."
        ),
        applicability="Natural field insufficient or absent for measurement.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (2, 0, 1)],
        examples=[
            "Eddy current testing: induced magnetic field reveals cracks in metal.",
            "Ultrasonic flaw detection: artificial ultrasound pulse detects internal defects.",
        ],
        related_principles=[28, 18],
    ),
    StandardSolution(
        id="4.2.2",
        name="Use Ferromagnetic Particles for Detection",
        description=(
            "Add ferromagnetic particles to the object or medium, then apply a magnetic "
            "field and measure the response for detection or imaging."
        ),
        applicability="Object is non-ferromagnetic or detection sensitivity is insufficient.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "MRI contrast agents: gadolinium enhances magnetic response for clearer imaging.",
            "Magnetic particle inspection: iron filings reveal surface cracks in steel.",
        ],
        related_principles=[28, 32],
    ),
    StandardSolution(
        id="4.2.3",
        name="Use Field-Activated Markers",
        description=(
            "Introduce markers that change their field response when exposed to the "
            "target property, enabling sensitive indirect detection."
        ),
        applicability="Target property needs amplification or transduction for detection.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "Fluorescent probes: bind to target molecule and emit light under UV excitation.",
            "Quantum dots: size-tunable optical emission for multiplexed biosensing.",
        ],
        related_principles=[28, 32],
    ),
    StandardSolution(
        id="4.3.1",
        name="Enhance Measurement by Field Amplification",
        description=(
            "Increase the field intensity or concentrate it to improve measurement "
            "sensitivity and signal-to-noise ratio."
        ),
        applicability="Signal is too weak for reliable detection.",
        c4_trajectory=[(1, 0, 0), (2, 0, 0), (2, 1, 0)],
        examples=[
            "Parabolic dish concentrates weak radio signals for better reception.",
            "Optical cavity enhances light-matter interaction for precision spectroscopy.",
        ],
        related_principles=[3, 19],
    ),
    StandardSolution(
        id="4.3.2",
        name="Measure Resonant Frequency Shift",
        description=(
            "Use resonant systems and measure the frequency shift caused by the target "
            "property. Highly sensitive to small changes."
        ),
        applicability="Target property affects mass, stiffness, or geometry of resonator.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Quartz crystal microbalance: mass adsorption shifts resonant frequency.",
            "MEMS resonant sensors: pressure or acceleration changes resonant frequency.",
        ],
        related_principles=[18, 28],
    ),
    StandardSolution(
        id="4.3.3",
        name="Measure Phase or Interference Pattern",
        description=(
            "Use wave interference or phase shifts to measure extremely small changes. "
            "Phase measurement is often more sensitive than amplitude."
        ),
        applicability="Target causes small path-length or refractive-index changes.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 1)],
        examples=[
            "Laser interferometer measures distance changes at nanometer scale.",
            "Holographic interferometry maps deformation via fringe patterns.",
        ],
        related_principles=[26, 28],
    ),
    StandardSolution(
        id="4.4.1",
        name="Use Chemical Indicator",
        description=(
            "Apply a chemical that changes color, pH, or other visible property when "
            "exposed to the target substance or condition."
        ),
        applicability="Target is chemical in nature or induces chemical change.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Litmus paper: color change indicates pH.",
            "CO2 indicator: solution turns yellow when CO2 concentration rises.",
        ],
        related_principles=[32, 28],
    ),
    StandardSolution(
        id="4.4.2",
        name="Use Thermal Indicator",
        description=(
            "Use materials that change thermal properties (emissivity, conductivity) "
            "or appearance (thermochromic) to indicate temperature or heat flow."
        ),
        applicability="Target property is thermal or causes temperature change.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (2, 1, 0)],
        examples=[
            "Thermochromic paint changes color at specific temperature thresholds.",
            "Thermal imaging camera detects infrared emission indicating heat distribution.",
        ],
        related_principles=[32, 28],
    ),
    StandardSolution(
        id="4.4.3",
        name="Use Mechanical Indicator",
        description=(
            "Use deformation, displacement, or vibration of an object to indicate "
            "the magnitude of the measured property."
        ),
        applicability="Target causes mechanical deformation or force.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "Bourdon tube: pressure deforms curved tube, moving needle on gauge.",
            "Seismograph: ground motion moves mass on spring, recording vibration amplitude.",
        ],
        related_principles=[28, 29],
    ),
    StandardSolution(
        id="4.5.1",
        name="Use Feedback for Measurement",
        description=(
            "Implement a feedback loop where the measurement result automatically "
            "adjusts the measurement process for optimal accuracy."
        ),
        applicability="Measurement conditions vary; adaptive control improves accuracy.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        examples=[
            "Auto-focus camera: measures contrast and adjusts lens position iteratively.",
            "Adaptive sampling ADC: adjusts resolution based on signal bandwidth.",
        ],
        related_principles=[23, 15],
    ),
    StandardSolution(
        id="4.5.2",
        name="Use Multiple Sensors and Sensor Fusion",
        description=(
            "Combine data from multiple sensors measuring different aspects to obtain "
            "a more accurate and robust measurement than any single sensor."
        ),
        applicability="Single sensor is noisy, biased, or has limited range.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 2)],
        examples=[
            "GPS + IMU fusion: GPS provides absolute position, IMU fills gaps between fixes.",
            "Autonomous vehicles fuse camera, lidar, and radar for robust perception.",
        ],
        related_principles=[5, 23],
    ),
    StandardSolution(
        id="4.5.3",
        name="Use Model-Based Estimation",
        description=(
            "Instead of direct measurement, use a mathematical model and a few indirect "
            "measurements to estimate the target property via state estimation."
        ),
        applicability="Target is not directly measurable but obeys known dynamics.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Kalman filter estimates robot position from wheel odometry + IMU.",
            "Soft sensors estimate distillation product quality from temperature/pressure.",
        ],
        related_principles=[26, 23],
    ),
    StandardSolution(
        id="4.6.1",
        name="Use Time-Domain Measurement",
        description=(
            "Measure the time taken for a signal or pulse to travel, reflect, or decay. "
            "Time-domain methods often provide better resolution."
        ),
        applicability="Target affects propagation time or temporal dynamics.",
        c4_trajectory=[(1, 0, 0), (2, 0, 0), (2, 1, 0)],
        examples=[
            "LIDAR: time-of-flight of laser pulse measures distance.",
            "Ultrasonic thickness gauge: echo time measures wall thickness.",
        ],
        related_principles=[19, 28],
    ),
    StandardSolution(
        id="4.6.2",
        name="Use Frequency-Domain Measurement",
        description=(
            "Analyze the frequency spectrum of the signal rather than time-domain amplitude. "
            "Frequency shifts reveal subtle property changes."
        ),
        applicability="Target modulates frequency, phase, or spectral content.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (2, 1, 0)],
        examples=[
            "Doppler radar: frequency shift measures velocity.",
            "NMR spectroscopy: chemical shift identifies molecular structure.",
        ],
        related_principles=[18, 28],
    ),
]


# =============================================================================
# CLASS 5: Simplification and Strategy (17 solutions)
# =============================================================================

CLASS_5_SOLUTIONS: list[StandardSolution] = [
    StandardSolution(
        id="5.1.1",
        name="Eliminate Redundant Functions",
        description=(
            "Remove functions that are duplicated across subsystems or that do not "
            "contribute to the overall system purpose."
        ),
        applicability="System has accumulated complexity; functions overlap.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Consolidate multiple databases into one to eliminate sync functions.",
            "Remove manual data entry where automated sensors already capture the data.",
        ],
        related_principles=[2, 6],
    ),
    StandardSolution(
        id="5.1.2",
        name="Eliminate Redundant Objects",
        description=(
            "Remove physical components that serve no unique function. Each part "
            "should justify its existence by a distinct, necessary role."
        ),
        applicability="System has parts that are historical artifacts, no longer needed.",
        c4_trajectory=[(1, 0, 0), (0, 0, 0), (0, 1, 0)],
        examples=[
            "Paperless office eliminates filing cabinets, printers, and physical mail.",
            "Digital wallet eliminates physical cards, coins, and receipts.",
        ],
        related_principles=[2, 27],
    ),
    StandardSolution(
        id="5.1.3",
        name="Eliminate Redundant Operations",
        description=(
            "Remove process steps that do not add value. Streamline the workflow "
            "to the minimum necessary sequence."
        ),
        applicability="Process has evolved with unnecessary approvals, checks, or handoffs.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 1, 1)],
        examples=[
            "Single-piece flow manufacturing eliminates batch queueing and inventory.",
            "One-click checkout removes cart, shipping form, and confirmation pages.",
        ],
        related_principles=[20, 25],
    ),
    StandardSolution(
        id="5.2.1",
        name="Replace Multiple Parts with One Universal Part",
        description=(
            "Find a single component or material that can perform the functions of "
            "several existing parts."
        ),
        applicability="Multiple parts each do one thing; a multifunctional alternative exists.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 1)],
        examples=[
            "Smartphone replaces camera, GPS, music player, and phone.",
            "Universal joint replaces multiple hinge and pivot mechanisms.",
        ],
        related_principles=[6, 5],
    ),
    StandardSolution(
        id="5.2.2",
        name="Replace Mechanical with Field-Based Interaction",
        description=(
            "Eliminate physical contact and mechanical linkages by replacing them with "
            "field-based (electromagnetic, optical) interactions."
        ),
        applicability="Mechanical parts wear, create friction, or limit speed.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (2, 0, 1)],
        examples=[
            "Wireless charging replaces mechanical plug and socket.",
            "Optical encoder replaces mechanical rotary encoder (no wear).",
        ],
        related_principles=[28, 23],
    ),
    StandardSolution(
        id="5.2.3",
        name="Replace Fixed with Adaptive Structures",
        description=(
            "Eliminate the need for multiple configurations by making the structure "
            "adapt dynamically to conditions."
        ),
        applicability="System needs different configurations for different conditions.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Variable-pitch propeller replaces fixed-pitch + gearbox combination.",
            "Adaptive optics replace multiple fixed corrective lenses.",
        ],
        related_principles=[15, 35],
    ),
    StandardSolution(
        id="5.3.1",
        name="Use Self-Service Principle",
        description=(
            "Design the system so that it performs auxiliary functions for itself, "
            "reducing the need for external maintenance or support."
        ),
        applicability="System requires frequent maintenance, calibration, or external support.",
        c4_trajectory=[(1, 0, 0), (1, 0, 2), (1, 1, 2)],
        examples=[
            "Self-cleaning oven: pyrolysis burns off residue at high temperature.",
            "Self-lubricating bearings: embedded solid lubricant releases during operation.",
        ],
        related_principles=[25, 23],
    ),
    StandardSolution(
        id="5.3.2",
        name="Use Waste Resources",
        description=(
            "Identify waste streams (energy, material, heat, information) and redesign "
            "the system to capture and reuse them."
        ),
        applicability="System produces significant waste that could be a resource.",
        c4_trajectory=[(1, 0, 0), (1, 1, 1), (1, 2, 2)],
        examples=[
            "Waste heat from data centers warms nearby buildings.",
            "CO2 from fermentation captured and used for beverage carbonation.",
        ],
        related_principles=[22, 25],
    ),
    StandardSolution(
        id="5.3.3",
        name="Use Environmental Resources",
        description=(
            "Instead of adding resources to the system, use what is freely available "
            "in the environment (air, water, gravity, solar energy)."
        ),
        applicability="System imports energy or materials that environment provides freely.",
        c4_trajectory=[(1, 0, 0), (0, 0, 1), (0, 1, 1)],
        examples=[
            "Passive solar heating uses sunlight instead of fuel combustion.",
            "Rainwater harvesting replaces potable water for irrigation.",
        ],
        related_principles=[22, 25],
    ),
    StandardSolution(
        id="5.4.1",
        name="Segment System for Modularity",
        description=(
            "Divide the system into independent, interchangeable modules. Each module "
            "can be developed, tested, and replaced independently."
        ),
        applicability="System is monolithic; upgrades or repairs require full shutdown.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Modular smartphone: camera, battery, screen are swappable modules.",
            "Containerized software: each service runs in independent container.",
        ],
        related_principles=[1, 2],
    ),
    StandardSolution(
        id="5.4.2",
        name="Segment System for Parallelization",
        description=(
            "Divide the system so that multiple segments can operate in parallel, "
            "increasing throughput without increasing individual unit speed."
        ),
        applicability="Single unit is at speed limit; parallel units multiply capacity.",
        c4_trajectory=[(1, 0, 0), (1, 0, 1), (1, 1, 2)],
        examples=[
            "Multi-lane highway: parallel lanes multiply vehicle throughput.",
            "GPU shader cores: hundreds of parallel execution units process pixels simultaneously.",
        ],
        related_principles=[1, 5],
    ),
    StandardSolution(
        id="5.4.3",
        name="Segment System for Specialization",
        description=(
            "Divide the system so that each segment specializes in one aspect, "
            "achieving higher efficiency than a generalist system."
        ),
        applicability="Generalist system is inefficient for all sub-tasks.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 1)],
        examples=[
            "CPU for sequential logic + GPU for parallel graphics + TPU for neural nets.",
            "Dedicated kitchen zones: prep, cook, bake, clean each optimized.",
        ],
        related_principles=[1, 3],
    ),
    StandardSolution(
        id="5.5.1",
        name="Transition to Pneumatic/Hydraulic Structure",
        description=(
            "Replace solid mechanical structures with gas- or liquid-filled structures "
            "for adaptability, shock absorption, and weight reduction."
        ),
        applicability="Solid structure is heavy, rigid, or transmits too much vibration.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Air suspension replaces steel springs for smoother ride.",
            "Inflatable kayak: collapses for transport, rigid when pressurized.",
        ],
        related_principles=[29, 30],
    ),
    StandardSolution(
        id="5.5.2",
        name="Transition to Flexible Shell or Film",
        description=(
            "Replace bulky 3D structures with thin films, membranes, or shells that "
            "provide the same function with minimal material."
        ),
        applicability="Material usage is excessive; thin barrier would suffice.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Thin-film solar cells replace bulky silicon wafers.",
            "Plastic wrap replaces rigid food containers for short-term storage.",
        ],
        related_principles=[30, 27],
    ),
    StandardSolution(
        id="5.5.3",
        name="Transition to Porous Material",
        description=(
            "Replace dense material with porous foam, lattice, or aerogel to reduce "
            "weight while maintaining structural or thermal properties."
        ),
        applicability="Weight reduction is critical; dense material is over-engineered.",
        c4_trajectory=[(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        examples=[
            "Aerogel insulation: extremely low density, excellent thermal performance.",
            "3D-printed lattice structures replace solid metal in aerospace brackets.",
        ],
        related_principles=[31, 30],
    ),
    StandardSolution(
        id="5.6.1",
        name="Invert the Problem",
        description=(
            "Instead of solving the stated problem directly, solve the inverse: "
            "make the harmful factor work for you, or do the opposite of the usual approach."
        ),
        applicability="Direct solution is complex or blocked by constraints.",
        c4_trajectory=[(1, 0, 0), (0, 0, 0), (0, 1, 1)],
        examples=[
            "Instead of preventing rust, use rust as a protective patina (weathering steel).",
            "Instead of cooling hot data center, use heat to warm offices (district heating).",
        ],
        related_principles=[13, 22],
    ),
    StandardSolution(
        id="5.6.2",
        name="Ideal Final Result (IFR) Simplification",
        description=(
            "Define the Ideal Final Result -- the function is performed without the system. "
            "Work backwards to find the minimal system that approaches this ideal."
        ),
        applicability="System is over-engineered; simpler approaches may exist.",
        c4_trajectory=[(1, 0, 0), (1, 1, 1), (1, 2, 2)],
        examples=[
            "Self-leveling concrete eliminates vibration and leveling tools.",
            "Gravity-fed water system eliminates pumps and energy consumption.",
        ],
        related_principles=[25, 23],
    ),
]
