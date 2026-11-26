#!/usr/bin/env python3
"""
Notifiche scritte dal pannello (Pages CMS → "Notifiche").

Ogni file in contenuti/notifiche/*.yml è una notifica:
    titolo, messaggio, link, immagine, quando (vuoto = subito), invia (true = da inviare)

GitHub Actions, dopo ogni salvataggio, esegue:
    python notifiche_pannello.py --salvati <file...> --eliminati <file...>

- "invia: true"  → la notifica parte subito o viene programmata su OneSignal per "quando";
                   poi il file viene aggiornato: invia=false, stato e codice OneSignal.
- Per reinviarla basta riattivare "Pronta da inviare" e salvare (si può cambiare anche data e ora).
- Se una notifica ancora programmata viene modificata o eliminata, quella vecchia viene annullata.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

import build

API = "https://api.onesignal.com/notifications"
FMT_IT = "%d/%m/%Y alle %H:%M"


def chiama(metodo: str, url: str, key: str, body: dict | None = None) -> dict:
    return build.onesignal_api(metodo, url, key, body)


def quando_di(v) -> datetime | None:
    if not v:
        return None
    if isinstance(v, datetime):
        return v.replace(tzinfo=build.TZ) if v.tzinfo is None else v
    try:
        d = datetime.fromisoformat(str(v).strip().replace(" ", "T"))
    except ValueError:
        return None
    return d.replace(tzinfo=build.TZ) if d.tzinfo is None else d


def link_assoluto(v: str) -> str:
    v = (v or "").strip()
    if not v:
        return build.abs_url("/")
    if v.startswith("http"):
        return v
    return build.abs_url(v if v.startswith("/") else "/" + v)


def annulla(app_id: str, key: str, nid: str) -> None:
    try:
        chiama("DELETE", f"{API}/{nid}?app_id={app_id}", key)
        print(f"  annullata la notifica programmata {nid}")
    except urllib.error.HTTPError as ex:  # già inviata o inesistente: va bene così
        print(f"  (non annullabile {nid}: {ex.code})")


def vecchio_contenuto(path: str) -> dict:
    before = os.environ.get("BEFORE_SHA", "")
    if not before or set(before) == {"0"}:
        return {}
    try:
        out = subprocess.run(["git", "show", f"{before}:{path}"], capture_output=True, text=True, check=True).stdout
        return build.live_mod.yaml_load(out) or {}
    except subprocess.CalledProcessError:
        return {}


def main(argv: list[str]) -> int:
    salvati, eliminati, cur = [], [], None
    for a in argv:
        if a in ("--salvati", "--eliminati"):
            cur = salvati if a == "--salvati" else eliminati
        elif cur is not None and a.startswith("contenuti/notifiche/"):
            cur.append(a)

    key = os.environ.get("ONESIGNAL_REST_API_KEY", "").strip()
    site = build.load_yaml(build.CONTENT / "sito.yml")
    app_id = str(site.get("onesignal_app_id") or "").strip()
    pronto = bool(key and app_id and not build.NOINDEX)
    adesso = datetime.now(build.TZ)

    # Notifiche eliminate dal pannello: se erano ancora programmate, si annullano
    for path in eliminati:
        old = vecchio_contenuto(path)
        nid, q = old.get("onesignal_id"), quando_di(old.get("quando"))
        if pronto and nid and q and q > adesso:
            annulla(app_id, key, nid)

    modificati = []
    imgs = build.ImagePipeline()
    for path in salvati:
        p = build.ROOT / path
        if not p.exists():
            continue
        d = build.live_mod.yaml_load(p.read_text(encoding="utf-8")) or {}
        if not d.get("invia"):
            continue
        print(f"Notifica: {path}")
        if not pronto:
            d["stato"] = "Non inviata: le notifiche non sono ancora configurate (manca la chiave OneSignal su GitHub)"
            p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
            modificati.append(path)
            continue

        # se c'era una versione ancora programmata, la si sostituisce
        old_id, old_q = d.get("onesignal_id"), quando_di(d.get("quando_programmato"))
        if old_id and old_q and old_q > adesso:
            annulla(app_id, key, old_id)

        titolo = str(d.get("titolo") or "AREA30").strip()
        testo = str(d.get("messaggio") or "").strip() or titolo
        body = {
            "app_id": app_id, "target_channel": "push", "included_segments": ["Total Subscriptions"],
            "headings": {"en": titolo, "it": titolo}, "contents": {"en": testo, "it": testo},
            "url": build.link_notifica(p.stem, titolo, testo, link_assoluto(d.get("link", "")) if d.get("link") else "",
                                       imgs.og(str(d["immagine"]), "notifica-" + p.stem, poster=True, titolo=titolo) if d.get("immagine") else ""),
            "chrome_web_icon": build.abs_url("/assets/icon-192.png"),
        }
        if d.get("immagine"):
            img = imgs.og(str(d["immagine"]), "notifica-" + p.stem, poster=True, titolo=titolo)
            body["chrome_web_image"] = img
        q = quando_di(d.get("quando"))
        if q and q > adesso:
            body["send_after"] = q.strftime("%Y-%m-%d %H:%M:%S GMT%z")
        try:
            r = chiama("POST", API + "?c=push", key, body)
        except urllib.error.HTTPError as ex:
            d["stato"] = f"Errore OneSignal {ex.code}: {ex.read().decode()[:200]}"
            print("  " + d["stato"], file=sys.stderr)
        else:
            d["onesignal_id"] = r.get("id", "")
            if q and q > adesso:
                d["quando_programmato"] = q.strftime("%Y-%m-%dT%H:%M")
                d["stato"] = f"Programmata per il {q.strftime(FMT_IT)}"
            else:
                d.pop("quando_programmato", None)
                d["stato"] = f"Inviata il {adesso.strftime(FMT_IT)}"
            print("  " + d["stato"])
        if d.get("onesignal_id") and not str(d.get("stato", "")).startswith("Errore"):
            d["inviata_il"] = adesso.strftime("%Y-%m-%dT%H:%M")
        d["invia"] = False  # per reinviarla: riattiva "Pronta da inviare" e salva
        p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
        modificati.append(path)

    Path(os.environ.get("ELENCO_MODIFICATI", "/dev/null")).write_text("\n".join(modificati))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
