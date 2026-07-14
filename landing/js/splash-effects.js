/**
 * TUI v9 splash visual effects — port of bio_aurora.go + canvas polish.
 */
(function (global) {
  const AURORA_PALETTE = ["#4ade80", "#22d3ee", "#60a5fa", "#c084fc", "#fbbf24", "#4ade80"];
  // Warm-biased palette for C4R waves (brand-forward, less neon than full aurora).
  const C4R_PALETTE = ["#fbbf24", "#fb923c", "#f97316", "#fbbf24", "#fde047"];
  const MAX_AURORA_OPACITY = 0.55;
  const BLOOM_FRAMES = 12;
  const PULSE_MS = 600;

  function tanh(x) {
    const e = Math.exp(2 * x);
    return (e - 1) / (e + 1);
  }

  class BioAurora {
    constructor(c4rStartRow) {
      this.startTime = 0;
      this.c4rStartRow = c4rStartRow >= 0 ? c4rStartRow : 9999;
    }

    tick(elapsedSec) {
      this.startTime = elapsedSec;
    }

    globalPhase() {
      return Math.sin(this.startTime * ((2 * Math.PI) / 48)) * 0.08;
    }

    isC4RRow(y) {
      return y >= this.c4rStartRow;
    }

    colorAt(x, y) {
      const t = this.startTime;
      const gp = this.globalPhase();
      const w1 = Math.sin(t * ((2 * Math.PI) / 4.3) + x * 0.3 + y * 0.2 + gp);
      const w2 = Math.sin(t * ((2 * Math.PI) / 6.7) + x * 0.15 - y * 0.4 - gp * 0.7);
      const w3 = Math.sin(t * ((2 * Math.PI) / 8.1) - x * 0.25 + y * 0.35 + gp * 1.1);
      const sweep = Math.sin(t * ((2 * Math.PI) / 19) - x * 0.08);
      let v = (w1 + w2 + w3 + sweep * 0.4) / 3.4;
      if (this.isC4RRow(y)) {
        v += w1 * 0.12;
      } else {
        const band = Math.sin(t * ((2 * Math.PI) / 12.5) - x * 0.15 + gp);
        v += band * 0.28;
      }
      const pulse = Math.sin(t * ((2 * Math.PI) / 7) + gp * 2);
      v += pulse * 0.18;
      const norm = (tanh(v) + 1) / 2;
      const steps = 3;
      let stepIdx = Math.floor(norm * steps);
      if (stepIdx >= steps) stepIdx = steps - 1;
      if (stepIdx < 0) stepIdx = 0;
      let idx = stepIdx * 2;
      if (norm * steps - stepIdx > 0.5) idx++;
      if (idx >= AURORA_PALETTE.length) idx = AURORA_PALETTE.length - 1;
      return idx;
    }

    intensityAt(x, y) {
      const t = this.startTime;
      const gp = this.globalPhase() * 1.5;
      const b1 = Math.sin(t * ((2 * Math.PI) / 5.2) + x * 0.1 + y * 0.15 + gp);
      const b2 = Math.sin(t * ((2 * Math.PI) / 3.8) - x * 0.05 - gp);
      const drift = Math.sin(t * ((2 * Math.PI) / 11) + y * 0.12) * 0.06;
      let intensity = 0.37 + 0.43 * ((b1 + b2) / 2) + 0.18 + drift;
      const flarePhase = t % 9;
      if (flarePhase < 0.6) {
        let flare = (1 - Math.abs(flarePhase - 0.3) / 0.3) * 0.1;
        if (flare < 0) flare = 0;
        intensity += flare;
      }
      let cap = MAX_AURORA_OPACITY;
      if (this.isC4RRow(y)) cap = 0.15;
      if (intensity > cap) intensity = cap;
      if (intensity < 0.15) intensity = 0.15;
      return intensity;
    }

    renderLine(plain, y, opts) {
      const ditherSkip = (y + Math.floor(y / 2)) % 4;
      let html = "";
      for (let i = 0; i < plain.length; i++) {
        const ch = plain[i];
        if (ch === " ") {
          html += " ";
          continue;
        }
        // C4R block: animated warm waves (per-char) while preserving readability on mobile.
        if (this.isC4RRow(y)) {
          const wave = Math.sin(this.startTime * 1.55 + i * 0.22 + y * 0.35) * 0.5 + 0.5;
          const idx = Math.min(C4R_PALETTE.length - 1, Math.floor(wave * C4R_PALETTE.length));
          const color = C4R_PALETTE[idx];
          const shimmer = 0.78 + 0.22 * Math.sin(this.startTime * 1.35 + i * 0.18 + y * 0.5);
          const compact = opts && opts.compactC4R ? " splash-ch-c4r-compact" : "";
          html += `<span class="splash-ch-c4r splash-ch-c4r-wave${compact}" style="color:${color};opacity:${shimmer.toFixed(
            2
          )}">${esc(ch)}</span>`;
          continue;
        }
        if ((i + ditherSkip) % 5 === 0 || ((i * 3 + y) % 7 === 0)) {
          html += `<span class="splash-aurora-dither">${esc(ch)}</span>`;
          continue;
        }
        const idx = this.colorAt(i, y);
        const intensity = this.intensityAt(i, y);
        const color = AURORA_PALETTE[idx];
        const bold = intensity > MAX_AURORA_OPACITY * 0.85 ? " splash-aurora-bold" : "";
        const faint = intensity < 0.1 ? " splash-aurora-faint" : "";
        html += `<span class="splash-aurora-ch${bold}${faint}" style="color:${color};opacity:${intensity.toFixed(2)}">${esc(ch)}</span>`;
      }
      return html;
    }
  }

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function bloomFrame(artLines, frame, total, c4rStartRow, c4rCells, opts = {}) {
    if (total <= 0 || frame >= total) return artLines;
    const baseRevealed = opts.baseRevealed ?? 0;
    if (!c4rCells || !c4rCells.length || baseRevealed >= c4rCells.length) return artLines;

    const t = 1 - Math.pow(1 - frame / total, 3);
    const span = c4rCells.length - baseRevealed;
    const revealCount = baseRevealed + Math.floor(t * span);
    const c4rStart = c4rStartRow >= 0 ? c4rStartRow : artLines.length;
    const blanked = artLines.map((line, i) => (i < c4rStart ? line : " ".repeat(line.length)));

    if (!global.C4_SPLASH_PAINT_C4R_CELLS) return artLines;
    return global.C4_SPLASH_PAINT_C4R_CELLS(blanked, c4rCells, revealCount, {
      fringeCount: 10,
      tick: frame,
    });
  }

  function findC4RStart(lines) {
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes("111111111111111111")) return i;
    }
    return lines.length;
  }

  function drawStars(ctx, w, h, t, count) {
    ctx.fillStyle = "#0F1117";
    ctx.fillRect(0, 0, w, h);
    for (let i = 0; i < count; i++) {
      const sx = ((i * 7919) % 1000) / 1000;
      const sy = ((i * 6271) % 1000) / 1000;
      const tw = 0.35 + 0.65 * Math.sin(t * 1.3 + i * 0.7);
      const alpha = 0.08 + tw * 0.22;
      ctx.fillStyle = `rgba(180,200,255,${alpha})`;
      const px = sx * w;
      const py = sy * h * 0.75;
      ctx.fillRect(px, py, 1.2, 1.2);
    }
  }

  function drawCrystalGlow(ctx, w, h, t, hold) {
    const cx = w * 0.5;
    const cy = h * 0.42;
    const radius = hold ? w * 0.62 : w * 0.55;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
    const pulse = 0.5 + 0.5 * Math.sin(t * (hold ? 0.55 : 0.9));
    if (hold) {
      g.addColorStop(0, `rgba(95,95,255,${0.22 + 0.08 * pulse})`);
      g.addColorStop(0.25, `rgba(124,108,248,${0.14 + 0.05 * pulse})`);
      g.addColorStop(0.55, `rgba(95,175,255,${0.06 + 0.02 * pulse})`);
      g.addColorStop(1, "rgba(15,17,23,0)");
    } else {
      g.addColorStop(0, `rgba(95,95,255,${0.14 + 0.06 * pulse})`);
      g.addColorStop(0.35, `rgba(124,108,248,${0.08 + 0.03 * pulse})`);
      g.addColorStop(0.7, `rgba(95,175,255,${0.03})`);
      g.addColorStop(1, "rgba(15,17,23,0)");
    }
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    if (hold) {
      const vg = ctx.createRadialGradient(cx, cy, w * 0.2, cx, cy, w * 0.85);
      vg.addColorStop(0, "rgba(15,17,23,0)");
      vg.addColorStop(0.72, "rgba(15,17,23,0)");
      vg.addColorStop(1, "rgba(15,17,23,0.55)");
      ctx.fillStyle = vg;
      ctx.fillRect(0, 0, w, h);
    }
  }

  function drawScanline(ctx, w, h, y) {
    const g = ctx.createLinearGradient(0, y - 2, 0, y + 2);
    g.addColorStop(0, "rgba(95,175,255,0)");
    g.addColorStop(0.5, "rgba(95,175,255,0.06)");
    g.addColorStop(1, "rgba(95,175,255,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, y - 2, w, 4);
  }

  function drawAuroraGlow(ctx, w, h, t) {
    const g = ctx.createRadialGradient(w * 0.5, h * 0.32, 0, w * 0.5, h * 0.32, w * 0.75);
    g.addColorStop(0, `rgba(74,222,128,${0.05 + 0.04 * Math.sin(t * 0.7)})`);
    g.addColorStop(0.4, `rgba(34,211,238,${0.03 + 0.025 * Math.cos(t * 0.5)})`);
    g.addColorStop(0.7, `rgba(192,132,252,${0.02 + 0.015 * Math.sin(t * 0.3)})`);
    g.addColorStop(1, "rgba(15,17,23,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  function drawShockwave(ctx, w, h, progress) {
    if (progress <= 0 || progress >= 1) return;
    const r = progress * Math.max(w, h) * 0.55;
    const alpha = (1 - progress) * 0.12;
    ctx.strokeStyle = `rgba(34,211,238,${alpha})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(w * 0.5, h * 0.34, r, 0, Math.PI * 2);
    ctx.stroke();
  }

  function isBlockChar(ch) {
    return "█▀▓▒░▄▌▐".includes(ch);
  }

  function isDotChar(ch) {
    return ch !== " " && !isBlockChar(ch) && ch !== "1";
  }

  function renderColoredLine(line, y, phase, phaseColor, c4rStartRow, opts) {
    const inC4R = y >= c4rStartRow;
    let html = "";
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === " ") {
        html += " ";
        continue;
      }
      if (inC4R || ch === "1") {
        const compact = opts && opts.compactC4R ? " splash-ch-c4r-compact" : "";
        html += `<span class="splash-ch-c4r${compact}">${esc(ch)}</span>`;
        continue;
      }
      if (isBlockChar(ch)) {
        const hold = phase === "crystal" && opts && opts.crystalHold;
        const cls = hold ? "splash-ch-crystal splash-ch-crystal-hold" : "splash-ch-crystal";
        html += `<span class="${cls}" style="color:${phaseColor}">${esc(ch)}</span>`;
        continue;
      }
      if (phase === "crystal") {
        const hold = opts && opts.crystalHold;
        const cls = hold ? "splash-ch-purple-cube splash-ch-crystal-hold" : "splash-ch-purple-cube";
        html += `<span class="${cls}" style="color:${phaseColor}">${esc(ch)}</span>`;
        continue;
      }
      const cls =
        phase === "dissolve" ? "splash-ch-dissolve-dot" : phase === "waiting" ? "splash-ch-cube" : "splash-ch-dot";
      html += `<span class="${cls}" style="color:${phaseColor}">${esc(ch)}</span>`;
    }
    return html;
  }

  function renderColoredLines(lines, opts) {
    const { phase, phaseColor, c4rStartRow, aurora, useAurora } = opts;
    return lines
      .map((line, y) => {
        if (useAurora && aurora) return aurora.renderLine(line, y, opts);
        return renderColoredLine(line, y, phase, phaseColor, c4rStartRow, opts);
      })
      .join("<br>");
  }

  global.C4SplashEffects = {
    BioAurora,
    bloomFrame,
    findC4RStart,
    renderColoredLines,
    renderColoredLine,
    drawStars,
    drawCrystalGlow,
    drawScanline,
    drawAuroraGlow,
    drawShockwave,
    BLOOM_FRAMES,
    PULSE_MS,
    esc,
  };
})(window);
