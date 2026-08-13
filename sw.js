/* 比特币学习地图 Service Worker — 保守策略
 * 导航请求：网络优先，失败回退缓存（保证内容最新，且不白屏）
 * 静态资源：缓存优先（样式/脚本二次访问秒开、可离线）
 */
const CACHE = 'btc-map-v1';
const CORE = [
  './',
  './index.html',
  './shared/style.css',
  './shared/nav.js',
  './icon.svg',
  './manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE).catch(() => {})).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // 导航请求：网络优先 + 回退
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const cp = res.clone();
          caches.open(CACHE).then((c) => c.put(req, cp)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match('./index.html')))
    );
    return;
  }

  // 静态资源：缓存优先 + 回填
  event.respondWith(
    caches.match(req).then((cached) =>
      cached ||
      fetch(req).then((res) => {
        const cp = res.clone();
        caches.open(CACHE).then((c) => c.put(req, cp)).catch(() => {});
        return res;
      }).catch(() => cached)
    )
  );
});
