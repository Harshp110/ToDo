// -----------------------------
//  SERVICE WORKER for PWA
// -----------------------------
const CACHE_NAME = "todo-cache-v1";

// Files to cache (add more if needed)
const FILES_TO_CACHE = [
  "/",
  "/login",
  "/signup",
  "/static/style.css",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png"
];

// Install Event — Cache all files
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(FILES_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate Event — Clean old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch Event — Offline support
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cachedFile) => {
      return (
        cachedFile ||
        fetch(event.request).catch(() => {
          // Offline fallback
          if (event.request.mode === "navigate") {
            return caches.match("/"); // Return home page offline
          }
        })
      );
    })
  );
});
