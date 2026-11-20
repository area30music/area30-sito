# Guida al nuovo sito AREA30

- **Anteprima provvisoria:** https://area30music.github.io/area30-sito/ (nascosta a Google finché non colleghiamo area30.it)
- **Codice del sito:** https://github.com/area30music/area30-sito
- **Pannello di gestione:** https://app.pagescms.org

---

## 1. Il pannello di gestione (Pages CMS)

È gratuito e ci entri solo tu, con il tuo account GitHub **area30music**.

### Primo accesso (una volta sola)
1. Apri https://app.pagescms.org e premi **Sign in with GitHub**.
2. Accedi con l'account GitHub **area30music** e premi **Authorize**.
3. Pages CMS ti chiede di installare la sua "GitHub App": premi **Install**, scegli **Only select repositories**, seleziona **area30-sito** e conferma.
4. Torni al pannello: scegli **area30music / area30-sito**, ramo **main**.

A sinistra trovi: **Eventi**, **Galleria foto "Dal vivo"**, **Parlano di noi**, **I nostri servizi**, **Impostazioni del sito**.

### Aggiungere un evento
1. **Eventi** → **Add an entry** (Aggiungi).
2. Compila: nome, rassegna (facoltativa), data, ora (es. `21:00`), apertura porte, luogo, indirizzo, città, descrizione breve, link dei biglietti di ticket.it.
3. **Locandina**: premi sul riquadro e carica il file direttamente dal computer o dal telefono.
4. Premi **Save**. Dopo 2-3 minuti l'evento è online: in Home, con conto alla rovescia, pulsante "Acquista qui", "Aggiungi al calendario" e i dati per Google.

### Modificare o eliminare un evento
- **Modificare:** Eventi → clic sull'evento → cambia → **Save**.
- **Eliminare:** Eventi → menu **⋯** accanto all'evento → **Delete**.

### Dopo il concerto
Non devi fare nulla: la notte dopo la data l'evento si sposta da solo in **Eventi passati**.
Se vuoi, apri l'evento e nel campo **Foto della serata** carica le foto: compariranno nella sua pagina, sfogliabili a tutto schermo.

### Galleria "Dal vivo"
Galleria foto → **Add an item** → carica la foto e scrivi una breve descrizione di cosa si vede → **Save**.

### Video di apertura
Impostazioni del sito → **Video di sfondo**: carica un MP4 breve (10-20 secondi, senza audio, massimo 8 MB). Per toglierlo, svuota il campo.

---

## 2. Collegare il dominio area30.it (solo dopo la tua approvazione)

> ⚠️ La posta **info@area30.it** resta su Aruba e continua a funzionare: si cambiano **solo** i record del sito.
> **Non toccare** i record **MX**, il record **mx**, i record **TXT** (SPF) né altri record della posta.

Nel pannello Aruba → **Gestione DNS** del dominio area30.it:

| Cosa | Tipo | Nome | Valore |
|---|---|---|---|
| Sostituisci il record A del dominio principale (oggi `62.149.189.6`) con questi 4 | A | @ (area30.it) | `185.199.108.153` · `185.199.109.153` · `185.199.110.153` · `185.199.111.153` |
| Aggiungi (facoltativo, consigliato) | AAAA | @ (area30.it) | `2606:50c0:8000::153` · `2606:50c0:8001::153` · `2606:50c0:8002::153` · `2606:50c0:8003::153` |
| Modifica www | CNAME | www | `area30music.github.io` |

Poi lo comunico a GitHub, attivo l'HTTPS e tolgo il blocco per Google. Il passaggio richiede da pochi minuti a qualche ora.

---

## 3. Google Search Console (dopo il collegamento del dominio)
1. Apri https://search.google.com/search-console e accedi con il tuo account Google.
2. **Aggiungi proprietà** → scegli **Dominio** → scrivi `area30.it`.
3. Google ti dà un record **TXT** (inizia con `google-site-verification=`). In Aruba → Gestione DNS → **aggiungi** un nuovo record TXT con nome `@` e quel valore. **Non modificare** il TXT esistente `v=spf1…` della posta: aggiungine uno nuovo.
4. Torna in Search Console e premi **Verifica** (può servire qualche ora).
5. Menu **Sitemap** → scrivi `sitemap.xml` → **Invia**.
6. Menu **Controllo URL** → incolla `https://area30.it/` → **Richiedi indicizzazione**.

## 4. Scheda Google Maps (Google Business Profile)
1. Apri https://business.google.com e cerca "AREA30 Sommariva del Bosco": se la scheda esiste, premi **Rivendica**; altrimenti **Aggiungi la tua attività**.
2. Categoria principale: **Servizio di noleggio di attrezzature audiovisive** (oppure "Tecnico del suono"); aggiungi come secondarie **Organizzatore di eventi**, **Studio di registrazione**, **Sala prove**.
3. Indirizzo: Via Mario Groppo, 4 – 12048 Sommariva del Bosco (CN). Controlla che lo spillo sulla mappa sia esattamente sulla sede.
4. Telefono `0172 56 00 87`, sito `https://area30.it`, orari di apertura.
5. Completa la verifica (cartolina, telefono o video).
6. Carica 10-15 foto (palco, impianti, studio, sala prove) e il logo.
7. Ogni concerto pubblicalo anche come **Evento** nella scheda, con la locandina e il link "Acquista".
8. Chiedi ai clienti soddisfatti una recensione e rispondi sempre.

Nome, indirizzo e telefono devono essere **identici** su sito, scheda Google e social.

---

## 5. App e notifiche

### Installare l'app
- **iPhone / iPad (Safari):** apri il sito → pulsante **Condividi** → **Aggiungi alla schermata Home**.
- **Android (Chrome):** pulsante **Installa l'app** sul sito, oppure menu ⋮ → **Installa app**.
- **Mac (Safari):** menu **File** → **Aggiungi al Dock**. Con Chrome: icona di installazione nella barra degli indirizzi.
- **Il pannello di gestione come app sul Mac:** apri https://app.pagescms.org in Safari → **File → Aggiungi al Dock**.

### Attivare le notifiche con OneSignal (dopo il collegamento di area30.it)
1. Vai su https://onesignal.com e crea un account gratuito.
2. **New App/Website** → nome `AREA30` → scegli **Web** → **Next**.
3. Scegli **Typical Site** e compila:
   - **Site Name:** `AREA30`
   - **Site URL:** `https://area30.it`
   - **Default Icon:** carica l'icona https://area30.it/assets/icon-192.png (scaricala e caricala)
   - **Permission Prompt:** non aggiungere nulla (sul sito c'è già il pulsante "Avvisami dei nuovi concerti").
   - Se c'è la sezione **Advanced / Service Workers**: attiva la personalizzazione e scrivi percorso `/`, file `sw.js` (in entrambi i campi), scope `/`.
4. **Save**. Copia l'**App ID** (una sequenza tipo `1a2b3c4d-…`) e mandamelo pure in chat: non è segreto.
5. In OneSignal → **Settings → Keys & IDs** → **Add Key** → nome `GitHub` → copia la chiave.
   ⚠️ **Questa chiave è segreta: non mandarla in chat.** Inseriscila tu su GitHub:
   https://github.com/area30music/area30-sito/settings/secrets/actions → **New repository secret** →
   Name: `ONESIGNAL_REST_API_KEY` · Secret: incolla la chiave → **Add secret**.

Da quel momento, ogni volta che crei un **nuovo evento futuro** dal pannello (con l'interruttore "Invia una notifica" acceso), chi ha attivato le notifiche riceve dopo pochi minuti l'avviso con la locandina.
Su iPhone e iPad le notifiche arrivano solo a chi ha installato l'app sulla schermata Home (iOS 16.4 o successivo).
