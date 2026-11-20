#!/usr/bin/env python3
"""
Invia una notifica OneSignal per ogni NUOVO evento futuro.

Viene eseguito da GitHub Actions dopo la pubblicazione del sito:
    python notifica.py contenuti/eventi/2027-01-30-nome.md [altri file...]

Serve:
  - onesignal_app_id in contenuti/sito.yml
  - il segreto ONESIGNAL_REST_API_KEY nelle impostazioni del repository GitHub
Un evento con "notifica: false" non viene annunciato.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

import build  # riusa lettura contenuti, date e immagini del generatore

API = "https://api.onesignal.com/notifications?c=push"


def main(files: list[str]) -> int:
    key = os.environ.get("ONESIGNAL_REST_API_KEY", "").strip()
    site = build.load_yaml(build.CONTENT / "sito.yml")
    app_id = str(site.get("onesignal_app_id") or "").strip()
    if not key or not app_id:
        print("Notifiche non configurate (manca App ID o chiave): nessun invio.")
        return 0
    if build.NOINDEX:
        print("Sito in anteprima: nessun invio.")
        return 0

    oggi = build.datetime.now(build.TZ).date()
    nuovi = set()
    for f in files:
        p = build.ROOT / f
        if f.startswith("contenuti/eventi/") and f.endswith(".md") and p.exists():
            fm, _ = build.read_front_matter(p)
            if fm.get("notifica") is not False:  # "notifica: false" = non annunciare
                nuovi.add(build.slugify(p.stem))
    eventi = [e for e in build.load_events(oggi) if e.slug in nuovi]
    imgs = build.ImagePipeline()
    for e in eventi:
        e.og = imgs.og(e.locandina, e.slug, poster=True, titolo=e.titolo) if e.locandina else ""

    inviati = 0
    for e in eventi:
        if e.passato:
            continue
        quando = build.data_it(e.data) + (f" ore {e.ora_it}" if e.ora else "")
        testo = f"{quando.capitalize()}" + (f" · {e.luogo}" if e.luogo else "") + (" · Biglietti disponibili" if e.biglietti else "")
        titolo = f"Nuovo evento: {e.titolo}"
        body = {
            "app_id": app_id,
            "target_channel": "push",
            "included_segments": ["Total Subscriptions"],
            "headings": {"en": titolo, "it": titolo},
            "contents": {"en": testo, "it": testo},
            "url": build.link_notifica("evento-" + e.slug, titolo, testo, build.abs_url(e.path), e.og or ""),
            "chrome_web_icon": build.abs_url("/assets/icon-192.png"),
            "chrome_web_badge": build.abs_url("/assets/icon-192.png"),
            "web_push_topic": e.slug,
        }
        if e.og:
            body["chrome_web_image"] = e.og
        try:
            r = build.onesignal_api("POST", API, key, body)
            print(f"Notifica inviata per «{e.titolo}»: {str(r)[:200]}")
            inviati += 1
        except urllib.error.HTTPError as ex:
            print(f"Errore OneSignal per «{e.titolo}»: {ex.code} {ex.read().decode()[:300]}", file=sys.stderr)
            return 1
    print(f"Notifiche inviate: {inviati}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
