#!/usr/bin/env python3
"""
Generatore del sito AREA30.

Legge i contenuti in /contenuti e le immagini in /media, ottimizza le immagini
(WebP in più misure + JPEG di riserva), crea le pagine HTML in /_site insieme a
sitemap.xml, robots.txt, llms.txt, calendari .ics e dati strutturati per Google.

Uso:
    python build.py                      # sito per area30.it
    BASE_PATH=/area30-sito python build.py   # anteprima su <utente>.github.io/area30-sito
    python build.py --serve              # costruisce e apre un'anteprima locale su :8000
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image, ImageFilter, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "contenuti"
MEDIA = ROOT / "media"
ASSETS = ROOT / "assets"
TEMPLATES = ROOT / "templates"
OUT = ROOT / "_site"
CACHE = ROOT / ".cache" / "img"

TZ = ZoneInfo("Europe/Rome")
SITE_URL = (os.environ.get("SITE_URL") or "https://area30.it").rstrip("/")
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
NOINDEX = os.environ.get("NOINDEX", "") == "1"  # anteprima: non farla indicizzare

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


# --------------------------------------------------------------------------- util
def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "evento"


def url(path: str = "/") -> str:
    """Percorso interno con eventuale BASE_PATH (per l'anteprima su GitHub)."""
    if path.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return BASE_PATH + path


def abs_url(path: str = "/") -> str:
    if path.startswith("http"):
        return path
    return SITE_URL + url(path)


def load_yaml(p: Path):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_front_matter(p: Path):
    text = p.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2).strip()


def data_it(d: date, giorno=True, anno=True) -> str:
    s = f"{d.day} {MESI[d.month - 1]}"
    if anno:
        s += f" {d.year}"
    if giorno:
        s = f"{GIORNI[d.weekday()]} {s}"
    return s


# ------------------------------------------------------------------------ immagini
@dataclass
class Img:
    src: str           # percorso del JPEG di riserva
    srcset: str        # srcset WebP
    width: int
    height: int
    largest: str       # WebP più grande (per lightbox / condivisioni)
    alt: str = ""


class ImagePipeline:
    PHOTO = (480, 800, 1200, 1800, 2400)
    POSTER = (360, 600, 900, 1400)

    def __init__(self):
        CACHE.mkdir(parents=True, exist_ok=True)
        (OUT / "img").mkdir(parents=True, exist_ok=True)
        self.done: dict[tuple, Img] = {}

    def _source(self, ref: str) -> Path | None:
        if not ref:
            return None
        ref = ref.split("?")[0]
        p = ROOT / ref.lstrip("/")
        if p.exists():
            return p
        p = MEDIA / Path(ref).name
        return p if p.exists() else None

    def get(self, ref: str, kind: str = "photo", alt: str = "") -> Img | None:
        key = (ref, kind)
        if key in self.done:
            img = self.done[key]
            return Img(**{**img.__dict__, "alt": alt})
        src = self._source(ref)
        if not src:
            print(f"  ! immagine non trovata: {ref}", file=sys.stderr)
            return None
        widths = self.POSTER if kind == "poster" else self.PHOTO
        h = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
        base = f"{slugify(src.stem)}-{h}"
        im = None
        with Image.open(src) as probe:
            ow, oh = ImageOps.exif_transpose(probe).size
        made = []
        for w in widths:
            if w > ow and made:
                continue
            tw = min(w, ow)
            name = f"{base}-{tw}.webp"
            cached = CACHE / name
            if not cached.exists():
                if im is None:
                    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
                r = im.copy()
                r.thumbnail((tw, 10_000), Image.LANCZOS)
                r.save(cached, "WEBP", quality=80 if tw > 1000 else 82, method=6)
            shutil.copy2(cached, OUT / "img" / name)
            made.append((tw, name))
        fb_w = min(1200, ow)
        fb = f"{base}-{fb_w}.jpg"
        cached = CACHE / fb
        if not cached.exists():
            if im is None:
                im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            r = im.copy()
            r.thumbnail((fb_w, 10_000), Image.LANCZOS)
            r.save(cached, "JPEG", quality=80, optimize=True, progressive=True)
        shutil.copy2(cached, OUT / "img" / fb)
        img = Img(
            src=url(f"/img/{fb}"),
            srcset=", ".join(f"{url('/img/' + n)} {w}w" for w, n in made),
            width=ow, height=oh,
            largest=url(f"/img/{made[-1][1]}"),
        )
        self.done[key] = img
        return Img(**{**img.__dict__, "alt": alt})

    def og(self, ref: str, name: str, poster: bool = False, titolo: str = "") -> str:
        """Immagine 1200x630 per le anteprime su WhatsApp/Facebook."""
        src = self._source(ref)
        if not src:
            return abs_url("/assets/og-default.jpg")
        h = hashlib.sha1(src.read_bytes() + titolo.encode() + b"og3").hexdigest()[:10]
        fname = f"og-{slugify(name)}-{h}.jpg"
        cached = CACHE / fname
        if not cached.exists():
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            W, H = 1200, 630
            if poster:
                bg = ImageOps.fit(im, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
                bg = Image.blend(bg, Image.new("RGB", (W, H), (8, 8, 10)), 0.55)
                p = im.copy()
                p.thumbnail((W - 80, H - 60), Image.LANCZOS)
                # locandina a sinistra, logo a destra
                x = 70 if p.size[0] < W * 0.55 else (W - p.size[0]) // 2
                bg.paste(p, (x, (H - p.size[1]) // 2))
                if p.size[0] < W * 0.55:
                    self._logo(bg, (x + p.size[0] + 60, 0, W - 50, H))
            else:
                bg = ImageOps.fit(im, (W, H), Image.LANCZOS)
                shade = Image.new("RGB", (W, H), (0, 0, 0))
                mask = Image.linear_gradient("L").rotate(180).resize((W, H))
                bg = Image.composite(shade, bg, mask.point(lambda v: int(v * 0.75)))
                self._logo(bg, (0, int(H * 0.55), W, H - 40))
            bg.save(cached, "JPEG", quality=84, optimize=True, progressive=True)
        (OUT / "img").mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached, OUT / "img" / fname)
        return abs_url(f"/img/{fname}")

    @staticmethod
    def _logo(canvas: Image.Image, box):
        lg = Image.open(ASSETS / "logo-area30.png").convert("RGBA")
        bw, bh = box[2] - box[0], box[3] - box[1]
        lg.thumbnail((int(bw * 0.8), int(bh * 0.5)), Image.LANCZOS)
        x = box[0] + (bw - lg.size[0]) // 2
        y = box[1] + (bh - lg.size[1]) // 2
        canvas.paste(lg, (x, y), lg)


# ------------------------------------------------------------------------- eventi
@dataclass
class Evento:
    slug: str
    titolo: str
    data: date
    ora: str
    luogo: str
    indirizzo: str
    citta: str
    descrizione: str
    biglietti: str
    locandina: str
    rassegna: str = ""
    apertura: str = ""
    foto: list = field(default_factory=list)
    testo: str = ""
    passato: bool = False
    img: Img | None = None
    foto_img: list = field(default_factory=list)
    og: str = ""

    @property
    def inizio(self) -> datetime:
        if self.ora:
            hh, mm = re.split(r"[:.]", self.ora)[:2]
            return datetime(self.data.year, self.data.month, self.data.day, int(hh), int(mm), tzinfo=TZ)
        return datetime(self.data.year, self.data.month, self.data.day, 0, 0, tzinfo=TZ)

    @property
    def fine(self) -> datetime:
        return self.inizio + (timedelta(hours=3) if self.ora else timedelta(days=1))

    @property
    def iso(self) -> str:
        return self.inizio.isoformat() if self.ora else self.data.isoformat()

    @property
    def data_lunga(self) -> str:
        return data_it(self.data).capitalize()

    @property
    def ora_it(self) -> str:
        return self.ora.replace(":", ".") if self.ora else ""

    @property
    def path(self) -> str:
        return f"/eventi/{self.slug}"

    @property
    def luogo_completo(self) -> str:
        return ", ".join(x for x in [self.luogo, self.indirizzo, self.citta] if x)

    @property
    def google_cal(self) -> str:
        fmt = "%Y%m%dT%H%M%S"
        if self.ora:
            dates = f"{self.inizio.strftime(fmt)}/{self.fine.strftime(fmt)}"
        else:
            dates = f"{self.data.strftime('%Y%m%d')}/{(self.data + timedelta(days=1)).strftime('%Y%m%d')}"
        det = self.descrizione
        if self.biglietti:
            det += f"\n\nBiglietti: {self.biglietti}"
        det += f"\n\n{abs_url(self.path)}"
        q = {"action": "TEMPLATE", "text": self.titolo, "dates": dates, "ctz": "Europe/Rome",
             "details": det, "location": self.luogo_completo}
        return "https://calendar.google.com/calendar/render?" + urlencode(q, quote_via=quote)


def to_date(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if not v:
        return None
    s = str(v).strip()
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s[:16] if "T" in s else s, f).date()
        except ValueError:
            pass
    return None


def link_notifica(nid: str, titolo: str, messaggio: str, link: str = "", immagine: str = "") -> str:
    """Indirizzo che si apre toccando la notifica: la pagina Notifiche con il dettaglio di quella notifica."""
    q = {"n": nid, "t": titolo, "m": messaggio}
    if link:
        q["l"] = link
    if immagine:
        q["i"] = immagine
    return abs_url("/notifiche") + "?" + urlencode(q, quote_via=quote)


def onesignal_api(method: str, url: str, key: str, body: dict | None = None) -> dict:
    """Chiamata a OneSignal: funziona sia con le chiavi nuove ("Key …") sia con quelle vecchie ("Basic …")."""
    import urllib.error
    import urllib.request
    data = json.dumps(body).encode() if body is not None else None
    for schema in ("Key", "Basic"):
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Content-Type": "application/json", "Authorization": f"{schema} {key}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as ex:
            if ex.code in (401, 403) and schema == "Key":
                continue
            raise
    return {}


ONESIGNAL_FILES = {
    "OneSignalSDK.sw.js": "https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js",
    "OneSignalSDK.page.es6.js": "https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.es6.js",
}


def onesignal_locale() -> dict:
    """Copia locale dei file OneSignal (servono anche quando cdn.onesignal.com è bloccato da VPN o blocchi pubblicità)."""
    import urllib.request
    dest = OUT / "assets" / "onesignal"
    dest.mkdir(parents=True, exist_ok=True)
    cache = ROOT / ".cache" / "onesignal"
    cache.mkdir(parents=True, exist_ok=True)
    out = {}
    for nome, src in ONESIGNAL_FILES.items():
        f = cache / nome
        try:
            with urllib.request.urlopen(src, timeout=30) as r:
                dati = r.read()
            if len(dati) > 1000:
                f.write_bytes(dati)
        except Exception as ex:  # noqa: BLE001
            print(f"  ! download {nome} non riuscito: {ex}", file=sys.stderr)
        if f.exists():
            shutil.copy2(f, dest / nome)
            out[nome] = url(f"/assets/onesignal/{nome}") + "?v=" + hashlib.sha1(f.read_bytes()).hexdigest()[:8]
        else:
            out[nome] = src
    return out


def immagine_notifica(n: dict) -> str:
    """OneSignal salva l'immagine in campi diversi a seconda di come è stata creata la notifica."""
    for k in ("chrome_web_image", "big_picture", "chrome_big_picture", "adm_big_picture", "huawei_big_picture",
              "web_push_big_picture", "image", "global_image"):
        v = n.get(k)
        if isinstance(v, str) and v.startswith("http"):
            return v
    att = n.get("ios_attachments")
    if isinstance(att, dict):
        for v in att.values():
            if isinstance(v, str) and v.startswith("http"):
                return v
    for k, v in n.items():  # qualunque altro campo con "image" o "picture"
        if ("image" in k or "picture" in k) and isinstance(v, str) and v.startswith("http"):
            return v
    campi = [k for k, v in n.items() if ("image" in k or "picture" in k or "attach" in k) and v]
    if campi:
        print(f"  (notifica {str(n.get('id'))[:8]}: campi immagine non riconosciuti {campi})", file=sys.stderr)
    return ""


def carica_storico(app_id: str) -> list[dict]:
    """Storico delle notifiche inviate, letto da OneSignal (serve la chiave, disponibile solo su GitHub)."""
    key = os.environ.get("ONESIGNAL_REST_API_KEY", "").strip()
    if not key or not app_id:
        return []
    try:
        dati = onesignal_api("GET", f"https://api.onesignal.com/notifications?app_id={app_id}&limit=50", key)
    except Exception as ex:  # noqa: BLE001
        print(f"  ! storico notifiche non disponibile: {ex}", file=sys.stderr)
        return []
    out = []
    print(f"  OneSignal: total_count={dati.get('total_count')} ricevute={len(dati.get('notifications', []))}")
    for n in dati.get("notifications", []):
        if n.get("canceled"):
            continue
        quando = n.get("send_after") or n.get("queued_at") or n.get("completed_at")
        if not quando:
            continue
        h, c = n.get("headings") or {}, n.get("contents") or {}
        titolo = (h.get("it") or h.get("en") or "AREA30").strip()
        testo = (c.get("it") or c.get("en") or "").strip()
        link = n.get("url") or n.get("web_url") or ""
        # se il link è già il dettaglio della notifica, si recupera il link "vero" (es. pagina evento)
        if "/notifiche?" in link:
            from urllib.parse import urlparse, parse_qs
            link = (parse_qs(urlparse(link).query).get("l") or [""])[0]
        out.append({
            "id": n.get("id", ""),
            "titolo": titolo, "messaggio": testo, "link": link,
            "immagine": immagine_notifica(n),
            "quando": datetime.fromtimestamp(int(quando), TZ).isoformat(),
        })
    out.sort(key=lambda x: datetime.fromisoformat(x["quando"]), reverse=True)
    return out


def norm_time(v) -> str:
    v = str(v or "").strip()
    if not re.match(r"^\d{1,2}[:.]\d{2}$", v):
        return ""
    hh, mm = re.split(r"[:.]", v)
    return f"{int(hh):02d}:{mm}"


def load_events(today: date) -> list[Evento]:
    out = []
    for p in sorted((CONTENT / "eventi").glob("*.md")):
        fm, body = read_front_matter(p)
        d = to_date(fm.get("data"))
        if not d or not fm.get("titolo"):
            print(f"  ! evento ignorato (manca titolo o data): {p.name}", file=sys.stderr)
            continue
        ora = norm_time(fm.get("ora"))
        apertura = norm_time(fm.get("apertura"))
        foto = fm.get("foto") or []
        if isinstance(foto, str):
            foto = [foto]
        out.append(Evento(
            slug=slugify(p.stem), titolo=str(fm["titolo"]).strip(), data=d, ora=ora,
            luogo=str(fm.get("luogo") or "").strip(), indirizzo=str(fm.get("indirizzo") or "").strip(),
            citta=str(fm.get("citta") or "Sommariva del Bosco").strip(),
            descrizione=str(fm.get("descrizione") or "").strip(),
            biglietti=str(fm.get("biglietti") or "").strip(), locandina=str(fm.get("locandina") or ""),
            rassegna=str(fm.get("rassegna") or "").strip(), apertura=apertura, foto=[f for f in foto if f], testo=body,
            passato=d < today,
        ))
    return out


# --------------------------------------------------------------------- dati Google
def org_schema(site) -> dict:
    a = site["indirizzo"]
    return {
        "@type": ["LocalBusiness", "EntertainmentBusiness"],
        "@id": abs_url("/#organizzazione"),
        "name": site["nome"],
        "alternateName": [site["nome_esteso"], "Area 30", site["ragione_sociale"]],
        "description": site["descrizione"],
        "url": abs_url("/"),
        "logo": abs_url("/assets/icon-512.png"),
        "image": abs_url("/assets/og-default.jpg"),
        "telephone": "+39 " + site["telefono"],
        "email": site["email"],
        "address": {
            "@type": "PostalAddress", "streetAddress": a["via"], "postalCode": str(a["cap"]),
            "addressLocality": a["citta"], "addressRegion": a["provincia"], "addressCountry": a["nazione"],
        },
        "geo": {"@type": "GeoCoordinates", "latitude": a["lat"], "longitude": a["lng"]},
        "areaServed": [{"@type": "AdministrativeArea", "name": n} for n in
                       ["Sommariva del Bosco", "Provincia di Cuneo", "Roero", "Langhe", "Piemonte"]],
        "knowsAbout": ["Service audio e luci", "Noleggio impianti audio", "Illuminotecnica per concerti",
                       "Organizzazione eventi live", "Studio di registrazione", "Sala prove"],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Servizi AREA30",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "areaServed": "Piemonte"}}
                for n in ["Service audio e luci per concerti ed eventi", "Strutture ed effetti speciali",
                          "Studio di registrazione", "Sala prove e sala di ripresa", "Organizzazione di eventi musicali"]
            ],
        },
        "sameAs": [v for v in site["social"].values() if v],
    }


def event_schema(e: Evento, site) -> dict:
    d = {
        "@type": "MusicEvent" if "concert" in e.titolo.lower() or "tour" in e.titolo.lower() else "Event",
        "@id": abs_url(e.path) + "#evento",
        "name": e.titolo,
        "startDate": e.iso,
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "url": abs_url(e.path),
        "description": e.descrizione or f"{e.titolo} a {e.citta}",
        "location": {
            "@type": "Place", "name": e.luogo or e.citta,
            "address": {"@type": "PostalAddress", "streetAddress": e.indirizzo or None,
                        "addressLocality": e.citta, "postalCode": site["indirizzo"]["cap"] if e.citta == site["indirizzo"]["citta"] else None,
                        "addressRegion": "CN", "addressCountry": "IT"},
        },
        "organizer": {"@type": "Organization", "@id": abs_url("/#organizzazione"), "name": site["nome"], "url": abs_url("/")},
    }
    if e.ora:
        d["endDate"] = e.fine.isoformat()
    if e.ora and e.apertura:
        hh, mm = e.apertura.split(":")
        d["doorTime"] = e.inizio.replace(hour=int(hh), minute=int(mm)).isoformat()
    if e.img:
        d["image"] = [SITE_URL + e.img.src]
    if e.biglietti:
        d["offers"] = {"@type": "Offer", "url": e.biglietti, "availability": "https://schema.org/InStock",
                       "validFrom": (e.data - timedelta(days=60)).isoformat()}
    # rimuove i campi vuoti
    d["location"]["address"] = {k: v for k, v in d["location"]["address"].items() if v}
    return d


def page_schema(*items) -> str:
    return json.dumps({"@context": "https://schema.org", "@graph": [i for i in items if i]},
                      ensure_ascii=False, separators=(",", ":"))


def breadcrumb(*pairs) -> dict:
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(u)} for i, (n, u) in enumerate(pairs)]}


# ----------------------------------------------------------------------------- ics
def ics(e: Evento, site) -> str:
    def esc(s):
        return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    now = datetime.now(TZ).astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AREA30//Eventi//IT", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", "BEGIN:VEVENT", f"UID:{e.slug}@area30.it", f"DTSTAMP:{now}"]
    if e.ora:
        u = ZoneInfo("UTC")
        lines += [f"DTSTART:{e.inizio.astimezone(u).strftime('%Y%m%dT%H%M%SZ')}",
                  f"DTEND:{e.fine.astimezone(u).strftime('%Y%m%dT%H%M%SZ')}"]
    else:
        lines += [f"DTSTART;VALUE=DATE:{e.data.strftime('%Y%m%d')}",
                  f"DTEND;VALUE=DATE:{(e.data + timedelta(days=1)).strftime('%Y%m%d')}"]
    det = e.descrizione + (f"\nBiglietti: {e.biglietti}" if e.biglietti else "")
    lines += [f"SUMMARY:{esc(e.titolo)}", f"DESCRIPTION:{esc(det)}", f"LOCATION:{esc(e.luogo_completo)}",
              f"URL:{abs_url(e.path)}", "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY",
              f"DESCRIPTION:{esc(e.titolo)} domani", "END:VALARM", "END:VEVENT", "END:VCALENDAR"]
    out = []
    for l in lines:  # righe max 75 caratteri
        b = l.encode()
        while len(b) > 74:
            cut = 74
            while (b[cut] & 0xC0) == 0x80:
                cut -= 1
            out.append(b[:cut].decode())
            b = b" " + b[cut:]
        out.append(b.decode())
    return "\r\n".join(out) + "\r\n"


# --------------------------------------------------------------------------- build
def short(t: str, n: int = 158) -> str:
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",;:.–-") + "…"


def event_title(e) -> str:
    d = data_it(e.data, giorno=False)
    for t in (f"{e.titolo} – {d}, {e.luogo or e.citta} | AREA30", f"{e.titolo} – {d} | AREA30",
              f"{e.titolo} | AREA30"):
        if len(t) <= 65:
            return t
    return short(e.titolo, 56) + " | AREA30"


def minify_html(s: str) -> str:
    parts = re.split(r"(<(?:script|style|pre|textarea)[\s\S]*?</(?:script|style|pre|textarea)>)", s)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r">\s+<", "> <", re.sub(r"\n\s*", "\n", parts[i]))
    return "".join(parts).strip()


def asset_version(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()[:8]


def build():
    today = datetime.now(TZ).date()
    print(f"Costruzione del sito ({today.isoformat()}) → {OUT}")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    site = load_yaml(CONTENT / "sito.yml")
    # Notifiche: attive solo con l'ID di OneSignal e sul sito definitivo (non nell'anteprima)
    onesignal_id = str(site.get("onesignal_app_id") or "").strip() if not NOINDEX else ""
    os_files = onesignal_locale() if onesignal_id else {}
    servizi = load_yaml(CONTENT / "servizi.yml").get("servizi", [])
    galleria = load_yaml(CONTENT / "galleria.yml").get("foto", []) or []
    stampa = load_yaml(CONTENT / "rassegna-stampa.yml").get("articoli", []) or []

    imgs = ImagePipeline()
    eventi = load_events(today)
    for e in eventi:
        e.img = imgs.get(e.locandina, "poster",
                         alt=f"Locandina di {e.titolo}, {data_it(e.data, giorno=False)}"
                             + (f", {e.luogo}" if e.luogo else "") + f", {e.citta}")
        e.foto_img = [i for i in (imgs.get(f, "photo", alt=f"Foto della serata {e.titolo}") for f in e.foto) if i]
        e.og = imgs.og(e.locandina, e.slug, poster=True, titolo=e.titolo) if e.locandina else ""
    # immagini delle notifiche scritte nel pannello (servono online per OneSignal)
    for nf in sorted((CONTENT / "notifiche").glob("*.yml")) if (CONTENT / "notifiche").exists() else []:
        nd = load_yaml(nf)
        if nd.get("immagine"):
            imgs.og(str(nd["immagine"]), "notifica-" + nf.stem, poster=True,
                    titolo=str(nd.get("titolo") or "AREA30").strip())
    prossimi = sorted([e for e in eventi if not e.passato], key=lambda e: e.inizio)
    passati = sorted([e for e in eventi if e.passato], key=lambda e: e.inizio, reverse=True)

    for s in servizi:
        s["img"] = imgs.get(s["immagine"], "photo", s.get("alt", s["titolo"]))
        if s.get("immagine2"):
            s["img2"] = imgs.get(s["immagine2"], "photo", s.get("alt2", s["titolo"]))
    gal = [i for i in (imgs.get(g["immagine"], "photo", g.get("descrizione", "Foto di un evento AREA30")) for g in galleria) if i]
    for a in stampa:
        a["img"] = imgs.get(a.get("immagine", ""), "photo", f"Foto per l'articolo: {a['titolo']}") if a.get("immagine") else None
        a["data_it"] = data_it(to_date(a.get("data")), giorno=False) if to_date(a.get("data")) else ""
    stampa.sort(key=lambda a: str(a.get("data", "")), reverse=True)

    hero = imgs.get(site.get("foto_apertura", "/media/live-01.jpg"), "photo",
                    "Palco illuminato e pubblico a un concerto organizzato da AREA30")
    video = site.get("video_apertura") or ""
    if video:
        vsrc = imgs._source(video)
        if vsrc:
            (OUT / "media").mkdir(exist_ok=True)
            shutil.copy2(vsrc, OUT / "media" / vsrc.name)
            video = url("/media/" + vsrc.name)
        else:
            video = ""

    # immagine predefinita per le condivisioni
    og_default_src = imgs.og(site.get("foto_apertura", "/media/live-01.jpg"), "area30", titolo="home")
    (OUT / "assets").mkdir(exist_ok=True)

    # asset statici
    shutil.copytree(ASSETS, OUT / "assets", dirs_exist_ok=True)
    shutil.copy2(OUT / "img" / og_default_src.rsplit("/", 1)[1], OUT / "assets" / "og-default.jpg")
    css = (ASSETS / "css" / "style.css").read_text(encoding="utf-8")
    css = css.replace("/assets/", url("/assets/"))
    css = re.sub(r"/\*[\s\S]*?\*/", "", css)
    css = re.sub(r"\s*\n\s*", "\n", css)

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "xml"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.globals.update(
        url=url, abs_url=abs_url, base_path=BASE_PATH, site=site, today=today, year=today.year, css=css, noindex=NOINDEX,
        js_v=asset_version(ASSETS / "js" / "main.js"), os_page_js=os_files.get("OneSignalSDK.page.es6.js", ""), icon_v=asset_version(ASSETS / "icon-512.png"), data_it=data_it, prossimi=prossimi, onesignal_id=onesignal_id,
        wa=lambda testo="": f"https://wa.me/{site['whatsapp']}" + (f"?text={quote(testo)}" if testo else ""),
    )

    org = org_schema(site)
    pages = []

    def render(tpl, path, out_name, **ctx):
        ctx.setdefault("canonical", abs_url(path))
        ctx.setdefault("og_image", abs_url("/assets/og-default.jpg"))
        ctx.setdefault("path", path)
        s = env.get_template(tpl).render(**ctx)
        dest = OUT / out_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(minify_html(s), encoding="utf-8")
        if not ctx.get("no_sitemap"):
            pages.append((path, ctx.get("lastmod", today.isoformat()), ctx.get("priority", "0.7")))

    nav_home = ("Home", "/")

    # Home
    home_events = [event_schema(e, site) for e in prossimi]
    render("index.html", "/", "index.html",
           title="AREA30 | Service audio e luci ed eventi live a Sommariva del Bosco",
           description="AREA30: service audio e luci, concerti ed eventi live a Sommariva del Bosco, provincia di Cuneo. "
                       "Studio di registrazione e sala prove tra Roero, Langhe e Piemonte. Scopri i prossimi eventi.",
           schema=page_schema(org, {"@type": "WebSite", "@id": abs_url("/#sito"), "url": abs_url("/"), "name": "AREA30",
                                    "inLanguage": "it-IT", "publisher": {"@id": abs_url("/#organizzazione")}}, *home_events),
           hero=hero, video=video, servizi=servizi, galleria=gal[:10], passati=passati[:12], stampa=stampa[:3],
           priority="1.0")

    render("servizi.html", "/i-nostri-servizi", "i-nostri-servizi.html",
           title="Service audio luci, studio di registrazione e sala prove – AREA30",
           description="Service audio e luci per concerti, feste e festival in provincia di Cuneo, Roero e Langhe. "
                       "Studio di registrazione analogico e digitale e sala prove a Sommariva del Bosco (CN).",
           schema=page_schema(org, breadcrumb(nav_home, ("I nostri servizi", "/i-nostri-servizi"))),
           servizi=servizi, og_image=imgs.og(servizi[0]["immagine"], "servizi", titolo="servizi"), priority="0.9")

    render("eventi-passati.html", "/eventi-passati", "eventi-passati.html",
           title="Eventi passati e foto – Controtempo | AREA30 Sommariva del Bosco",
           description="La storia di AREA30 in locandine e foto: le edizioni di Controtempo, concerti e spettacoli "
                       "al Teatro Bongioanni e in piazza a Sommariva del Bosco (CN).",
           schema=page_schema(org, breadcrumb(nav_home, ("Eventi passati", "/eventi-passati"))),
           passati=passati, galleria=gal, priority="0.8")

    render("parlano-di-noi.html", "/parlano-di-noi", "parlano-di-noi.html",
           title="Parlano di noi – Rassegna stampa | AREA30 Sommariva del Bosco",
           description="Articoli e notizie su AREA30 e sul festival Controtempo di Sommariva del Bosco: "
                       "cosa scrivono i giornali del Roero e della provincia di Cuneo.",
           schema=page_schema(org, breadcrumb(nav_home, ("Parlano di noi", "/parlano-di-noi"))),
           stampa=stampa, priority="0.6")

    render("contatti.html", "/contattaci", "contattaci.html",
           title="Contatti – AREA30, Via Mario Groppo 4, Sommariva del Bosco (CN)",
           description="Contatta AREA30 per service audio e luci, eventi, studio di registrazione e sala prove: "
                       "telefono 0172 56 00 87, WhatsApp, email info@area30.it. Sommariva del Bosco (CN).",
           schema=page_schema(org, breadcrumb(nav_home, ("Contatti", "/contattaci"))), priority="0.8")

    for e in eventi:
        render("evento.html", e.path, f"eventi/{e.slug}.html", e=e,
               title=event_title(e),
               description=short(f"{e.titolo}: {data_it(e.data)}" + (f" ore {e.ora_it}" if e.ora else "")
                                 + (f", {e.luogo}" if e.luogo else "") + f", {e.citta}. " + e.descrizione),
               og_image=e.og or abs_url("/assets/og-default.jpg"), og_type="event",
               schema=page_schema(event_schema(e, site), breadcrumb(
                   nav_home, ("Eventi passati", "/eventi-passati") if e.passato else ("Prossimi eventi", "/#eventi"),
                   (e.titolo, e.path))),
               priority="0.5" if e.passato else "0.9")
        (OUT / "eventi" / f"{e.slug}.ics").write_text(ics(e, site), encoding="utf-8")

    if onesignal_id:
        storico = carica_storico(onesignal_id)
        print(f"  storico notifiche: {len(storico)}")
        render("notifiche.html", "/notifiche", "notifiche.html", title="Notifiche | AREA30",
               storico=storico, generato=datetime.now(TZ).isoformat(), storico_json=json.dumps(storico, ensure_ascii=False).replace("</", "<\\/"),
               description="Attiva le notifiche di AREA30 per sapere subito quando annunciamo un nuovo concerto.",
               no_sitemap=True, noindex_page=True)

    render("404.html", "/404", "404.html", title="Pagina non trovata | AREA30",
           description="La pagina che cerchi non esiste.", no_sitemap=True, noindex_page=True)

    # File per i motori di ricerca
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p, lm, pr in pages:
        sm.append(f"<url><loc>{html.escape(abs_url(p))}</loc><lastmod>{lm}</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    if NOINDEX:
        (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    else:
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {abs_url('/sitemap.xml')}\n", encoding="utf-8")
    (OUT / "llms.txt").write_text(env.get_template("llms.txt").render(
        prossimi=prossimi, passati=passati, servizi=servizi), encoding="utf-8")
    (OUT / "site.webmanifest").write_text(json.dumps({
        "id": url("/"), "name": "AREA30 – Eventi live e service audio luci", "short_name": "AREA30",
        "description": "Prossimi concerti AREA30 a Sommariva del Bosco: biglietti, calendario e notizie.",
        "lang": "it", "dir": "ltr", "start_url": url("/?app=1"), "scope": url("/"),
        "display": "standalone", "display_override": ["standalone", "minimal-ui"], "orientation": "any",
        "background_color": "#09090b", "theme_color": "#09090b", "categories": ["music", "entertainment", "events"],
        "icons": [{"src": url("/assets/icon-192.png") + "?v=" + env.globals["icon_v"], "sizes": "192x192", "type": "image/png", "purpose": "any"},
                  {"src": url("/assets/icon-512.png") + "?v=" + env.globals["icon_v"], "sizes": "512x512", "type": "image/png", "purpose": "any"},
                  {"src": url("/assets/icon-maskable-512.png") + "?v=" + env.globals["icon_v"], "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
        "shortcuts": [
            {"name": "Prossimi eventi", "url": url("/#eventi"), "icons": [{"src": url("/assets/icon-192.png") + "?v=" + env.globals["icon_v"], "sizes": "192x192"}]},
            {"name": "Eventi passati", "url": url("/eventi-passati"), "icons": [{"src": url("/assets/icon-192.png") + "?v=" + env.globals["icon_v"], "sizes": "192x192"}]},
            {"name": "Contatti", "url": url("/contattaci"), "icons": [{"src": url("/assets/icon-192.png") + "?v=" + env.globals["icon_v"], "sizes": "192x192"}]}]},
        ensure_ascii=False), encoding="utf-8")

    # Web app: pagina offline + service worker (la versione cambia a ogni pubblicazione)
    render("offline.html", "/offline", "offline.html", title="Sei offline | AREA30",
           description="Nessuna connessione a Internet.", no_sitemap=True, noindex_page=True)
    precache = [url("/"), url("/offline.html"), url("/assets/js/main.js") + "?v=" + env.globals["js_v"],
                url("/assets/logo-area30.png"), url("/assets/icon-192.png") + "?v=" + env.globals["icon_v"],
                url("/assets/fonts/big-shoulders.woff2"), url("/assets/fonts/manrope.woff2")]
    ver = hashlib.sha1("".join(sorted(p.name + str(p.stat().st_size) for p in OUT.rglob("*.html"))).encode()
                       + datetime.now(TZ).date().isoformat().encode()).hexdigest()[:10]
    sw = (ASSETS / "js" / "sw.js").read_text(encoding="utf-8")
    sw = sw.replace("__VERSIONE__", ver).replace("__BASE__", BASE_PATH).replace("__PRECACHE__", json.dumps(precache))
    if onesignal_id:
        # OneSignal gestisce ricezione e clic delle notifiche dentro lo stesso service worker
        sw = re.sub(r"/\* PUSH-PROPRIO-INIZIO[\s\S]*?PUSH-PROPRIO-FINE \*/", "", sw)
        # se OneSignal è bloccato (blocchi pubblicità, reti filtrate) l'app deve funzionare lo stesso
        clic = (ASSETS / "js" / "sw-clic.js").read_text(encoding="utf-8").replace("__BASE__", BASE_PATH)
        sw = (clic + f'try {{ importScripts("{os_files["OneSignalSDK.sw.js"]}"); }}'
              ' catch (e) { try { importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js"); } catch (e2) {} }\n') + sw
    (OUT / "sw.js").write_text(sw, encoding="utf-8")
    if onesignal_id:
        # stesso service worker anche con il nome predefinito di OneSignal: qualunque percorso usi, il comportamento è identico
        (OUT / "OneSignalSDKWorker.js").write_text(sw, encoding="utf-8")
    shutil.copy2(ASSETS / "favicon.ico", OUT / "favicon.ico")
    (OUT / ".nojekyll").write_text("")
    if (ROOT / "CNAME").exists() and not BASE_PATH:
        shutil.copy2(ROOT / "CNAME", OUT / "CNAME")

    print(f"Fatto: {len(pages)} pagine, {len(prossimi)} prossimi eventi, {len(passati)} eventi passati.")


def serve():
    import http.server
    import functools

    def stamp():
        return max(f.stat().st_mtime for d in (CONTENT, TEMPLATES, ASSETS, MEDIA) for f in d.rglob("*") if f.is_file())
    last = [stamp()]

    class H(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            p = self.path.split("?")[0]
            if not Path(p).suffix or p.endswith(".html"):
                s = stamp()
                if s > last[0]:
                    last[0] = s
                    try:
                        build()
                    except Exception as ex:  # noqa: BLE001
                        print("Errore di costruzione:", ex, file=sys.stderr)
            if BASE_PATH and p.startswith(BASE_PATH):
                p = p[len(BASE_PATH):] or "/"
            f = OUT / p.lstrip("/")
            if not f.exists() and (OUT / (p.lstrip("/") + ".html")).exists():
                p += ".html"
            elif f.is_dir() and not (f / "index.html").exists():
                pass
            if not (OUT / p.lstrip("/")).exists() and p != "/":
                self.path = "/404.html"
            else:
                self.path = p
            return super().do_GET()

    port = int(os.environ.get("PORT", 8000))
    print(f"Anteprima su http://localhost:{port}{BASE_PATH}/")
    http.server.ThreadingHTTPServer(("", port), functools.partial(H, directory=str(OUT))).serve_forever()


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        serve()
