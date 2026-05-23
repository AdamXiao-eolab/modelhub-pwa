// ModelHub Service Worker — basic offline + cache-first
const CACHE = 'modelhub-v1';
const PRECACHE = [
  '/index.html',
  '/pricing.html',
  '/docs.html',
  '/dashboard.html',
  '/privacy.html',
  '/ai-assistant.css?v=3',
  '/ai-assistant.js?v=3',
  '/dashboard.js'
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE).then(function(cache) {
      return cache.addAll(PRECACHE);
    }).then(function() {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE; })
          .map(function(k) { return caches.delete(k); })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function(e) {
  // Only handle same-origin GET requests
  if (e.request.method !== 'GET' || !e.request.url.startsWith(self.location.origin)) return;

  e.respondWith(
    caches.match(e.request).then(function(cached) {
      var fetchPromise = fetch(e.request).then(function(response) {
        // Cache successful responses
        if (response && response.status === 200) {
          var copy = response.clone();
          caches.open(CACHE).then(function(cache) {
            cache.put(e.request, copy);
          });
        }
        return response;
      }).catch(function() {
        // Network failed, return cached
        return cached;
      });
      return cached || fetchPromise;
    })
  );
});
