/* Service Worker — network-first برای اپ، کش فقط fallback آفلاین */
const VERSION = "v10";                 // فقط اگر لیست SHELL عوض شد بالا ببر
const CACHE = `lms-shell-${VERSION}`;
const SHELL = [
  "/",
  "/manifest.webmanifest",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/img/ui-logo.png",
];
const NET_TIMEOUT = 5000;

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (e) => {
  if (e.data === "SKIP_WAITING") self.skipWaiting();
});

async function networkFirst(req, fallbackKey) {
  const cache = await caches.open(CACHE);
  try {
    const res = await Promise.race([
      fetch(req),
      new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), NET_TIMEOUT)),
    ]);
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  } catch (_) {
    return (await cache.match(req)) || (fallbackKey ? await cache.match(fallbackKey) : null)
      || new Response("آفلاین هستید", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
}

async function staleWhileRevalidate(req) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(req);
  const net = fetch(req).then((res) => { if (res && res.ok) cache.put(req, res.clone()); return res; }).catch(() => cached);
  return cached || net;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;          // API و SSE هرگز کش نشوند

  if (req.mode === "navigate" || url.pathname === "/") {
    e.respondWith(networkFirst(req, "/"));
    return;
  }
  if (/\.(js|css|webmanifest)$/.test(url.pathname)) {
    e.respondWith(networkFirst(req));                     // کد همیشه تازه
    return;
  }
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(staleWhileRevalidate(req));             // عکس/فونت به‌ندرت عوض می‌شوند
  }
});