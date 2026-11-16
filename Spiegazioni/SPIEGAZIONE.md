# SPIEGAZIONE

## Come è stato costruito «Cosa Mi Metto?», passo per passo

Questo documento racconta **in ordine cronologico** come sono nati i file del progetto:
dalla prima analisi fino all'ultima revisione. Non è un manuale d'uso dell'applicazione:
è la ricostruzione del lavoro di costruzione, utile per capire il progetto e per
spiegarlo durante l'esposizione orale.

---

## 1. Come è stata ricostruita la cronologia

La cronologia non è inventata: è stata ricavata incrociando alcuni indizi presenti
nel progetto.

1. **La data del documento di analisi**: `AnalisiFattibilità.pdf` è del **23/10/2026**.
   È quindi il primo documento del progetto.
2. **Le date di creazione dei file**: tutti i file Python e di configurazione sono
   stati creati il **28/10/2026**, tra le **17:49** e le **17:52**. L'ordine dei
   timestamp corrisponde quasi perfettamente all'ordine delle dipendenze nel codice.
3. **Gli import tra i file**: per esempio `main.py` importa `ui/finestra.py`, che a
   sua volta importa tutte le schede; `ui/armadio.py` importa `ui/form_capo.py`; ecc.
   Un file che viene importato da un altro è stato necessariamente pensato prima.
4. **Le date di ultima modifica**: il **3 e 4 novembre** c'è stata una seconda passata
   di revisione, con rifiniture ai commenti, alla documentazione e ai dettagli.
5. **La data del database**: `data/armadio.db` è del **04/11/2026 15:08:57**, cioè è
   stato creato alla prima esecuzione dell'app, non scritto a mano.

> Nota importante: i file sono stati creati in una sessione molto concentrata il
> 28 ottobre. La divisione in quattro settimane descritta nel PDF era la
> pianificazione iniziale; la cronologia reale dei file è quella indicata dai
> timestamp. La seconda passata di novembre è stata la fase di rifinitura.

---

## 2. Cronologia in sintesi

| # | Data e ora | File | Prima cosa fatta |
|---|------------|------|------------------|
| 0 | 23/10/2026 16:15 | `AnalisiFattibilità.pdf` | Analisi del problema, funzionalità e pianificazione |
| 1 | 28/10/2026 17:49:31 | `database.py` | Schema SQLite e tutte le operazioni sui dati |
| 2 | 28/10/2026 17:49:38 | `logica.py` | Importazione foto e algoritmo «Sorprendimi» |
| 3 | 28/10/2026 17:50:07 | `ui/stile.py` | Colori, font e stili comuni dell'interfaccia |
| 4 | 28/10/2026 17:50:15 | `ui/widgets.py` | Miniatura, area scorrevole e anteprima look |
| 5 | 28/10/2026 17:50:33 | `ui/__init__.py` | Rende `ui/` un pacchetto Python |
| 6 | 28/10/2026 17:50:33 | `ui/form_capo.py` | Form condiviso per aggiungere/modificare un capo |
| 7 | 28/10/2026 17:50:56 | `ui/armadio.py` | Scheda Armadio: sezioni, filtri, griglia e dettaglio |
| 8 | 28/10/2026 17:51:01 | `ui/aggiungi_capo.py` | Scheda Aggiungi capo |
| 9 | 28/10/2026 17:51:16 | `ui/look.py` | Scheda Look: composizione e look salvati |
| 10 | 28/10/2026 17:51:27 | `ui/idee.py` | Scheda Idee con il pulsante «Sorprendimi» |
| 11 | 28/10/2026 17:51:45 | `ui/diario.py` | Scheda Diario e statistiche dei capi |
| 12 | 28/10/2026 17:51:56 | `ui/finestra.py` | Finestra principale con schede e barra di stato |
| 13 | 28/10/2026 17:51:56 | `main.py` | Punto di avvio dell'applicazione |
| 14 | 28/10/2026 17:51:56 | `requirements.txt` | Dipendenza Pillow |
| 15 | 28/10/2026 17:52:38 | `README.md` | Istruzioni, funzionalità e scelte di progetto |
| 16 | 28/10/2026 17:52:55 | `.gitignore` | Esclusione di `.venv/`, `__pycache__/` e `data/` |
| 17 | 03/11/2026 | `README.md`, `main.py` | Prime rifiniture |
| 18 | 04/11/2026 15:08:57 | `data/armadio.db` | Database creato automaticamente al primo avvio |
| 19 | 04/11/2026 15:09–15:17 | vari file | Revisione finale, commenti e rifiniture |

---

## 3. Fase 0 — L'idea e l'analisi (23 ottobre)

Il progetto è partito da un bisogno quotidiano: **«l'armadio è pieno ma non c'è
niente da mettere»**. Prima di scrivere una sola riga di codice è stato preparato
il documento `AnalisiFattibilità.pdf`, che contiene:

- l'**oggetto** dell'applicazione: un armadio digitale con foto, sezioni
  personalizzabili, look salvati e diario;
- lo **scopo**: avere tutto in un posto, scegliere più in fretta, capire quali capi
  si usano davvero e preparare la valigia;
- gli **strumenti** scelti: Python, Tkinter per la grafica, Pillow per le foto,
  SQLite per i dati, Visual Studio Code e Git;
- le **schermate previste**: Armadio, Aggiungi capo, Look, Idee, Valigia, Diario;
- le **funzionalità essenziali e aggiuntive**;
- la **privacy**: tutti i dati restano sul computer, nulla viene inviato in rete;
- le **tempistiche** in quattro settimane.

In questa fase sono state prese alcune decisioni importanti:

- la parte **dati** doveva essere separata dalla parte **grafica**;
- le foto dovevano essere copiate in una cartella locale e non salvate dentro il
  database;
- il progetto finale avrebbe incluso **Armadio, Aggiungi capo, Look, Idee e Diario**.

Nel PDF comparivano anche la **Valigia** e il **backup**, ma il progetto consegnato
non le comprende: il `README.md` finale lo dice esplicitamente. Sono state escluse
per restare dentro le richieste concordate e concentrare il lavoro sulle funzioni
principali.

---

## 4. Fase 1 — Il cuore dei dati: `database.py` (28/10, 17:49:31)

È stato il **primo file di codice**. La scelta è stata deliberata: senza un archivio
solido, le schede non avrebbero avuto nulla da mostrare. Il principio guida è stato:

> **L'interfaccia non scrive mai SQL.** Tutta la parte dati passa da `database.py`.

### 4.1 Import e percorsi

All'inizio del file sono stati importati i moduli necessari:

- `sqlite3` per il database;
- `unicodedata` per confrontare i nomi delle sezioni senza accenti;
- `date` per controllare le date del diario;
- `Path` per gestire i percorsi in modo portabile.

Sono state definite le cartelle:

```text
data/          → dati dell'app
data/foto/     → copie delle foto dei capi
data/armadio.db → file SQLite
```

`BASE_DIR` viene calcolato da `Path(__file__).resolve().parent`, così l'app funziona
anche se viene spostata in un'altra cartella.

### 4.2 Costanti del progetto

Sono state raccolte in un unico punto:

- le **otto sezioni iniziali**: Maglie corte, Maglie lunghe, Pantaloni,
  Pantaloncini, Gonne, Scarpe, Borse, Accessori;
- le **stagioni**: Primavera, Estate, Autunno, Inverno, Tutte;
- le **occasioni**: Quotidiano, Sport, Elegante;
- i **ruoli** del look: parte superiore, parte inferiore, scarpe, borsa,
  accessorio, altro;
- i **ruoli obbligatori** per salvare un look: parte superiore, parte inferiore e
  scarpe;
- i **ruoli facoltativi**: borsa e accessorio.

È stata aggiunta anche la funzione `ruolo_da_sezione()`: deduce il ruolo dal nome
della sezione. Per esempio «Pantaloni» diventa `bottom`, «Scarpe» diventa `scarpe`.
Serve per proporre automaticamente il ruolo nel form, anche con sezioni
personalizzate.

### 4.3 La classe `Database`

Il costruttore `__init__` fa cinque cose, in quest'ordine:

1. crea la cartella `data/` se non esiste;
2. crea la cartella `data/foto/` se non esiste;
3. apre la connessione a SQLite;
4. imposta `row_factory = sqlite3.Row`, così le righe si leggono anche per nome
   (`riga["nome"]`) e non solo per posizione;
5. attiva `PRAGMA foreign_keys = ON`, perché SQLite controlla le chiavi esterne
   solo se glielo si chiede esplicitamente.

Poi chiama `_crea_schema()` e `_sezioni_iniziali()`.

### 4.4 Lo schema SQL

Sono state create cinque tabelle:

| Tabella | A cosa serve |
|---------|--------------|
| `sezioni` | Le sezioni dell'armadio, con nome unico e ordine |
| `capi` | I capi, collegati a una sezione, con ruolo, colore, stagione, occasione e foto |
| `look` | I look salvati, con nome e data |
| `look_capi` | I capi che compongono ogni look, con il ruolo dentro il look |
| `diario` | I capi indossati, con data e vincolo di unicità per giorno |

Sono stati aggiunti anche due indici:

- `idx_capi_sezione`, per velocizzare la ricerca per sezione;
- `idx_diario_data`, per velocizzare la lettura del diario per data.

Le relazioni importanti sono:

- un capo appartiene a una sezione;
- un look contiene più capi;
- se si elimina un look, i suoi collegamenti spariscono in cascata;
- se si elimina un capo, spariscono anche i collegamenti a look e diario;
- una sezione **non** può essere eliminata se contiene ancora capi.

### 4.5 Le sezioni iniziali

`_sezioni_iniziali()` controlla se la tabella `sezioni` è vuota. Se lo è, inserisce
le otto sezioni di partenza con `executemany`, dentro una transazione: o vengono
salvate tutte, o nessuna. Questo evita che un errore a metà lasci il database
incompleto.

### 4.6 I metodi per le sezioni

Sono state create le operazioni di base:

- `sezioni()` e `nomi_sezioni()` per leggere l'elenco;
- `sezione_per_nome()` per cercare una sezione ignorando maiuscole/minuscole;
- `aggiungi_sezione()` per creare una nuova sezione in fondo all'elenco;
- `rinomina_sezione()` per cambiare nome;
- `elimina_sezione()` per eliminarla solo se è vuota.

I controlli sono stati messi **nel database**, non solo nell'interfaccia: un nome
vuoto o duplicato solleva un `ValueError` con un messaggio comprensibile.

### 4.7 I metodi per i capi

Sono state implementate le operazioni principali:

- `capi()` per leggere l'elenco applicando i filtri;
- `capo()` per leggere un singolo capo;
- `aggiungi_capo()` per inserire un nuovo capo;
- `modifica_capo()` per aggiornare un capo e cancellare la vecchia foto se viene
  sostituita;
- `elimina_capo()` per eliminare capo, foto e collegamenti;
- `conta_capi()` per il conteggio nella barra di stato.

La query di `capi()` è costruita a pezzi: si parte da una base e si aggiungono
condizioni `AND ...` solo per i filtri attivi. I valori non vengono mai incollati
dentro la query: si usano i segnaposto `?` e una lista di parametri. Questo protegge
dalle SQL injection e gestisce correttamente apici e virgolette.

I filtri previsti sono:

1. **sezione**;
2. **stagione** (un capo con stagione «Tutte» compare in qualsiasi filtro);
3. **testo libero** su nome, colore o nome della sezione.

### 4.8 La gestione delle foto

Nel database viene salvato **solo il nome del file**, non l'immagine. La foto vera
sta in `data/foto/`.

- `percorso_foto()` trasforma il nome in un percorso completo;
- `_elimina_file_foto()` cancella il file solo se si trova davvero dentro
  `data/foto/`, per evitare di cancellare per errore file esterni.

La cancellazione della vecchia foto avviene dopo la modifica del capo: se la foto
è cambiata, il vecchio file non serve più e viene rimosso.

### 4.9 I look

Sono state create:

- `salva_look()`: crea il look e collega i capi scelti;
- `look_salvati()`: elenca i look con il numero di capi;
- `capi_look()`: legge i capi di un look;
- `elimina_look()`: elimina il look e, in cascata, i suoi collegamenti.

`salva_look()` controlla che il nome non sia vuoto, che ci sia almeno un capo e che
ogni capo scelto esista ancora.

### 4.10 Il diario

Sono state aggiunte:

- `aggiungi_voce_diario()`: segna un capo come indossato in una data;
- `voci_diario()`: legge i capi indossati in una data;
- `elimina_voce_diario()`: rimuove una voce;
- `capi_piu_usati()`: conta quante volte compare ogni capo;
- `capi_mai_usati()`: trova i capi senza nessuna voce nel diario.

La data viene controllata con `date.fromisoformat()`: deve essere nel formato
`AAAA-MM-GG`. Il vincolo `UNIQUE (data, capo_id)` impedisce di segnare due volte lo
stesso capo nello stesso giorno.

### 4.11 I suggerimenti

`capi_per_suggerimento()` restituisce i capi adatti a una stagione e, se indicata,
a un'occasione. Include i capi con stagione «Tutte» e esclude i capi con ruolo
«altro», perché non servono a comporre un look automatico.

Infine `chiudi()` chiude la connessione quando l'app termina, per evitare che il
file del database resti bloccato, soprattutto su Windows.

---

## 5. Fase 2 — La logica applicativa: `logica.py` (28/10, 17:49:38)

Creato subito dopo `database.py`, perché usa la classe `Database` e le costanti dei
ruoli. Contiene le regole che non sono né pura grafica né pura SQL.

### 5.1 Importazione delle foto

`importa_foto()`:

1. controlla che il file scelto esista;
2. apre l'immagine con Pillow;
3. corregge l'orientamento con `ImageOps.exif_transpose`, utile per le foto da
   smartphone;
4. ridimensiona il lato più lungo a **1600 pixel** con `thumbnail`, mantenendo le
   proporzioni;
5. converte l'immagine in RGB, mettendo uno sfondo bianco se c'era trasparenza;
6. genera un nome unico con `uuid.uuid4().hex`;
7. salva una copia JPEG con qualità 88 in `data/foto/`;
8. restituisce **solo il nome del file**, che verrà scritto nel database.

Il nome unico evita di sovrascrivere foto con lo stesso nome. Il ridimensionamento
avviene una volta sola, al momento dell'importazione: dopo, l'app usa sempre la
copia ottimizzata.

### 5.2 Controllo del look

`valida_selezione()` verifica che siano presenti i tre ruoli obbligatori: parte
superiore, parte inferiore e scarpe. Se mancano, costruisce un messaggio con
l'elenco dei ruoli mancanti.

### 5.3 Algoritmo «Sorprendimi»

L'algoritmo è diviso in tre funzioni:

- `_raggruppa()`: divide i capi per ruolo;
- `_componi()`: sceglie un capo per ogni ruolo, evitando quelli già proposti;
- `suggerisci_look()`: coordina il tutto.

`_componi()` sceglie prima i tre ruoli obbligatori. Se manca anche solo uno di
questi, restituisce `None` e l'elenco dei ruoli mancanti. Poi, se ci sono capi
disponibili, aggiunge borsa e accessorio.

`random.choice()` sceglie a caso; se tutti i capi disponibili sono già stati
proposti, l'algoritmo riusa l'intera lista invece di bloccarsi.

Se non trova abbastanza capi per l'occasione scelta, `suggerisci_look()` riprova
**ignorando l'occasione** e usa i capi della stessa stagione, avvisando l'utente.
Se anche così mancano i ruoli obbligatori, solleva un `ValueError` che spiega quali
capi aggiungere.

---

## 6. Fase 3 — L'aspetto comune: `ui/stile.py` (28/10, 17:50:07)

Prima di costruire le schede è stato creato il tema grafico, per evitare che ogni
scheda inventasse colori e font propri.

Il file contiene:

- il dizionario `COLORI`, con la tavolozza unica dell'app (sfondo, superficie,
  testo, bordi, indaco primario, rosso per le eliminazioni, intestazione scura,
  barra di stato);
- `applica_stile()`, che configura `ttk.Style`.

Sono stati definiti:

- il tema `clam`, più personalizzabile di quello predefinito;
- il font base `Segoe UI 10`;
- gli stili per frame, label, titoli, sottotitoli, card;
- gli stili delle schede (`TNotebook` e `TNotebook.Tab`);
- i pulsanti `Accent.TButton`, `Secondario.TButton` e `Pericolo.TButton`;
- gli stili per campi di testo, menu a tendina, riquadri con titolo, tabelle e
  barre di scorrimento.

Questo file è stato pensato prima delle schede perché tutte lo importano.

---

## 7. Fase 4 — I componenti riutilizzabili: `ui/widgets.py` (28/10, 17:50:15)

Qui sono stati raccolti i pezzi grafici che servono in più punti dell'app.

### 7.1 Cache delle miniature

`_CACHE` è un dizionario che tiene in memoria le immagini già create. La chiave è
`(percorso, dimensione, testo)`, il valore è la `PhotoImage` pronta. In questo modo
la stessa foto non viene riletta e ridisegnata ogni volta. Se la cache supera 400
elementi, viene svuotata per non consumare troppa memoria.

### 7.2 Segnaposto e miniature

- `_font()` cerca un font adatto al sistema e ripiega su quello di Pillow;
- `_segnaposto()` disegna un riquadro grigio con la scritta «Nessuna foto»;
- `immagine()` apre la foto, corregge l'orientamento, la ritaglia con
  `ImageOps.fit` per riempire esattamente il riquadro richiesto e la converte in
  `PhotoImage`.

Se la foto manca o è illeggibile, viene usato il segnaposto.

### 7.3 Area scorrevole

`ScrollableFrame` è un frame con Canvas e barra di scorrimento verticale. Serve per
la griglia dell'armadio. Gestisce anche la rotella del mouse su Windows, macOS e
Linux. Il frame interno viene aggiornato quando cambiano le dimensioni del
contenuto o della finestra.

### 7.4 Anteprima del look

`AnteprimaLook` mostra cinque riquadri affiancati, uno per ogni ruolo:
parte superiore, parte inferiore, scarpe, borsa, accessorio. Per ogni ruolo mostra
la foto e il nome del capo, oppure un trattino se il ruolo è vuoto.

---

## 8. Fase 5 — Il pacchetto e il form condiviso (28/10, 17:50:33)

### 8.1 `ui/__init__.py`

È un file molto breve, ma indispensabile: dice a Python che la cartella `ui/` è un
**pacchetto**. Senza di lui non funzionerebbero import come:

```python
from ui.finestra import App
```

### 8.2 `ui/form_capo.py`

È stato creato subito dopo, perché serve sia alla scheda «Aggiungi capo» sia alla
modifica di un capo esistente.

Il file contiene due classi:

1. **`FormCapo`**: il form vero e proprio;
2. **`DialogoModificaCapo`**: la finestra modale per modificare un capo.

`FormCapo` è organizzato in due colonne:

- a sinistra i campi: nome, sezione, ruolo nel look, colore, stagione, occasione;
- a destra l'anteprima della foto, con i pulsanti «Scegli foto…» e «Rimuovi foto».

I campi sono collegati a `StringVar`, così Tkinter aggiorna automaticamente i
valori. Il menu delle sezioni viene riempito dal database. Quando l'utente cambia
sezione, il ruolo viene proposto automaticamente con `ruolo_da_sezione()`.

La foto scelta viene solo **verificata** in questa fase con `img.verify()`; la
copia ottimizzata viene creata al salvataggio con `importa_foto()`. In questo modo
non si riempie `data/foto/` di file che poi l'utente non salva.

`raccogli()` legge i campi, li controlla e restituisce un dizionario pronto per il
database. `prepara_foto()` importa la nuova foto oppure restituisce quella già
salvata.

`DialogoModificaCapo` è una finestra separata (`tk.Toplevel`), legata alla finestra
principale e resa modale con `transient` e `grab_set`. Alla chiusura con Esc o con
«Annulla» non salva nulla; con «Salva modifiche» chiama `modifica_capo()`.

---

## 9. Fase 6 — La scheda Armadio: `ui/armadio.py` (28/10, 17:50:56)

È la prima scheda completa, perché è il cuore dell'applicazione. Il layout è:

- a sinistra il pannello delle **sezioni**, con i pulsanti Nuova, Rinomina, Elimina;
- a destra la **ricerca**, i due **filtri** (sezione e stagione) e la **griglia**
  dei capi.

### 9.1 Sezioni

L'elenco delle sezioni viene letto dal database e mostrato in una `Listbox`.
Cliccando una sezione si applica il filtro. I pulsanti aprono piccole finestre di
dialogo:

- «Nuova sezione» chiede il nome con `simpledialog.askstring`;
- «Rinomina» chiede il nuovo nome, partendo da quello attuale;
- «Elimina» chiede conferma con `messagebox.askyesno`.

Se la sezione contiene capi, l'eliminazione viene bloccata con un messaggio che
spiega il motivo.

### 9.2 Ricerca e filtri

La ricerca è testuale su nome, colore e sezione. I filtri sono due: sezione e
stagione. «Tutte le sezioni» e «Tutte le stagioni» significano «nessun filtro».

La ricerca parte **mentre si scrive**, ma con un ritardo di 250 ms: ogni tasto
annulla il timer precedente e ne crea uno nuovo. Questo evita di eseguire una query
per ogni singola lettera.

### 9.3 Griglia dei capi

La griglia mostra quattro card per riga. Ogni card contiene:

- la miniatura della foto;
- il nome del capo;
- sezione e stagione.

Le card sono cliccabili. Al passaggio del mouse il bordo diventa indaco. Cliccando
si apre `DettaglioCapo`, una finestra modale con:

- la foto ingrandita;
- nome, sezione, ruolo;
- colore, stagione, occasione e data di inserimento;
- i pulsanti Elimina, Chiudi e Modifica.

L'eliminazione chiede conferma e avvisa che il capo verrà tolto anche dai look e dal
diario. La modifica apre `DialogoModificaCapo`.

Se non ci sono capi, la griglia mostra un messaggio diverso a seconda del caso:

- armadio vuoto: invita ad aggiungere il primo capo;
- filtri troppo stretti: invita a cambiarli.

---

## 10. Fase 7 — La scheda Aggiungi capo: `ui/aggiungi_capo.py` (28/10, 17:51:01)

Questa scheda è volutamente sottile: riusa `FormCapo`, aggiunge il titolo, una card
bianca e i pulsanti «Svuota form» e «Salva capo».

Il flusso di salvataggio è:

1. `raccogli()` legge e controlla i campi;
2. `prepara_foto()` importa l'eventuale foto;
3. `db.aggiungi_capo()` salva il capo;
4. il form viene svuotato e il cursore torna sul campo nome;
5. `app.dati_cambiato()` aggiorna tutte le altre schede;
6. un messaggio conferma l'aggiunta.

Il fatto che il form sia condiviso evita di duplicare la stessa logica in due punti.

---

## 11. Fase 8 — La scheda Look: `ui/look.py` (28/10, 17:51:16)

La scheda permette di comporre un look scegliendo un capo per ogni ruolo.

A sinistra c'è una card con:

- un menu a tendina per parte superiore, parte inferiore, scarpe, borsa e
  accessorio;
- il campo per il nome del look;
- i pulsanti «Salva look» e «Pulisci».

A destra ci sono:

- l'anteprima con `AnteprimaLook`;
- l'elenco dei look salvati.

Per ogni ruolo viene costruita una mappa «testo mostrato → id del capo». Il testo è
del tipo `Nome (Sezione)`. Se due capi hanno lo stesso nome e la stessa sezione,
viene aggiunto `· #id` per distinguerli.

Quando si sceglie un capo, l'anteprima si aggiorna subito. Al salvataggio:

1. si costruisce la selezione con solo i ruoli pieni;
2. `valida_selezione()` controlla i ruoli obbligatori;
3. `db.salva_look()` salva il look;
4. l'elenco dei look viene aggiornato.

Dall'elenco si può:

- caricare un look nel form con doppio clic o con «Carica nel form»;
- eliminarlo dopo conferma.

---

## 12. Fase 9 — La scheda Idee: `ui/idee.py` (28/10, 17:51:27)

La scheda propone un look automatico.

A sinistra si scelgono:

- la **stagione** (Primavera, Estate, Autunno, Inverno);
- l'**occasione** (Quotidiano, Sport, Elegante).

Il pulsante «Sorprendimi» chiama `suggerisci_look()`. Se c'era già una proposta,
viene passato l'insieme degli id già mostrati, così il secondo clic propone capi
diversi.

Se la proposta viene trovata:

- le foto compaiono nell'anteprima;
- il pulsante «Salva come look» si attiva;
- un messaggio spiega la proposta o l'eventuale ripiego.

Se non ci sono abbastanza capi, compare un avviso che spiega quali ruoli mancano.

«Salva come look» chiede il nome, controlla la selezione e salva il look nel
database.

---

## 13. Fase 10 — La scheda Diario: `ui/diario.py` (28/10, 17:51:45)

La scheda registra cosa si è indossato.

A sinistra ci sono:

- il campo della data, già impostato su oggi in formato `AAAA-MM-GG`;
- i pulsanti «Oggi» e «Mostra»;
- il menu per scegliere un capo;
- il pulsante «Segna come indossato»;
- l'elenco dei capi del giorno, con «Rimuovi selezionato».

A destra ci sono:

- la tabella «Capi più indossati», con capo e numero di utilizzi;
- l'elenco «Capi mai indossati».

La data viene controllata con `date.fromisoformat()`. Se è sbagliata, compare un
messaggio che mostra il formato corretto. Il database impedisce di segnare due volte
lo stesso capo nello stesso giorno.

Le statistiche vengono ricalcolate dopo ogni aggiunta o rimozione:

- `capi_piu_usati(10)` restituisce i primi dieci capi per numero di utilizzi;
- `capi_mai_usati()` restituisce i capi senza nessuna voce nel diario.

---

## 14. Fase 11 — La finestra principale, l'avvio e le dipendenze (28/10, 17:51:56)

### 14.1 `ui/finestra.py`

Questo file è stato creato dopo tutte le schede, perché le importa e le mette
insieme. Contiene la classe `App`, che eredita da `tk.Tk`.

La finestra principale:

- crea la finestra e imposta titolo e dimensione minima;
- applica il tema con `applica_stile()`;
- centra la finestra sullo schermo;
- intercetta la chiusura con la X per chiudere prima il database;
- costruisce l'intestazione scura con titolo e sottotitolo;
- crea la barra di stato in basso, con messaggio a sinistra e conteggi a destra;
- crea il `ttk.Notebook` con le cinque schede, nell'ordine:
  1. Armadio;
  2. Aggiungi capo;
  3. Look;
  4. Idee;
  5. Diario;
- mostra subito i conteggi e un messaggio di benvenuto.

Sono stati aggiunti anche:

- `dati_cambiati()`: avvisa tutte le schede che i dati sono cambiati e le ricarica;
- `aggiorna_stato()`: aggiorna il numero di capi e look;
- `messaggio()`: mostra un messaggio temporaneo e lo cancella dopo 8 secondi;
- `_chiudi()`: chiude il database e poi la finestra.

### 14.2 `main.py`

È il punto di ingresso. Il flusso è:

```python
db = Database()          # apre o crea il database
app = App(db)            # costruisce la finestra
app.mainloop()           # avvia il ciclo grafico
```

La riga `if __name__ == "__main__":` fa partire l'app solo quando il file viene
eseguito direttamente con `python main.py`, non quando viene importato.

### 14.3 `requirements.txt`

Contiene la sola dipendenza esterna:

```text
Pillow>=10.0
```

Tkinter e SQLite sono già inclusi in Python e non vanno installati con pip.

---

## 15. Fase 12 — La documentazione: `README.md` (28/10, 17:52:38)

Solo alla fine è stato scritto il README, quando ormai il progetto era chiaro.

Contiene:

- la descrizione dell'app;
- le funzionalità essenziali e aggiuntive;
- i requisiti;
- le istruzioni di avvio su Windows e Linux/macOS;
- una prova guidata in due minuti;
- la struttura del progetto;
- le scelte di progetto;
- la nota sulla privacy.

Nel README è scritto esplicitamente che **Valigia** e **backup** non sono inclusi,
perché fuori dalle richieste concordate. Questo evita contraddizioni con il PDF
iniziale, che invece li citava.

---

## 16. Fase 13 — La pulizia del repository: `.gitignore` (28/10, 17:52:55)

L'ultimo file creato è `.gitignore`. Serve a evitare di salvare nel repository:

- `.venv/`: l'ambiente virtuale, personale e ricostruibile;
- `__pycache__/` e `*.pyc`: file compilati automaticamente da Python;
- `data/`: database e foto personali dell'utente.

Questa scelta è coerente con la privacy: i dati dell'armadio restano sul computer e
non finiscono nel repository.

---

## 17. Fase 14 — Prima esecuzione e revisione finale (3–4 novembre)

Il **3 novembre** sono stati aggiornati `README.md` e `main.py`. Il **4 novembre
alle 15:08:57** è stato creato `data/armadio.db`: non è un file scritto a mano, è il
database generato automaticamente dalla prima esecuzione di `main.py`, quando
`Database()` ha chiamato `_crea_schema()` e `_sezioni_iniziali()`.

Subito dopo, tra le **15:09 e le 15:17 del 4 novembre**, è stata fatta una seconda
passata di revisione sui file Python. Questa passata è servita a:

- rifinire i commenti in italiano, con le sezioni `# SINTASSI —` e `# LOGICA —`;
- controllare i messaggi all'utente;
- verificare i flussi di aggiunta, modifica ed eliminazione;
- rendere il codice più leggibile per l'esposizione orale.

I commenti didattici sono una scelta precisa: spiegano non solo **cosa** fa una
riga, ma anche **perché** è scritta così. Per esempio spiegano `from __future__
import annotations`, `with self.conn`, `COLLATE NOCASE`, `LEFT JOIN`, `NOT EXISTS`,
le lambda con valore catturato e così via.

---

## 18. Ordine di esecuzione dell'applicazione

Quando l'utente lancia `python main.py`, l'ordine è questo:

1. `main.py` importa `Database` e `App`.
2. `Database()` crea le cartelle, apre SQLite, crea le tabelle e inserisce le otto
   sezioni se il database è nuovo.
3. `App(db)` crea la finestra, applica il tema, costruisce intestazione e barra di
   stato.
4. `App` crea le cinque schede e ognuna si ricarica dal database.
5. `mainloop()` resta in ascolto di clic, tasti e ridisegni.
6. Quando l'utente chiude la finestra, `_chiudi()` chiude prima il database e poi
   la finestra.

---

## 19. Perché è stato scelto questo ordine

L'ordine non è casuale: segue le **dipendenze** del codice.

```text
database.py
   ↓
logica.py
   ↓
ui/stile.py
   ↓
ui/widgets.py
   ↓
ui/form_capo.py
   ↓
ui/armadio.py ── ui/aggiungi_capo.py
   ↓
ui/look.py ── ui/idee.py ── ui/diario.py
   ↓
ui/finestra.py
   ↓
main.py
   ↓
requirements.txt, README.md, .gitignore
```

In pratica:

- prima i **dati**, perché tutto il resto li usa;
- poi la **logica**, perché usa i dati;
- poi i **componenti grafici comuni**, perché tutte le schede li usano;
- poi le **singole schede**, in ordine di dipendenza;
- poi la **finestra che le contiene**;
- poi il **punto di avvio**;
- infine **documentazione e pulizia**.

Questo modo di lavorare si chiama **bottom-up**: si parte dai mattoni più piccoli e
si costruisce sopra. Il vantaggio è che ogni file può essere provato e compreso
senza dover avere già tutta l'interfaccia pronta.

---

## 20. Riassunto: un file, una responsabilità

| File | Responsabilità principale |
|------|---------------------------|
| `database.py` | Schema SQLite, query, validazioni e regole di accesso ai dati |
| `logica.py` | Importazione foto, controllo del look e algoritmo «Sorprendimi» |
| `main.py` | Avvio dell'applicazione |
| `requirements.txt` | Dipendenza Pillow |
| `README.md` | Istruzioni, funzionalità e scelte di progetto |
| `.gitignore` | Esclusione di ambiente virtuale, cache e dati personali |
| `ui/__init__.py` | Rende `ui/` un pacchetto Python |
| `ui/stile.py` | Colori, font e stili comuni |
| `ui/widgets.py` | Miniatura, segnaposto, area scorrevole e anteprima look |
| `ui/form_capo.py` | Form condiviso per aggiungere/modificare un capo |
| `ui/armadio.py` | Sezioni, ricerca, filtri, griglia e dettaglio capo |
| `ui/aggiungi_capo.py` | Scheda per inserire un nuovo capo |
| `ui/look.py` | Composizione, anteprima e archivio dei look |
| `ui/idee.py` | Proposta automatica con «Sorprendimi» |
| `ui/diario.py` | Capi indossati, più usati e mai usati |
| `ui/finestra.py` | Finestra principale, schede e barra di stato |
| `data/armadio.db` | Database creato al primo avvio |
| `data/foto/` | Copie ottimizzate delle foto dei capi |

---

## 21. Scaletta per raccontare il progetto all'esame

Se devi spiegare il lavoro in pochi minuti, segui questo ordine:

1. **Il problema**: l'armadio pieno e la difficoltà di scegliere cosa mettersi.
2. **La soluzione**: un'app desktop in Python con Tkinter, Pillow e SQLite.
3. **La separazione dei compiti**: `database.py` per i dati, `logica.py` per le
   regole, `ui/` per la grafica.
4. **Il database**: cinque tabelle e le relazioni tra sezioni, capi, look e diario.
5. **Le foto**: copiate in `data/foto/`, ridimensionate a 1600 px e salvate in JPEG;
   nel database resta solo il nome del file.
6. **Le schede**: Armadio, Aggiungi capo, Look, Idee, Diario.
7. **Le funzioni aggiuntive**: «Sorprendimi» e diario con capi più/mai usati.
8. **Le scelte di progetto**: ruoli del look, due filtri, stagione «Tutte», messaggi
   di errore chiari, eliminazioni con conferma.
9. **La privacy**: nessun dato inviato in rete.
10. **La prova pratica**: aggiungi un capo, crea un look, genera una proposta,
    segna un capo nel diario e prova ricerca e filtri.

---

## 22. Conclusione

Il progetto è stato costruito partendo dall'analisi del problema, poi dal
**database**, quindi dalla **logica**, poi dai **componenti grafici comuni**, dalle
**singole schede**, dalla **finestra principale**, dall'**avvio** e infine dalla
**documentazione**.

Questo ordine ha permesso di avere sempre una base funzionante su cui costruire:
prima i dati, poi le regole, poi l'interfaccia. È anche il motivo per cui il codice
si può spiegare facilmente: ogni file ha un compito preciso e le dipendenze sono
chiare.






CHE COSA SONO I METODI STATICI