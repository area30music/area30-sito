#!/usr/bin/env python3
"""
Dati della pagina Live: YouTube (archivio + feed + diretta in corso) e Mixcloud (puntate).

- contenuti/live.yml            impostazioni (canali, giorni e orari delle dirette)
- contenuti/live-youtube.yml    archivio di tutte le puntate YouTube (si allunga da solo)

Uso da GitHub Actions per aggiungere all'archivio i nuovi video:
    python live.py aggiorna-archivio
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "contenuti"
ARCHIVIO = CONTENT / "live-youtube.yml"
TZ = ZoneInfo("Europe/Rome")
UA = "Mozilla/5.0 (compatible; AREA30-sito/1.0; +https://area30.it)"
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


def _get(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def config() -> dict:
    p = CONTENT / "live.yml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


def giorno_num(nome: str) -> int:
    """lunedì=0 … domenica=6 (come datetime.weekday)."""
    n = (nome or "").strip().lower().replace("ì", "i")
    for i, g in enumerate(GIORNI):
        if g.replace("ì", "i").startswith(n[:3]) and n:
            return i
    return 0


# ------------------------------------------------------------------ YouTube
def youtube_feed(canale_id: str) -> list[dict]:
    """Ultimi 15 video dal feed pubblico del canale (non serve nessuna chiave)."""
    try:
        xml = _get(f"https://www.youtube.com/feeds/videos.xml?channel_id={canale_id}")
    except Exception as ex:  # noqa: BLE001
        print(f"  ! feed YouTube non disponibile: {ex}", file=sys.stderr)
        return []
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    out = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        vid = e.findtext("yt:videoId", "", ns)
        pub = e.findtext("a:published", "", ns)
        out.append({"id": vid, "titolo": (e.findtext("a:title", "", ns) or "").strip(),
                    "data": pub[:10], "durata": None})
    return out


def youtube_archivio() -> list[dict]:
    if not ARCHIVIO.exists():
        return []
    return (yaml.safe_load(ARCHIVIO.read_text(encoding="utf-8")) or {}).get("video", []) or []


def youtube_video(canale_id: str) -> list[dict]:
    """Archivio + ultimi video del feed, senza doppioni, dal più recente."""
    per_id = {v["id"]: dict(v) for v in youtube_archivio() if v.get("id")}
    for v in youtube_feed(canale_id):
        if v["id"] in per_id:
            per_id[v["id"]]["titolo"] = v["titolo"] or per_id[v["id"]].get("titolo")
        else:
            per_id[v["id"]] = v
    lista = [v for v in per_id.values() if not v.get("nascosto")]
    for v in lista:
        d = int(v.get("durata") or 0)
        v["durata_txt"] = (f"{d // 3600}:{d % 3600 // 60:02d}:{d % 60:02d}" if d >= 3600 else f"{d // 60}:{d % 60:02d}") if d else ""
    lista.sort(key=lambda v: (str(v.get("data") or ""), v["id"]), reverse=True)
    return lista


def youtube_stato(canale_id: str) -> dict:
    """Controlla la pagina pubblica /live del canale: se c'è una diretta in corso ne restituisce l'ID."""
    stato = {"live": False, "id": "", "titolo": "", "programmata": None}
    try:
        html = _get(f"https://www.youtube.com/channel/{canale_id}/live").decode("utf-8", "ignore")
    except Exception as ex:  # noqa: BLE001
        print(f"  ! stato diretta YouTube non disponibile: {ex}", file=sys.stderr)
        return stato
    m = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([A-Za-z0-9_-]{11})"', html)
    if not m:
        return stato
    stato["id"] = m.group(1)
    t = re.search(r'<meta name="title" content="([^"]*)"', html)
    stato["titolo"] = t.group(1) if t else ""
    if re.search(r'"isLiveNow"\s*:\s*true', html):
        stato["live"] = True
    else:
        s = re.search(r'"scheduledStartTime"\s*:\s*"(\d+)"', html)
        if s:
            stato["programmata"] = datetime.fromtimestamp(int(s.group(1)), TZ).isoformat()
    return stato


# ------------------------------------------------------------------ Mixcloud
def mixcloud_puntate(utente: str) -> list[dict]:
    out, url = [], f"https://api.mixcloud.com/{utente}/cloudcasts/?limit=100"
    try:
        while url and len(out) < 500:
            d = json.loads(_get(url))
            for c in d.get("data", []):
                pics = c.get("pictures") or {}
                out.append({"key": c.get("key", ""), "titolo": c.get("name", ""), "url": c.get("url", ""),
                            "data": (c.get("created_time") or "")[:10], "durata": c.get("audio_length"),
                            "immagine": pics.get("extra_large") or pics.get("large") or ""})
            url = (d.get("paging") or {}).get("next")
    except Exception as ex:  # noqa: BLE001
        print(f"  ! Mixcloud non disponibile: {ex}", file=sys.stderr)
    return out


# ------------------------------------------------------------------ insieme
def dati_live() -> dict:
    cfg = config()
    yt, mc = cfg.get("youtube") or {}, cfg.get("mixcloud") or {}
    dati = {"cfg": cfg, "youtube": [], "mixcloud": [], "stato": {"live": False},
            "aggiornato": datetime.now(TZ).isoformat()}
    if yt.get("attivo") and yt.get("canale_id"):
        dati["youtube"] = youtube_video(yt["canale_id"])
        dati["stato"] = youtube_stato(yt["canale_id"])
    if mc.get("attivo") and mc.get("utente"):
        dati["mixcloud"] = mixcloud_puntate(mc["utente"])
    return dati


def aggiorna_archivio() -> bool:
    """Aggiunge all'archivio i video nuovi del feed. True se il file è cambiato."""
    cfg = (config().get("youtube") or {})
    if not cfg.get("canale_id"):
        return False
    archivio = youtube_archivio()
    noti = {v["id"] for v in archivio}
    nuovi = [v for v in youtube_feed(cfg["canale_id"]) if v["id"] not in noti]
    if not nuovi:
        print("Archivio YouTube già aggiornato.")
        return False
    archivio = nuovi + archivio
    archivio.sort(key=lambda v: (str(v.get("data") or ""), v["id"]), reverse=True)
    scrivi_archivio(archivio)
    print(f"Archivio YouTube: aggiunti {len(nuovi)} video.")
    return True


def scrivi_archivio(video: list[dict]) -> None:
    testa = ("# Archivio delle puntate YouTube mostrate nella pagina Live.\n"
             "# Si aggiorna da solo con i nuovi video. Per nascondere un video aggiungi:  nascosto: true\n")
    ARCHIVIO.write_text(testa + yaml.safe_dump({"video": video}, allow_unicode=True, sort_keys=False, width=1000),
                        encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "aggiorna-archivio":
        aggiorna_archivio()
    else:
        d = dati_live()
        print(json.dumps({"youtube": len(d["youtube"]), "mixcloud": len(d["mixcloud"]), "stato": d["stato"]},
                         ensure_ascii=False, indent=1))
