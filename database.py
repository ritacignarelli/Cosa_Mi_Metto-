"""Archivio SQLite di «Cosa Mi Metto?».

Qui c'è tutta la parte dati: l'interfaccia grafica non scrive mai SQL.
"""
# SINTASSI — `from __future__ import annotations`
# Rinvia la valutazione delle annotazioni dei tipi (quelle scritte dopo `:` e
# dopo `->`). Serve per poter scrivere `str | None` o `list[sqlite3.Row]`
# anche su versioni di Python che altrimenti le valuterebbero subito.
# Le annotazioni NON cambiano il comportamento: sono solo informazioni per chi
# legge il codice e per l'editor.
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import sqlite3  # modulo standard per gestire un database SQLite
import unicodedata  # serve a togliere accenti e segni dai nomi delle sezioni
from datetime import date  # usata per controllare le date inserite nel diario
from pathlib import Path  # gestisce i percorsi di file e cartelle in modo portabile

# SINTASSI — `Path(__file__).resolve().parent`
# `__file__` è il percorso di questo file. `resolve()` lo rende assoluto,
# `.parent` prende la cartella che lo contiene. L'operatore `/` tra due Path
# unisce cartella e nome file: non è una divisione matematica.
BASE_DIR = Path(__file__).resolve().parent  # cartella che contiene questo file
DATA_DIR = BASE_DIR / "data"  # cartella dei dati, creata al primo avvio
FOTO_DIR = DATA_DIR / "foto"  # cartella con le copie delle foto dei capi
DB_PATH = DATA_DIR / "armadio.db"  # percorso del file del database SQLite

SEZIONI_DEFAULT = (  # sezioni create automaticamente al primo avvio
    "Maglie corte",  # maglie leggere
    "Maglie lunghe",  # maglie pesanti o a manica lunga
    "Pantaloni",  # pantaloni lunghi
    "Pantaloncini",  # pantaloni corti
    "Gonne",  # gonne
    "Scarpe",  # scarpe e stivali
    "Borse",  # borse e zaini
    "Accessori",  # cinture, sciarpe, gioielli, ecc.
)
STAGIONI = ("Primavera", "Estate", "Autunno", "Inverno", "Tutte")  # stagioni possibili per un capo
STAGIONI_FILTRO = ("Primavera", "Estate", "Autunno", "Inverno")  # stagioni mostrate nei filtri
OCCASIONI = ("Quotidiano", "Sport", "Elegante")  # occasioni possibili per un capo

RUOLI = {  # codice interno -> etichetta mostrata all'utente
    "top": "Parte superiore",  # maglie, camicie, giacche...
    "bottom": "Parte inferiore",  # pantaloni, gonne, shorts...
    "scarpe": "Scarpe",  # scarpe e stivali
    "borsa": "Borsa",  # borse e zaini
    "accessorio": "Accessorio",  # cinture, sciarpe, gioielli...
    "altro": "Altro",  # capi che non rientrano nei ruoli precedenti
}
RUOLI_ORDINE = ("top", "bottom", "scarpe", "borsa", "accessorio", "altro")  # ordine dei ruoli nei menu
RUOLI_LOOK = ("top", "bottom", "scarpe", "borsa", "accessorio")  # ruoli mostrati nell'anteprima del look
RUOLI_RICHIESTI = ("top", "bottom", "scarpe")  # ruoli obbligatori per salvare un look
RUOLI_OPZIONALI = ("borsa", "accessorio")  # ruoli aggiunti al look solo se ci sono capi disponibili
# SINTASSI — dizionario inverso con comprehension
# `{v: k for k, v in RUOLI.items()}` crea un nuovo dizionario scambiando
# chiavi e valori. Serve a passare dall'etichetta italiana («Parte superiore»)
# al codice interno («top»).
RUOLI_DA_ETICHETTA = {v: k for k, v in RUOLI.items()}  # etichetta visibile -> codice interno


# SINTASSI — `unicodedata.normalize(...).encode(...).decode(...)`
# NFKD separa le lettere dagli accenti; `encode("ascii", "ignore")` elimina i
# segni che non sono ASCII; `decode("ascii")` torna a stringa; `.lower()`
# rende tutto minuscolo. Serve per confrontare «Magliè» e «maglie».
def _semplifica(testo: str) -> str:
    """Minuscolo e senza accenti, per confrontare i nomi delle sezioni."""
    testo = unicodedata.normalize("NFKD", testo)  # separa le lettere dai segni di accento
    return testo.encode("ascii", "ignore").decode("ascii").lower()  # elimina gli accenti e passa a minuscolo


def ruolo_da_sezione(nome: str) -> str:
    """Deduce il ruolo nel look dal nome della sezione."""
    n = _semplifica(nome)  # confronto senza maiuscole né accenti
    if any(k in n for k in ("magli", "top", "camic", "felp", "maglion", "giacch",
                            "giubb", "cappott", "blus", "canottier", "dolcevita")):
        return "top"  # il nome ricorda una parte superiore
    if any(k in n for k in ("pantal", "gonn", "short", "jeans", "bermuda", "leggins")):
        return "bottom"  # il nome ricorda una parte inferiore
    if any(k in n for k in ("scarp", "stival", "sneaker", "sandal", "ciabatt")):
        return "scarpe"  # il nome ricorda un paio di scarpe
    if any(k in n for k in ("bors", "zain", "tracolla")):
        return "borsa"  # il nome ricorda una borsa o uno zaino
    if any(k in n for k in ("access", "cintur", "sciarp", "cappell", "gioiell",
                            "orecchin", "collan", "occhial", "guant")):
        return "accessorio"  # il nome ricorda un accessorio
    return "altro"  # sezione personalizzata senza parole riconoscibili


# LOGICA — la classe `Database` è l'unico punto che parla con SQLite.
# Ogni metodo esegue una query e restituisce righe già pronte per
# l'interfaccia: in questo modo la grafica non deve conoscere SQL.
class Database:
    """Gestisce il database SQLite e tutte le operazioni sui dati.

    L'interfaccia grafica chiama questi metodi e non scrive mai SQL:
    in questo modo la parte dati resta separata dalla parte grafica.
    """

    # SINTASSI — parametri con valore predefinito e tipo `str | Path | None`
    # `percorso: str | Path = DB_PATH` significa: accetta una stringa o un Path;
    # se non viene passato, usa DB_PATH. `None` come default indica «non
    # specificato» e viene gestito dentro il costruttore.
    def __init__(self, percorso: str | Path = DB_PATH,
                 cartella_foto: str | Path | None = None):
        self.percorso = Path(percorso)  # memorizza il percorso del file del database
        self.percorso.parent.mkdir(parents=True, exist_ok=True)  # crea la cartella data/ se manca
        self.foto_dir = Path(cartella_foto) if cartella_foto else FOTO_DIR  # sceglie la cartella delle foto
        self.foto_dir.mkdir(parents=True, exist_ok=True)  # crea la cartella delle foto se manca
        self.conn = sqlite3.connect(self.percorso)  # apre la connessione al database
        # SINTASSI — `sqlite3.Row`
        # Di default SQLite restituisce tuple. Con `row_factory = sqlite3.Row`
        # ogni riga si può leggere sia per posizione (`riga[0]`) sia per nome
        # (`riga["nome"]`), che è molto più leggibile.
        self.conn.row_factory = sqlite3.Row  # permette di leggere i campi per nome
        # SINTASSI — `PRAGMA foreign_keys = ON`
        # SQLite controlla le chiavi esterne solo se lo si attiva esplicitamente,
        # e l'impostazione vale per la singola connessione: va rifatta ogni volta.
        self.conn.execute("PRAGMA foreign_keys = ON")  # attiva i vincoli tra le tabelle
        # LOGICA — al primo avvio non esiste nulla: creiamo le tabelle e poi,
        # se la tabella `sezioni` è vuota, inseriamo le otto sezioni iniziali.
        self._crea_schema()  # crea le tabelle se non esistono
        self._sezioni_iniziali()  # inserisce le sezioni di partenza al primo avvio

    # ------------------------------------------------------------------ schema
    def _crea_schema(self) -> None:
        """Crea le tabelle del database se non esistono già.

        `CREATE TABLE IF NOT EXISTS` rende l'operazione sicura anche quando
        il database esiste già: le tabelle non vengono ricreate.
        """
        # SINTASSI — `executescript`
        # Esegue più istruzioni SQL separate da `;` in una sola chiamata.
        # Le righe che iniziano con `--` sono commenti SQL: SQLite le ignora.
        self.conn.executescript(  # esegue in una volta tutte le istruzioni SQL di creazione
            """
            -- Sezioni personalizzabili dell'armadio
            CREATE TABLE IF NOT EXISTS sezioni (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,  -- identificativo univoco
                nome    TEXT NOT NULL COLLATE NOCASE UNIQUE,  -- nome unico, senza distinzione maiuscole/minuscole
                ordine  INTEGER NOT NULL DEFAULT 0  -- posizione della sezione nell'elenco
            );
            -- Capi caricati dall'utente
            CREATE TABLE IF NOT EXISTS capi (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- identificativo univoco
                nome        TEXT NOT NULL,  -- nome del capo
                sezione_id  INTEGER NOT NULL REFERENCES sezioni(id) ON DELETE RESTRICT,  -- sezione di appartenenza
                ruolo       TEXT NOT NULL DEFAULT 'altro',  -- ruolo usato per comporre i look
                colore      TEXT NOT NULL DEFAULT '',  -- colore libero scelto dall'utente
                stagione    TEXT NOT NULL DEFAULT 'Tutte',  -- stagione adatta al capo
                occasione   TEXT NOT NULL DEFAULT 'Quotidiano',  -- occasione d'uso
                foto        TEXT,  -- nome del file della foto dentro data/foto
                creato      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))  -- data di inserimento
            );
            CREATE INDEX IF NOT EXISTS idx_capi_sezione ON capi(sezione_id);  -- velocizza la ricerca per sezione
            -- Look salvati dall'utente
            CREATE TABLE IF NOT EXISTS look (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,  -- identificativo univoco
                nome    TEXT NOT NULL,  -- nome scelto per il look
                creato  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))  -- data di creazione
            );
            -- Capi che compongono ogni look
            CREATE TABLE IF NOT EXISTS look_capi (
                look_id  INTEGER NOT NULL REFERENCES look(id) ON DELETE CASCADE,  -- look di appartenenza
                capo_id  INTEGER NOT NULL REFERENCES capi(id) ON DELETE CASCADE,  -- capo usato nel look
                ruolo    TEXT NOT NULL,  -- ruolo del capo dentro il look
                PRIMARY KEY (look_id, capo_id)  -- evita di inserire due volte lo stesso capo nello stesso look
            );
            -- Diario dei capi indossati
            CREATE TABLE IF NOT EXISTS diario (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,  -- identificativo univoco
                data     TEXT NOT NULL,  -- giorno nel formato AAAA-MM-GG
                capo_id  INTEGER NOT NULL REFERENCES capi(id) ON DELETE CASCADE,  -- capo indossato
                UNIQUE (data, capo_id)  -- lo stesso capo non può comparire due volte nello stesso giorno
            );
            CREATE INDEX IF NOT EXISTS idx_diario_data ON diario(data);  -- velocizza la lettura per data
            """
        )

    def _sezioni_iniziali(self) -> None:
        """Inserisce le otto sezioni di partenza solo al primo avvio."""
        # SINTASSI — `fetchone()[0]`
        # `fetchone()` restituisce la prima riga (o None). Con `[0]` prendiamo
        # la prima colonna, cioè il risultato di COUNT(*). Se è diverso da 0,
        # significa che ci sono già sezioni.
        if self.conn.execute("SELECT COUNT(*) FROM sezioni").fetchone()[0]:  # controlla se esistono già sezioni
            return  # se ci sono, non aggiunge nulla
        # SINTASSI — `with self.conn:`
        # La connessione SQLite è un context manager: se tutto va bene fa
        # COMMIT, se scoppia un'eccezione fa ROLLBACK. Così non restano dati
        # scritti a metà.
        with self.conn:  # transazione: salva tutte le sezioni oppure nessuna
            # SINTASSI — `executemany`
            # Esegue la stessa INSERT una volta per ogni tupla della lista.
            # `enumerate(SEZIONI_DEFAULT)` fornisce coppie (indice, nome):
            # l'indice diventa il valore della colonna `ordine`.
            self.conn.executemany(  # inserisce più righe con una sola istruzione
                "INSERT INTO sezioni (nome, ordine) VALUES (?, ?)",
                [(nome, i) for i, nome in enumerate(SEZIONI_DEFAULT)],  # usa l'indice come ordine
            )

    # ---------------------------------------------------------------- sezioni
    # SINTASSI — `COLLATE NOCASE`
    # In SQLite confronta il testo ignorando maiuscole/minuscole. Qui serve
    # per ordinare i nomi in modo naturale e per rendere unica una sezione
    # anche se viene scritta con maiuscole diverse.
    def sezioni(self) -> list[sqlite3.Row]:
        """Restituisce tutte le sezioni nell'ordine scelto dall'utente."""
        return self.conn.execute(  # legge tutte le sezioni
            "SELECT id, nome FROM sezioni ORDER BY ordine, nome COLLATE NOCASE"  # rispetta l'ordine scelto
        ).fetchall()

    def nomi_sezioni(self) -> list[str]:
        """Restituisce solo i nomi delle sezioni, utili per i menu a tendina."""
        return [r["nome"] for r in self.sezioni()]  # estrae solo i nomi delle sezioni

    def sezione_per_nome(self, nome: str) -> sqlite3.Row | None:
        """Cerca una sezione per nome, senza distinguere maiuscole e minuscole."""
        return self.conn.execute(  # cerca una sezione dal nome, ignorando maiuscole/minuscole
            "SELECT id, nome FROM sezioni WHERE nome = ? COLLATE NOCASE", (nome,)
        ).fetchone()

    def aggiungi_sezione(self, nome: str) -> int:
        """Crea una nuova sezione in fondo all'elenco e ne restituisce l'id."""
        nome = nome.strip()  # toglie gli spazi iniziali e finali
        if not nome:  # controlla che il nome non sia vuoto
            raise ValueError("Il nome della sezione non può essere vuoto.")
        # SINTASSI — `COALESCE(MAX(ordine), -1) + 1`
        # Se la tabella è vuota `MAX` restituisce NULL; `COALESCE` lo sostituisce
        # con -1, quindi il primo ordine sarà 0. Se ci sono righe, prende il
        # massimo e aggiunge 1 per mettere la nuova sezione in fondo.
        ordine = self.conn.execute(  # calcola la nuova posizione in fondo all'elenco
            "SELECT COALESCE(MAX(ordine), -1) + 1 FROM sezioni"
        ).fetchone()[0]
        try:
            with self.conn:  # transazione di inserimento
                cur = self.conn.execute(  # inserisce la nuova sezione
                    "INSERT INTO sezioni (nome, ordine) VALUES (?, ?)", (nome, ordine)
                )
        # SINTASSI — `except ... as exc` e `raise ... from exc`
        # `exc` è l'oggetto dell'eccezione. `from exc` conserva la causa
        # originale: chi legge il traceback capisce che il nostro ValueError
        # è nato dal vincolo UNIQUE di SQLite, non da un errore casuale.
        except sqlite3.IntegrityError as exc:  # il nome esiste già (vincolo UNIQUE)
            raise ValueError(f"Esiste già una sezione chiamata «{nome}».") from exc
        return int(cur.lastrowid)  # restituisce l'id della sezione appena creata

    def rinomina_sezione(self, sezione_id: int, nome: str) -> None:
        """Cambia il nome di una sezione esistente."""
        nome = nome.strip()  # toglie gli spazi iniziali e finali
        if not nome:  # controlla che il nome non sia vuoto
            raise ValueError("Il nome della sezione non può essere vuoto.")
        try:
            with self.conn:  # transazione di modifica
                cur = self.conn.execute(  # aggiorna il nome della sezione scelta
                    "UPDATE sezioni SET nome = ? WHERE id = ?", (nome, sezione_id)
                )
        except sqlite3.IntegrityError as exc:  # esiste già un'altra sezione con quel nome
            raise ValueError(f"Esiste già una sezione chiamata «{nome}».") from exc
        if cur.rowcount == 0:  # nessuna riga modificata: la sezione non esiste
            raise ValueError("La sezione scelta non esiste più.")

    def elimina_sezione(self, sezione_id: int) -> None:
        """Elimina una sezione solo se non contiene capi."""
        n = self.conn.execute(  # conta i capi ancora collegati alla sezione
            "SELECT COUNT(*) FROM capi WHERE sezione_id = ?", (sezione_id,)
        ).fetchone()[0]
        if n:  # una sezione con capi non può essere eliminata
            raise ValueError(
                f"Questa sezione contiene {n} capi. Sposta o elimina prima quei capi."
            )
        with self.conn:  # transazione di eliminazione
            self.conn.execute("DELETE FROM sezioni WHERE id = ?", (sezione_id,))  # elimina la sezione vuota

    # ------------------------------------------------------------------- capi
    # LOGICA — i controlli sono nel database e non solo nella grafica.
    # Anche se un domani l'interfaccia cambia, i dati sbagliati non entrano.
    def _valida_capo(self, nome: str, sezione_id: int, ruolo: str, stagione: str,
                     occasione: str) -> None:
        """Controlla che i dati di un capo siano completi e coerenti."""
        if not nome.strip():  # il nome è obbligatorio
            raise ValueError("Inserisci il nome del capo.")
        if not self.conn.execute(  # controlla che la sezione esista davvero
            "SELECT 1 FROM sezioni WHERE id = ?", (sezione_id,)
        ).fetchone():
            raise ValueError("Scegli una sezione valida.")
        if ruolo not in RUOLI:  # il ruolo deve essere uno di quelli previsti
            raise ValueError("Scegli un ruolo valido per il look.")
        if stagione not in STAGIONI:  # la stagione deve essere una di quelle previste
            raise ValueError("Scegli una stagione valida.")
        if occasione not in OCCASIONI:  # l'occasione deve essere una di quelle previste
            raise ValueError("Scegli un'occasione valida.")

    # SINTASSI — query costruita a pezzi
    # Invece di scrivere quattro query diverse, mettiamo le parti comuni in
    # una lista e aggiungiamo `AND ...` solo per i filtri attivi. I `?` sono
    # segnaposto: i valori veri arrivano nella lista `parametri`. Questo evita
    # problemi con virgolette e apici e blocca le SQL injection.
    def capi(self, sezione_id: int | None = None, stagione: str | None = None,
             testo: str = "") -> list[sqlite3.Row]:
        """Restituisce i capi applicando i filtri di sezione, stagione e testo."""
        sql = [  # parti della query costruite in base ai filtri attivi
            "SELECT c.id, c.nome, c.foto, c.colore, c.stagione, c.occasione,",  # campi del capo
            "       c.ruolo, s.id AS sezione_id, s.nome AS sezione",  # ruolo e nome della sezione
            "FROM capi c JOIN sezioni s ON s.id = c.sezione_id WHERE 1 = 1",  # collega capi e sezioni
        ]
        parametri: list[object] = []  # valori da passare alla query in modo sicuro
        # SINTASSI — `is not None`
        # `None` è un valore speciale che significa «nessun valore». Si
        # confronta con `is`/`is not`, non con `==`. Qui distingue «nessun
        # filtro» da un id valido (che potrebbe anche essere 0).
        if sezione_id is not None:  # filtro per sezione
            sql.append("AND c.sezione_id = ?")
            parametri.append(sezione_id)
        if stagione:  # filtro per stagione
            sql.append("AND (c.stagione = ? OR c.stagione = 'Tutte')")  # «Tutte» va bene sempre
            parametri.append(stagione)
        testo = testo.strip()  # toglie gli spazi dalla ricerca
        if testo:  # ricerca testuale per nome, colore o sezione
            like = f"%{testo.lower()}%"  # prepara il testo per LIKE
            sql.append(
                "AND (LOWER(c.nome) LIKE ? OR LOWER(c.colore) LIKE ? "
                "OR LOWER(s.nome) LIKE ?)"
            )
            parametri.extend((like, like, like))  # lo stesso testo serve per i tre campi
        sql.append("ORDER BY s.ordine, c.nome COLLATE NOCASE")  # ordina per sezione e nome
        return self.conn.execute(" ".join(sql), parametri).fetchall()  # esegue la query completa

    def capo(self, capo_id: int) -> sqlite3.Row | None:
        """Restituisce un singolo capo con il nome della sua sezione."""
        return self.conn.execute(  # legge un singolo capo con il nome della sua sezione
            "SELECT c.*, s.nome AS sezione FROM capi c "
            "JOIN sezioni s ON s.id = c.sezione_id WHERE c.id = ?",
            (capo_id,),
        ).fetchone()

    def aggiungi_capo(self, nome: str, sezione_id: int, ruolo: str, colore: str,
                      stagione: str, occasione: str, foto: str | None = None) -> int:
        """Inserisce un nuovo capo e restituisce il suo id."""
        self._valida_capo(nome, sezione_id, ruolo, stagione, occasione)  # controlla i dati
        with self.conn:  # transazione di inserimento
            cur = self.conn.execute(  # salva il nuovo capo nel database
                "INSERT INTO capi (nome, sezione_id, ruolo, colore, stagione, "
                "occasione, foto) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nome.strip(), sezione_id, ruolo, colore.strip(), stagione,
                 occasione, foto),
            )
        return int(cur.lastrowid)  # restituisce l'id del capo appena creato

    # LOGICA — prima leggiamo la vecchia foto, poi aggiorniamo la riga. Se la
    # foto è cambiata, cancelliamo il vecchio file: altrimenti resterebbe un
    # file orfano dentro data/foto.
    def modifica_capo(self, capo_id: int, nome: str, sezione_id: int, ruolo: str,
                      colore: str, stagione: str, occasione: str,
                      foto: str | None = None) -> None:
        """Aggiorna un capo esistente e cancella la vecchia foto se sostituita."""
        vecchio = self.conn.execute(  # legge la foto attuale prima di cambiarla
            "SELECT foto FROM capi WHERE id = ?", (capo_id,)
        ).fetchone()
        if vecchio is None:  # il capo potrebbe essere stato eliminato nel frattempo
            raise ValueError("Il capo scelto non esiste più.")
        self._valida_capo(nome, sezione_id, ruolo, stagione, occasione)  # controlla i nuovi dati
        with self.conn:  # transazione di modifica
            self.conn.execute(  # aggiorna tutti i campi del capo
                "UPDATE capi SET nome = ?, sezione_id = ?, ruolo = ?, colore = ?, "
                "stagione = ?, occasione = ?, foto = ? WHERE id = ?",
                (nome.strip(), sezione_id, ruolo, colore.strip(), stagione,
                 occasione, foto, capo_id),
            )
        if vecchio["foto"] and vecchio["foto"] != foto:  # la vecchia foto non serve più
            self._elimina_file_foto(vecchio["foto"])  # cancella il vecchio file dal disco

    def elimina_capo(self, capo_id: int) -> None:
        """Elimina un capo, la sua foto e i collegamenti a look e diario."""
        riga = self.conn.execute(  # legge il nome della foto prima di eliminare il capo
            "SELECT foto FROM capi WHERE id = ?", (capo_id,)
        ).fetchone()
        with self.conn:  # transazione di eliminazione
            self.conn.execute("DELETE FROM capi WHERE id = ?", (capo_id,))  # elimina il capo
        if riga and riga["foto"]:  # se esisteva una foto collegata
            self._elimina_file_foto(riga["foto"])  # cancella anche il file della foto

    def conta_capi(self) -> int:
        """Restituisce il numero totale di capi nell'armadio."""
        return int(self.conn.execute("SELECT COUNT(*) FROM capi").fetchone()[0])  # numero totale di capi

    def conta_look(self) -> int:
        """Restituisce il numero totale di look salvati."""
        return int(self.conn.execute("SELECT COUNT(*) FROM look").fetchone()[0])  # numero totale di look

    # ------------------------------------------------------------------ foto
    # SINTASSI — percorso assoluto o relativo
    # Se nel database c'è un nome semplice (es. "abc.jpg"), lo cerchiamo dentro
    # `data/foto`; se è già un percorso assoluto (es. C:\...), lo usiamo così
    # com'è. `is_absolute()` fa questo controllo.
    def percorso_foto(self, nome: str | None) -> Path | None:
        """Trasforma il nome salvato nel database in un percorso completo della foto."""
        if not nome:  # nessun nome di file: nessuna foto
            return None
        percorso = Path(nome)  # trasforma il nome in percorso
        return percorso if percorso.is_absolute() else self.foto_dir / percorso  # usa data/foto per i nomi relativi

    # SINTASSI — `resolve()` e `unlink()`
    # `resolve()` trasforma un percorso in assoluto e risolve `..` e i link.
    # Confrontiamo la cartella del file con `self.foto_dir`: così non
    # cancelliamo per errore un file che sta fuori da data/foto.
    # `unlink()` elimina il file dal disco.
    def _elimina_file_foto(self, nome: str) -> None:
        """Cancella dal disco una foto, solo se si trova dentro data/foto."""
        percorso = self.percorso_foto(nome)  # ricava il percorso completo della foto
        if not percorso:  # se non c'è nulla da eliminare esce
            return
        try:
            if percorso.is_file() and percorso.resolve().parent == self.foto_dir.resolve():  # controlla che sia dentro data/foto
                percorso.unlink()  # elimina il file dal disco
        except OSError:
            pass  # se il file è già sparito non blocca l'applicazione

    # ------------------------------------------------------------------ look
    # SINTASSI — `dict[str, int]` e `.items()`
    # La selezione è un dizionario ruolo -> id del capo. Il ciclo `.items()`
    # restituisce coppie (chiave, valore). Se un ruolo è impostato a None lo
    # saltiamo, così borsa e accessorio restano facoltativi.
    def salva_look(self, nome: str, selezione: dict[str, int]) -> int:
        """Salva un look con i capi scelti e restituisce il suo id."""
        nome = nome.strip()  # toglie gli spazi dal nome del look
        if not nome:  # il nome è obbligatorio
            raise ValueError("Dai un nome al look prima di salvarlo.")
        if not selezione:  # serve almeno un capo
            raise ValueError("Scegli almeno un capo per il look.")
        with self.conn:  # transazione: look e capi vengono salvati insieme
            cur = self.conn.execute("INSERT INTO look (nome) VALUES (?)", (nome,))  # crea il look
            look_id = int(cur.lastrowid)  # id del look appena creato
            for ruolo, capo_id in selezione.items():  # inserisce ogni capo scelto
                if capo_id is None:  # salta i ruoli lasciati vuoti
                    continue
                if not self.conn.execute(  # verifica che il capo esista ancora
                    "SELECT 1 FROM capi WHERE id = ?", (capo_id,)
                ).fetchone():
                    raise ValueError("Uno dei capi scelti non esiste più.")
                self.conn.execute(  # collega il capo al look con il suo ruolo
                    "INSERT INTO look_capi (look_id, capo_id, ruolo) VALUES (?, ?, ?)",
                    (look_id, capo_id, ruolo),
                )
        return look_id  # restituisce l'id del look salvato

    # SINTASSI — `LEFT JOIN`, `COUNT` e `GROUP BY`
    # `LEFT JOIN` tiene anche i look senza capi (che non dovrebbero esistere,
    # ma è più sicuro). `COUNT(lc.capo_id)` conta i capi collegati; `GROUP BY
    # l.id` raggruppa una riga per look.
    def look_salvati(self) -> list[sqlite3.Row]:
        """Elenca i look salvati con il numero di capi che li compongono."""
        return self.conn.execute(  # elenca i look con il numero di capi di ciascuno
            "SELECT l.id, l.nome, l.creato, COUNT(lc.capo_id) AS n_capi "
            "FROM look l LEFT JOIN look_capi lc ON lc.look_id = l.id "
            "GROUP BY l.id ORDER BY l.creato DESC, l.id DESC"
        ).fetchall()

    def capi_look(self, look_id: int) -> list[sqlite3.Row]:
        """Restituisce i capi che compongono un look."""
        return self.conn.execute(  # legge tutti i capi che compongono un look
            "SELECT c.id, c.nome, c.foto, s.nome AS sezione, lc.ruolo "
            "FROM look_capi lc JOIN capi c ON c.id = lc.capo_id "
            "JOIN sezioni s ON s.id = c.sezione_id "
            "WHERE lc.look_id = ? ORDER BY s.ordine, c.nome COLLATE NOCASE",
            (look_id,),
        ).fetchall()

    def elimina_look(self, look_id: int) -> None:
        """Elimina un look e, in cascata, i suoi collegamenti ai capi."""
        with self.conn:  # transazione di eliminazione
            self.conn.execute("DELETE FROM look WHERE id = ?", (look_id,))  # i capi del look vengono tolti in cascata

    # ----------------------------------------------------------------- diario
    # SINTASSI — `@staticmethod`
    # Un metodo statico non riceve `self`: è una funzione di supporto che sta
    # dentro la classe perché riguarda il database, ma non usa la connessione.
    @staticmethod
    def _valida_data(data_iso: str) -> None:
        """Controlla che la data sia scritta nel formato AAAA-MM-GG."""
        try:
            # SINTASSI — `date.fromisoformat`
            # Converte una stringa "AAAA-MM-GG" in un oggetto `date`. Se la
            # stringa è scritta male solleva `ValueError`; noi lo intercettiamo
            # e mostriamo un messaggio comprensibile.
            date.fromisoformat(data_iso)  # controlla che la data sia nel formato AAAA-MM-GG
        except (TypeError, ValueError) as exc:  # data vuota o scritta male
            raise ValueError("La data deve essere nel formato AAAA-MM-GG.") from exc

    def aggiungi_voce_diario(self, data_iso: str, capo_id: int) -> int:
        """Segna un capo come indossato in una data."""
        self._valida_data(data_iso)  # controlla il formato della data
        if not self.conn.execute(  # verifica che il capo esista ancora
            "SELECT 1 FROM capi WHERE id = ?", (capo_id,)
        ).fetchone():
            raise ValueError("Il capo scelto non esiste più.")
        try:
            with self.conn:  # transazione di inserimento
                cur = self.conn.execute(  # segna il capo come indossato in quella data
                    "INSERT INTO diario (data, capo_id) VALUES (?, ?)",
                    (data_iso, capo_id),
                )
        except sqlite3.IntegrityError as exc:  # violazione del vincolo UNIQUE
            raise ValueError("Questo capo è già segnato per il giorno scelto.") from exc
        return int(cur.lastrowid)  # restituisce l'id della voce creata

    def voci_diario(self, data_iso: str) -> list[sqlite3.Row]:
        """Restituisce i capi indossati in una data."""
        self._valida_data(data_iso)  # controlla il formato della data
        return self.conn.execute(  # legge i capi indossati in quella data
            "SELECT d.id, c.id AS capo_id, c.nome, s.nome AS sezione "
            "FROM diario d JOIN capi c ON c.id = d.capo_id "
            "JOIN sezioni s ON s.id = c.sezione_id "
            "WHERE d.data = ? ORDER BY s.ordine, c.nome COLLATE NOCASE",
            (data_iso,),
        ).fetchall()

    def elimina_voce_diario(self, voce_id: int) -> None:
        """Rimuove una voce dal diario."""
        with self.conn:  # transazione di eliminazione
            self.conn.execute("DELETE FROM diario WHERE id = ?", (voce_id,))  # elimina la voce scelta

    # SINTASSI — `JOIN`, `GROUP BY` e `COUNT`
    # `JOIN` collega ogni riga del diario al capo corrispondente. `GROUP BY
    # c.id` raggruppa per capo e `COUNT(d.id)` conta quante volte compare.
    # `ORDER BY volte DESC` mette in cima i più usati.
    def capi_piu_usati(self, limite: int = 10) -> list[sqlite3.Row]:
        """Restituisce i capi indossati più spesso, dal più usato."""
        return self.conn.execute(  # conta quante volte compare ogni capo nel diario
            "SELECT c.id, c.nome, s.nome AS sezione, COUNT(d.id) AS volte "
            "FROM capi c JOIN sezioni s ON s.id = c.sezione_id "
            "JOIN diario d ON d.capo_id = c.id "
            "GROUP BY c.id ORDER BY volte DESC, c.nome COLLATE NOCASE LIMIT ?",
            (limite,),
        ).fetchall()

    # SINTASSI — `NOT EXISTS`
    # Restituisce i capi per cui NON esiste nessuna riga nel diario. È più
    # sicuro di `NOT IN` quando ci sono valori NULL.
    def capi_mai_usati(self) -> list[sqlite3.Row]:
        """Restituisce i capi che non compaiono mai nel diario."""
        return self.conn.execute(  # capi che non hanno nessuna voce nel diario
            "SELECT c.id, c.nome, s.nome AS sezione FROM capi c "
            "JOIN sezioni s ON s.id = c.sezione_id "
            "WHERE NOT EXISTS (SELECT 1 FROM diario d WHERE d.capo_id = c.id) "
            "ORDER BY s.ordine, c.nome COLLATE NOCASE"
        ).fetchall()

    # ------------------------------------------------------------ suggerimenti
    # SINTASSI — `'Tutte'` e `OR`
    # Un capo con stagione «Tutte» va bene per ogni stagione. La condizione
    # `(c.stagione = ? OR c.stagione = 'Tutte')` esprime proprio questo.
    def capi_per_suggerimento(self, stagione: str,
                              occasione: str | None = None) -> list[sqlite3.Row]:
        """Restituisce i capi adatti a una stagione e, se indicata, a un'occasione."""
        sql = [  # query costruita in base a stagione e occasione
            "SELECT c.id, c.nome, c.foto, c.ruolo, c.stagione, c.occasione,",  # dati utili all'anteprima
            "       s.nome AS sezione FROM capi c",
            "JOIN sezioni s ON s.id = c.sezione_id",
            "WHERE (c.stagione = ? OR c.stagione = 'Tutte')",  # include anche i capi «Tutte»
        ]
        parametri: list[object] = [stagione]  # la stagione è il primo parametro
        if occasione:  # se richiesta, filtra anche per occasione
            sql.append("AND c.occasione = ?")
            parametri.append(occasione)
        sql.append("AND c.ruolo != 'altro'")  # i capi «Altro» non entrano nei look automatici
        return self.conn.execute(" ".join(sql), parametri).fetchall()  # esegue la query

    # LOGICA — la connessione va chiusa quando l'app termina, altrimenti il
    # file del database può restare bloccato (soprattutto su Windows).
    def chiudi(self) -> None:
        """Chiude la connessione al database quando l'applicazione termina."""
        self.conn.close()  # chiude la connessione quando l'applicazione termina
