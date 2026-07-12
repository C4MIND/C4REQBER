const CACHE_NAME = 'c4reqber-v5';
const CORE_ASSETS = [
  './',
  './index.html',
  './css/main.css',
  './js/main.js',
  './js/components.js',
  './js/splash-art.js',
  './js/splash-effects.js',
  './js/splash-engine.js',
  './js/splash.js',
  './404.html',
  './manifest.json',
  './discoveries/',
  './discoveries/index.html',
  './showcase/',
  './showcase/index.html',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  const isNavigate = e.request.mode === 'navigate';
  const isHtml = e.request.destination === 'document' || isNavigate;
  const isI18n = url.pathname.includes('/i18n/');

  if (isHtml || isI18n) {
    // Network-first for HTML and translations — fresh deploys visible immediately
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(e.request, clone));
          return res;
        })
        .catch(() => caches.match(e.request).then((r) => r || caches.match('./404.html')))
    );
    return;
  }

  // Cache-first for static assets (css, js, images)
  e.respondWith(
    caches.match(e.request).then(
      (cached) =>
        cached ||
        fetch(e.request).then((res) => {
          if (res.ok && e.request.method === 'GET') {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(e.request, clone));
          }
          return res;
        })
    )
  );
});
