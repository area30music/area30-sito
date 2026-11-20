/* AREA30 – service worker della web app (generato da build.py) */
const VERSIONE = "__VERSIONE__";
const BASE = "__BASE__";
const PAGINE = "area30-pagine-" + VERSIONE;
const STATICI = "area30-statici-v1";
const IMMAGINI = "area30-immagini-v1";
const PRECACHE = __PRECACHE__;
const MAX_IMMAGINI = 120;

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(PAGINE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("area30-pagine-") && k !== PAGINE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function limita(nome, max) {
  const c = await caches.open(nome);
  const keys = await c.keys();
  for (let i = 0; i < keys.length - max; i++) await c.delete(keys[i]);
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const u = new URL(req.url);
  if (u.origin !== self.location.origin) return;
  const path = u.pathname;

  // Pagine: prima la rete (contenuti sempre aggiornati), poi la copia salvata, poi la pagina offline
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) { const copia = res.clone(); caches.open(PAGINE).then((c) => c.put(req, copia)); }
          return res;
        })
        .catch(async () => (await caches.match(req, { ignoreSearch: true })) || caches.match(BASE + "/offline.html"))
    );
    return;
  }

  // Immagini (nomi con impronta: non cambiano mai) → prima la copia salvata
  if (path.startsWith(BASE + "/img/")) {
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok) { const copia = res.clone(); caches.open(IMMAGINI).then((c) => c.put(req, copia).then(() => limita(IMMAGINI, MAX_IMMAGINI))); }
        return res;
      }))
    );
    return;
  }

  // Font, logo, script: copia salvata subito, aggiornata in sottofondo
  if (path.startsWith(BASE + "/assets/")) {
    e.respondWith(
      caches.open(STATICI).then(async (c) => {
        const hit = await c.match(req);
        const rete = fetch(req).then((res) => { if (res.ok) c.put(req, res.clone()); return res; }).catch(() => hit);
        return hit || rete;
      })
    );
  }
});

/* Notifiche (pronte per quando attiveremo l'invio) */
self.addEventListener("push", (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { body: e.data && e.data.text() }; }
  e.waitUntil(self.registration.showNotification(d.title || "AREA30", {
    body: d.body || "Nuovo evento in calendario",
    icon: BASE + "/assets/icon-192.png",
    badge: BASE + "/assets/icon-192.png",
    image: d.image,
    data: { url: d.url || BASE + "/" },
    lang: "it",
  }));
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || BASE + "/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
    for (const c of list) if (c.url.includes(url) && "focus" in c) return c.focus();
    return self.clients.openWindow(url);
  }));
});
