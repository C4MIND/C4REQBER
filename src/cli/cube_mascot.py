from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

import os
import random
import time

from src.terminal_.cyberpunk_theme import CyberpunkTheme as T


RESET = T.RESET

CUBE_STATES = {
    "idle": "▫▫▫",
    "thinking": "▫◈▫",
    "processing": "◈▣▫",
    "discovery": "◈▣◈",
    "error": "✖▫▫",
    "done": "◈▣◈ ✓",
    "paradigm": "✦◈▣◈✦",
}

CUBE_COMMENTS = {
    "idle": [
        "Z₃³ lattice stable. 27 states ready.",
        "Cognitive exoskeleton deployed.",
        "Neural classifier: ONNX standby.",
    ],
    "thinking": [
        "Tau-plus engaging... temporal shift initiated.",
        "Navigating cognitive space via Theorem 9...",
        "Pattern resonance active.",
    ],
    "processing": [
        "TRIZ contradiction matrix accessed.",
        "Bayesian inference running...",
        "Multi-agent synthesis in progress...",
    ],
    "discovery": [
        "◈ ISOMORPHISM DETECTED ◈ — knowledge graph resonance at 0.847",
        "Novel hypothesis exceeds novelty threshold (0.8)!",
        "Paradigm shift probability: 66.67%",
    ],
    "error": [
        "⚠ CONTRADICTION — Su-Field analysis recommended",
        "Anomaly in cognitive field. Filtering...",
        "State mismatch. Recalibrating via λ⁻...",
    ],
    "done": [
        "Discovery recorded in cognitive history.",
        "Pipeline step completed. Output cached.",
        "Verification: Lean4 proof accepted.",
    ],
    "paradigm": [
        "✦ PARADIGM SHIFT CASCADE INITIATED ✦",
        "C4-META observer invariance triggered!",
        "UCOS Layer 4: Meta-reflection complete.",
    ],
}


class CubeMascot:
    """Cognitive daemon — 8-bit cube visualization with cyberpunk flair."""

    DISCOVERY_KEYWORDS = {
        "discovery",
        "novel",
        "hypothesis",
        "breakthrough",
        "paradigm",
        "isomorphism",
    }
    ERROR_KEYWORDS = {"error", "fail", "anomaly", "exception", "traceback", "contradiction"}
    PARADIGM_KEYWORDS = {"paradigm shift", "revolutionary", "game-changing", "paradigm"}
    BLAST_MODE_KEYWORDS = {
        "solve": {"prd", "blueprint", "architecture", "plan", "strategy", "artifact"},
        "turbo": {"dissertation", "a+", "quality gate", "research proposal", "bibliography"},
        "flash": {"quick answer", "flash mode", "instant", "concise"},
        "turbofactory": {"parallel", "factory", "orchestrator", "synthesis", "100 pipelines"},
    }

    def __init__(self) -> None:
        self.state = "idle"
        self.last_update = time.time()
        self.comment = ""
        self._update_comment()
        self._pulse_phase = 0.0
        self._discovery_burst_frame = 0
        self._subscribe_to_pipeline_events()
        self._load_personality()
        self._check_streak()

    def _load_personality(self) -> None:
        """Load session stats from history."""
        import json

        self.history_path = os.path.expanduser("~/.c4reqber/mascot_memory.json")
        self.today_discoveries = 0
        self.total_discoveries = 0
        self.favorite_domain = ""
        self._domain_counts: dict[str, int] = {}
        try:
            if os.path.exists(self.history_path):
                data = json.loads(open(self.history_path).read())
                self.today_discoveries = data.get("today_discoveries", 0)
                self.total_discoveries = data.get("total_discoveries", 0)
                self.favorite_domain = data.get("favorite_domain", "")
                self._domain_counts = data.get("domain_counts", {})
        except Exception as _exc:
            logger.debug("swallowed exception: %s", _exc, exc_info=True)

    def _check_streak(self) -> None:
        """Check consecutive days streak."""
        import json

        streak_path = os.path.expanduser("~/.c4reqber/streak.json")
        today = time.strftime("%Y-%m-%d")
        try:
            if os.path.exists(streak_path):
                data = json.loads(open(streak_path).read())
                last = data.get("last_date", "")
                self.streak = data.get("streak", 0)
                if last != today:
                    yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
                    self.streak = self.streak + 1 if last == yesterday else 1
            else:
                self.streak = 1
            with open(streak_path, "w") as f:
                json.dump({"last_date": today, "streak": self.streak}, f)
        except Exception:
            self.streak = 1

    def record_discovery(self, domain: str = "") -> None:
        """Record a discovery for personality tracking."""
        self.today_discoveries += 1
        self.total_discoveries += 1
        if domain:
            self._domain_counts[domain] = self._domain_counts.get(domain, 0) + 1
            self.favorite_domain = max(self._domain_counts, key=lambda k: self._domain_counts[k])
        import json

        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            with open(self.history_path, "w") as f:
                json.dump(
                    {
                        "today_discoveries": self.today_discoveries,
                        "total_discoveries": self.total_discoveries,
                        "favorite_domain": self.favorite_domain,
                        "domain_counts": self._domain_counts,
                    },
                    f,
                )
        except Exception as _exc:
            logger.debug("swallowed exception: %s", _exc, exc_info=True)

    def personal_comment(self) -> str:
        """Return a personalized comment based on session history."""
        if self.state == "idle":
            if self.total_discoveries == 0:
                return "Fresh canvas. 27 states awaiting your first question. Type 'help' to begin."
            if self.streak >= 7:
                return f"{self.streak}-day streak. The cube remembers every question you've asked. Today's {self.streak}th session."
            if self.today_discoveries >= 5:
                return f"5 discoveries today. Theorem 11 approves. Cognitive momentum: {min(1.0, self.today_discoveries / 10):.1f}"
            if self.favorite_domain:
                return f"Your favorite domain: {self.favorite_domain}. Ready for another question?"
        return random.choice(CUBE_COMMENTS.get(self.state, ["Ready."]))

    def proactive_suggestion(self, idle_seconds: float) -> str | None:
        """After idle, suggest something useful based on context."""
        if idle_seconds < 60:
            return None
        suggestions = []
        if self.today_discoveries < 3:
            suggestions.append(
                f'Try: blast analyze "{self.favorite_domain or "supply chain optimization"}"'
            )
        suggestions.append("Explore: blast packages install --id pymc")
        suggestions.append('Discover: blast auto "cancer early detection"')
        suggestions.append("Visualize: blast tui --packages    # arrow-key package installer")
        return random.choice(suggestions)

    def _subscribe_to_pipeline_events(self) -> None:
        """Subscribe to pipeline events for real-time mascot reactions."""
        try:
            from src.pipeline.events import PipelineEvent, event_bus

            def on_event(event: PipelineEvent) -> None:
                if event.event_type == "pipeline_start":
                    self.set_state("thinking")
                    self.comment = f"BLAST {event.mode} pipeline starting..."
                elif event.event_type == "phase_start":
                    phase = event.data.get("name", event.data.get("phase", ""))
                    self.set_state("processing")
                    self.comment = f"Phase: {phase}"
                elif event.event_type == "quality_report":
                    score = event.data.get("score", 0)
                    if score >= 95:
                        self.set_state("paradigm")
                        self.comment = f"A+ quality achieved! ({score}/100)"
                    elif score >= 85:
                        self.set_state("discovery")
                        self.comment = f"High quality output ({score}/100)"
                    elif score >= 60:
                        self.set_state("done")
                        self.comment = f"Quality acceptable ({score}/100)"
                    else:
                        self.set_state("error")
                        self.comment = f"Quality below threshold ({score}/100)"
                elif event.event_type == "verification_start":
                    self.set_state("processing")
                    backend = event.data.get("backend", "")
                    self.comment = f"Verifying with {backend.upper()}..."
                elif event.event_type == "verification_progress":
                    status = event.data.get("status", "")
                    elapsed = event.data.get("elapsed_seconds", 0)
                    backend = event.data.get("backend", "")
                    if status == "killed":
                        self.set_state("error")
                        self.comment = f"{backend.upper()} killed after {elapsed:.0f}s"
                    elif status == "soft_timeout_exceeded":
                        self.set_state("thinking")
                        self.comment = f"{backend.upper()} is slow ({elapsed:.0f}s)..."
                    else:
                        self.set_state("processing")
                        self.comment = f"{backend.upper()} verifying ({elapsed:.0f}s)..."
                elif event.event_type == "pipeline_complete":
                    self.set_state("done")
                    self.comment = "Pipeline complete. Output saved."

            event_bus.add_callback(on_event)
        except (ImportError, RuntimeError):
            pass  # Event bus not available

    def set_state(self, state: str) -> None:
        if state in CUBE_STATES:
            self.state = state
            self._update_comment()
            self.last_update = time.time()
            if state == "discovery":
                self._discovery_burst_frame = 6

    def react_to_content(self, text: str) -> None:
        """React to content."""
        text_lower = text.lower()
        if any(word in text_lower for word in self.PARADIGM_KEYWORDS):
            self.set_state("paradigm")
        elif any(word in text_lower for word in self.DISCOVERY_KEYWORDS):
            self.set_state("discovery")
        elif any(word in text_lower for word in self.ERROR_KEYWORDS):
            self.set_state("error")

    def react_to_blast_mode(self, mode: str, quality_score: int = 0) -> None:
        """React to BLAST pipeline mode and quality."""
        mode_comments = {
            "solve": [
                "BLAST solve: Strategic artifact generation engaged.",
                "IMPACT entities mapped. C4 navigation active.",
                "Plugin auto-selection running...",
            ],
            "turbo": [
                "BLAST turbo: Paradigm-shifting dissertation pipeline.",
                "27 sources, 9 functors, 6 verifiers activated.",
                f"Quality target: A+ (score ≥ 95). Current: {quality_score}.",
            ],
            "flash": [
                "BLAST flash: Quick cognitive response.",
                "USP components engaged in deep mode.",
                "Instant answer with source citations.",
            ],
            "turbofactory": [
                "BLAST turbofactory: Parallel paradigm factory.",
                "Orchestrating 10-100 concurrent pipelines...",
                "Synthesis layer standing by.",
            ],
        }
        if mode in mode_comments:
            self.state = "processing"
            self.comment = random.choice(mode_comments[mode])
            self.last_update = time.time()

    def _update_comment(self) -> None:
        comments = CUBE_COMMENTS.get(self.state, CUBE_COMMENTS["idle"])
        self.comment = random.choice(comments)

    def _pulse_color(self) -> str:
        import math

        self._pulse_phase = (self._pulse_phase + 0.05) % (2 * math.pi)
        brightness = 0.5 + 0.5 * math.sin(self._pulse_phase)
        if brightness > 0.8:
            return T.FG_PRIMARY
        elif brightness > 0.5:
            return T.FG_SECONDARY
        else:
            return T.FG_GHOST

    def render(self, width: int = 40) -> str:
        """Render."""
        cube = CUBE_STATES.get(self.state, CUBE_STATES["idle"])
        comment = self.comment
        if len(comment) > width - 12:
            comment = comment[: width - 15] + "..."

        if self.state == "idle":
            color = self._pulse_color()
            return f"{color}{cube}{RESET} {T.FG_GHOST}{comment}{RESET}"
        elif self.state == "thinking":
            return f"{T.FG_SECONDARY}{T.BLINK}{cube}{RESET} {T.FG_SECONDARY}{comment}{RESET}"
        elif self.state == "processing":
            return f"{T.FG_WARNING}{cube}{RESET} {T.FG_WARNING}{comment}{RESET}"
        elif self.state == "discovery":
            if self._discovery_burst_frame > 0:
                burst = "✦ " * (7 - self._discovery_burst_frame)
                self._discovery_burst_frame -= 1
                return f"{burst}{T.FG_ACCENT}{T.BOLD}{cube}{RESET} {T.FG_ACCENT}{comment}{RESET} {burst}"
            return f"{T.FG_ACCENT}{T.BOLD}{cube}{RESET} {T.FG_ACCENT}{comment}{RESET}"
        elif self.state == "paradigm":
            return (
                f"{T.FG_ACCENT}{T.BOLD}{T.BLINK}{cube}{RESET} {T.FG_ACCENT}{T.BOLD}{comment}{RESET}"
            )
        elif self.state == "error":
            return f"{T.FG_DANGER}{T.BOLD}{cube}{RESET} {T.FG_DANGER}{comment}{RESET}"
        elif self.state == "done":
            return f"{T.FG_PRIMARY}{cube}{RESET} {T.FG_PRIMARY}{comment}{RESET}"
        else:
            return f"{T.DIM}{cube}{RESET} {T.FG_MUTED}{comment}{RESET}"

    def tick(self) -> str:
        """Tick."""
        now = time.time()
        if now - self.last_update > 3.0:
            self._update_comment()
            self.last_update = now
        return self.render()


_MASCOT = CubeMascot()


def inject_mascot_status(
    mode: str = "solve",
    state: str = "done",
    sources: int = 0,
    papers: int = 0,
    confidence: float = 0.0,
    domain: str = "",
) -> str:
    """Inject mascot status line into CLI output. Returns ANSI-styled string.

    Usage at end of any CLI command output:
        console.print(inject_mascot_status(mode=\"solve\", sources=310, papers=12, confidence=0.83))
    """
    _MASCOT.set_state(state)
    if state == "done":
        _MASCOT.comment = f"{mode} complete. {papers or sources} sources."
    elif state == "thinking":
        _MASCOT.comment = f"Running {mode} pipeline..."
    elif state == "error":
        _MASCOT.comment = f"{mode} encountered an error."

    _MASCOT.last_update = time.time()
    return _MASCOT.render()
