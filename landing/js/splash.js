/**
 * c4reqber web splash — inspired by TUI v9 crystal→aurora→fade.
 * Skip: button, Escape, click backdrop, any key. Respects prefers-reduced-motion.
 */
(function () {
  const STORAGE_KEY = "c4r_splash_seen";
  const DURATION_MS = 3200;

  const CUBE_FRAMES = [
    `   ┌─────────┐\n  ╱         ╱│\n ┌─────────┐ │\n │  C4R    │ │\n │  ███     ╱\n └─────────┘`,
    `   ┌─────────┐\n  ╱    ▓    ╱│\n ┌─────────┐ │\n │  C4REQ  │ │\n │  ▓▓▓     ╱\n └─────────┘`,
    `   ┌─────────┐\n  ╱    ░    ╱│\n ┌─────────┐ │\n │  BER    │ │\n │  ░░░     ╱\n └─────────┘`,
  ];

  function shouldShow() {
    try {
      if (sessionStorage.getItem(STORAGE_KEY)) return false;
    } catch (_) {}
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return false;
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    return path === "" || path === "/" || path === "/index.html";
  }

  function t(key, fallback) {
    const lang = window.c4rCurrentLang || "en";
    const dict = (window.i18n && window.i18n[lang]) || (window.i18n && window.i18n.en) || {};
    return dict[key] || fallback;
  }

  function dismiss(overlay) {
    overlay.classList.add("splash-out");
    try {
      sessionStorage.setItem(STORAGE_KEY, "1");
    } catch (_) {}
    setTimeout(() => overlay.remove(), 500);
  }

  function init() {
    if (!shouldShow()) return;

    const overlay = document.createElement("div");
    overlay.id = "splash-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "c4reqber splash");
    overlay.innerHTML = `
      <canvas id="splash-canvas" aria-hidden="true"></canvas>
      <div class="splash-content">
        <pre id="splash-cube" aria-hidden="true"></pre>
        <p class="splash-tagline" data-i18n="splash_tagline">Cognitive exoskeleton for humans and AI agents</p>
        <p class="splash-motto" data-i18n="splash_motto">Shift paradigms</p>
      </div>
      <button type="button" class="splash-skip" id="splash-skip" data-i18n="splash_skip">Skip →</button>
    `;
    document.body.appendChild(overlay);
    document.body.classList.add("splash-active");

    const skipBtn = overlay.querySelector("#splash-skip");
    const cubeEl = overlay.querySelector("#splash-cube");
    const canvas = overlay.querySelector("#splash-canvas");
    const ctx = canvas.getContext("2d");

    let frame = 0;
    const cubeInterval = setInterval(() => {
      cubeEl.textContent = CUBE_FRAMES[frame % CUBE_FRAMES.length];
      frame++;
    }, 400);

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    let start = performance.now();
    function aurora(now) {
      const t = (now - start) / 1000;
      const w = canvas.width;
      const h = canvas.height;
      const g = ctx.createLinearGradient(0, 0, w, h);
      g.addColorStop(0, `hsla(174, 62%, 45%, ${0.08 + 0.04 * Math.sin(t)})`);
      g.addColorStop(0.5, `hsla(280, 70%, 50%, ${0.06 + 0.03 * Math.cos(t * 1.2)})`);
      g.addColorStop(1, `hsla(45, 90%, 55%, ${0.05 + 0.02 * Math.sin(t * 0.8)})`);
      ctx.fillStyle = "#0F1117";
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
      if (overlay.parentNode) requestAnimationFrame(aurora);
    }
    requestAnimationFrame(aurora);

    const end = () => {
      clearInterval(cubeInterval);
      document.body.classList.remove("splash-active");
      dismiss(overlay);
    };

    skipBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      end();
    });
    overlay.addEventListener("click", end);
    const onKey = (e) => {
      end();
      document.removeEventListener("keydown", onKey);
    };
    document.addEventListener("keydown", onKey);

    setTimeout(end, DURATION_MS);

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
