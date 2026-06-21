// ═══════════════════════════════════════════════════════
// Shared Components — Header, Footer, Nav
// ═══════════════════════════════════════════════════════

const SITE_NAV = [
  { label: 'Home',        path: './index.html',         id: 'nav-home' },
  { label: 'Theory',      path: './theory/index.html',  id: 'nav-theory' },
  { label: 'Architecture',path: './architecture/index.html', id: 'nav-architecture' },
  { label: 'Docs',        path: './docs/index.html',    id: 'nav-docs' },
  { label: 'API',         path: './api/index.html',     id: 'nav-api' },
  { label: 'Showcase',    path: './showcase/index.html',id: 'nav-showcase' },
];

function getBasePath() {
  const script = document.querySelector('script[src*="components.js"]');
  if (!script) return './';
  const src = script.getAttribute('src');
  // src is like ../js/components.js or ../../js/components.js
  // Project root relative to current page = src with js/components.js stripped
  return src.replace(/js\/components\.js$/, '');
}

function resolvePath(relative) {
  const base = getBasePath();
  return base + relative.replace(/^\.\//, '');
}

function injectHeader() {
  const current = window.location.pathname;
  const base = getBasePath();

  const navItems = SITE_NAV.map(item => {
    const href = item.path.replace(/^\.\//, base);
    const itemPath = item.path.replace(/^\.\//, '');
    const isActive = current === '/' + itemPath || current.startsWith('/' + itemPath) || (item.path === './index.html' && (current === '/' || current === '/index.html'));
    return `<a href="${href}" class="nav-link${isActive ? ' active' : ''}" data-nav-id="${item.id}" data-i18n="${item.id.replace('nav-', 'nav_')}">${item.label}</a>`;
  }).join('');

  const headerHTML = `
<header class="site-header">
  <div class="navbar">
    <div class="navbar-inner">
      <a href="${base}" class="navbar-brand">c4<span>reqber</span></a>
      <button class="hamburger" aria-label="Toggle menu" aria-expanded="false"><span></span><span></span><span></span></button>
      <nav class="navbar-links" aria-label="Main navigation">
        ${navItems}
      </nav>
      <div style="display:flex;align-items:center;gap:8px">
        <div class="lang-switcher" style="display:flex;gap:4px;align-items:center">
          <button class="lang-btn" data-lang="en" aria-label="English">EN</button>
          <button class="lang-btn" data-lang="ru" aria-label="Русский">RU</button>
          <button class="lang-btn" data-lang="zh" aria-label="中文">ZH</button>
          <button class="lang-btn" data-lang="ja" aria-label="日本語">JA</button>
          <button class="lang-btn" data-lang="de" aria-label="Deutsch">DE</button>
          <button class="lang-btn" data-lang="ar" aria-label="العربية">AR</button>
          <button class="lang-btn" data-lang="hi" aria-label="हिन्दी">HI</button>
        </div>
        <button class="theme-toggle" id="theme-toggle" aria-label="Toggle dark mode" title="Toggle dark/light">&#127769;</button>
      </div>
    </div>
  </div>
</header>`;

  const container = document.getElementById('site-header') || document.body;
  if (container === document.body) {
    const div = document.createElement('div');
    div.id = 'site-header';
    div.innerHTML = headerHTML;
    document.body.insertBefore(div, document.body.firstChild);
  } else {
    container.innerHTML = headerHTML;
  }

  // Hamburger toggle
  const hamburger = document.querySelector('.hamburger');
  const navLinks = document.querySelector('.navbar-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', function() {
      const expanded = this.getAttribute('aria-expanded') === 'true';
      this.setAttribute('aria-expanded', !expanded);
      navLinks.classList.toggle('open');
    });
    document.querySelectorAll('.navbar-links a').forEach(a => {
      a.addEventListener('click', () => {
        navLinks.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('click', e => {
      if (!navLinks.contains(e.target) && !hamburger.contains(e.target)) {
        navLinks.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      }
    });
  }
}

function injectMascot() {
  if (document.getElementById('mascot')) return;
  const div = document.createElement('div');
  div.id = 'mascot';
  div.innerHTML = `<pre id="mascot-art" style="margin:0;line-height:1.2;font-size:10px;letter-spacing:1px">   ┌─────────┐
  ╱         ╱│
 ┌─────────┐ │
 │  C4R    │ │
 │  ███     ╱
 └─────────┘  </pre><div id="mascot-comment" style="margin-top:4px;font-size:10px;color:#8088a8;max-width:140px">Ready.</div>`;
  document.body.appendChild(div);
}

function injectFooter() {
  const base = getBasePath();
  const footerHTML = `
<footer class="footer">
  <div class="container">
    <div style="display:flex;justify-content:center;gap:24px;margin-bottom:16px;flex-wrap:wrap">
      <a href="${base}docs/getting-started.html" class="footer-link" data-i18n="footer_quickstart">Quickstart</a>
      <a href="https://gitlab.com/cognitive-functors/turbo-cdi" class="footer-link" rel="noopener noreferrer" target="_blank">GitLab</a>
      <a href="${base}docs/setup/gpu.html" class="footer-link" data-i18n="footer_gpu">GPU Setup</a>
      <a href="${base}showcase/index.html" class="footer-link" data-i18n="footer_showcase">Showcase</a>
    </div>
    <p>c4reqber v5.6.0 + TUI v9.13.0 · <a href="https://gitlab.com/cognitive-functors/turbo-cdi" rel="noopener noreferrer" target="_blank">GitLab</a> · <a href="${base}docs/index.html" rel="noopener noreferrer" data-i18n="footer_docs">Docs</a> · AGPL-3.0</p>
    <p style="margin-top:8px" data-i18n="footer_slogan">Think. Simulate. Prove. Discover.</p>
  </div>
</footer>`;

  const container = document.getElementById('site-footer');
  if (container) container.innerHTML = footerHTML;
}

function injectShared() {
  injectHeader();
  injectFooter();
  injectMascot();
}

// Auto-inject on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectShared);
} else {
  injectShared();
}
