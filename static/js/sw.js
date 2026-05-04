/**
 * EventPro Service Worker
 * Enables offline scanning by caching the scanner shell + registration data
 */

const CACHE_NAME = 'wristbandsng-scanner-v1';
const SHELL_ASSETS = [
  '/static/css/scanner-pwa.css',
  '/static/js/scanner-pwa.js',
  'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap',
];

// Install – cache shell assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL_ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

// Activate – clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch – serve shell from cache, pass API calls through
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Always network-first for scan API and stats
  if (url.pathname.includes('/scan/') || url.pathname.includes('/stats/') || url.pathname.includes('/offline-registrations/')) {
    event.respondWith(fetch(event.request).catch(() => new Response('{"status":"offline"}', { headers: { 'Content-Type': 'application/json' } })));
    return;
  }

  // Cache-first for static assets
  if (url.pathname.startsWith('/static/') || url.hostname.includes('jsdelivr') || url.hostname.includes('googleapis')) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request).then(resp => {
        const clone = resp.clone();
        caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        return resp;
      }))
    );
    return;
  }

  // PWA scanner page – serve from cache if offline
  if (url.pathname.includes('/pwa/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  }
});

// Background sync – flush queued check-ins when back online
self.addEventListener('sync', event => {
  if (event.tag === 'flush-checkins') {
    event.waitUntil(flushQueue());
  }
});

async function flushQueue() {
  // Notify all clients to flush their queue
  const clients = await self.clients.matchAll();
  clients.forEach(c => c.postMessage({ type: 'FLUSH_QUEUE' }));
}
