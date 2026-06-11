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

// ── Push notifications ────────────────────────────────────────────────────
const PUSH_ICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 192 192'%3E%3Crect width='192' height='192' rx='32' fill='%2304040f'/%3E%3Cdefs%3E%3ClinearGradient id='g1' x1='0' y1='0' x2='192' y2='192' gradientUnits='userSpaceOnUse'%3E%3Cstop offset='0%25' stop-color='%234f6eff'/%3E%3Cstop offset='50%25' stop-color='%238855ff'/%3E%3Cstop offset='100%25' stop-color='%23ffd700'/%3E%3C/linearGradient%3E%3C/defs%3E%3Ccircle cx='96' cy='96' r='80' stroke='url(%23g1)' stroke-width='6' fill='none' opacity='.5'/%3E%3Ccircle cx='96' cy='96' r='56' stroke='url(%23g1)' stroke-width='4' fill='none' opacity='.3'/%3E%3Ccircle cx='96' cy='96' r='28' fill='url(%23g1)' opacity='.9'/%3E%3Cline x1='96' y1='8' x2='96' y2='36' stroke='url(%23g1)' stroke-width='6' stroke-linecap='round'/%3E%3Cline x1='96' y1='156' x2='96' y2='184' stroke='url(%23g1)' stroke-width='6' stroke-linecap='round'/%3E%3Cline x1='8' y1='96' x2='36' y2='96' stroke='url(%23g1)' stroke-width='6' stroke-linecap='round'/%3E%3Cline x1='156' y1='96' x2='184' y2='96' stroke='url(%23g1)' stroke-width='6' stroke-linecap='round'/%3E%3C/svg%3E";

self.addEventListener('push', event => {
  let data = { title: 'PREDIKTA', body: 'Nouveaux résultats disponibles !' };
  try { if (event.data) data = event.data.json(); } catch (e) {}
  event.waitUntil(
    self.registration.showNotification(data.title || 'PREDIKTA', {
      body:    data.body || '',
      icon:    PUSH_ICON,
      badge:   PUSH_ICON,
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
