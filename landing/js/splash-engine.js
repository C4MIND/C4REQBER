/**
 * TUI v9 splash morph engine — crystal → dissolve → waiting.
 */
(function (global) {
  const FORM_DURATION = 10;
  const TICK_MS = 75;
  const CRYSTAL_DELAY_MS = 5500;
  const SCRAMBLE = "░▒▓█▄▀▌▐│─┌┐└┘@#%&*+=-~:.";

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
    const shifts = forms.map((f) => Math.max(0, Math.floor(target - visualCenterColumn(f))));
    forms = forms.map((f, i) => (shifts[i] > 0 ? shiftLines(f, shifts[i]) : f));
    let maxW = 0;
    for (const f of forms) {
      for (const l of f) maxW = Math.max(maxW, contentWidth(l));
    }
    if (maxW > 0) forms = forms.map((f) => padToWidth(f, maxW));
    return forms;
  }

  function buildFinalForm(h) {
    const art = global.C4_SPLASH_ART;
    const cubeLines = splitLines(art.greenCube);
    let c4rLines = splitLines(art.bigC4R).map((l) => l.trimStart());
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
    all.push("");
    for (const l of c4rLines) {
      const pad = maxArt - contentWidth(l);
      all.push(pad > 0 ? l + " ".repeat(pad) : l);
    }
    return padToHeight(all, h);
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

  function buildCrystalFrames(seedArt, h, rng, targetCenter) {
    let seedLines = padToHeight(splitLines(seedArt), h);
    const final = buildFinalForm(h);
    let compositeMaxW = 0;
    for (const l of final) compositeMaxW = Math.max(compositeMaxW, contentWidth(l));
    if (compositeMaxW > 0) seedLines = padToWidth(seedLines, compositeMaxW);

    const forms = Array.from({ length: 12 }, () => []);
    forms[0] = [...seedLines];
    for (let row = 0; row < seedLines.length; row++) {
      const idx = 1 + (row % 2);
      if (!forms[idx].length) forms[idx] = Array(seedLines.length).fill("");
      forms[idx][row] = seedLines[row];
    }
    for (let f = 3; f <= 4; f++) {
      forms[f] = Array(seedLines.length).fill("");
      const center = Math.floor(seedLines.length / 2);
      const bw = (f - 2) * 3;
      for (let row = 0; row < seedLines.length; row++) {
        const dist = Math.abs(row - center);
        forms[f][row] = dist <= bw ? seedLines[row] : scrambleRow(seedLines, row, rng);
      }
    }
    for (let f = 5; f <= 6; f++) {
      forms[f] = [];
      for (let row = 0; row < seedLines.length; row++) {
        const plain = [...seedLines[row]];
        const center = Math.floor(plain.length / 2);
        const radius = (f - 4) * Math.floor(plain.length / 4);
        forms[f][row] = plain.map((ch, i) => (Math.abs(i - center) <= radius ? ch : " ")).join("");
      }
    }
    for (let f = 7; f <= 8; f++) forms[f] = seedLines.map((l) => dimFlickerRow(l, rng));
    forms[9] = [...seedLines];
    forms[10] = seedLines.map((_, row) => scrambleRow(seedLines, row, rng));
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

  function buildSplashForms(h, seedArt, rng, targetCenter) {
    const final = buildFinalForm(h);
    seedArt = seedArt.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, "");
    let compositeMaxW = 0;
    for (const l of final) compositeMaxW = Math.max(compositeMaxW, contentWidth(l));
    let form0 = padToHeight(splitLines(seedArt), h);
    if (compositeMaxW > 0) form0 = padToWidth(form0, compositeMaxW);
    const form1 = form0.map((_, i) => scrambleRow(form0, i, rng));
    const c4r = padToWidth(splitLines(global.C4_SPLASH_ART.bigC4R).map((l) => l.trimStart()), compositeMaxW);
    const form2 = padToHeight(c4r, h);
    return alignFormsCenterX([form0, form1, form2, final], targetCenter);
  }

  function finalFormTargetCenter(h) {
    const final = buildFinalForm(h);
    for (let i = 0; i < final.length; i++) {
      if (final[i].includes("111111111111111111")) {
        return visualCenterColumn(final.slice(i));
      }
    }
    return 0;
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
      this.artH = opts.artHeight || 40;
      this.rng = mulberry32((Date.now() ^ 0x5a5a5a5a) >>> 0);
      this.phase = "crystal";
      this.crystalFrame = 0;
      this.morphTick = 0;
      this.morphLines = [];
      this.forms = [];
      this.crystalForms = [];
      this.seedArt = global.C4_SPLASH_ART.crystalSeed;
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
      this.crystalForms = buildCrystalFrames(this.seedArt, this.artH, this.rng, target);
      this.dissolveForms = buildSplashForms(this.artH, this.seedArt, this.rng, target);
      this.finalForm = this.dissolveForms[this.dissolveForms.length - 1];
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
      this.morphLines = [...this.finalForm];
      this.onPhase(this.phase);
      this.onFrame(this.morphLines, this.colorForPhase());
    }

    totalMorphTicks() {
      return Math.max(0, (this.forms.length - 1) * FORM_DURATION);
    }

    _startDissolve() {
      this.phase = "dissolve";
      const hold = this.morphLines.length
        ? [...this.morphLines]
        : [...this.crystalForms[Math.min(this.crystalFrame, this.crystalForms.length - 1)]];
      this.forms = [hold, ...this.dissolveForms];
      this.morphLines = [...hold];
      this.morphTick = 0;
      this.onPhase(this.phase);
    }

    _enterWaiting() {
      this.phase = "waiting";
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
        const dist = Math.abs(row - center);
        if (dist <= waveReach) {
          this.morphLines[row] = blendRow(prev, curr, row, tickInForm, this.rng);
        } else {
          this.morphLines[row] = scrambleRow(prev, row, this.rng);
        }
      }
    }

    _step() {
      this._tick++;
      if (this.phase === "crystal") {
        const frameInterval = Math.max(1, Math.floor(CRYSTAL_DELAY_MS / TICK_MS / 12));
        if (this._tick % frameInterval === 0 && this.crystalFrame < this.crystalForms.length - 1) {
          this.crystalFrame++;
          this.morphLines = [...this.crystalForms[this.crystalFrame]];
        }
        const elapsed = this._tick * TICK_MS;
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

  global.C4_SPLASH_FINAL = function (artHeight) {
    const eng = new C4SplashEngine({ artHeight: artHeight || 40 });
    eng._prepareForms();
    return [...eng.finalForm];
  };
})(window);
