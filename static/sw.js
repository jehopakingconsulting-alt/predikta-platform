/**
 * PREDIKTA — Service Worker v2.0
 * Offline cache for PWA installability
 */

const CACHE_NAME = 'predikta-v2';
const OFFLINE_URL = '/offline';

const PRECACHE = [
  '/',
  '/results',
  '/pro',
  '/about',
  '/faq',
  '/contact',
  '/offline',
  '/nav.js',
  '/manifest.json',
];

// ── Install: precache shell ──────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE))
  );
  self.skipWaiting();
});

// ── Activate: purge old caches ───────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: network-first with offline fallback ───────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  // API calls: network only (no cache)
  if (url.pathname.startsWith('/api/')) return;

  event.respondWith(
    fetch(request)
      .then(response => {
        // Cache successful responses for navigation requests
        if (response.ok && request.mode === 'navigate') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      })
      .catch(() =>
        caches.match(request).then(cached => {
          if (cached) return cached;
          if (request.mode === 'navigate') return caches.match(OFFLINE_URL);
          return new Response('Offline', { status: 503 });
        })
      )
  );
});

// ── Background sync: queue scrape when back online ───────────────────────
self.addEventListener('sync', event => {
  if (event.tag === 'sync-results') {
    event.waitUntil(
      fetch('/api/scrape?state=NY&months=1').catch(() => {})
    );
  }
});

// ── Push notifications (placeholder) ────────────────────────────────────
self.addEventListener('push', event => {
  const data = event.data?.json() || { title: 'PREDIKTA', body: 'Nouveaux résultats disponibles !' };
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body:    data.body,
      icon:    '/manifest.json',
      badge:   '/manifest.json',
      vibrate: [200, 100, 200],
      data:    { url: data.url || '/results' },
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data?.url || '/results')
  );
});
