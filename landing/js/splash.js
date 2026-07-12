/**
 * c4reqber web splash — TUI v9 port: morph engine + 600ms bio-aurora pulse.
 */
(function () {
  const SEEN_KEY = "c4r_splash_seen";
  const VERSION = "v5.6.0";
  const FX = () => window.C4SplashEffects;
  const BLOOM_FRAMES = () => FX().BLOOM_FRAMES;
  const PULSE_MS = () => FX().PULSE_MS;

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
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    return path === "" || path === "/" || path === "/index.html";
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
      const d = phaseElapsed > 0 ? "Discover.  " : "";
      const inv = phaseElapsed > 0.6 ? "Invent.  " : "";
      const sh = phaseElapsed > 1.2 ? "Shift" : "";
      const sp = phaseElapsed > 1.2 ? " " : "";
      const par = phaseElapsed > 1.2 ? "paradigms." : "";
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
      status = `${t("splash_status_boot", "booting")} ${window.C4_SPLASH_CRYSTAL_MS / 1000}s ${sepBlink} ${prog} ${sepBlink} ${t("splash_status_skip_hint", "click to skip to final")}`;
    } else if (phase === "dissolve") {
      status = `${t("splash_status_awakening", "◆ awakening cube state ◆")} ${sepBlink} ${t("splash_status_skip_hint", "click to skip to final")}`;
    } else if (phase === "waiting") {
      status = readyToLaunch
        ? t("splash_status_launch", "press Enter to launch")
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
    if (!shouldShow() || !window.C4_SPLASH_ART || !window.C4SplashEngine || !window.C4SplashEffects) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const overlay = document.createElement("div");
    overlay.id = "splash-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "c4reqber splash");
    overlay.innerHTML = `
      <canvas id="splash-canvas" aria-hidden="true"></canvas>
      <div class="splash-stage">
        <pre id="splash-art" aria-hidden="true"></pre>
      </div>
      <div class="splash-text" id="splash-text"></div>
      <button type="button" class="splash-skip" id="splash-skip" data-i18n="splash_skip">Skip →</button>
    `;
    document.body.appendChild(overlay);
    document.body.classList.add("splash-active");

    const artEl = overlay.querySelector("#splash-art");
    const textEl = overlay.querySelector("#splash-text");
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
    let done = false;
    let engine = null;
    let aurora = null;
    let readyToLaunch = false;
    let rafId = 0;
    let c4rStartRow = 9999;
    let artSized = false;

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

    function fitArt() {
      artEl.style.transform = "";
      const naturalW = artEl.scrollWidth;
      const naturalH = artEl.scrollHeight;
      if (!naturalW || !naturalH) return;
      const maxW = window.innerWidth * 0.98;
      const maxH = window.innerHeight * 0.58;
      const scale = Math.min(maxW / naturalW, maxH / naturalH, 2.2);
      if (Math.abs(scale - 1) > 0.02) {
        artEl.style.transform = `scale(${scale})`;
      }
      artSized = true;
    }

    function paintCanvas(now) {
      const elapsed = (now - crystalStart) / 1000;
      const w = canvas.width;
      const h = canvas.height;
      const fx = FX();

      if (phase === "crystal") {
        fx.drawStars(ctx, w, h, elapsed, 120);
        scanY = (scanY + 1) % Math.max(h, 1);
        fx.drawScanline(ctx, w, h, scanY);
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

    function colorizeLine(line, rowIdx, phaseColor) {
      const esc = FX().esc;
      if (phase === "crystal") {
        return `<span class="splash-ch-crystal" style="color:${phaseColor}">${esc(line)}</span>`;
      }
      if (phase === "dissolve") {
        return `<span class="splash-ch-dissolve" style="color:${phaseColor}">${esc(line)}</span>`;
      }
      if (phase === "waiting" && bloomFrameIdx >= BLOOM_FRAMES() && aurora) {
        return aurora.renderLine(line, rowIdx);
      }
      if (line.includes("111")) {
        return `<span class="splash-ch-c4r">${esc(line)}</span>`;
      }
      if (line.trim()) {
        return `<span class="splash-ch-cube">${esc(line)}</span>`;
      }
      return esc(line);
    }

    function renderArt(lines) {
      const src = lines || (engine ? engine.artLines() : null);
      if (!src || !src.length) return;

      c4rStartRow = FX().findC4RStart(src);
      if (!aurora || aurora.c4rStartRow !== c4rStartRow) {
        aurora = new FX().BioAurora(c4rStartRow);
      }

      let display = src;
      if (phase === "waiting" && bloomFrameIdx < BLOOM_FRAMES()) {
        display = FX().bloomFrame(src, bloomFrameIdx, BLOOM_FRAMES());
      }

      const phaseColor = engine ? engine.colorForPhase() : "#4ade80";
      artEl.innerHTML = display.map((l, i) => colorizeLine(l, i, phaseColor)).join("\n");
      artEl.style.setProperty("--splash-phase-color", phaseColor);
      if (!artSized) fitArt();
    }

    function renderText(now) {
      const tx = buildTextLines(phase, phaseStart, crystalStart, now, isLaunchReady());
      let mottoHtml = "";
      if (tx.motto && typeof tx.motto === "object") {
        mottoHtml = `<span class="splash-motto-muted">${FX().esc(tx.motto.d)}</span><span class="splash-motto-accent">${FX().esc(tx.motto.inv)}</span><span class="splash-motto-shift">${FX().esc(tx.motto.sh)}</span><span class="splash-motto-muted">${FX().esc(tx.motto.sp)}</span><span class="splash-motto-paradigm">${FX().esc(tx.motto.par)}</span>`;
      }
      textEl.innerHTML = `
        <p class="splash-line splash-subtitle">${FX().esc(tx.subtitle)}</p>
        <p class="splash-line splash-tagline-caps">${FX().esc(tx.tagline)}</p>
        <p class="splash-line splash-motto">${mottoHtml}</p>
        <p class="splash-line splash-version">${FX().esc(tx.version)}</p>
        <p class="splash-line splash-spacer"></p>
        <p class="splash-line splash-status">${FX().esc(tx.status)}</p>
        <p class="splash-line splash-footer">${FX().esc(tx.footer)}</p>
        <p class="splash-line splash-easter">${FX().esc(tx.easter)}</p>
      `;
      updateActionButton();
    }

    function onPhase(p) {
      phase = p;
      phaseStart = performance.now();
      artSized = false;

      if (p === "waiting") {
        bloomFrameIdx = 0;
        readyToLaunch = false;
        shockProgress = 0.05;
      }

      renderArt();
      fitArt();
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
          if (aurora) aurora.tick((now - crystalStart) / 1000);
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

    function jumpToFinal() {
      if (!engine) return;
      engine.jumpToFinal();
      bloomFrameIdx = BLOOM_FRAMES();
      readyToLaunch = true;
      shockProgress = 0.15;
      phaseStart = performance.now() - 2500;
      if (aurora) aurora.tick((performance.now() - crystalStart) / 1000);
      renderArt();
      fitArt();
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
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      artSized = false;
      fitArt();
    }

    skipBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      onAdvance();
    });
    overlay.addEventListener("click", (e) => {
      if (e.target === skipBtn) return;
      if (isLaunchReady()) return;
      if (phase !== "waiting") onAdvance();
    });
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", resize);
    resize();
    rafId = requestAnimationFrame(paintCanvas);

    timers.push(setInterval(() => onPulse(), PULSE_MS()));
    timers.push(setInterval(() => renderText(performance.now()), 50));

    if (reduced) {
      const finalLines = window.C4_SPLASH_FINAL(40);
      c4rStartRow = FX().findC4RStart(finalLines);
      aurora = new FX().BioAurora(c4rStartRow);
      bloomFrameIdx = BLOOM_FRAMES();
      phase = "waiting";
      phaseStart = performance.now() - 2500;
      readyToLaunch = true;
      renderArt(finalLines);
      fitArt();
      renderText(performance.now());
      if (typeof applyLanguage === "function") applyLanguage(window.c4rCurrentLang || "en");
      return;
    }

    engine = new window.C4SplashEngine({
      artHeight: 40,
      onFrame: () => renderArt(),
      onPhase: (p) => onPhase(p),
    });
    crystalStart = performance.now();
    engine.start();
    phase = engine.phase;

    if (hasSeenBefore()) jumpToFinal();

    if (typeof applyLanguage === "function") applyLanguage(window.c4rCurrentLang || "en");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
