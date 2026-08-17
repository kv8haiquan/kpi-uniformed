const CACHE_NAME = 'lichkv8-v170-leadercard-instant-resilient';
const STATIC_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './modules/duty.js?v=163',
  './modules/duty.css?v=163',
  './modules/docreport.js?v=163',
  './modules/docreport.css?v=163',
  './Mau_import_lich_truc_ban_HQKV8_v127.xlsx'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  // Một asset tùy chọn bị thiếu không được làm hỏng toàn bộ precache.
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      Promise.allSettled(STATIC_ASSETS.map(asset => cache.add(asset)))
    )
  );
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE_NAME && /^lct-|lichkv8|hqkv8/i.test(k)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Không can thiệp request Apps Script/Google Drive.
  if (/script\.google\.com|script\.googleusercontent\.com|googleapis\.com|googleusercontent\.com/.test(url.hostname)) return;

  // HTML luôn network-first để không giữ giao diện/GAS_URL cũ.
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(fetch(req, { cache: 'no-store' }).then(res => {
      const clone = res.clone();
      caches.open(CACHE_NAME).then(cache => cache.put('./index.html', clone)).catch(() => null);
      return res;
    }).catch(() => caches.match('./index.html')));
    return;
  }

  // JS/CSS/manifest: network-first, fallback cache. Đây là các file cần ưu tiên bản mới.
  if (/\.(?:js|css|json)$/i.test(url.pathname)) {
    event.respondWith(fetch(req, { cache: 'no-store' }).then(res => {
      if (res && res.ok) {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(req, clone)).catch(() => null);
      }
      return res;
    }).catch(() => caches.match(req)));
    return;
  }

  // Ảnh/file tĩnh lớn: cache-first + cập nhật nền.
  event.respondWith(caches.match(req).then(cached => {
    const fetchPromise = fetch(req).then(res => {
      if (res && res.ok) {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(req, clone)).catch(() => null);
      }
      return res;
    }).catch(() => cached);
    return cached || fetchPromise;
  }));
});
