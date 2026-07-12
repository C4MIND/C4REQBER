/**
 * c4reqber web splash — TUI v9 port (crystal → dissolve → waiting + bottom captions).
 */
(function () {
  const SEEN_KEY = "c4r_splash_seen";
  const VERSION = "v5.6.0";
  const BLOOM_FRAMES = 12;
  const PULSE_MS = 600;
  const TEXT_MS = 50;

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

  function bloomFrame(artLines, frame, total) {
    if (total <= 0 || frame >= total) return artLines;
    const t = 1 - Math.pow(1 - frame / total, 3);
    const fringe = ["░", "▒", "░", "░", "▒"];
    const centerLine = Math.floor(artLines.length / 2);
    return artLines.map((line, i) => {
      const plain = [...line];
      const plainLen = plain.length;
      if (!plainLen) return line;
      const center = Math.floor(plainLen / 2);
      const dist = Math.abs(i - centerLine);
      const revealLines = Math.floor(t * (artLines.length + 1));
      if (dist > revealLines) return " ".repeat(plainLen);
      let maxR = Math.floor(t * (plainLen + 1));
      if (frame > total - 3) maxR += 2;
      return plain
        .map((ch, j) => {
          const dc = Math.abs(j - center);
          if (dc <= maxR) return ch;
          if (dc <= maxR + 3 && (j + i + frame) % 4 !== 0) return fringe[(j + i + frame) % fringe.length];
          return " ";
        })
        .join("");
    });
  }

  function colorizeLine(line, phase) {
    if (phase === "crystal") return `<span class="splash-ch-crystal">${esc(line)}</span>`;
    const isC4R = line.includes("111");
    if (isC4R) return `<span class="splash-ch-c4r">${esc(line)}</span>`;
    if (line.trim()) return `<span class="splash-ch-cube">${esc(line)}</span>`;
    return esc(line);
  }

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function buildTextLines(phase, phaseStart, crystalStart, now) {
    const sub1 = t("splash_subtitle_1", "Creative & Destructive Insights");
    const sub2 = t("splash_subtitle_2", "At Your Fingertips");
    const fullSub = `${sub1}  ·  ${sub2}`;
    const phaseElapsed = (now - phaseStart) / 1000;
    const crystalElapsed = (now - crystalStart) / 1000;

    let subtitle = "";
    if (phase === "crystal") subtitle = "";
    else {
      const cut = Math.floor(phaseElapsed / 0.003);
      subtitle = cut < fullSub.length ? fullSub.slice(0, cut) : fullSub;
    }

    const showTagline =
      phase === "waiting" || (phase === "dissolve" && phaseElapsed > 0.25);
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

    const showVersion =
      phase === "waiting" || (phase === "dissolve" && phaseElapsed > 0.5);
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
      status = `${t("splash_status_ready", "✨ ready")} ${sepBlink} ${t("splash_status_launch", "press any key to launch")}`;
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

  function dismiss(overlay, engine, timers) {
    if (engine) engine.stop();
    timers.forEach(clearInterval);
    overlay.classList.add("splash-out");
    document.body.classList.remove("splash-active");
    markSeen();
    setTimeout(() => overlay.remove(), 500);
  }

  function init() {
    if (!shouldShow() || !window.C4_SPLASH_ART || !window.C4SplashEngine) return;

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
    let done = false;
    let engine = null;

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      const w = artEl.scrollWidth;
      const vw = window.innerWidth * 0.96;
      if (w > vw && w > 0) {
        const s = vw / w;
        artEl.style.transform = `scale(${s})`;
      } else {
        artEl.style.transform = "";
      }
    }

    function aurora(now) {
      const t = (now - crystalStart) / 1000;
      const w = canvas.width;
      const h = canvas.height;
      ctx.fillStyle = "#0F1117";
      ctx.fillRect(0, 0, w, h);
      if (phase === "waiting" && bloomFrameIdx >= BLOOM_FRAMES) {
        const g = ctx.createRadialGradient(w * 0.5, h * 0.35, 0, w * 0.5, h * 0.35, w * 0.7);
        g.addColorStop(0, `rgba(74,222,128,${0.06 + 0.03 * Math.sin(t * 0.7)})`);
        g.addColorStop(0.45, `rgba(95,175,255,${0.04 + 0.02 * Math.cos(t)})`);
        g.addColorStop(1, `rgba(15,17,23,0)`);
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, w, h);
      }
      if (!done) requestAnimationFrame(aurora);
    }
    requestAnimationFrame(aurora);
    window.addEventListener("resize", resize);

    function renderArt(lines) {
      const display =
        phase === "waiting" && bloomFrameIdx < BLOOM_FRAMES
          ? bloomFrame(lines, bloomFrameIdx, BLOOM_FRAMES)
          : lines;
      artEl.innerHTML = display.map((l) => colorizeLine(l, phase)).join("\n");
      artEl.style.setProperty("--splash-phase-color", engine ? engine.colorForPhase() : "#5f5fff");
      requestAnimationFrame(resize);
    }

    function renderText(now) {
      const tx = buildTextLines(phase, phaseStart, crystalStart, now);
      let mottoHtml = "";
      if (tx.motto && typeof tx.motto === "object") {
        mottoHtml = `<span class="splash-motto-muted">${esc(tx.motto.d)}</span><span class="splash-motto-accent">${esc(tx.motto.inv)}</span><span class="splash-motto-shift">${esc(tx.motto.sh)}</span><span class="splash-motto-muted">${esc(tx.motto.sp)}</span><span class="splash-motto-paradigm">${esc(tx.motto.par)}</span>`;
      }
      textEl.innerHTML = `
        <p class="splash-line splash-subtitle">${esc(tx.subtitle)}</p>
        <p class="splash-line splash-tagline-caps">${esc(tx.tagline)}</p>
        <p class="splash-line splash-motto">${mottoHtml}</p>
        <p class="splash-line splash-version">${esc(tx.version)}</p>
        <p class="splash-line splash-spacer"></p>
        <p class="splash-line splash-status">${esc(tx.status)}</p>
        <p class="splash-line splash-footer">${esc(tx.footer)}</p>
        <p class="splash-line splash-easter">${esc(tx.easter)}</p>
      `;
    }

    function onPhase(p) {
      phase = p;
      phaseStart = performance.now();
      if (engine) renderArt(engine.artLines());
      if (p === "waiting" && bloomFrameIdx < BLOOM_FRAMES) {
        bloomFrameIdx = 0;
        const pulse = setInterval(() => {
          if (bloomFrameIdx < BLOOM_FRAMES) {
            bloomFrameIdx++;
            renderArt(engine.artLines());
          }
        }, PULSE_MS);
        timers.push(pulse);
      }
    }

    function end() {
      if (done) return;
      done = true;
      dismiss(overlay, engine, timers);
      window.removeEventListener("resize", resize);
      document.removeEventListener("keydown", onKey);
    }

    function jumpToFinal() {
      if (!engine) return;
      bloomFrameIdx = BLOOM_FRAMES;
      engine.jumpToFinal();
      phase = "waiting";
      phaseStart = performance.now() - 2500;
      renderArt(engine.artLines());
      renderText(performance.now());
    }

    function onAdvance() {
      if (phase !== "waiting") {
        jumpToFinal();
        return;
      }
      end();
    }

    function onSkipButton() {
      if (phase !== "waiting") {
        jumpToFinal();
        return;
      }
      end();
    }

    function onKey(e) {
      if (done) return;
      onAdvance();
    }

    skipBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      onSkipButton();
    });
    overlay.addEventListener("click", (e) => {
      if (e.target === skipBtn) return;
      onAdvance();
    });
    document.addEventListener("keydown", onKey);

    if (reduced) {
      const finalLines = window.C4_SPLASH_FINAL(40);
      artEl.innerHTML = finalLines.map((l) => colorizeLine(l, "waiting")).join("\n");
      phase = "waiting";
      phaseStart = performance.now();
      renderText(performance.now());
      resize();
      const textLoop = setInterval(() => renderText(performance.now()), TEXT_MS);
      timers.push(textLoop);
      return;
    }

    engine = new window.C4SplashEngine({
      artHeight: 40,
      onFrame: (lines) => renderArt(lines),
      onPhase: (p) => onPhase(p),
    });
    engine.start();
    phase = engine.phase;
    crystalStart = performance.now();

    if (hasSeenBefore()) {
      jumpToFinal();
    }

    const textLoop = setInterval(() => renderText(performance.now()), TEXT_MS);
    timers.push(textLoop);

    const watchWaiting = setInterval(() => {
      if (engine.phase === "waiting") {
        phase = "waiting";
        renderArt(engine.artLines());
      }
    }, 200);
    timers.push(watchWaiting);

    if (typeof applyLanguage === "function") {
      applyLanguage(window.c4rCurrentLang || "en");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
