"""Form riutilizzabile per aggiungere o modificare un capo."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from pathlib import Path  # gestisce i percorsi delle foto
from tkinter import filedialog, messagebox, ttk  # finestre di dialogo, messaggi e widget

from PIL import Image, UnidentifiedImageError  # Pillow: controlla che il file sia un'immagine valida

from database import (OCCASIONI, RUOLI, RUOLI_DA_ETICHETTA, RUOLI_ORDINE,
                      STAGIONI, Database, ruolo_da_sezione)  # costanti e archivio
from logica import importa_foto  # copia e ridimensiona la foto scelta
from ui.stile import COLORI  # colori dell'interfaccia
from ui.widgets import immagine  # crea l'anteprima della foto

# SINTASSI — formato dei filtri di `filedialog`
# Ogni voce è una tupla (descrizione, estensioni). Le estensioni sono separate
# da uno spazio e usano `*` come jolly. Tkinter mostra la descrizione nel menu
# e filtra i file in base alle estensioni.
TIPI_IMMAGINE = [  # filtri mostrati nella finestra di scelta del file
    ("Immagini", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
    ("Tutti i file", "*.*"),
]


class FormCapo(ttk.Frame):
    """Campi del capo con anteprima della foto."""

    def __init__(self, master, db: Database, capo=None):
        super().__init__(master, style="Card.TFrame", padding=24)  # card bianca del form
        self.db = db  # archivio da cui leggere sezioni e foto
        self.capo = capo  # capo da modificare, oppure None per un nuovo capo
        self.foto_esistente = capo["foto"] if capo else None  # foto già salvata nel database
        self.foto_sorgente: str | None = None  # percorso di una nuova foto scelta ma non ancora importata
        self._sezioni = []  # elenco delle sezioni lette dal database

        # SINTASSI — `tk.StringVar`
        # È una variabile speciale collegata ai widget Tkinter. Il widget
        # mostra il suo valore e, quando l'utente scrive o sceglie, il valore
        # cambia dentro la variabile. Si legge con `.get()` e si scrive con
        # `.set(...)`.
        self.var_nome = tk.StringVar()  # testo del campo nome
        self.var_sezione = tk.StringVar()  # sezione scelta
        self.var_ruolo = tk.StringVar()  # ruolo del capo nel look
        self.var_colore = tk.StringVar()  # colore scritto dall'utente
        self.var_stagione = tk.StringVar()  # stagione scelta
        self.var_occasione = tk.StringVar()  # occasione scelta

        # SINTASSI — `columnconfigure(..., weight=...)`
        # `weight` decide come si dividono lo spazio extra quando la finestra
        # viene allargata. Con 3 e 2, i campi prendono il 60% e l'anteprima
        # il 40% dello spazio disponibile.
        self.columnconfigure(0, weight=3)  # i campi occupano più spazio dell'anteprima
        self.columnconfigure(1, weight=2)

        campi = ttk.Frame(self, style="Card.TFrame")  # colonna sinistra con i campi
        campi.grid(row=0, column=0, sticky="nsew", padx=(0, 28))
        campi.columnconfigure(1, weight=1)  # i campi si allargano con la finestra
        self._crea_campi(campi)  # costruisce le etichette e i campi

        foto = ttk.Frame(self, style="Card.TFrame")  # colonna destra con l'anteprima
        foto.grid(row=0, column=1, sticky="n")
        ttk.Label(foto, text="Foto del capo", style="CardTitolo.TLabel"
                  ).pack(anchor="w", pady=(0, 8))  # titolo dell'anteprima
        self.lbl_foto = ttk.Label(foto, style="Card.TLabel")  # spazio per l'immagine
        self.lbl_foto.pack()
        ttk.Button(foto, text="Scegli foto…", style="Secondario.TButton",
                   command=self._scegli_foto).pack(fill="x", pady=(10, 4))  # apre la scelta del file
        ttk.Button(foto, text="Rimuovi foto", style="Secondario.TButton",
                   command=self._rimuovi_foto).pack(fill="x")  # toglie la foto dal form
        ttk.Label(foto, text="JPG, PNG, GIF, BMP o WEBP.\nLa foto resta sul tuo computer.",
                  style="CardTenue.TLabel", justify="center").pack(pady=(8, 0))  # informazione sulla privacy

        # SINTASSI — `<<ComboboxSelected>>`
        # È un evento virtuale di Tkinter: scatta quando l'utente sceglie una
        # voce dal menu a tendina. Il secondo argomento è la funzione da
        # chiamare; riceverà un oggetto evento (che qui non ci serve).
        self.combo_sezione.bind("<<ComboboxSelected>>", self._sezione_cambiata)  # aggiorna il ruolo quando cambia sezione
        self.ricarica()  # carica le sezioni disponibili
        if capo:  # se stiamo modificando un capo esistente
            self._carica_capo(capo)  # riempie i campi con i suoi dati
        else:  # se stiamo aggiungendo un nuovo capo
            self.reset()  # prepara i campi vuoti

    def _crea_campi(self, genitore) -> None:
        """Crea le etichette e i campi del form nella colonna sinistra."""
        # SINTASSI — funzione annidata
        # `campo` è definita dentro `_crea_campi` e usa `genitore`, che è una
        # variabile del metodo esterno. Questo si chiama «closure»: la funzione
        # interna ricorda il valore della variabile esterna.
        def campo(riga: int, testo: str) -> None:  # piccola funzione per creare una riga del form
            ttk.Label(genitore, text=testo, style="Card.TLabel"
                      ).grid(row=riga, column=0, sticky="w", pady=4, padx=(0, 12))  # etichetta del campo

        campo(0, "Nome *")  # etichetta del nome
        self.entry_nome = ttk.Entry(genitore, textvariable=self.var_nome)  # campo di testo del nome
        self.entry_nome.grid(row=0, column=1, sticky="ew", pady=4)

        campo(1, "Sezione *")  # etichetta della sezione
        # SINTASSI — `state="readonly"`
        # L'utente può scegliere solo una delle voci presenti, ma non può
        # scrivere testo libero. È diverso da `state="disabled"`, che blocca
        # completamente il widget.
        self.combo_sezione = ttk.Combobox(genitore, textvariable=self.var_sezione,
                                          state="readonly", width=28)  # menu delle sezioni
        self.combo_sezione.grid(row=1, column=1, sticky="ew", pady=4)

        campo(2, "Ruolo nel look *")  # etichetta del ruolo
        self.combo_ruolo = ttk.Combobox(
            genitore, textvariable=self.var_ruolo, state="readonly", width=28,
            values=[RUOLI[r] for r in RUOLI_ORDINE],  # mostra le etichette leggibili dei ruoli
        )
        self.combo_ruolo.grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(genitore, text="Serve per comporre i look e i suggerimenti.",
                  style="CardTenue.TLabel").grid(row=3, column=1, sticky="w")  # spiegazione del ruolo

        campo(4, "Colore")  # etichetta del colore
        ttk.Entry(genitore, textvariable=self.var_colore).grid(
            row=4, column=1, sticky="ew", pady=(10, 4))  # campo di testo libero

        campo(5, "Stagione *")  # etichetta della stagione
        ttk.Combobox(genitore, textvariable=self.var_stagione, state="readonly",
                     values=list(STAGIONI), width=28).grid(
            row=5, column=1, sticky="ew", pady=4)  # menu delle stagioni

        campo(6, "Occasione *")  # etichetta dell'occasione
        ttk.Combobox(genitore, textvariable=self.var_occasione, state="readonly",
                     values=list(OCCASIONI), width=28).grid(
            row=6, column=1, sticky="ew", pady=4)  # menu delle occasioni

        ttk.Label(genitore, text="* campo obbligatorio", style="CardTenue.TLabel"
                  ).grid(row=7, column=1, sticky="w", pady=(12, 0))  # nota sui campi obbligatori

    # ------------------------------------------------------------------ dati
    def ricarica(self) -> None:
        """Rilegge le sezioni dal database e aggiorna il menu a tendina."""
        self._sezioni = self.db.sezioni()  # rilegge le sezioni dal database
        nomi = [r["nome"] for r in self._sezioni]  # estrae solo i nomi
        self.combo_sezione.configure(values=nomi)  # aggiorna il menu a tendina
        if self.var_sezione.get() not in nomi:  # se la sezione scelta non esiste più
            self.var_sezione.set(nomi[0] if nomi else "")  # sceglie la prima disponibile

    def _carica_capo(self, capo) -> None:
        """Riempie i campi del form con i dati di un capo esistente."""
        self.var_nome.set(capo["nome"])  # nome del capo
        self.var_sezione.set(capo["sezione"])  # sezione attuale
        self.var_ruolo.set(RUOLI.get(capo["ruolo"], RUOLI["altro"]))  # ruolo leggibile
        self.var_colore.set(capo["colore"])  # colore salvato
        self.var_stagione.set(capo["stagione"])  # stagione salvata
        self.var_occasione.set(capo["occasione"])  # occasione salvata
        self.carica_anteprima()  # mostra la foto già salvata

    def reset(self) -> None:
        """Riporta il form ai valori iniziali per un nuovo capo."""
        self.var_nome.set("")  # svuota il nome
        self.var_colore.set("")  # svuota il colore
        nomi = [r["nome"] for r in self._sezioni]  # nomi delle sezioni disponibili
        self.var_sezione.set(nomi[0] if nomi else "")  # seleziona la prima sezione
        self.var_ruolo.set(RUOLI[ruolo_da_sezione(self.var_sezione.get())])  # deduce il ruolo dal nome della sezione
        self.var_stagione.set("Tutte")  # stagione predefinita
        self.var_occasione.set(OCCASIONI[0])  # occasione predefinita
        self.foto_sorgente = None  # nessuna nuova foto scelta
        self.foto_esistente = None  # nessuna foto salvata
        self.carica_anteprima()  # mostra il segnaposto

    def _sezione_cambiata(self, _event=None) -> None:
        """Propone il ruolo nel look in base alla sezione scelta."""
        self.var_ruolo.set(RUOLI[ruolo_da_sezione(self.var_sezione.get())])  # propone il ruolo adatto alla sezione

    def raccogli(self) -> dict:
        """Legge i campi, li controlla e restituisce i dati pronti per il database."""
        nome = self.var_nome.get().strip()  # legge e pulisce il nome
        if not nome:  # il nome è obbligatorio
            raise ValueError("Inserisci il nome del capo.")
        sezione = self.db.sezione_per_nome(self.var_sezione.get())  # cerca la sezione scelta
        if sezione is None:  # la sezione potrebbe non esistere più
            raise ValueError("Crea prima una sezione nella scheda «Armadio».")
        ruolo = RUOLI_DA_ETICHETTA.get(self.var_ruolo.get())  # trasforma l'etichetta nel codice interno
        if ruolo is None:  # ruolo non riconosciuto
            raise ValueError("Scegli il ruolo del capo nel look.")
        if self.var_stagione.get() not in STAGIONI:  # stagione non valida
            raise ValueError("Scegli una stagione.")
        if self.var_occasione.get() not in OCCASIONI:  # occasione non valida
            raise ValueError("Scegli un'occasione.")
        return {  # dati pronti per essere salvati nel database
            "nome": nome,
            "sezione_id": sezione["id"],
            "ruolo": ruolo,
            "colore": self.var_colore.get().strip(),
            "stagione": self.var_stagione.get(),
            "occasione": self.var_occasione.get(),
        }

    def prepara_foto(self) -> str | None:
        """Importa la nuova foto scelta oppure restituisce quella già salvata."""
        if self.foto_sorgente:  # se l'utente ha scelto una nuova foto
            return importa_foto(self.db, self.foto_sorgente)  # la copia e la ridimensiona
        return self.foto_esistente  # altrimenti mantiene la foto già salvata

    # ------------------------------------------------------------------ foto
    def _scegli_foto(self) -> None:
        """Apre la finestra di scelta del file e mostra l'anteprima."""
        # SINTASSI — `filedialog.askopenfilename`
        # Restituisce il percorso del file scelto oppure una stringa vuota ""
        # se l'utente preme Annulla. `parent` indica la finestra sopra cui
        # mostrare il dialogo.
        percorso = filedialog.askopenfilename(
            parent=self.winfo_toplevel(), title="Scegli la foto del capo",
            filetypes=TIPI_IMMAGINE,
        )  # apre la finestra di scelta del file
        if not percorso:  # l'utente ha annullato
            return
        try:
            with Image.open(percorso) as img:  # apre il file scelto
                # SINTASSI — `img.verify()`
                # Controlla l'integrità del file senza decodificare tutti i
                # pixel. Dopo `verify()` l'immagine non è più utilizzabile:
                # per questo, al salvataggio, `importa_foto` riapre il file.
                img.verify()  # controlla che sia davvero un'immagine
        except (UnidentifiedImageError, OSError, ValueError):  # file non valido o danneggiato
            messagebox.showerror(
                "Foto non valida",
                "Il file scelto non è un'immagine valida o è danneggiato.",
                parent=self.winfo_toplevel(),
            )  # spiega l'errore all'utente
            return
        self.foto_sorgente = percorso  # memorizza la foto da importare al salvataggio
        self.carica_anteprima()  # mostra subito l'anteprima

    def _rimuovi_foto(self) -> None:
        """Toglie la foto dal form e mostra il segnaposto."""
        self.foto_sorgente = None  # elimina la nuova foto scelta
        self.foto_esistente = None  # elimina il riferimento alla foto salvata
        self.carica_anteprima()  # torna al segnaposto

    def carica_anteprima(self) -> None:
        """Mostra nel form la foto scelta o quella già salvata."""
        if self.foto_sorgente:  # se c'è una nuova foto da mostrare
            percorso = Path(self.foto_sorgente)
        else:  # altrimenti usa la foto già salvata
            percorso = self.db.percorso_foto(self.foto_esistente)
        foto = immagine(percorso, (230, 230))  # crea la miniatura
        self.lbl_foto.configure(image=foto)  # aggiorna l'anteprima
        # SINTASSI — riferimento all'immagine
        # Tkinter non conserva da solo la PhotoImage: se la variabile locale
        # sparisce, l'immagine può essere cancellata e il label resta vuoto.
        # Per questo la salviamo come attributo del label.
        self.lbl_foto.image = foto  # evita che Tk elimini l'immagine dalla memoria


# SINTASSI — `tk.Toplevel`
# È una seconda finestra, separata da quella principale. Si usa per i dialoghi
# di modifica. `transient` la lega alla finestra madre e `grab_set` la rende
# modale: finché è aperta, non puoi cliccare sulle altre finestre dell'app.
class DialogoModificaCapo(tk.Toplevel):
    """Finestra modale per modificare un capo esistente."""

    def __init__(self, master, db: Database, capo, al_salvataggio):
        super().__init__(master)  # crea la finestra di dialogo
        self.db = db  # archivio condiviso
        self.capo = capo  # capo da modificare
        self.al_salvataggio = al_salvataggio  # funzione da chiamare dopo il salvataggio
        self.title(f"Modifica — {capo['nome']}")  # titolo della finestra
        self.configure(bg=COLORI["superficie"])  # sfondo bianco
        self.resizable(False, False)  # dimensione fissa
        self.transient(master.winfo_toplevel())  # resta sopra la finestra principale
        # SINTASSI — `grab_set`
        # «Prende» il controllo degli eventi: i clic vanno a questa finestra
        # finché non viene chiusa. È ciò che rende il dialogo modale.
        self.grab_set()  # blocca l'interazione con le altre finestre

        self.form = FormCapo(self, db, capo)  # form precompilato con i dati del capo
        self.form.pack(fill="both", expand=True)

        pulsanti = ttk.Frame(self, style="Card.TFrame", padding=(24, 0, 24, 20))  # barra dei pulsanti
        pulsanti.pack(fill="x")
        ttk.Button(pulsanti, text="Annulla", style="Secondario.TButton",
                   command=self.destroy).pack(side="right")  # chiude senza salvare
        ttk.Button(pulsanti, text="Salva modifiche", style="Accent.TButton",
                   command=self._salva).pack(side="right", padx=(0, 8))  # salva le modifiche

        # SINTASSI — `lambda _e: self.destroy()`
        # Una lambda è una funzione anonima di una sola espressione. Tkinter
        # passa un evento alla funzione, quindi serve un parametro `_e` anche
        # se non lo usiamo. Il nome con `_` indica «parametro volutamente
        # ignorato».
        self.bind("<Escape>", lambda _e: self.destroy())  # Esc chiude la finestra
        # SINTASSI — `update_idletasks`
        # Tkinter calcola le dimensioni dei widget in modo «pigro». Questa
        # chiamata forza il calcolo, così `winfo_width()` restituisce misure
        # vere e possiamo centrare la finestra.
        self.update_idletasks()  # calcola le dimensioni reali
        self._centra()  # centra la finestra sul genitore

    def _centra(self) -> None:
        """Centra la finestra di modifica sopra la finestra principale."""
        genitore = self.master.winfo_toplevel()  # finestra principale
        # `winfo_rootx/rooty` danno la posizione assoluta sullo schermo;
        # `winfo_width/height` danno le dimensioni attuali.
        x = genitore.winfo_rootx() + (genitore.winfo_width() - self.winfo_width()) // 2  # centro orizzontale
        y = genitore.winfo_rooty() + (genitore.winfo_height() - self.winfo_height()) // 2  # centro verticale
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")  # sposta la finestra

    def _salva(self) -> None:
        """Salva le modifiche al capo e chiude la finestra."""
        try:
            dati = self.form.raccogli()  # legge e controlla i campi
            foto = self.form.prepara_foto()  # importa l'eventuale nuova foto
            # SINTASSI — `**dati`
            # `dati` è un dizionario con chiavi "nome", "sezione_id", ecc.
            # `**dati` lo «apre» e passa ogni voce come argomento nominato:
            # equivale a scrivere nome=..., sezione_id=..., ruolo=...
            self.db.modifica_capo(self.capo["id"], foto=foto, **dati)  # salva le modifiche
        except ValueError as exc:  # dati non validi
            messagebox.showerror("Dati non validi", str(exc), parent=self)  # mostra il messaggio
            return
        self.destroy()  # chiude la finestra
        self.al_salvataggio()  # avvisa la scheda che i dati sono cambiati
