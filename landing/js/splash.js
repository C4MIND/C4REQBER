/**
 * c4reqber web splash — TUI v9 port (crystal → dissolve → waiting).
 */
(function () {
  const SEEN_KEY = "c4r_splash_seen";
  const VERSION = "v5.7.1";
  const ART_H = 42;
  const effects = () => window.C4SplashEffects;
  const BLOOM_FRAMES = () => effects().BLOOM_FRAMES;
  const PULSE_MS = () => effects().PULSE_MS;
  const SCANLINE_MS = 525;

  function hasSeenBefore() {
    try {
      return !!localStorage.getItem(SEEN_KEY);
    } catch (_) {
      return false;
    }
  }

  function markSeen() {
    try {
      localStorage.setItem(SEEN_KEY, "1");
    } catch (_) {}
  }

  function shouldShow() {
    if (typeof window.c4rIsHomePath === "function") return window.c4rIsHomePath();
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    return path === "" || path === "/" || path === "/index.html";
  }

  function isMobileSplash() {
    return window.matchMedia("(max-width: 768px)").matches;
  }

  function isTouchSplash() {
    return isMobileSplash() || window.matchMedia("(pointer: coarse)").matches;
  }

  function skipHint() {
    return isTouchSplash()
      ? t("splash_status_skip_touch", "tap to skip")
      : t("splash_status_skip_hint", "click to skip to final");
  }

  function clearSplashPending() {
    document.documentElement.classList.remove("splash-pending");
  }

  function t(key, fallback) {
    const lang = window.c4rCurrentLang || "en";
    const dict = (window.i18n && window.i18n[lang]) || (window.i18n && window.i18n.en) || {};
    return dict[key] || fallback;
  }

  function bootingProgress(progress) {
    const p = Math.max(0, Math.min(1, progress));
    const width = 12;
    const total = p * width;
    const filled = Math.floor(total);
    const grad = ["▏", "▎", "▍", "▌", "▋", "▊", "▉"];
    let bar = "[";
    for (let i = 0; i < width; i++) {
      if (i < filled) bar += "█";
      else if (i === filled) {
        const frac = total - filled;
        bar += frac > 0 ? grad[Math.min(grad.length - 1, Math.floor(frac * grad.length))] : " ";
      } else bar += " ";
    }
    return bar + "]";
  }

  function buildTextLines(phase, phaseStart, crystalStart, now, readyToLaunch) {
    const sub1 = t("splash_subtitle_1", "Creative & Destructive Insights");
    const sub2 = t("splash_subtitle_2", "At Your Fingertips");
    const fullSub = `${sub1}  ·  ${sub2}`;
    const phaseElapsed = (now - phaseStart) / 1000;
    const crystalElapsed = (now - crystalStart) / 1000;

    let subtitle = "";
    if (phase !== "crystal") {
      const cut = Math.floor(phaseElapsed / 0.003);
      subtitle = cut < fullSub.length ? fullSub.slice(0, cut) : fullSub;
    }

    const showTagline = phase === "waiting" || (phase === "dissolve" && phaseElapsed > 0.25);
    const tagline = showTagline
      ? t("splash_tagline_caps", "COGNITIVE EXOSKELETON FOR AI-AGENTS AND HUMANS")
      : "";

    let motto = "";
    if (phase !== "crystal") {
      const d = phaseElapsed > 0 ? t("splash_motto_discover", "Discover.") + "  " : "";
      const inv = phaseElapsed > 0.6 ? t("splash_motto_invent", "Invent.") + "  " : "";
      const sh = phaseElapsed > 1.2 ? t("splash_motto_shift", "Shift") : "";
      const sp = phaseElapsed > 1.2 ? " " : "";
      const par = phaseElapsed > 1.2 ? t("splash_motto_paradigms", "paradigms.") : "";
      motto = { d, inv, sh, sp, par };
    }

    const showVersion = phase === "waiting" || (phase === "dissolve" && phaseElapsed > 0.5);
    let version = "";
    if (showVersion) {
      version = `C4REQBER ${VERSION}`;
      if (Math.sin(phaseElapsed * Math.PI) > 0) version = version.replace(".", "·");
    }

    const sepBlink = Math.sin(phaseElapsed * ((2 * Math.PI) / 3.3)) > 0.5 ? "·" : " ";
    let status = "";
    if (phase === "crystal") {
      const prog = bootingProgress(crystalElapsed / (window.C4_SPLASH_CRYSTAL_MS / 1000));
      status = `${t("splash_status_boot", "booting")} ${window.C4_SPLASH_CRYSTAL_MS / 1000}s ${sepBlink} ${prog} ${sepBlink} ${skipHint()}`;
    } else if (phase === "dissolve") {
      status = `${t("splash_status_awakening", "◆ awakening cube state ◆")} ${sepBlink} ${skipHint()}`;
    } else if (phase === "waiting") {
      status = readyToLaunch
        ? isTouchSplash()
          ? t("splash_status_launch_touch", "tap Enter to launch")
          : t("splash_status_launch", "press Enter to launch")
        : `${t("splash_status_ready", "✨ ready")} ${sepBlink} …`;
    }

    let footerSuffix = "Z";
    if (phase !== "crystal" && phaseElapsed >= 1.0) footerSuffix = "Z₃³";
    else if (phase !== "crystal" && phaseElapsed >= 0.5) footerSuffix = "Z₃";
    const footer = `${t("splash_footer", "GitLab · c4reqber · ")}${footerSuffix}`;

    const easter =
      phase === "waiting"
        ? `${t("splash_easter_1", "♭ Garmon doloy — bito usee ♭")}  ·  ${t("splash_easter_2", "old school russian-style science mafia")}`
        : "";

    return { subtitle, tagline, motto, version, status, footer, easter };
  }

  function init() {
    if (!shouldShow() || !window.C4_SPLASH_ART || !window.C4SplashEngine || !window.C4SplashEffects) {
      clearSplashPending();
      return;
    }

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const returning = hasSeenBefore();

    const overlay = document.createElement("div");
    overlay.id = "splash-overlay";
    overlay.className = "splash-phase-crystal splash-crystal-hold";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "c4reqber splash");
    overlay.innerHTML = `
      <canvas id="splash-canvas" aria-hidden="true"></canvas>
      <div class="splash-column" id="splash-column">
        <div class="splash-stage">
          <pre id="splash-art" aria-hidden="true"></pre>
        </div>
        <div class="splash-text" id="splash-text"></div>
      </div>
      <div class="splash-crystal-hud" id="splash-crystal-hud" aria-hidden="true"></div>
      <button type="button" class="splash-skip" id="splash-skip" data-i18n="splash_skip">Skip →</button>
    `;
    document.body.appendChild(overlay);
    document.body.classList.add("splash-active");
    clearSplashPending();

    const artEl = overlay.querySelector("#splash-art");
    const textEl = overlay.querySelector("#splash-text");
    const columnEl = overlay.querySelector("#splash-column");
    const crystalHud = overlay.querySelector("#splash-crystal-hud");
    const skipBtn = overlay.querySelector("#splash-skip");
    const canvas = overlay.querySelector("#splash-canvas");
    const ctx = canvas.getContext("2d");

    const timers = [];
    let phase = "crystal";
    let phaseStart = performance.now();
    let crystalStart = phaseStart;
    let bloomFrameIdx = 0;
    let shockProgress = 0;
    let scanY = 0;
    let lastScanAt = 0;
    let done = false;
    let engine = null;
    let aurora = null;
    let readyToLaunch = false;
    let rafId = 0;
    let c4rStartRow = 9999;
    let baseArtScale = 0;
    let compactAnim = 1;
    const ART_VIEWPORT_H = 0.68;
    const ART_COMPACT_MUL = 0.86;

    function artCompactMul() {
      return phase === "crystal" ? 1 : compactAnim;
    }

    function animateCompactScale() {
      if (phase === "crystal") {
        compactAnim = 1;
        fitArt();
        return;
      }
      const start = performance.now();
      const from = 1;
      const to = ART_COMPACT_MUL;
      const dur = 750;
      function step(now) {
        const t = Math.min(1, (now - start) / dur);
        const eased = 1 - (1 - t) ** 3;
        compactAnim = from + (to - from) * eased;
        fitArt();
        if (t < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }

    function isCrystalHold() {
      return phase === "crystal" && performance.now() - crystalStart < (window.C4_SPLASH_CRYSTAL_HOLD_MS || 3000);
    }

    function setPhaseClass(p) {
      overlay.classList.remove("splash-phase-crystal", "splash-phase-dissolve", "splash-phase-waiting", "splash-crystal-hold");
      overlay.classList.add(`splash-phase-${p}`);
      if (p === "crystal" && isCrystalHold()) overlay.classList.add("splash-crystal-hold");
    }

    function updateCrystalHud(now) {
      if (phase !== "crystal") {
        crystalHud.innerHTML = "";
        crystalHud.setAttribute("aria-hidden", "true");
        return;
      }
      overlay.classList.toggle("splash-crystal-hold", isCrystalHold());
      const crystalElapsed = (now - crystalStart) / 1000;
      const holdSec = (window.C4_SPLASH_CRYSTAL_HOLD_MS || 3000) / 1000;
      const sepBlink = Math.sin(crystalElapsed * ((2 * Math.PI) / 3.3)) > 0.5 ? "·" : " ";
      let status = "";
      if (isCrystalHold()) {
        status = `${t("splash_status_boot", "booting")} ${holdSec.toFixed(0)}s ${sepBlink} ${skipHint()}`;
      } else {
        const prog = bootingProgress(crystalElapsed / (window.C4_SPLASH_CRYSTAL_MS / 1000));
        status = `${t("splash_status_awakening", "◆ awakening cube state ◆")} ${sepBlink} ${prog}`;
      }
      crystalHud.innerHTML = `<p class="splash-crystal-hud-line">${effects().esc(status)}</p>`;
      crystalHud.setAttribute("aria-hidden", "false");
    }

    function isLaunchReady() {
      return phase === "waiting" && bloomFrameIdx >= BLOOM_FRAMES() && readyToLaunch;
    }

    function updateActionButton() {
      if (isLaunchReady()) {
        skipBtn.textContent = t("splash_enter", "Enter ↵");
        skipBtn.classList.add("splash-enter-ready");
        skipBtn.setAttribute("aria-label", t("splash_enter", "Enter"));
        overlay.classList.add("splash-await-enter");
      } else {
        skipBtn.textContent = t("splash_skip", "Skip →");
        skipBtn.classList.remove("splash-enter-ready");
        skipBtn.setAttribute("aria-label", t("splash_skip", "Skip"));
        overlay.classList.remove("splash-await-enter");
      }
    }

    function anchorCenterX() {
      const el = columnEl || textEl;
      const r = el.getBoundingClientRect();
      return r.left + r.width / 2;
    }

    function artVisualCenterX() {
      const spans = artEl.querySelectorAll("span");
      let minX = Infinity;
      let maxX = -Infinity;
      let found = false;
      spans.forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width <= 0) return;
        found = true;
        minX = Math.min(minX, r.left);
        maxX = Math.max(maxX, r.right);
      });
      if (!found) {
        const r = artEl.getBoundingClientRect();
        return r.left + r.width / 2;
      }
      return (minX + maxX) / 2;
    }

    function fitArt() {
      const mobile = isMobileSplash();
      artEl.classList.toggle("splash-art-mobile", mobile);
      overlay.classList.toggle("splash-mobile", mobile);
      artEl.style.transform = "";
      artEl.style.fontSize = "";
      void artEl.offsetWidth;

      let rect = artEl.getBoundingClientRect();
      if (!rect.width || !rect.height) return;

      const maxW = (columnEl ? columnEl.clientWidth : window.innerWidth * 0.94) * (mobile ? 0.99 : 0.98);
      const maxH = window.innerHeight * (mobile ? 0.5 : ART_VIEWPORT_H);
      const compact = artCompactMul();

      if (mobile) {
        const basePx = parseFloat(getComputedStyle(artEl).fontSize) || 10;
        const ratio = Math.min(maxW / rect.width, maxH / rect.height, 2.2) * compact;
        let px = Math.max(4.5, Math.min(basePx * ratio, 10.5));
        artEl.style.fontSize = `${px.toFixed(2)}px`;
        void artEl.offsetWidth;
        rect = artEl.getBoundingClientRect();
        if (rect.width > maxW || rect.height > maxH) {
          const fix = Math.min(maxW / rect.width, maxH / rect.height, 1);
          px = Math.max(4.5, px * fix);
          artEl.style.fontSize = `${px.toFixed(2)}px`;
          void artEl.offsetWidth;
        }
        const dx = anchorCenterX() - artVisualCenterX();
        artEl.style.transform = Math.abs(dx) > 0.5 ? `translateX(${dx.toFixed(2)}px)` : "";
      } else {
        const raw = Math.min(maxW / rect.width, maxH / rect.height, 2.4);
        if (!baseArtScale) baseArtScale = raw;
        const s = Math.min(baseArtScale * compact, 2.4);
        artEl.style.transform = `translateX(0px) scale(${s})`;
        void artEl.offsetWidth;
        const dx = anchorCenterX() - artVisualCenterX();
        artEl.style.transform = `translateX(${dx.toFixed(2)}px) scale(${s})`;
      }
      artEl.classList.add("splash-art-fitted");
    }

    function paintCanvas(now) {
      const elapsed = (now - crystalStart) / 1000;
      const w = canvas.width;
      const h = canvas.height;
      const fx = effects();

      if (phase === "crystal") {
        fx.drawStars(ctx, w, h, elapsed, 120);
        const holding = isCrystalHold();
        fx.drawCrystalGlow(ctx, w, h, elapsed, holding);
        if (!holding && now - lastScanAt >= SCANLINE_MS) {
          scanY = (scanY + 1) % Math.max(h, 1);
          lastScanAt = now;
        }
        if (!holding) fx.drawScanline(ctx, w, h, scanY);
      } else {
        ctx.fillStyle = "#0F1117";
        ctx.fillRect(0, 0, w, h);
        if (phase === "dissolve") {
          const g = ctx.createRadialGradient(w * 0.5, h * 0.34, 0, w * 0.5, h * 0.34, w * 0.65);
          g.addColorStop(0, `rgba(95,95,255,${0.04 + 0.02 * Math.sin(elapsed * 1.1)})`);
          g.addColorStop(1, "rgba(15,17,23,0)");
          ctx.fillStyle = g;
          ctx.fillRect(0, 0, w, h);
        }
      }

      if (phase === "waiting" && bloomFrameIdx >= BLOOM_FRAMES()) {
        fx.drawAuroraGlow(ctx, w, h, elapsed);
        if (shockProgress > 0 && shockProgress < 1) {
          fx.drawShockwave(ctx, w, h, shockProgress);
          shockProgress += 0.018;
        }
      }

      if (!done) rafId = requestAnimationFrame(paintCanvas);
    }

    function renderArt(lines) {
      let src = lines || (engine ? engine.artLines() : null);
      if (!src || !src.length) {
        if (window.C4_SPLASH_FINAL) {
          src = window.C4_SPLASH_FINAL(ART_H);
        } else {
          return;
        }
      }

      c4rStartRow = effects().findC4RStart(src);
      if (!aurora || aurora.c4rStartRow !== c4rStartRow) {
        aurora = new (effects().BioAurora)(c4rStartRow);
      }

      let display = src;
      if (phase === "waiting" && bloomFrameIdx < BLOOM_FRAMES()) {
        const cells = engine && engine.c4rCells ? engine.c4rCells : [];
        const baseRevealed = engine && engine.c4rAssemblyComplete ? cells.length : 0;
        display = effects().bloomFrame(src, bloomFrameIdx, BLOOM_FRAMES(), c4rStartRow, cells, {
          baseRevealed,
        });
      }

      const phaseColor = engine ? engine.colorForPhase() : "#8b7cf8";
      const useAurora = phase === "waiting" && bloomFrameIdx >= BLOOM_FRAMES();
      const crystalHold = isCrystalHold();
      if (useAurora) {
        aurora.tick((performance.now() - crystalStart) / 1000);
      }

      artEl.innerHTML = effects().renderColoredLines(display, {
        phase,
        phaseColor,
        c4rStartRow,
        aurora,
        useAurora,
        crystalHold,
        compactC4R: isMobileSplash(),
      });

      requestAnimationFrame(() => requestAnimationFrame(fitArt));
    }

    function renderText(now) {
      const tx = buildTextLines(phase, phaseStart, crystalStart, now, isLaunchReady());
      let mottoHtml = "";
      if (tx.motto && typeof tx.motto === "object") {
        mottoHtml = `<span class="splash-motto-muted">${effects().esc(tx.motto.d)}</span><span class="splash-motto-accent">${effects().esc(tx.motto.inv)}</span><span class="splash-motto-shift">${effects().esc(tx.motto.sh)}</span><span class="splash-motto-muted">${effects().esc(tx.motto.sp)}</span><span class="splash-motto-paradigm">${effects().esc(tx.motto.par)}</span>`;
      }
      textEl.innerHTML = `
        <p class="splash-line splash-subtitle">${effects().esc(tx.subtitle)}</p>
        <p class="splash-line splash-tagline-caps">${effects().esc(tx.tagline)}</p>
        <p class="splash-line splash-motto">${mottoHtml}</p>
        <p class="splash-line splash-version">${effects().esc(tx.version)}</p>
        <p class="splash-line splash-spacer"></p>
        <p class="splash-line splash-status">${effects().esc(tx.status)}</p>
        <p class="splash-line splash-footer">${effects().esc(tx.footer)}</p>
        <p class="splash-line splash-easter">${effects().esc(tx.easter)}</p>
      `;
      updateActionButton();
      updateCrystalHud(now);
      requestAnimationFrame(() => requestAnimationFrame(fitArt));
    }

    function onPhase(p) {
      phase = p;
      phaseStart = performance.now();
      setPhaseClass(p);
      if (p === "waiting") {
        bloomFrameIdx = 0;
        readyToLaunch = false;
        shockProgress = 0.05;
      }
      if (p === "dissolve" || p === "waiting") {
        artEl.classList.add("splash-art-compact");
        animateCompactScale();
      } else {
        artEl.classList.remove("splash-art-compact");
        compactAnim = 1;
      }
      renderArt();
      renderText(performance.now());
    }

    function onPulse() {
      const now = performance.now();
      if (phase === "waiting") {
        if (bloomFrameIdx < BLOOM_FRAMES()) {
          bloomFrameIdx++;
          renderArt();
        } else {
          if (!readyToLaunch) {
            readyToLaunch = true;
            shockProgress = 0.12;
          }
          renderArt();
        }
      }
      renderText(now);
    }

    function dismiss() {
      if (engine) engine.stop();
      timers.forEach(clearInterval);
      if (rafId) cancelAnimationFrame(rafId);
      overlay.classList.add("splash-out");
      document.body.classList.remove("splash-active");
      markSeen();
      setTimeout(() => overlay.remove(), 500);
    }

    function end() {
      if (done) return;
      done = true;
      dismiss();
      window.removeEventListener("resize", resize);
      document.removeEventListener("keydown", onKey);
    }

    function showFinalState() {
      engine = new window.C4SplashEngine({
        artHeight: ART_H,
        onFrame: () => renderArt(),
        onPhase: (p) => onPhase(p),
      });
      engine._prepareForms();
      engine.phase = "waiting";
      engine.morphLines = [...engine.finalForm];
      phase = "waiting";
      bloomFrameIdx = BLOOM_FRAMES();
      readyToLaunch = true;
      shockProgress = 0.12;
      phaseStart = performance.now() - 3000;
      setPhaseClass("waiting");
      artEl.classList.add("splash-art-compact");
      compactAnim = ART_COMPACT_MUL;
      renderArt(engine.finalForm);
      renderText(performance.now());
    }

    function jumpToFinal() {
      if (!engine) return;
      engine.jumpToFinal();
      bloomFrameIdx = BLOOM_FRAMES();
      readyToLaunch = true;
      shockProgress = 0.15;
      phaseStart = performance.now() - 2500;
      renderArt();
      renderText(performance.now());
    }

    function onAdvance() {
      if (isLaunchReady()) {
        end();
        return;
      }
      if (phase !== "waiting") jumpToFinal();
    }

    function onKey(e) {
      if (done) return;
      if (isLaunchReady()) {
        if (e.key === "Enter") end();
        return;
      }
      if (phase !== "waiting") onAdvance();
    }

    function resize() {
      baseArtScale = 0;
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      fitArt();
    }

    skipBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      onAdvance();
    });
    overlay.addEventListener("click", (e) => {
      if (e.target === skipBtn) return;
      if (isLaunchReady()) {
        if (isTouchSplash()) end();
        return;
      }
      if (phase !== "waiting") onAdvance();
    });
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", resize);
    resize();
    rafId = requestAnimationFrame(paintCanvas);

    timers.push(setInterval(onPulse, PULSE_MS()));
    timers.push(setInterval(() => {
      const now = performance.now();
      renderText(now);
      updateCrystalHud(now);
    }, 50));

    // Never auto-skip to final. The only ways to reach the final state are:
    // - play through the splash animation
    // - user explicitly taps/clicks "Skip →"
    //
    // We still *respect* reduced motion by shortening the crystal hold to near-zero
    // (engine timing stays deterministic, just much faster visually).
    if (reduced) {
      window.C4_SPLASH_CRYSTAL_HOLD_MS = Math.min(window.C4_SPLASH_CRYSTAL_HOLD_MS || 3000, 250);
      window.C4_SPLASH_CRYSTAL_MS = Math.min(window.C4_SPLASH_CRYSTAL_MS || 5500, 1200);
    }

    engine = new window.C4SplashEngine({
      artHeight: ART_H,
      onFrame: () => renderArt(),
      onPhase: (p) => onPhase(p),
    });
    crystalStart = performance.now();
    engine.start();
    phase = engine.phase;
    setPhaseClass(phase);
    renderArt();
    renderText(performance.now());

    if (typeof applyLanguage === "function") applyLanguage(window.c4rCurrentLang || "en");
    updateActionButton();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
