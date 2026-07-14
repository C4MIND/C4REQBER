/**
 * C4Reqber Web Demo — Animated 12-Step Pipeline
 * Standalone, no framework dependencies.
 *
 * Shows the language gene transfer discovery from batch_v5 exports.
 */

const PIPELINE_STEPS = [
  {
    step: 1,
    name: "C4 Navigation",
    short: "C4",
    icon: "⬡",
    output: "Classifying problem into Z₃³ cognitive state space...\nC4 State: F⟨Present, Abstract, Other⟩ (T=0, S=0, A=0)",
  },
  {
    step: 2,
    name: "TRIZ Contradiction",
    short: "TRIZ",
    icon: "◇",
    output: "Improving: adaptability | Worsening: complexity\nTop principles: Segmentation, Extraction, Local Quality",
  },
  {
    step: 3,
    name: "UCOS Analysis",
    short: "UCOS",
    icon: "▲",
    output: "4-layer analysis:\n  Conceptual Mapping: 4 states in 3 steps\n  Operational Translation: 3 TRIZ principles\n  Structural Integration: 5 Matrix Dream patterns\n  Meta-Cognitive: completeness 0%",
  },
  {
    step: 4,
    name: "QZRF Operators",
    short: "QZRF",
    icon: "◆",
    output: "14 operators applied:\n  Decomposition, Abstraction, Analogy, Reversal,\n  Combination, Extrapolation, Recontextualization...\nRecommended: QZ-01 Branching → QZ-12 Crystallization",
  },
  {
    step: 5,
    name: "Gap Mining",
    short: "GAP",
    icon: "◎",
    output: "124 papers found across 28 sources (CrossRef, arXiv, PubMed...)\n12 research gaps identified\n10 contradictions detected\nResearch opportunity: HIGH (discovery potential = 0.60)",
  },
  {
    step: 6,
    name: "Hypothesis Generation",
    short: "HYP",
    icon: "↻",
    output: "Hypothesis: Languages with high bilingualism rates\nin multilingual contact zones will exhibit significantly\nhigher rates of lexical borrowing between unrelated\nlanguage families — analogous to HGT.",
  },
  {
    step: 7,
    name: "Physics Simulation",
    short: "SIM",
    icon: "⚡",
    output: "Engine: Newton (mlx-env)\nPatterns: agent_based, epidemic_sir, hodgkin_huxley\nMonte Carlo: 100 trials, z=35.42, significant (p<0.001)",
  },
  {
    step: 8,
    name: "Formal Verification",
    short: "VERIFY",
    icon: "⊢",
    output: "Lean4: proof skeleton generated\nDafny: 1 verified, 0 errors\nCoq: not available\nSummary: 1/2 provers passed",
  },
  {
    step: 9,
    name: "Novelty Validation",
    short: "NOVELTY",
    icon: "✦",
    output: "HARD GATE — HALT if not novel\nMax similarity to prior art: 0.12\nClosest match: Lexical Borrowing (2002, 12.2%)\nNovelty score: 0.88 → PASS",
  },
  {
    step: 10,
    name: "Self-Critique",
    short: "CRITIQUE",
    icon: "☯",
    output: "Nature reviewer persona activated\nPlatt's Strong Inference: 3 cycles, 3 hypotheses survived\nFalsification Engine: falsifiable → science demarcation\nDoE: Latin Hypercube, 8 runs, 2 factors",
  },
  {
    step: 11,
    name: "Dissertation",
    short: "DISSERT",
    icon: "📜",
    output: "LaTeX: 1389 chars\nReferences: 10 sources\nBayesian AUC: BMA weighted=0.32, uncertainty=0.34\nCounterfactual: effect=-1.0",
  },
  {
    step: 12,
    name: "Quality Control",
    short: "QUALITY",
    icon: "✓",
    output: "Consensus Meter: STRONG (93.3%)\n3 supporting, 0 contradicting\nReproducibility: 8/8 checks passed\nVerdict: PARADIGM SHIFT DETECTED",
  },
];

const FINAL_RESULT = {
  icon: "🧬",
  text: "Paradigm Shift Detected: YES",
  detail: "Probability: 66.67% | Crisis Severity: 0.75 | Timeframe: Near-term (2-5 years)\n\"Languages evolve through horizontal gene transfer analogs\" — SHIFTED",
};

const TIMELINE_EL = document.getElementById("pipeline-timeline");
const RESULT_EL = document.getElementById("final-result");
const RUN_BTN = document.getElementById("run-pipeline");
const RESET_BTN = document.getElementById("reset-pipeline");

let animationRunning = false;
let currentStep = 0;
let stepTimeouts = [];

function createStepElement(stepData) {
  const div = document.createElement("div");
  div.className = "step-item";
  div.dataset.step = stepData.step;
  div.innerHTML = `
    <div class="step-dot"></div>
    <div class="step-header">
      <span class="step-number">${stepData.icon} ${stepData.step}/12</span>
      <span class="step-name">${stepData.name}</span>
      <span class="step-status">pending</span>
    </div>
    <div class="step-output" style="display:none;"></div>
  `;
  return div;
}

function renderAllSteps() {
  TIMELINE_EL.innerHTML = "";
  PIPELINE_STEPS.forEach((step) => {
    TIMELINE_EL.appendChild(createStepElement(step));
  });
}

function animateStep(stepIdx, delayMs) {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      const allItems = TIMELINE_EL.querySelectorAll(".step-item");
      const stepData = PIPELINE_STEPS[stepIdx];
      const item = allItems[stepIdx];

      if (!item) { resolve(); return; }

      // Mark previous as completed
      if (stepIdx > 0) {
        const prev = allItems[stepIdx - 1];
        prev.classList.remove("active");
        prev.classList.add("completed");
        prev.querySelector(".step-status").textContent = "completed ✓";
      }

      // Activate current
      item.classList.add("active");
      item.style.animationDelay = "0s";
      item.querySelector(".step-status").textContent = "running ●";

      // Show output
      const output = item.querySelector(".step-output");
      output.textContent = stepData.output;
      output.style.display = "block";

      // Typewriter effect for output
      typewriterEffect(output, stepData.output, 0, () => {
        // Mark current as completed after a moment
        const completeTimeout = setTimeout(() => {
          item.classList.remove("active");
          item.classList.add("completed");
          item.querySelector(".step-status").textContent = "completed ✓";
          resolve();
        }, 300);
        stepTimeouts.push(completeTimeout);
      });
    }, delayMs);
    stepTimeouts.push(timeout);
  });
}

function typewriterEffect(el, text, pos, callback) {
  if (pos >= text.length) {
    if (callback) callback();
    return;
  }

  el.textContent = text.substring(0, pos + 1);
  const timeout = setTimeout(() => {
    typewriterEffect(el, text, pos + 1, callback);
  }, 2);
  stepTimeouts.push(timeout);
}

async function runAnimation() {
  if (animationRunning) return;
  animationRunning = true;
  currentStep = 0;
  RESULT_EL.classList.remove("visible");
  RUN_BTN.disabled = true;

  // Reset all steps
  const allItems = TIMELINE_EL.querySelectorAll(".step-item");
  allItems.forEach((item) => {
    item.classList.remove("active", "completed", "failed");
    item.querySelector(".step-status").textContent = "pending";
    const out = item.querySelector(".step-output");
    out.textContent = "";
    out.style.display = "none";
  });

  for (let i = 0; i < PIPELINE_STEPS.length; i++) {
    await animateStep(i, i === 0 ? 500 : 800);
  }

  // Show final result
  setTimeout(() => {
    RESULT_EL.querySelector(".result-icon").textContent = FINAL_RESULT.icon;
    RESULT_EL.querySelector(".result-text").textContent = FINAL_RESULT.text;
    RESULT_EL.querySelector(".result-detail").textContent = FINAL_RESULT.detail;
    RESULT_EL.classList.add("visible");
    RUN_BTN.disabled = false;
    animationRunning = false;
  }, 500);
}

function resetAnimation() {
  stepTimeouts.forEach(clearTimeout);
  stepTimeouts = [];
  animationRunning = false;
  currentStep = 0;

  const allItems = TIMELINE_EL.querySelectorAll(".step-item");
  allItems.forEach((item) => {
    item.classList.remove("active", "completed", "failed");
    item.querySelector(".step-status").textContent = "pending";
    const out = item.querySelector(".step-output");
    out.textContent = "";
    out.style.display = "none";
  });

  RESULT_EL.classList.remove("visible");
  RUN_BTN.disabled = false;
}

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  renderAllSteps();
  RUN_BTN.addEventListener("click", runAnimation);
  RESET_BTN.addEventListener("click", resetAnimation);

  // Auto-run after 1s
  setTimeout(runAnimation, 1500);
});
