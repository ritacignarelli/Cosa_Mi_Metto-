# Cosa Mi Metto?

Applicazione desktop in **Python + Tkinter**, con archivio **SQLite**, per gestire
l'armadio digitale, comporre look, ricevere proposte automatiche e tenere il
diario di cosa si indossa.

Progetto per il corso di Python — ITS ICT Piemonte, a.s. 2026/2027.

## Funzionalità

**Essenziali**

- Sezioni dell'armadio personalizzabili (aggiunta, rinomina, eliminazione).
- Caricamento dei capi con foto, nome, sezione, colore, stagione e occasione.
- Griglia con miniature e dettaglio del capo con foto ingrandita.
- Modifica ed eliminazione dei capi, con conferma prima di eliminare.
- Ricerca per nome/colore e **2 filtri**: sezione e stagione.
- Creazione e salvataggio dei look, con anteprima affiancata.

**Aggiuntive richieste**

- **Idee / Sorprendimi**: propone un look completo in base a stagione e occasione.
- **Diario dell'indossato**: registra i capi indossati per giorno e mostra i capi
  più usati e quelli mai usati.

Non sono incluse la «Valigia intelligente» e la funzione di backup, perché fuori
dalle richieste concordate.

## Requisiti

- Python 3.10 o superiore
- Pillow (`pip install -r requirements.txt`)
- Tkinter, incluso in Python su Windows. Su alcune distribuzioni Linux:
  `sudo apt install python3-tk`

## Avvio

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Al primo avvio vengono create automaticamente la cartella `data/` con il
database `data/armadio.db`, la cartella `data/foto/` e le otto sezioni iniziali.

## Come provare l'app in due minuti

1. **Aggiungi capo**: scegli una foto, compila i dati e salva. Il ruolo nel look
   viene proposto in base alla sezione (es. «Pantaloni» → parte inferiore), ma
   si può cambiare.
2. Aggiungi almeno una parte superiore, una parte inferiore e un paio di scarpe
   della stessa stagione.
3. **Look**: scegli i capi nei menu, guarda l'anteprima e salva il look con un nome.
4. **Idee**: imposta stagione e occasione, premi «Sorprendimi» e salva la proposta.
5. **Diario**: scegli la data, seleziona un capo e premi «Segna come indossato».
   In basso a destra compaiono i capi più usati e quelli mai usati.
6. **Armadio**: prova ricerca e i due filtri (sezione, stagione), apri un capo e
   modificalo o eliminalo.

## Struttura del progetto

```
main.py              avvio dell'applicazione
database.py          schema SQLite, query e regole di accesso ai dati
logica.py            importazione foto e algoritmo «Sorprendimi»
requirements.txt     dipendenze (Pillow)
ui/
  finestra.py        finestra principale, schede e barra di stato
  stile.py           tema e colori
  widgets.py         miniature, area scorrevole, anteprima look
  form_capo.py       form condiviso per aggiungere/modificare un capo
  armadio.py         scheda Armadio
  aggiungi_capo.py   scheda Aggiungi capo
  look.py            scheda Look
  idee.py            scheda Idee
  diario.py          scheda Diario
data/                creata al primo avvio (database e foto)
```

La parte dati è separata dalla grafica: `database.py` contiene tutto l'SQL e
l'interfaccia non scrive mai query. Le foto vengono copiate in `data/foto/`,
ridimensionate e salvate in JPEG; nel database si conserva solo il nome del file.
Tutti i dati restano sul computer e non viene inviato nulla in rete.

Il codice è commentato in italiano: accanto alle righe principali ci sono
commenti che spiegano cosa fa ogni passaggio, utili anche per l'esposizione
orale del progetto.

## Scelte di progetto

- **Ruolo nel look**: ogni capo ha un ruolo (parte superiore, parte inferiore,
  scarpe, borsa, accessorio, altro), dedotto dal nome della sezione e
  modificabile. Serve per comporre look e suggerimenti anche con sezioni
  personalizzate.
- **Filtri**: sono due (sezione e stagione). La casella «Cerca» è una ricerca
  testuale per nome, colore o sezione, non un terzo filtro.
- **Stagione «Tutte»**: un capo con questa stagione compare in qualsiasi filtro
  stagionale.
- **Suggerimento**: se non ci sono abbastanza capi per l'occasione scelta, l'app
  ripiega sui capi della stessa stagione e lo segnala; se mancano comunque i
  ruoli obbligatori, spiega quali capi aggiungere.
- **Eliminazioni**: un capo eliminato sparisce anche dai look e dal diario; una
  sezione può essere eliminata solo se è vuota.
