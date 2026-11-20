/* AREA30 – interazioni del sito */
(() => {
  "use strict";
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const root = document.documentElement;

  /* Header che si scurisce allo scorrimento */
  const header = $(".site-header");
  const onScrollHeader = () => header && header.classList.toggle("scrolled", window.scrollY > 30);
  onScrollHeader();
  window.addEventListener("scroll", onScrollHeader, { passive: true });

  /* Menu mobile */
  const toggle = $(".menu-toggle");
  const setMenu = (open) => {
    root.classList.toggle("menu-open", open);
    document.body.classList.toggle("menu-open", open);
    toggle && toggle.setAttribute("aria-expanded", String(open));
    toggle && toggle.setAttribute("aria-label", open ? "Chiudi il menu" : "Apri il menu");
  };
  toggle && toggle.addEventListener("click", () => setMenu(!document.body.classList.contains("menu-open")));
  $$(".main-nav a").forEach((a) => a.addEventListener("click", () => setMenu(false)));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setMenu(false); });

  /* Eventi già passati: spariscono subito dalla Home (il sito si rigenera comunque ogni notte) */
  const now = Date.now();
  $$(".ev-card[data-end]").forEach((c) => { if (Date.parse(c.dataset.end) < now) c.remove(); });
  const list = $(".ev-list");
  if (list) {
    const cards = $$(".ev-card", list);
    if (!cards.length) { list.remove(); const empty = $(".ev-empty"); empty && (empty.hidden = false); }
    else if (!cards.some((c) => c.classList.contains("ev-card--big"))) cards[0].classList.add("ev-card--big");
  }

  /* Comparsa elegante degli elementi */
  const reveals = $$(".reveal");
  if ("IntersectionObserver" in window && !reduce) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach((el) => io.observe(el));
  } else reveals.forEach((el) => el.classList.add("in"));

  /* Profondità (parallasse leggera) */
  const par = $$("[data-parallax]");
  if (par.length && !reduce) {
    let ticking = false;
    const update = () => {
      const vh = window.innerHeight;
      par.forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.bottom < -200 || r.top > vh + 200) return;
        const k = parseFloat(el.dataset.parallax) || 0;
        const off = (r.top + r.height / 2 - vh / 2) * k;
        el.style.transform = `translate3d(0, ${(-off).toFixed(1)}px, 0)`;
      });
      ticking = false;
    };
    window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  /* Conto alla rovescia */
  const cds = $$("[data-countdown]");
  if (cds.length) {
    const pad = (n) => String(n).padStart(2, "0");
    const tick = () => {
      cds.forEach((el) => {
        let d = Math.max(0, Date.parse(el.dataset.countdown) - Date.now());
        const box = el.classList.contains("cd") ? el : $(".cd", el);
        if (!box) return;
        if (d === 0) { box.innerHTML = "<span style='padding:8px 14px'><b style='font-size:1.1rem'>Stasera!</b></span>"; return; }
        const days = Math.floor(d / 864e5); d -= days * 864e5;
        const h = Math.floor(d / 36e5); d -= h * 36e5;
        const m = Math.floor(d / 6e4); d -= m * 6e4;
        const s = Math.floor(d / 1e3);
        const set = (k, v) => { const b = $(`[data-cd="${k}"]`, box); if (b && b.textContent !== v) b.textContent = v; };
        set("d", String(days)); set("h", pad(h)); set("m", pad(m)); set("s", pad(s));
      });
    };
    tick();
    setInterval(tick, 1000);
  }

  /* Menu "Aggiungi al calendario" */
  $$(".cal-toggle").forEach((btn) => {
    const menu = btn.nextElementSibling;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = menu.hidden;
      $$(".cal-list").forEach((m) => { m.hidden = true; m.previousElementSibling.setAttribute("aria-expanded", "false"); });
      menu.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
    });
  });
  document.addEventListener("click", () => $$(".cal-list").forEach((m) => { m.hidden = true; }));

  /* Locandine in scorrimento continuo */
  $$(".marquee-track").forEach((t) => {
    if (reduce) return;
    $$(":scope > *", t).forEach((n) => { const c = n.cloneNode(true); c.setAttribute("aria-hidden", "true"); c.tabIndex = -1; t.appendChild(c); });
  });

  /* Galleria a tutto schermo */
  const lb = $("#lightbox");
  if (lb) {
    const img = $(".lb-stage img", lb), cap = $("figcaption", lb), count = $(".lb-count", lb);
    let items = [], idx = 0, lastFocus = null;
    const show = (i) => {
      idx = (i + items.length) % items.length;
      const it = items[idx];
      img.classList.add("loading");
      const srcEl = it.querySelector("source");
      const srcset = srcEl ? srcEl.srcset : "";
      const pre = new Image();
      pre.onload = () => {
        img.sizes = "100vw"; img.srcset = srcset; img.src = it.dataset.full;
        img.alt = it.dataset.caption || ""; img.classList.remove("loading");
      };
      if (srcset) { pre.sizes = "100vw"; pre.srcset = srcset; }
      pre.src = it.dataset.full;
      cap.textContent = it.dataset.caption || "";
      count.textContent = items.length > 1 ? `${idx + 1} / ${items.length}` : "";
      $(".lb-prev", lb).hidden = $(".lb-next", lb).hidden = items.length < 2;
      // precarica la successiva
      if (items.length > 1) {
        const nx = items[(idx + 1) % items.length], ns = nx.querySelector("source"), n = new Image();
        if (ns) { n.sizes = "100vw"; n.srcset = ns.srcset; } n.src = nx.dataset.full;
      }
    };
    const open = (group, i) => {
      items = group; lastFocus = document.activeElement;
      lb.hidden = false; requestAnimationFrame(() => lb.classList.add("open"));
      document.body.style.overflow = "hidden";
      show(i); $(".lb-close", lb).focus();
    };
    const close = () => {
      lb.classList.remove("open");
      setTimeout(() => { lb.hidden = true; img.removeAttribute("srcset"); img.removeAttribute("src"); }, 300);
      document.body.style.overflow = "";
      lastFocus && lastFocus.focus();
    };
    document.addEventListener("click", (e) => {
      const t = e.target.closest("[data-full]");
      if (!t) return;
      e.preventDefault();
      const group = t.closest("[data-gallery]");
      const all = group ? $$("[data-full]", group) : [t];
      open(all, all.indexOf(t));
    });
    $(".lb-close", lb).addEventListener("click", close);
    $(".lb-prev", lb).addEventListener("click", () => show(idx - 1));
    $(".lb-next", lb).addEventListener("click", () => show(idx + 1));
    lb.addEventListener("click", (e) => { if (e.target === lb || e.target.classList.contains("lb-stage")) close(); });
    document.addEventListener("keydown", (e) => {
      if (lb.hidden) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") show(idx - 1);
      else if (e.key === "ArrowRight") show(idx + 1);
      else if (e.key === "Tab") { // focus dentro la galleria
        const f = $$("button:not([hidden])", lb); const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    let sx = 0, sy = 0;
    lb.addEventListener("touchstart", (e) => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
    lb.addEventListener("touchend", (e) => {
      const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(idx + (dx < 0 ? 1 : -1));
      else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close();
    }, { passive: true });
  }

  /* Mappa caricata solo su richiesta */
  $$(".map-load").forEach((b) => b.addEventListener("click", () => {
    const box = b.closest("[data-map]");
    box.innerHTML = `<iframe src="${box.dataset.map}" title="Mappa: sede AREA30 a Sommariva del Bosco" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>`;
  }));

  /* Video di apertura (se presente) */
  const v = $(".hero-video");
  if (v && !reduce && !(navigator.connection && navigator.connection.saveData)) {
    v.addEventListener("playing", () => v.classList.add("playing"));
    v.preload = "auto"; v.play().catch(() => {});
  }

  /* Condivisione nativa del telefono */
  $$(".share-native").forEach((b) => {
    if (!navigator.share) return;
    b.hidden = false;
    b.addEventListener("click", () => navigator.share({ title: b.dataset.title, url: b.dataset.url }).catch(() => {}));
  });
})();
