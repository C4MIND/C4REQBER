window.i18n = {};
window.i18nFallback = {"en":{"hero_badge":"v5.6.0 + TUI v9.13.0 · Open source","hero_subtitle":"The cognitive exoskeleton for <strong>humans and AI agents</strong>.<br>Think. Simulate. Prove. Discover.","hero_tags":"Z₃³ COGNITIVE EXOSKELETON · 27 STATES · 6 OPERATORS · 51+ SOURCES · 38 ENGINES · 21 MCP TOOLS · TUI v9 COCKPIT · O₀→O₁→O₂ OBSERVER · 23 MPs","hero_cta_primary":"pip install c4reqber","hero_cta_secondary":"GitLab","gitlab_badge":"GitLab","stat_states":"Cognitive States","stat_operators":"C4 Operators","stat_sources":"Knowledge Sources","stat_engines":"Simulation Engines","stat_mcp":"MCP Tools","stat_tests":"Tests Passing","fp_label":"First Principles","fp_title":"Agents Can Talk. But Can They Think?","fp_desc":"AI agents have language. They lack cognition. c4reqber is the scientific body for the agentic mind.","fp_no_sim":"No Simulation","fp_no_sim_desc":"LLMs generate hypotheses but cannot test them. No physics engine, no statistical validation, no ground truth.","fp_no_verify":"No Verification","fp_no_verify_desc":"ChatGPT \"proves\" theorems by generating convincing text. Formal verification requires Lean4, Coq, Dafny.","fp_no_cog":"No Blind-Spot Detection","fp_no_cog_desc":"Agents cannot recognize their own observational biases or identify gaps in their reasoning. c4reqber uses O₀→O₁ observer shifts to surface blind spots automatically.","fp_no_rigor":"No Scientific Rigor","fp_no_rigor_desc":"Falsifiability, real citations, reproducibility — the foundation of science. Absent from most agent frameworks.","fp_conclusion":"c4reqber solves all four. Formal verification + 36 simulation engines + Z₃³ cognitive topology + real citations + O₀→O₁→O₂ meta-cognitive observer.","features_label":"Capabilities","features_title":"The Only AI Cognitive Exoskeleton","features_desc":"Not features. Cognitive organs. Each module is a real implementation.","feat_c4":"Z₃³ Cognitive Topology","feat_c4_desc":"27 discrete cognitive states across Time, Scale, and Agency dimensions. Every query is mapped, tracked, and navigable.","feat_verify":"Formal Verification Engine","feat_verify_desc":"Lean4, Coq, Dafny, Agda, Z3, Hoare logic — your hypotheses don't just claim, they prove.","feat_sim":"36 Simulation Engines","feat_sim_desc":"Molecular dynamics (GROMACS, OpenMM), quantum (PySCF), CFD (OpenFOAM), neuro (NEURON), and more.","feat_kg":"43 Knowledge Sources","feat_kg_desc":"arXiv, PubMed, Semantic Scholar, OpenAlex, Europe PMC, Crossref, Zenodo, ClinicalTrials.gov, GBIF, NASA Earthdata, Materials Project, Kaggle, OpenFDA, ORCID, and 30 more. MultiSourceSearcher with circuit breaker and semantic dedup.","feat_pub":"Automated Dissertation Generator","feat_pub_desc":"LaTeX + BibTeX + Markdown + JSON + HTML exports. Citation verifier with hallucination detection. Ready for arXiv, bioRxiv, or peer review.","feat_mcp":"MCP Server — 21 Tools","feat_mcp_desc":"Expose full C4REQBER capability to AI agents. JSON Schema compliant. stdio JSON-RPC via blast serve --mcp.","nav_home":"Home","nav_theory":"Theory","nav_architecture":"Architecture","nav_docs":"Docs","nav_api":"API","nav_showcase":"Showcase","footer_quickstart":"Quickstart","footer_gpu":"GPU Setup","footer_showcase":"Showcase","footer_docs":"Docs","footer_slogan":"Think. Simulate. Prove. Discover.","breadcrumb_home":"Home","badge_live_demos":"Live Demos"}};

function getI18nPath() {
  const script = document.querySelector('script[src*="main.js"]');
  if (!script) return './i18n/';
  const src = script.getAttribute('src');
  const base = src.replace(/js\/main\.js$/, '');
  return base + 'i18n/';
}

async function loadTranslations(lang) {
  if (window.i18n[lang]) return;
  try {
    const base = getI18nPath();
    const res = await fetch(base + lang + '.json');
    if (!res.ok) throw new Error('Failed to load ' + lang);
    window.i18n[lang] = await res.json();
  } catch (e) {
    console.warn('i18n load failed for', lang, e);
    if (window.i18nFallback && window.i18nFallback[lang]) {
      window.i18n[lang] = window.i18nFallback[lang];
    } else if (window.i18nFallback && window.i18nFallback.en) {
      window.i18n[lang] = window.i18nFallback.en;
    } else if (lang !== 'en') {
      await loadTranslations('en');
    }
  }
}

async function ensureI18nBase(lang) {
  const tasks = [];
  if (!window.i18n.en) tasks.push(loadTranslations('en'));
  if (lang !== 'en' && !window.i18n[lang]) tasks.push(loadTranslations(lang));
  if (tasks.length) await Promise.all(tasks);
}

// ═══════════════════════════════════════════════════════
// i18n Engine — 7 languages
// ═══════════════════════════════════════════════════════
let currentLang = 'en';
try { currentLang = localStorage.getItem('c4r_lang') || 'en'; } catch (e) {}
window.c4rCurrentLang = currentLang;

function applyLanguage(lang) {
  currentLang = lang;
  window.c4rCurrentLang = lang;
  try { localStorage.setItem('c4r_lang', lang); } catch (e) {}
  if (!window.i18n.en || (lang !== 'en' && !window.i18n[lang])) {
    ensureI18nBase(lang).then(() => applyLanguage(lang));
    return;
  }
  const t = window.i18n[lang] || window.i18n.en || {};
  const en = window.i18n.en || {};
  const htmlKeys = new Set([
    'hero_subtitle','pip_scope_note','theory_phi_desc','disc_epistemic',
    'show_tui_sub','show_verified_desc','cl_use_desc','gs_next_gpu','gs_next_arch',
    'gs_next_api','gs_next_showcase','ref_notice',
    'keys_required_html','keys_llm_html','keys_search_html','keys_science_html',
    'keys_pending_html','keys_nokey_html','keys_full_html','keys_setup_note','gs_next_keys',
    'arch_reading_wp','footer_version',
    'theory_c4_state_000','theory_c4_state_111','theory_c4_state_222','theory_c4_operators_desc',
    'theory_cdi_step_1','theory_cdi_step_2','theory_cdi_step_3','theory_cdi_step_4','theory_cdi_step_5','theory_cdi_step_6',
    'theory_meta_th_1','theory_meta_th_2','theory_meta_th_3','theory_meta_th_4','theory_meta_th_5','theory_meta_th_6',
    'theory_proofs_agda','theory_proofs_lean4','theory_proofs_coq'
  ]);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const val = t[key] || en[key];
    if (!val) return;
    if (el.hasAttribute('data-i18n-html') || htmlKeys.has(key)) el.innerHTML = val;
    else el.textContent = val;
  });
  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const key = el.getAttribute('data-i18n-aria');
    const val = t[key] || en[key];
    if (val) el.setAttribute('aria-label', val);
  });
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    const val = t[key] || en[key];
    if (val) el.setAttribute('title', val);
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang === 'ja' ? 'ja-JP' : lang === 'ar' ? 'ar-SA' : lang === 'hi' ? 'hi-IN' : lang === 'ru' ? 'ru-RU' : lang === 'de' ? 'de-DE' : 'en';
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  const pageTitleKey = document.body && document.body.dataset.pageTitle;
  if (pageTitleKey && t[pageTitleKey]) document.title = t[pageTitleKey];
  const metaDesc = document.querySelector('meta[name="description"]');
  const metaKey = document.body && document.body.dataset.metaDesc;
  if (metaDesc) {
    const desc = (metaKey && t[metaKey]) || t.meta_desc_home;
    if (desc) metaDesc.setAttribute('content', desc);
  }
  document.querySelectorAll('[data-copy-btn]').forEach(btn => {
    if (!btn.dataset.copied) btn.textContent = t.btn_copy || 'copy';
  });
  const mascotComment = document.getElementById('mascot-comment');
  if (mascotComment && window.mascotComments) {
    const msgs = window.mascotComments[lang] || window.mascotComments.en;
    const idx = (typeof window.mascotCommentIndex === 'number') ? window.mascotCommentIndex : 0;
    mascotComment.textContent = msgs[idx % msgs.length];
  }
}

function initLangSwitcher() {
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => applyLanguage(btn.dataset.lang));
  });
}
window.applyLanguage = applyLanguage;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLangSwitcher);
} else {
  initLangSwitcher();
}

// GitLab repo links — primary remote only
(function(){
  const gitlabRepo = 'https://gitlab.com/cognitive-functors/c4reqber';
  document.querySelectorAll('a[href*="gitlab.com/c4reqber"]').forEach(a => {
    a.href = a.href.replace('https://gitlab.com/c4reqber/c4reqber', gitlabRepo);
  });
  document.querySelectorAll('#gitlab-badge,.gitlab-badge').forEach(el => {
    if (el.tagName === 'A') el.href = gitlabRepo;
  });
})();

// Scroll reveal animation with stagger
const revealObserver=new IntersectionObserver((entries)=>{entries.forEach(e=>{if(e.isIntersecting){let delay=0;if(!e.target.classList.contains('section-header')){delay=Array.from(e.target.parentElement.children).indexOf(e.target)*80}e.target.style.transitionDelay=delay+'ms';e.target.style.opacity='1';e.target.style.transform='translateY(0)';revealObserver.unobserve(e.target)}})},{threshold:.1});
document.querySelectorAll('.section-header,.feature-card,.stat-card,.term-block,.pricing-card').forEach(el=>{el.style.opacity='0';el.style.transform='translateY(20px)';el.style.transition='opacity .6s ease, transform .6s ease';revealObserver.observe(el)});

ensureI18nBase(currentLang).then(() => {
  applyLanguage(currentLang);
});

// Fix sticky table column offsets dynamically
function updateStickyOffsets(){
  document.querySelectorAll('.comp-table').forEach(table=>{
    const firstTh=table.querySelector('thead th:first-child');
    if(firstTh)table.style.setProperty('--sticky-2',firstTh.offsetWidth+'px');
  });
}
window.addEventListener('load',()=>setTimeout(updateStickyOffsets,100));
let resizeTimer;
window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(updateStickyOffsets,100);});

// Reading progress + back-to-top
const readProg=document.getElementById('read-progress');
const backTop=document.getElementById('back-to-top');
window.addEventListener('scroll',()=>{
  const scrolled=window.scrollY/(document.documentElement.scrollHeight-window.innerHeight);
  if(readProg)readProg.style.width=Math.min(scrolled*100,100)+'%';
  if(backTop){backTop.style.opacity=window.scrollY>500?'1':'0';backTop.style.pointerEvents=window.scrollY>500?'auto':'none'}
});
if(backTop)backTop.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));

function initThemeToggle(){
  const html=document.documentElement;
  const btn=document.getElementById('theme-toggle');
  if(!btn||btn.dataset.bound)return;
  btn.dataset.bound='1';
  function setTheme(t){html.setAttribute('data-theme',t);btn.innerHTML=t==='light'?'&#9728;':'&#127769;';try{localStorage.setItem('c4r_theme',t)}catch(e){}}
  let theme='dark';
  try{theme=localStorage.getItem('c4r_theme')||(window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark')}catch(e){}
  setTheme(theme);
  btn.addEventListener('click',()=>setTheme(html.getAttribute('data-theme')==='light'?'dark':'light'));
}
window.initThemeToggle = initThemeToggle;

// Copy buttons
document.querySelectorAll('[data-copy-btn]').forEach(btn=>{btn.addEventListener('click',()=>copyCode(btn))});

function copyCode(btn){
  const code=btn.parentElement.querySelector('code');
  if(!code)return;
  const t=(window.i18n&&window.i18n[window.c4rCurrentLang])||(window.i18n&&window.i18n.en)||{};
  navigator.clipboard.writeText(code.innerText).then(()=>{
    btn.dataset.copied='1';
    btn.textContent=t.btn_copied||'copied!';
    btn.classList.add('show-tooltip');
    setTimeout(()=>{
      btn.classList.remove('show-tooltip');
      btn.dataset.copied='';
      btn.textContent=t.btn_copy||'copy';
    },1200);
  }).catch(()=>{});
}

// blink animation for TUI cursor
const blinkStyle=document.createElement('style');
blinkStyle.textContent='@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}';
document.head.appendChild(blinkStyle);

// ═══════════════════════════════════════════════════════
// MASCOT — 3-frame ASCII cube with live i18n
// ═══════════════════════════════════════════════════════
(function(){
const frames=[
`   ┌─────────┐
  ╱         ╱│
 ┌─────────┐ │
 │  C4R    │ │
 │  ███     ╱
 └─────────┘  `,
`   ┌─────────┐
  ╱ ∿∿∿∿∿∿∿ ╱│
 ┌─────────┐ │
 │  C4R    │ │
 │  ◈◈◈     ╱
 └─────────┘  `,
`   ┌─────────┐
  ╱ ▓▓▓▓▓▓▓ ╱│
 ┌─────────┐ │
 │  C4R    │ │
 │  ███     ╱
 └─────────┘  `,
];
window.mascotComments={
  en:['Ready.','Thinking...','Processing...','Discovery!','All done.'],
  ru:['Готов.','Думаю...','Обработка...','Открытие!','Готово.'],
  zh:['就绪。','思考中...','处理中...','发现！','完成。'],
  ja:['準備完了。','考え中...','処理中...','発見！','完了。'],
  de:['Bereit.','Denke...','Verarbeite...','Entdeckung!','Fertig.'],
  ar:['جاهز.','يفكر...','يعالج...','اكتشاف!','تم.'],
  hi:['तैयार.','सोच रहा है...','प्रसंस्करण...','खोज!','पूर्ण।']
};
let f=0,c=0;
window.mascotCommentIndex=0;
function tickMascot(){
  const art=document.getElementById('mascot-art');
  const com=document.getElementById('mascot-comment');
  if(!art||!com) return; // mascot not injected yet
  f=(f+1)%frames.length;
  art.textContent=frames[f];
  let lang='en';
  try{lang=window.c4rCurrentLang||localStorage.getItem('c4r_lang')||'en';}catch(e){}
  const msgs=window.mascotComments[lang]||window.mascotComments.en;
  c=(c+1)%msgs.length;
  window.mascotCommentIndex=c;
  com.textContent=msgs[c];
}
// Wait for mascot injection before starting ticker
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',()=>{tickMascot();setInterval(tickMascot,3000);});
}else{
  tickMascot();setInterval(tickMascot,3000);
}
})();
