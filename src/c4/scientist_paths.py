# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations


"""
All 18 cognitive routes through Z₃³ mapped to scientist-level discovery patterns.

Each path is a sequence of C4 states with engines assigned.
Documented for explainability: the system explains WHY it chose a specific path.
"""
ALL_SCIENTIST_PATHS = {
    # ═══════════════════════════════════════════════════════════════════════
    # CONTRADICTION PATTERNS (start: observe conflict → resolve via abstraction)
    # ═══════════════════════════════════════════════════════════════════════
    "einstein": {
        "scientist": "Albert Einstein",
        "era": "1905",
        "discovery": "Special Relativity — resolved Maxwell vs Newton contradiction",
        "method": "Contradiction detection → abstraction ladder → constraint solver → counterfactual derivation → validation",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Detect Michelson-Morley null result vs expected aether drift"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Speed of light is absolute invariant — generalize to principle"),
            ("ABSTRACT", "PRESENT", "SYSTEM", "ConstraintSolver", "Lorentz SO(3,1) — find transformations preserving c"),
            ("ABSTRACT", "FUTURE", "SYSTEM", "CounterfactualEngine", "If c=const → derive time dilation, length contraction, E=mc²"),
            ("ABSTRACT", "PRESENT", "SYSTEM", "MultiStepChain", "Refine against known data: Mercury perihelion, starlight deflection"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Does theory pass all tests? Self-validate"),
        ],
    },
    "planck": {
        "scientist": "Max Planck",
        "era": "1900",
        "discovery": "Quantum hypothesis — resolved blackbody ultraviolet catastrophe",
        "method": "Unexplained data → radical hypothesis → meta principle",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Blackbody spectrum: classical predicts infinite UV (catastrophe)"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Energy must be quantized — E=hν as abstract hypothesis"),
            ("META", "PRESENT", "SELF", "ConstraintSolver", "Quantization as universal principle — dimensional analysis"),
            ("ABSTRACT", "FUTURE", "SELF", "CounterfactualEngine", "If energy is quantized → discrete atomic transitions, photoelectric effect"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Does quantization resolve catastrophe? Yes → Nobel 1918"),
        ],
    },
    "bohr": {
        "scientist": "Niels Bohr",
        "era": "1913",
        "discovery": "Atomic model — resolved Rutherford atom instability via quantization",
        "method": "Empirical data → model → test against data → refine → meta-principle",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Rutherford atom: electrons should spiral into nucleus"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Quantized orbits as abstract model — borrowing from Planck"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "Predict Balmer series spectral lines"),
            ("ABSTRACT", "PRESENT", "SELF", "MultiStepChain", "Refine model: correspondence principle, selection rules"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Model explains hydrogen spectrum — but fails for helium (boundary found)"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # OBSERVATION PATTERNS (start: observe → generalize → validate)
    # ═══════════════════════════════════════════════════════════════════════
    "darwin": {
        "scientist": "Charles Darwin",
        "era": "1859",
        "discovery": "Natural Selection — observed pattern across species → generalized to principle",
        "method": "Observation → pattern across instances → abstract principle → test against data → validate",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Anomaly: finches on different islands have different beaks"),
            ("CONCRETE", "PRESENT", "OTHER", "AbstractionLadder", "Pattern: beak variation correlates with food source across islands"),
            ("ABSTRACT", "PRESENT", "OTHER", "AbstractionLadder", "Generalize: natural selection as universal mechanism"),
            ("ABSTRACT", "FUTURE", "SYSTEM", "CounterfactualEngine", "Predict: fossil record patterns, vestigial organs, common descent"),
            ("ABSTRACT", "PRESENT", "SELF", "MultiStepChain", "Refine: integrate with Mendel's genetics (modern synthesis)"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "150 years of validation across biology, genetics, paleontology"),
        ],
    },
    "mendeleev": {
        "scientist": "Dmitri Mendeleev",
        "era": "1869",
        "discovery": "Periodic Table — classification → prediction → validation",
        "method": "Classification pattern → abstract structure → predict → confirm",
        "path": [
            ("CONCRETE", "PRESENT", "OTHER", "ContradictionEngine", "Known elements: no systematic organization"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Pattern: properties recur periodically by atomic weight"),
            ("ABSTRACT", "PRESENT", "SYSTEM", "ConstraintSolver", "Periodic law: structural constraint on element properties"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "Predict: Ga, Sc, Ge — unknown elements with specific properties"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Ga discovered 1875 — matches predicted properties exactly"),
        ],
    },
    "crick_watson": {
        "scientist": "Francis Crick & James Watson",
        "era": "1953",
        "discovery": "DNA double helix — model building from crystallographic data",
        "method": "Data constraint → model building → prediction → validation",
        "path": [
            ("CONCRETE", "PRESENT", "OTHER", "ContradictionEngine", "Chargaff's rules: A=T, G=C — unexplained pattern"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Double helix model with complementary base pairing"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "If double helix → semi-conservative replication predicts specific banding"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Meselson-Stahl 1958: semi-conservative replication confirmed"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FIRST-PRINCIPLES INVENTION PATTERNS (start: abstract → concrete)
    # ═══════════════════════════════════════════════════════════════════════
    "tesla": {
        "scientist": "Nikola Tesla",
        "era": "1888",
        "discovery": "AC induction motor — first principles engineering invention",
        "method": "First principles → design space → constraints → prototype → validate",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "First principles: rotating magnetic field from polyphase AC"),
            ("ABSTRACT", "FUTURE", "SELF", "CounterfactualEngine", "If field rotates → induction motor possible without commutator"),
            ("ABSTRACT", "FUTURE", "SYSTEM", "ConstraintSolver", "Physical constraints: torque, frequency, voltage relationships"),
            ("CONCRETE", "PRESENT", "SELF", "MultiStepChain", "Prototype → test → refine: Westinghouse deal 1888"),
        ],
    },
    "shannon": {
        "scientist": "Claude Shannon",
        "era": "1948",
        "discovery": "Information Theory — concrete signal problem → meta-mathematical framework",
        "method": "Concrete → abstract → meta → constraint → chain",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Signal vs noise tension in communication channels"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Information = reduction in uncertainty — abstract definition"),
            ("META", "PRESENT", "SELF", "ConstraintSolver", "Channel capacity = B log₂(1+S/N) — mathematical upper bound"),
            ("META", "FUTURE", "SYSTEM", "CounterfactualEngine", "Source coding theorem: data can be compressed to entropy limit"),
            ("META", "PRESENT", "SELF", "MultiStepChain", "Refine: error-correcting codes, noisy channel theorem"),
        ],
    },
    "von_neumann": {
        "scientist": "John von Neumann",
        "era": "1945",
        "discovery": "Stored-program computer architecture — mathematical abstraction → concrete machine",
        "method": "Abstract → meta → system → concrete implementation",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Turing's universal machine as abstract concept"),
            ("META", "PRESENT", "SELF", "ConstraintSolver", "Architecture constraints: memory hierarchy, instruction format"),
            ("META", "PRESENT", "SYSTEM", "AbstractionLadder", "EDVAC report: stored program, ALU, control unit, memory, I/O"),
            ("CONCRETE", "FUTURE", "SYSTEM", "CounterfactualEngine", "If von Neumann architecture → programmable general-purpose computers"),
        ],
    },
    "nash": {
        "scientist": "John Nash",
        "era": "1950",
        "discovery": "Nash Equilibrium — abstraction for multi-agent systems",
        "method": "Abstract → multi-agent → system-level → meta-principle",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Zero-sum equilibrium (von Neumann) — generalize to N-person"),
            ("ABSTRACT", "PRESENT", "OTHER", "ContradictionEngine", "Multi-agent tension: each player optimizes independently"),
            ("ABSTRACT", "PRESENT", "SYSTEM", "ConstraintSolver", "Fixed-point theorem: every finite game has equilibrium"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Nobel 1994 — equilibrium concept across economics, biology, CS"),
        ],
    },
    "turing": {
        "scientist": "Alan Turing",
        "era": "1936",
        "discovery": "Universal computation — meta-mathematical → concrete machine",
        "method": "Meta → abstract → concrete machine design",
        "path": [
            ("META", "PRESENT", "SELF", "ContradictionEngine", "Entscheidungsproblem: can all mathematical questions be decided?"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Turing machine: abstract model of computation"),
            ("CONCRETE", "FUTURE", "SYSTEM", "CounterfactualEngine", "If universal machine → ACE computer, Turing test, AI foundations"),
        ],
    },
    "godel": {
        "scientist": "Kurt Gödel",
        "era": "1931",
        "discovery": "Incompleteness Theorems — meta-system self-reference",
        "method": "Meta → self-reference → system → concrete consequence",
        "path": [
            ("META", "PRESENT", "SELF", "ContradictionEngine", "Hilbert's program: prove all mathematics consistent — can it work?"),
            ("META", "PRESENT", "SYSTEM", "AbstractionLadder", "Gödel numbering: encode meta-statements IN the system"),
            ("CONCRETE", "PRESENT", "SYSTEM", "ConstraintSolver", "Self-referential sentence: 'I am unprovable' → incompleteness"),
            ("META", "FUTURE", "SELF", "CounterfactualEngine", "If incomplete → Turing's halting problem, limits of AI, philosophy"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # EXPERIMENTAL SERENDIPITY PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    "curie": {
        "scientist": "Marie Curie",
        "era": "1898",
        "discovery": "Radium & Polonium — experimental anomaly → new elements",
        "method": "Anomalous measurement → compare → hypothesize → validate",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Anomaly: pitchblende more radioactive than pure uranium"),
            ("CONCRETE", "PRESENT", "OTHER", "AbstractionLadder", "Compare: uranium compounds vs pitchblende — systematic difference"),
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Hypothesis: unknown radioactive elements in pitchblende"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "Predict: chemical separation → isolate new element → measure properties"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Polonium (Jul 1898) + Radium (Dec 1898) confirmed. Nobel ×2"),
        ],
    },
    "pasteur": {
        "scientist": "Louis Pasteur",
        "era": "1857",
        "discovery": "Germ theory — experimental serendipity → paradigm shift",
        "method": "Observation → controlled experiment → generalize → apply",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Observation: fermentation produces living organisms"),
            ("CONCRETE", "PRESENT", "OTHER", "AbstractionLadder", "Control: sterile broth = no growth. Open broth = growth"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "Predict: if germs cause disease → pasteurization, vaccination"),
            ("ABSTRACT", "PRESENT", "SELF", "MultiStepChain", "Refine: specific germs → specific diseases (Koch's postulates)"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Germ theory → modern medicine, antibiotics, sterile surgery"),
        ],
    },
    "feynman": {
        "scientist": "Richard Feynman",
        "era": "1948",
        "discovery": "QED — diagrammatic thinking bridging abstract and concrete",
        "method": "Abstract formalism → visual representation → system-level → prediction",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "ContradictionEngine", "QED: infinite self-energy — renormalization required"),
            ("ABSTRACT", "PRESENT", "OTHER", "AbstractionLadder", "Feynman diagrams: visual calculus for particle interactions"),
            ("CONCRETE", "PRESENT", "SYSTEM", "ConstraintSolver", "Path integral formulation: sum over histories"),
            ("ABSTRACT", "FUTURE", "SELF", "CounterfactualEngine", "Predict: Lamb shift, anomalous magnetic moment → 12-digit match"),
        ],
    },
    "fermi": {
        "scientist": "Enrico Fermi",
        "era": "1942",
        "discovery": "Nuclear chain reaction — back-of-envelope estimation → prototype",
        "method": "Abstract estimate → concrete design → prediction → build",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Estimate: critical mass ≈ 6 kg U-235 (Fermi problem)"),
            ("CONCRETE", "PRESENT", "SELF", "ConstraintSolver", "Chicago Pile-1 design constraints: geometry, moderator, control"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "Predict: k_eff > 1 → chain reaction → 0.5 watt → 200 watts"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Dec 2, 1942: first controlled nuclear chain reaction. Confirmed."),
        ],
    },
    "ramanujan": {
        "scientist": "Srinivasa Ramanujan",
        "era": "1910s",
        "discovery": "Mathematical intuition — meta-insight → formal proof",
        "method": "Meta-intuition → abstract formalism → concrete verification",
        "path": [
            ("META", "PRESENT", "SELF", "AbstractionLadder", "Intuitive insight: theta functions, modular forms — from dreams"),
            ("ABSTRACT", "PRESENT", "SELF", "ConstraintSolver", "Formalize: infinite series, continued fractions, pi formulas"),
            ("CONCRETE", "PRESENT", "SYSTEM", "CounterfactualEngine", "Verify: mock theta functions, partition congruences — all correct"),
            ("META", "FUTURE", "SELF", "RecursiveValidation", "Black hole entropy, string theory — Ramanujan's work prefigured physics"),
        ],
    },
    "lovelace": {
        "scientist": "Ada Lovelace",
        "era": "1843",
        "discovery": "First computer algorithm — abstract analytical engine → universal computation",
        "method": "Abstract formalism → future system design → concrete algorithm",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Babbage's Analytical Engine as abstract computing concept"),
            ("ABSTRACT", "FUTURE", "SYSTEM", "CounterfactualEngine", "If engine can manipulate symbols → it can compose music, compute Bernoulli numbers"),
            ("CONCRETE", "FUTURE", "SELF", "ConstraintSolver", "Algorithm G: first published computer program for Bernoulli numbers"),
            ("META", "FUTURE", "SYSTEM", "RecursiveValidation", "Universal computation prefigured: 'the Engine might act upon other things besides number' — AI prediction in 1843"),
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # MODERN NOBEL PATTERNS (2000s–2020s)
    # ═══════════════════════════════════════════════════════════════════════
    "kariko": {
        "scientist": "Katalin Karikó",
        "era": "2005–2023",
        "discovery": "mRNA vaccine technology — decades of rejection → pseudouridine breakthrough → COVID vaccines",
        "method": "Concrete contradiction → abstract principle (base modification) → concrete validation (protein production) → system impact (billion-dose vaccines)",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "mRNA injection causes lethal inflammation in mice — immunogenicity blocks therapeutic use"),
            ("CONCRETE", "PRESENT", "OTHER", "AbstractionLadder", "Transfer RNA does NOT trigger immune response — insight: nucleoside modifications matter"),
            ("ABSTRACT", "PRESENT", "SELF", "ConstraintSolver", "Pseudouridine (ψ) replaces uridine: eliminates TLR3/7/8 activation while preserving translation"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "If modified mRNA avoids immune response → safe protein expression → vaccines possible"),
            ("CONCRETE", "PRESENT", "SYSTEM", "MultiStepChain", "2005→2008→2010→2013→2020: BioNTech/Moderna, 1-methyl-ψ, lipid nanoparticles, COVID vaccines"),
            ("META", "FUTURE", "SYSTEM", "RecursiveValidation", "Nobel 2023. mRNA platform for cancer, HIV, influenza, personalized medicine. Perseverance paradigm."),
        ],
    },
    "doudna_charpentier": {
        "scientist": "Jennifer Doudna & Emmanuelle Charpentier",
        "era": "2012–2020",
        "discovery": "CRISPR-Cas9 gene editing — bacterial immune serendipity → universal genome editor",
        "method": "Concrete serendipity → abstract mechanism → concrete repurposing → system revolution",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "Bacteria defend against viruses via CRISPR repeats — unknown mechanism"),
            ("CONCRETE", "PRESENT", "OTHER", "AbstractionLadder", "tracrRNA guides Cas9 to viral DNA — mechanism understood"),
            ("ABSTRACT", "PRESENT", "SELF", "ConstraintSolver", "Simplified two-component system: guide RNA + Cas9 protein = programmable DNA cutter"),
            ("ABSTRACT", "FUTURE", "SYSTEM", "CounterfactualEngine", "If CRISPR works in human cells → any gene can be edited, crops improved, diseases cured"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Nobel 2020. First all-female science Nobel team. Patent battle won. Sickle cell cure 2023."),
        ],
    },
    "baker": {
        "scientist": "David Baker",
        "era": "2003–2024",
        "discovery": "De novo protein design — reverse engineering folding → creating proteins that don't exist in nature",
        "method": "Abstract biophysics → concrete software (Rosetta) → reverse design → AI integration → Nobel 2024",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "AbstractionLadder", "Protein folding principles: hydrophobic core, hydrogen bonds, energy landscape"),
            ("ABSTRACT", "PRESENT", "SYSTEM", "ConstraintSolver", "Rosetta software: given backbone → predicts optimal amino acid sequence"),
            ("CONCRETE", "FUTURE", "SELF", "CounterfactualEngine", "If we design a protein that nature never made → Top7: 93-residue novel fold (2003)"),
            ("CONCRETE", "PRESENT", "SYSTEM", "MultiStepChain", "2003→2019→2024: RFdiffusion, ProteinMPNN, open-source Rosetta, Nobel 2024"),
            ("META", "FUTURE", "SYSTEM", "RecursiveValidation", "200M proteins predicted. Designer enzymes, vaccines, nanomaterials. Open science."),
        ],
    },
    "hassabis_jumper": {
        "scientist": "Demis Hassabis & John Jumper",
        "era": "2018–2024",
        "discovery": "AlphaFold — AI solves 50-year protein folding problem, predicts all 200M known proteins",
        "method": "META grand challenge → ABSTRACT transformer architecture → CONCRETE predictions → META open database",
        "path": [
            ("META", "PRESENT", "SELF", "ContradictionEngine", "50-year grand challenge: can we predict 3D structure from amino acid sequence?"),
            ("ABSTRACT", "PRESENT", "SELF", "ConstraintSolver", "Evoformer: MSA + pairwise representation + equivariant attention architecture"),
            ("ABSTRACT", "PRESENT", "SYSTEM", "AbstractionLadder", "Three-cycle refinement: sequence → distance map → structure → recycle"),
            ("CONCRETE", "FUTURE", "SYSTEM", "CounterfactualEngine", "If AlphaFold works → 200M protein structures, antibiotic resistance, plastic-degrading enzymes"),
            ("META", "FUTURE", "SYSTEM", "RecursiveValidation", "Nobel 2024. 2M+ researchers in 190 countries. RosettaFold. Open database."),
        ],
    },
    "hinton": {
        "scientist": "Geoffrey Hinton",
        "era": "1986–2024",
        "discovery": "Deep learning — 40-year persistence through AI winter → ImageNet breakthrough → Nobel 2024",
        "method": "Abstract theory → decades of rejection → concrete proof → paradigm shift → Nobel Physics",
        "path": [
            ("ABSTRACT", "PRESENT", "SELF", "ContradictionEngine", "Neural networks dismissed by AI community — 'connectionist nonsense' (Minsky, 1969)"),
            ("ABSTRACT", "PAST", "OTHER", "AbstractionLadder", "Backpropagation (1986), Boltzmann machines (1985), dropout, ReLU, layer-wise pretraining — persisting through AI winter"),
            ("CONCRETE", "PRESENT", "SELF", "ConstraintSolver", "AlexNet (2012): GPU + ImageNet + ReLU + dropout = 15.3% error → 84% accuracy. Paradigm shattered."),
            ("ABSTRACT", "FUTURE", "SYSTEM", "CounterfactualEngine", "If deep learning works → GPT, AlphaFold, self-driving cars, medical diagnosis — everything changes"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Nobel Physics 2024. 40 years from outcast to revolution. Boltzmann machine cited."),
        ],
    },
    "moser": {
        "scientist": "May-Britt & Edvard Moser",
        "era": "2005–2014",
        "discovery": "Grid cells — hexagonal coordinate system for spatial navigation in entorhinal cortex",
        "method": "Concrete observation → pattern recognition → abstract model → Nobel 2014",
        "path": [
            ("CONCRETE", "PRESENT", "SELF", "ContradictionEngine", "O'Keefe's place cells fire in single locations — but how is the map organized?"),
            ("CONCRETE", "PRESENT", "OTHER", "AbstractionLadder", "Larger recording arena reveals hexagonal firing pattern — grid cells discovered (no one had seen before)"),
            ("ABSTRACT", "PRESENT", "SELF", "ConstraintSolver", "Grid cells organized in modules with different spacing — functional coordinate system"),
            ("ABSTRACT", "FUTURE", "SYSTEM", "CounterfactualEngine", "If grid cells provide metric → path integration → Alzheimer's early diagnosis → neural computation principles"),
            ("META", "PRESENT", "SELF", "RecursiveValidation", "Nobel 2014. Grid cells found in humans, bats, monkeys. Paradigm shift in spatial cognition."),
        ],
    },
}

# Backward mapping: problem keyword → scientist path
PROBLEM_TO_SCIENTIST = {
    "contradiction": "einstein", "anomaly": "einstein", "paradox": "einstein",
    "inconsistency": "einstein", "catastrophe": "planck",
    "contradict": "einstein", "conflict": "einstein", "tension": "einstein",
    "instability": "bohr", "model": "bohr",
    "observation": "darwin", "pattern": "darwin", "variation": "darwin",
    "classification": "mendeleev", "periodic": "mendeleev",
    "crystal": "crick_watson", "structure": "crick_watson", "helix": "crick_watson",
    "invent": "tesla", "design": "tesla", "engineer": "tesla", "create": "tesla",
    "information": "shannon", "entropy": "shannon", "signal": "shannon",
    "architecture": "von_neumann", "computer": "von_neumann",
    "game": "nash", "equilibrium": "nash", "strategy": "nash",
    "decidable": "turing", "compute": "turing", "halting": "turing",
    "proof": "godel", "incompleteness": "godel", "self": "godel",
    "experiment": "curie", "measurement": "curie", "detection": "curie",
    "serendipity": "pasteur", "accidental": "pasteur",
    "diagram": "feynman", "particle": "feynman", "interaction": "feynman",
    "estimate": "fermi", "approximation": "fermi",
    "intuition": "ramanujan", "insight": "ramanujan", "dream": "ramanujan",
    "algorithm": "lovelace", "symbolic": "lovelace", "program": "lovelace", "engine": "lovelace",
    # Modern Nobel
    "mrna": "kariko", "vaccine": "kariko", "pseudouridine": "kariko", "nucleoside": "kariko",
    "immune": "doudna_charpentier", "crispr": "doudna_charpentier", "gene edit": "doudna_charpentier",
    "genome": "doudna_charpentier", "cas9": "doudna_charpentier", "dna cut": "doudna_charpentier",
    "protein design": "baker", "de novo": "baker", "rosetta": "baker", "top7": "baker",
    "protein fold": "hassabis_jumper", "alphafold": "hassabis_jumper", "casp": "hassabis_jumper",
    "deep learning": "hinton", "neural net": "hinton", "backprop": "hinton", "imagenet": "hinton",
    "grid cell": "moser", "spatial nav": "moser", "entorhinal": "moser", "hippocampus": "moser", "place cell": "moser",
}

__all__ = ["ALL_SCIENTIST_PATHS", "PROBLEM_TO_SCIENTIST"]
