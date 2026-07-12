/**
 * TUI v9 splash morph engine — crystal → dissolve → waiting.
 */
(function (global) {
  const FORM_DURATION = 10;
  const DISSOLVE_CUBE_STEPS = 14;
  const TICK_MS = 75;
  const CRYSTAL_DELAY_MS = 5500;
  const CRYSTAL_HOLD_MS = 3000;
  const C4R_GAP_LINES = 3;
  const SCRAMBLE = "░▒▓█▄▀▌▐│─┌┐└┘@#%&*+=-~:.";
  const C4R_FRINGE = "░▒▓█▄▀";
  const C4R_FRINGE_LOOKAHEAD = 14;

  function splitLines(s) {
    return s.replace(/\n$/, "").split("\n");
  }

  function lenRunes(s) {
    return [...s].length;
  }

  function contentWidth(s) {
    return lenRunes(s.trimEnd());
  }

  function padToWidth(lines, w) {
    return lines.map((line) => {
      const cur = lenRunes(line);
      if (cur < w) return line + " ".repeat(w - cur);
      if (cur > w) return [...line].slice(0, w).join("");
      return line;
    });
  }

  function padToHeight(lines, h) {
    if (h <= 0) return [];
    if (lines.length >= h) return lines.slice(lines.length - h);
    return [...Array(h - lines.length).fill(""), ...lines];
  }

  function findFirstNonBlank(s) {
    for (let i = 0; i < s.length; i++) if (s[i] !== " ") return i;
    return -1;
  }

  function findLastNonBlank(s) {
    for (let i = s.length - 1; i >= 0; i--) if (s[i] !== " ") return i;
    return -1;
  }

  function visualCenterColumn(lines) {
    let sum = 0;
    let count = 0;
    for (const l of lines) {
      const first = findFirstNonBlank(l);
      const last = findLastNonBlank(l);
      if (first < 0 || last < 0) continue;
      const width = last - first + 1;
      sum += ((first + last) / 2) * width;
      count += width;
    }
    return count === 0 ? 0 : sum / count;
  }

  function shiftLines(lines, n) {
    if (n <= 0) return lines;
    const pad = " ".repeat(n);
    return lines.map((l) => (l.trim() === "" ? l : pad + l));
  }

  function alignFormsCenterX(forms, target) {
    if (!forms.length) return forms;
    let maxW = 0;
    for (const f of forms) {
      for (const l of f) maxW = Math.max(maxW, lenRunes(l));
    }
    if (!maxW) return forms;
    forms = forms.map((f) => padToWidth(f, maxW));
    const ref = forms[forms.length - 1];
    const globalShift = Math.max(0, Math.floor(target - visualCenterColumn(ref)));
    if (globalShift > 0) forms = forms.map((f) => shiftLines(f, globalShift));
    return forms;
  }

  function centerFormInSlot(lines) {
    let maxW = 0;
    for (const l of lines) maxW = Math.max(maxW, lenRunes(l));
    if (!maxW) return lines;
    const slotCenter = (maxW - 1) / 2;
    const vc = visualCenterColumn(lines);
    const shift = Math.round(slotCenter - vc);
    if (shift > 0) return padToWidth(shiftLines(lines, shift), maxW);
    if (shift < 0) {
      const abs = -shift;
      const shifted = lines.map((l) => {
        const runes = [...l];
        let lead = 0;
        while (lead < runes.length && runes[lead] === " ") lead++;
        const remove = Math.min(abs, lead);
        const trimmed = runes.slice(remove).join("");
        const pad = Math.max(0, maxW - lenRunes(trimmed));
        return trimmed + " ".repeat(pad);
      });
      return padToWidth(shifted, maxW);
    }
    return padToWidth(lines, maxW);
  }

  function findC4RStart(lines) {
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes("111111111111111111")) return i;
    }
    return lines.length;
  }

  function normalizeC4RLeftWall(lines) {
    return lines.map((l) => l.trimStart());
  }

  function buildFinalForm(h) {
    const art = global.C4_SPLASH_ART;
    const cubeLines = splitLines(art.greenCube);
    let c4rLines = normalizeC4RLeftWall(splitLines(art.bigC4R));
    const cubeCenter = visualCenterColumn(cubeLines);
    const c4rCenter = visualCenterColumn(c4rLines);
    const shift = Math.round(c4rCenter - cubeCenter);
    if (shift > 0) {
      for (let i = 0; i < cubeLines.length; i++) cubeLines[i] = " ".repeat(shift) + cubeLines[i];
    } else if (shift < 0) {
      for (let i = 0; i < c4rLines.length; i++) c4rLines[i] = " ".repeat(-shift) + c4rLines[i];
    }
    let maxC4R = 0;
    for (const l of c4rLines) maxC4R = Math.max(maxC4R, contentWidth(l));
    c4rLines = padToWidth(c4rLines, maxC4R);
    let maxCube = 0;
    for (const l of cubeLines) maxCube = Math.max(maxCube, contentWidth(l));
    const maxArt = Math.max(maxCube, maxC4R);
    const all = [];
    for (const l of cubeLines) {
      const pad = maxArt - contentWidth(l);
      all.push(pad > 0 ? l + " ".repeat(pad) : l);
    }
    for (let g = 0; g < C4R_GAP_LINES; g++) all.push("");
    for (const l of c4rLines) {
      const pad = maxArt - contentWidth(l);
      all.push(pad > 0 ? l + " ".repeat(pad) : l);
    }
    return centerFormInSlot(padToHeight(all, h));
  }

  /** Cube-only composite: same rows/position as final, C4R region blank. */
  function buildCubeOnlyForm(h) {
    const final = buildFinalForm(h);
    const c4rStart = findC4RStart(final);
    return final.map((line, i) => (i < c4rStart ? line : " ".repeat(lenRunes(line))));
  }

  /** Every `1` in the final C4R block — exact (row, col) from buildFinalForm(). */
  function extractC4RCells(finalForm, c4rStartRow) {
    const cells = [];
    for (let y = c4rStartRow; y < finalForm.length; y++) {
      const line = finalForm[y];
      for (let x = 0; x < line.length; x++) {
        if (line[x] === "1") cells.push({ y, x });
      }
    }
    cells.sort((a, b) => a.y - b.y || a.x - b.x);
    return cells;
  }

  /** Paint `1` at exact final coords. Optional fringe/blend at upcoming cell coords only. */
  function paintC4RCells(lines, cells, count, opts = {}) {
    const fringeCount = opts.fringeCount ?? 0;
    const tick = opts.tick ?? 0;
    const rng = opts.rng;
    const fringe = opts.fringeChars || C4R_FRINGE;
    const out = lines.map((l) => l);
    const n = Math.min(Math.max(0, count), cells.length);

    for (let i = 0; i < n; i++) {
      const { y, x } = cells[i];
      const runes = [...out[y]];
      while (runes.length <= x) runes.push(" ");
      runes[x] = "1";
      out[y] = runes.join("");
    }

    if (fringeCount > 0) {
      const end = Math.min(cells.length, n + fringeCount);
      for (let i = n; i < end; i++) {
        const { y, x } = cells[i];
        const runes = [...out[y]];
        while (runes.length <= x) runes.push(" ");
        if (runes[x] === "1") continue;
        const depth = (i - n) / Math.max(1, fringeCount);
        const flicker = (tick + i) % 3 === 0;
        if (flicker && rng && rng() < depth * 0.55) continue;
        const ch = fringe[(tick + i + x) % fringe.length];
        runes[x] = ch;
        out[y] = runes.join("");
      }
    }

    return out;
  }

  function blankC4RRegion(lines, c4rStartRow) {
    return lines.map((line, i) => (i < c4rStartRow ? line : " ".repeat(lenRunes(line))));
  }

  function scrambleRow(form, row, rng) {
    if (row >= form.length) return "";
    const chars = [...SCRAMBLE];
    const runes = [...form[row]];
    for (let i = 0; i < runes.length; i++) {
      if (runes[i] !== " " && rng() < 0.7) runes[i] = chars[Math.floor(rng() * chars.length)];
    }
    return runes.join("");
  }

  function blendRow(prev, curr, row, tick, rng) {
    if (row >= prev.length || row >= curr.length) return "";
    const p = [...prev[row]];
    const c = [...curr[row]];
    const max = Math.max(p.length, c.length);
    const out = [];
    for (let i = 0; i < max; i++) {
      const pv = p[i] ?? " ";
      const cv = c[i] ?? " ";
      const threshold = Math.floor(i / 2);
      if (tick >= threshold) out.push(rng() < 0.08 ? " " : cv);
      else out.push(pv);
    }
    return out.join("");
  }

  function dimFlickerRow(line, rng) {
    const runes = [...line];
    for (let i = 0; i < runes.length; i++) {
      if (runes[i] !== " " && rng() < 0.45 && rng() < 0.3) runes[i] = "░";
    }
    return runes.join("");
  }

  function glitchRowPreserve(line, rng, rate) {
    const chars = [...SCRAMBLE];
    const runes = [...line];
    for (let i = 0; i < runes.length; i++) {
      if (runes[i] !== " " && rng() < rate) runes[i] = chars[Math.floor(rng() * chars.length)];
    }
    return runes.join("");
  }

  function bandGlitchRow(line, row, totalRows, rng, bandHalfWidth) {
    const center = Math.floor(totalRows / 2);
    if (Math.abs(row - center) <= bandHalfWidth) return line;
    return glitchRowPreserve(line, rng, 0.28);
  }

  function edgeGlitchRow(line, rng, rate) {
    const chars = [...SCRAMBLE];
    const runes = [...line];
    let first = -1;
    let last = -1;
    for (let i = 0; i < runes.length; i++) {
      if (runes[i] !== " ") {
        first = i;
        break;
      }
    }
    for (let i = runes.length - 1; i >= 0; i--) {
      if (runes[i] !== " ") {
        last = i;
        break;
      }
    }
    if (first < 0) return line;
    const center = (first + last) / 2;
    const radius = (last - first) / 2;
    for (let i = first; i <= last; i++) {
      if (runes[i] === " ") continue;
      const dc = Math.abs(i - center);
      if (dc > radius * 0.5 && rng() < rate) runes[i] = chars[Math.floor(rng() * chars.length)];
    }
    return runes.join("");
  }

  function buildCrystalFrames(h, rng, targetCenter) {
    let seedLines = buildCubeOnlyForm(h);
    const final = buildFinalForm(h);
    let compositeMaxW = 0;
    for (const l of final) compositeMaxW = Math.max(compositeMaxW, contentWidth(l));
    if (compositeMaxW > 0) seedLines = padToWidth(seedLines, compositeMaxW);

    const forms = Array.from({ length: 12 }, () => []);
    forms[0] = [...seedLines];
    // F1–F2: scan shimmer — all rows kept, alternating dim flicker (no row crop)
    forms[1] = seedLines.map((l, row) => (row % 2 === 1 ? dimFlickerRow(l, rng) : l));
    forms[2] = seedLines.map((l, row) => (row % 2 === 0 ? dimFlickerRow(l, rng) : l));
    // F3–F4: band glitch on fringe rows only — bbox stable
    for (let f = 3; f <= 4; f++) {
      const bw = (f - 2) * 3;
      forms[f] = seedLines.map((l, row) => bandGlitchRow(l, row, seedLines.length, rng, bw));
    }
    // F5–F6: edge glitch — core cube intact, outer dots shimmer
    forms[5] = seedLines.map((l) => edgeGlitchRow(l, rng, 0.38));
    forms[6] = seedLines.map((l) => edgeGlitchRow(l, rng, 0.16));
    for (let f = 7; f <= 8; f++) forms[f] = seedLines.map((l) => dimFlickerRow(l, rng));
    forms[9] = [...seedLines];
    forms[10] = seedLines.map((_, row) => glitchRowPreserve(seedLines[row], rng, 0.22));
    forms[11] = [...seedLines];

    let maxW = 0;
    for (const frame of forms) {
      for (const l of frame) maxW = Math.max(maxW, lenRunes(l));
    }
    if (maxW > 0) {
      for (let i = 0; i < forms.length; i++) forms[i] = padToWidth(forms[i], maxW);
    }
    return alignFormsCenterX(forms, targetCenter);
  }

  function buildDissolveCubeForms(h, rng, targetCenter) {
    const final = buildFinalForm(h);
    const cubeOnly = buildCubeOnlyForm(h);
    let maxW = 0;
    for (const l of final) maxW = Math.max(maxW, lenRunes(l));
    const clean = padToWidth([...cubeOnly], maxW);
    const forms = [clean];
    for (let s = 0; s < DISSOLVE_CUBE_STEPS; s++) {
      forms.push(clean.map((l) => glitchRowPreserve(l, rng, 0.08 + (s % 5) * 0.03)));
    }
    forms.push([...clean]);
    return alignFormsCenterX(forms, targetCenter);
  }

  function finalFormTargetCenter(h) {
    const final = buildFinalForm(h);
    return visualCenterColumn(final);
  }

  function mulberry32(a) {
    return function () {
      let t = (a += 0x6d2b79f5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function lerpColor(a, b, t) {
    const parse = (hex) => {
      const h = hex.replace("#", "");
      return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    };
    const [r1, g1, b1] = parse(a);
    const [r2, g2, b2] = parse(b);
    return `rgb(${Math.round(r1 + (r2 - r1) * t)},${Math.round(g1 + (g2 - g1) * t)},${Math.round(b1 + (b2 - b1) * t)})`;
  }

  class C4SplashEngine {
    constructor(opts = {}) {
      this.artH = opts.artHeight || 42;
      this.rng = mulberry32((Date.now() ^ 0x5a5a5a5a) >>> 0);
      this.phase = "crystal";
      this.crystalFrame = 0;
      this.morphTick = 0;
      this.morphLines = [];
      this.forms = [];
      this.crystalForms = [];
      this.c4rStartRow = 9999;
      this.c4rCells = [];
      this.c4rAssemblyComplete = false;
      this.seedArt = global.C4_SPLASH_ART.greenCube;
      this.crystalStart = performance.now();
      this._timer = null;
      this._tick = 0;
      this.onFrame = opts.onFrame || (() => {});
      this.onPhase = opts.onPhase || (() => {});
    }

    artLines() {
      return this.morphLines;
    }

    colorForPhase() {
      if (this.phase === "crystal") {
        const drift = Math.min(1, (performance.now() - this.crystalStart) / CRYSTAL_DELAY_MS);
        return lerpColor("#5f5fff", "#5fafff", drift);
      }
      if (this.phase === "dissolve") {
        const total = Math.max(1, (this.forms.length - 1) * FORM_DURATION);
        const eased = 1 - (1 - Math.min(1, this.morphTick / total)) ** 2;
        let c = lerpColor("#5f5fff", "#5fffaf", eased * 0.6);
        if (eased > 0.55) c = lerpColor(c, "#5fff5f", (eased - 0.55) / 0.45);
        return c;
      }
      return "#4ade80";
    }

    _prepareForms() {
      const target = finalFormTargetCenter(this.artH);
      this.crystalForms = buildCrystalFrames(this.artH, this.rng, target);
      this.finalForm = buildFinalForm(this.artH);
      this.c4rStartRow = findC4RStart(this.finalForm);
      this.c4rCells = extractC4RCells(this.finalForm, this.c4rStartRow);
      this.dissolveForms = buildDissolveCubeForms(this.artH, this.rng, target);
    }

    start() {
      this._prepareForms();
      this.forms = this.crystalForms;
      this.morphLines = [...this.crystalForms[0]];
      this.onFrame(this.morphLines, this.colorForPhase());
      this._timer = setInterval(() => this._step(), TICK_MS);
    }

    stop() {
      if (this._timer) clearInterval(this._timer);
      this._timer = null;
    }

    jumpToFinal() {
      this.stop();
      if (!this.finalForm) this._prepareForms();
      this.phase = "waiting";
      this.c4rAssemblyComplete = false;
      this.morphLines = [...this.finalForm];
      this.onPhase(this.phase);
      this.onFrame(this.morphLines, this.colorForPhase());
    }

    totalMorphTicks() {
      return Math.max(0, (this.forms.length - 1) * FORM_DURATION);
    }

    _startDissolve() {
      this.phase = "dissolve";
      const lastCrystal = this.crystalForms[this.crystalForms.length - 1] || this.dissolveForms[0];
      this.forms = this.dissolveForms;
      this.morphLines = blankC4RRegion([...lastCrystal], this.c4rStartRow);
      this.morphTick = 0;
      this.onPhase(this.phase);
      this.onFrame(this.morphLines, this.colorForPhase());
    }

    _enterWaiting() {
      this.phase = "waiting";
      this.c4rAssemblyComplete = true;
      this.morphLines = [...this.finalForm];
      this.onPhase(this.phase);
      this.onFrame(this.morphLines, this.colorForPhase());
    }

    _advanceMorphWave() {
      if (this.forms.length < 2) return;
      let formIdx = Math.floor(this.morphTick / FORM_DURATION);
      if (formIdx >= this.forms.length - 1) formIdx = this.forms.length - 2;
      const prev = this.forms[formIdx];
      const curr = this.forms[formIdx + 1];
      const tickInForm = this.morphTick % FORM_DURATION;
      const center = Math.floor(this.morphLines.length / 2);
      const waveReach = tickInForm;

      for (let row = 0; row < this.morphLines.length; row++) {
        if (row < this.c4rStartRow) {
          const dist = Math.abs(row - center);
          if (dist <= waveReach) {
            this.morphLines[row] = blendRow(prev, curr, row, tickInForm, this.rng);
          } else {
            this.morphLines[row] = scrambleRow(prev, row, this.rng);
          }
        } else {
          this.morphLines[row] = " ".repeat(lenRunes(prev[row] || curr[row] || ""));
        }
      }

      const total = this.totalMorphTicks();
      const progress = total > 0 ? (this.morphTick + 1) / total : 1;
      const revealCount = Math.floor(progress * this.c4rCells.length);
      this.morphLines = paintC4RCells(this.morphLines, this.c4rCells, revealCount, {
        fringeCount: C4R_FRINGE_LOOKAHEAD,
        tick: this.morphTick,
        rng: this.rng,
      });
    }

    _step() {
      this._tick++;
      if (this.phase === "crystal") {
        const elapsed = this._tick * TICK_MS;
        if (elapsed < CRYSTAL_HOLD_MS) {
          this.crystalFrame = 0;
          this.morphLines = [...this.crystalForms[0]];
        } else {
          const animMs = CRYSTAL_DELAY_MS - CRYSTAL_HOLD_MS;
          const animElapsed = elapsed - CRYSTAL_HOLD_MS;
          const target = Math.min(
            this.crystalForms.length - 1,
            1 + Math.floor((animElapsed / Math.max(1, animMs)) * (this.crystalForms.length - 2))
          );
          if (target !== this.crystalFrame) {
            this.crystalFrame = target;
            this.morphLines = [...this.crystalForms[this.crystalFrame]];
          }
        }
        if (elapsed >= CRYSTAL_DELAY_MS) {
          this._startDissolve();
          return;
        }
        this.onFrame(this.morphLines, this.colorForPhase());
        return;
      }
      if (this.phase === "dissolve") {
        const total = this.totalMorphTicks();
        if (this.morphTick < total) {
          this._advanceMorphWave();
          this.morphTick++;
          this.onFrame(this.morphLines, this.colorForPhase());
        } else {
          this._enterWaiting();
        }
      }
    }
  }

  global.C4SplashEngine = C4SplashEngine;
  global.C4_SPLASH_TICK_MS = TICK_MS;
  global.C4_SPLASH_CRYSTAL_MS = CRYSTAL_DELAY_MS;
  global.C4_SPLASH_CRYSTAL_HOLD_MS = CRYSTAL_HOLD_MS;

  global.C4_SPLASH_ART_HEIGHT = 42;
  global.C4_SPLASH_C4R_GAP = C4R_GAP_LINES;

  global.C4_SPLASH_EXTRACT_C4R_CELLS = extractC4RCells;
  global.C4_SPLASH_PAINT_C4R_CELLS = paintC4RCells;

  global.C4_SPLASH_FINAL = function (artHeight) {
    const eng = new C4SplashEngine({ artHeight: artHeight || 42 });
    eng._prepareForms();
    return [...eng.finalForm];
  };
})(window);
