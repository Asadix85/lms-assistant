/* Service Worker — کش استاتیک؛ API همیشه از شبکه */
const CACHE = "lms-static-v2";
const PRECACHE = [
  "/",
  "/manifest.webmanifest",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/img/ui-logo.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  // API و SSE را کش نکن
  if (url.pathname.startsWith("/api/")) return;

  // استاتیک: stale-while-revalidate ساده
  if (
    url.pathname.startsWith("/static/") ||
    url.pathname === "/" ||
    url.pathname === "/manifest.webmanifest"
  ) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const cached = await cache.match(req);
        const network = fetch(req)
          .then((res) => {
            if (res && res.ok) cache.put(req, res.clone());
            return res;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
  }
});