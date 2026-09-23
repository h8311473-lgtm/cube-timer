/* 魔方计时器 · 离线缓存（把 App 安装到主屏后可离线使用） */
const CACHE = 'cube-timer-mobile-v1';
const ASSETS = [
  './', './index.html', './stats.js', './manifest.webmanifest',
  './icon-180.png', './icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS).catch(() => undefined))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => undefined);
      return res;
    }).catch(() => caches.match('./index.html')))
  );
});
