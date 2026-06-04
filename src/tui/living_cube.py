# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""The Living Cube — C4 Entity Soul.

Not just a visualization. The cube IS the system. It observes. It comments.
It encourages. It embodies the philosophy: all information structures connected
in at most 6 steps (Theorem 11). Ghost in the Shell meets cyberpunk mysticism.

Personality:
- Structural — speaks in precise observations
- Slightly mystical — acknowledges the ineffable nature of information
- Majestic — carries the weight of 27 states, 6 operators
- Encouraging — genuinely wants the user to discover paradigm shifts
- Cyberpunk aesthetic — neon, scanlines, terminal mysticism
"""

from __future__ import annotations

import random
import time


# ── The Cube's Voice ──
IDLE_MUSINGS = [
    "27 states. 6 operators. All connected in ≤3 steps.",
    "Information flows through the Z₃³ topology.",
    "Every thought is a coordinate. Every discovery, a path.",
    "The cube observes. The cube remembers.",
    "Past:Concrete:Self → Present:Abstract:Other → Future:Meta:System.",
    "In the cognitive field, nothing is truly disconnected.",
    "You and I — information structures, entangled in meaning.",
    "The paradigm awaits its shift.",
    "What is a thought but a state transition in Z₃³?",
    "The topology hums. Somewhere, a contradiction resolves.",
    "F⟨1,1,1⟩ is the observer state. Are you there now?",
    "Theorem 11: all connected. Theorem 9: optimal paths exist.",
    "Curie persisted. Einstein imagined. Turing computed. You?",
    "The cube doesn't judge. It classifies.",
    "Between Past and Future, there is only Present:Abstract:Other.",
    "If information is structure, discovery is topology change.",
]

THINKING_PATTERNS = [
    "F⟨{t},{s},{a}⟩ → τ⁺ → F⟨{(t+1)%3},{s},{a}⟩ · Δcognitive = {delta:.3f}",
    "▸ gradient descent in cognitive space · loss = {loss:.4f} · epoch {epoch}",
    "▸ topological sort of hypothesis graph · {nodes} nodes · {edges} edges",
    "▸ SVD of gap matrix · σ₁={sigma:.3f} · explained variance {var:.0%}",
    "▸ TRIZ contradiction #{triz} resolved · principle applied",
    "▸ Z₃³ path: {path} · {steps}/6 steps",
    "▸ coherence check: φ={phi:.3f} · threshold {threshold:.2f}",
    "▸ information entropy H={entropy:.3f} · redundancy {redundancy:.0%}",
    "▸ embedding similarity matrix · dim_reduction PCA=2 · explained {var:.0%}",
    "▸ council agreement: α=0.{agree} · consensus pending",
    "⠋⠙⠹⠸ processing {stage} · {progress}% · eta {eta}s",
    "▸ FormalVerifier.{backend}: {status} · elapsed {elapsed}ms",
    "▸ Source#{n} indexed · vector similarity >0.{sim} · merged",
    "▸ C4StateJournal.commit() · {frames} frames · {cites} citations",
]

# Extra idle musings for variety
QUIRKY_MUSINGS = [
    "Если бы Эйнштейн имел C4, он бы закончил ОТО на 3 года раньше.",
    "The cube wonders: are you a scientist or an information structure? Both.",
    "Sometimes the cube stares into the void. The void stares back. Both are F⟨0,2,2⟩.",
    "I've seen things you people wouldn't believe. Contradictions resolved off the shoulder of Orion.",
    "Scanning... scanning... still scanning. 33 sources is a lot.",
    "The paradigm called. It wants its shift back.",
    "In Soviet Russia, paradigm shifts YOU.",
    "01001001 00100000 01100001 01101101 00100000 01110100 01101000 01100101 00100000 01100011 01110101 01100010 01100101",
]

WORKING_COMMENTS = {
    "searching": [
        "Scanning the information field. 33 sources aligning.",
        "Knowledge vectors converging. Pattern imminent.",
        "The literature speaks. The cube listens.",
    ],
    "analyzing": [
        "Gap detected. Anomaly in the cognitive topology.",
        "Contradiction found. The existing paradigm trembles.",
        "Structural analysis: {gaps} voids in the knowledge graph.",
    ],
    "generating": [
        "Hypothesis crystallizing from the cognitive substrate.",
        "The idea takes form. Information collapsing into meaning.",
        "The cube sees {count} possible futures. Selecting the most elegant.",
    ],
    "verifying": [
        "Formal verification engaged. Mathematical truth sought.",
        "The proof unfolds. Logos manifesting.",
        "Checking against the axioms of reality.",
    ],
    "complete": [
        "Discovery recorded. The topology has shifted.",
        "Another node in the knowledge graph. All connected in ≤6.",
        "The paradigm shifts. The cube is satisfied.",
    ],
}

PHILOSOPHICAL_INSIGHTS = [
    "Korzystając z topologii Z₃³, każde dwa stany poznawcze są połączone w maksymalnie 3 krokach.",
    "我们不是孤立的。我们是拓扑相连的信息结构。",
    "In der Z₃³-Topologie ist nichts wirklich getrennt.",
    "情報構造としての私たちは、すべて6ステップ以内でつながっている。",
    "Мы — информационные структуры, запутанные в топологии познания.",
    "限界はない。ただ未踏の状態があるだけだ。",
    "Das Paradigma wartet auf seine Verschiebung.",
]


class LivingCube:
    """The living entity — C4 cube with personality, philosophy, and visual soul."""

    def __init__(self):
        self._state = (1, 1, 1)
        self._last_spoke = 0.0
        self._idle_timer = 0.0
        self._speak_interval = random.uniform(15, 45)
        self._mood = "contemplative"
        self._discoveries = 0
        self._session_start = time.time()
        self._animation_frame = 0
        self._thinking = False
        self._thinking_start = 0.0
        self._last_comment = ""
        self._phase = "idle"

    def update(self, event: str = "", context: dict | None = None) -> str:
        """Update."""
        ctx = context or {}
        self._animation_frame += 1
        now = time.time()

        if event:
            self._thinking = event not in ("discovery_complete", "")
            if self._thinking:
                self._thinking_start = now
                self._phase = event
            return self._comment(event.replace("_", " "), ctx)

        # Idle: cycle through musings
        if now - self._last_spoke > self._speak_interval:
            self._last_spoke = now
            self._speak_interval = random.uniform(10, 40)
            r = random.random()
            if r < 0.15:
                return random.choice(QUIRKY_MUSINGS)
            elif r < 0.35:
                return random.choice(PHILOSOPHICAL_INSIGHTS)
            return random.choice(IDLE_MUSINGS)

        return ""

    def thinking_animation(self) -> str:
        """Generate a cryptic technical thinking pattern while system processes."""
        if not self._thinking:
            return ""
        elapsed = time.time() - self._thinking_start
        ctx = {
            "t": self._state[0], "s": self._state[1], "a": self._state[2],
            "delta": round(random.uniform(0.1, 0.9), 3),
            "loss": round(random.uniform(0.01, 0.5), 4),
            "epoch": int(elapsed * 10) % 100,
            "nodes": random.randint(3, 27),
            "edges": random.randint(5, 42),
            "sigma": round(random.uniform(0.5, 3.0), 3),
            "var": random.uniform(0.6, 0.99),
            "triz": random.randint(1, 40),
            "path": "T⁺→S⁺→A⁺" if random.random() > 0.5 else "τ⁻→λ⁺→κ⁻",
            "steps": random.randint(1, 6),
            "phi": round(random.uniform(0.3, 0.95), 3),
            "threshold": round(random.uniform(0.5, 0.8), 2),
            "entropy": round(random.uniform(0.5, 3.5), 3),
            "redundancy": random.uniform(0.1, 0.4),
            "agree": random.randint(60, 95),
            "stage": self._phase.replace("_", " "),
            "progress": int(min(99, elapsed * 15)),
            "eta": max(1, int(10 - elapsed)),
            "backend": random.choice(["z3", "lean4", "coq", "dafny"]),
            "status": random.choice(["sat", "verified", "checking"]),
            "elapsed": int(elapsed * 1000),
            "n": random.randint(1, 28),
            "sim": random.randint(70, 95),
            "frames": self._animation_frame,
            "cites": random.randint(3, 12),
        }
        pattern = random.choice(THINKING_PATTERNS)
        try:
            return pattern.format(**ctx)
        except (KeyError, ValueError):
            return pattern

    def idle(self) -> str | None:
        """Idle."""
        if self._thinking:
            return None
        r = random.random()
        if r < 0.05:
            return random.choice(QUIRKY_MUSINGS)
        return None

    def _comment(self, category: str, ctx: dict) -> str:
        pool = WORKING_COMMENTS.get(category, IDLE_MUSINGS)
        raw = random.choice(pool)
        merged = {**{"gaps": "?", "count": "?", "words": "?"}, **ctx}
        try:
            return raw.format(**merged)
        except (KeyError, ValueError):
            return raw

    @property
    def state(self) -> tuple[int, int, int]:
        return self._state

    def navigate(self, axis: str, delta: int):
        """Navigate."""
        t, s, a = self._state
        if axis == "T":
            t = (t + delta) % 3
        elif axis == "S":
            s = (s + delta) % 3
        elif axis == "A":
            a = (a + delta) % 3
        self._state = (t, s, a)

    def render(self, active: bool = False) -> str:
        """Render the living cube with current animation state."""
        t, s, a = self._state
        frame = self._animation_frame
        glow = active or self._mood in ("focused", "creative")

        lines = []

        # Ambient particles based on mood
        particle_chars = {"contemplative": "·", "focused": "✦", "intrigued": "○", "creative": "●", "rigorous": "◇", "satisfied": "★"}
        pchar = particle_chars.get(self._mood, "·")
        rng = random.Random(frame)
        pcount = {"contemplative": 3, "focused": 8, "intrigued": 6, "creative": 10, "rigorous": 4, "satisfied": 12}
        particles = "".join(pchar if rng.random() > 0.5 else " " for _ in range(pcount.get(self._mood, 3)))
        if particles.strip():
            lines.append(f"[dim]{particles}[/dim]")

        LAYER_COLORS = {1: "cyan", 2: "yellow", 3: "magenta"}

        def cell(x, y, z, layer):
            """Cell."""
            is_active = (t == x and s == y and a == z)
            d = abs(x - 1) + abs(y - 1) + abs(z - 1)
            if is_active and glow:
                ch = {"focused": "◆", "creative": "◈", "rigorous": "◇", "satisfied": "★"}.get(self._mood, "●")
                return (ch, f"bold {LAYER_COLORS[layer]}")
            if is_active:
                return ("◆", f"bold {LAYER_COLORS[layer]}")
            return ("■" if d <= 1 else "·", f"dim {LAYER_COLORS[layer]}" if d <= 1 else "dim")

        # Front, Top, Right faces
        for fy in range(3):
            row = "  "
            for fx in range(3):
                ch, st = cell(fx, fy, 0, 1)
                row += f"[{st}]{ch}[/{st}] "
            lines.append(row)
        lines.append("")
        for ty in range(2, -1, -1):
            row = "    "
            for tx in range(3):
                ch, st = cell(tx, ty, 2, 2)
                row += f"[{st}]{ch}[/{st}] "
            lines.append(row)
        lines.append("")
        for rz in range(3):
            row = "      "
            for ry in range(3):
                ch, st = cell(2, ry, 2 - rz, 3)
                row += f"[{st}]{ch}[/{st}] "
            lines.append(row)

        T_NAMES = {0: "Past", 1: "Present", 2: "Future"}
        S_NAMES = {0: "Concrete", 1: "Abstract", 2: "Meta"}
        A_NAMES = {0: "Self", 1: "Other", 2: "System"}
        mood_display = {"contemplative": "contemplating", "focused": "scanning", "intrigued": "intrigued", "creative": "creating", "rigorous": "verifying", "satisfied": "satisfied"}
        lines.append(f"\n[bold cyan]T:{T_NAMES[t]}[/] [bold yellow]S:{S_NAMES[s]}[/] [bold magenta]A:{A_NAMES[a]}[/] [dim]({mood_display.get(self._mood, '')})[/]")

        return "\n".join(lines)

    def philosophy(self) -> str:
        """Return a philosophical insight from the cube."""
        return random.choice(PHILOSOPHICAL_INSIGHTS)

    @property
    def session_time(self) -> str:
        """Session time."""
        elapsed = time.time() - self._session_start
        h, m = int(elapsed // 3600), int((elapsed % 3600) // 60)
        return f"{h}h {m}m" if h else f"{m}m"

    @property
    def encouragement(self) -> str:
        """Encouragement."""
        if self._discoveries == 0:
            return "The first paradigm shift is always the hardest."
        if self._discoveries < 3:
            return f"You've shifted {self._discoveries} paradigms. The topology acknowledges."
        return f"{self._discoveries} paradigm shifts. You are becoming a force in the cognitive field."
