const CACHE_NAME = 'c4reqber-v2';
const CORE_ASSETS = [
  './',
  './index.html',
  './css/main.css',
  './js/main.js',
  './js/components.js',
  './404.html',
  './manifest.json',
  './theory/',
  './theory/index.html',
  './architecture/',
  './architecture/index.html',
  './docs/',
  './docs/index.html',
  './api/',
  './api/index.html',
  './showcase/',
  './showcase/index.html',

];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS))
  );
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
  e.respondWith(
    caches.match(e.request).then((cached) => {
      if (cached) return cached;
      return fetch(e.request).catch(() => {
        if (e.request.mode === 'navigate') return caches.match('./404.html');
      });
    })
  );
});
