# Sito AREA30 – note per Claude

Sito statico di AREA30 (service audio e luci, Sommariva del Bosco). Il proprietario non è uno sviluppatore: parla in italiano semplice, una domanda alla volta.

## Come è fatto
- `build.py` (Python + Jinja2 + Pillow) genera `_site/` da: `contenuti/` (dati), `media/` (foto originali), `templates/` (HTML), `assets/` (CSS, JS, font, logo).
- Pubblicazione: GitHub Actions (`.github/workflows/pubblica.yml`) su GitHub Pages a ogni push su `main` e ogni notte (gli eventi con data passata si spostano da soli in "Eventi passati").
- Pannello di gestione: Pages CMS, configurato in `.pages.yml`.
- Variabili del repository GitHub: `SITE_URL`, `BASE_PATH`, `NOINDEX` (vuote = sito definitivo su https://area30.it).
- Anteprima locale: `python build.py --serve` (porta 8000, si ricostruisce da sola quando cambi i file).

## Aggiungere un evento (richiesta tipica: "aggiungi questo concerto con questa locandina")
1. Copia la locandina in `media/` con nome breve senza spazi, es. `media/locandina-nome-evento-2027.jpg` (massimo ~2400 px sul lato lungo: ridimensiona se più grande).
2. Crea `contenuti/eventi/AAAA-MM-GG-nome-evento.md`:
   ```yaml
   ---
   titolo: NOME in Concerto
   rassegna: Controtempo Winter Edition 2027   # facoltativo
   data: '2027-01-30'
   ora: '21:00'
   apertura: '20:30'                            # facoltativo
   luogo: Teatro Bongioanni
   indirizzo: Viale Scuole, 13
   citta: Sommariva del Bosco
   descrizione: Una o due frasi.
   biglietti: https://www.ticket.it/...        # link della pagina biglietti
   locandina: /media/locandina-nome-evento-2027.jpg
   foto: []
   ---
   ```
3. Leggi la locandina per ricavare data, ora, luogo: non inventare nulla; se manca un dato, chiedi.
4. `python build.py` per controllare che non ci siano errori, poi commit e push su `main`.

Dati per Google (Event), sitemap, llms.txt, calendario .ics e anteprime per WhatsApp si aggiornano da soli.

## Regole
- Mai toccare i record DNS della posta (MX ecc.) di area30.it: la posta è su Aruba.
- Non cambiare nulla sul dominio senza conferma esplicita.
- Ogni immagine deve avere un testo alternativo descrittivo.
- Tutti i link in https.
