// Offline cache for the app shell and content. Bump VERSION whenever files change.
const VERSION = "devopsscroll-v2";
const FILES = [
  "./", "index.html", "styles.css", "js/app.js", "manifest.webmanifest",
  "data/curriculum.js", "data/mcq.js", "data/scen.js", "data/lab.js", "data/learn.js",
  "vendor/mermaid.min.js",
  "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png",
  "feed/index.html", "feed/styles.css", "feed/app.js", "feed/config.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// Same-origin files: network first (so updates arrive), falling back to the cache when offline.
// Other origins (dev.to, Hacker News) are left alone.
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request, { ignoreSearch: true }))
  );
});
