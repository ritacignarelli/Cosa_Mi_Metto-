"""Scheda Armadio: sezioni a sinistra, griglia dei capi a destra."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from tkinter import messagebox, simpledialog, ttk  # messaggi, richieste di testo e widget

from database import RUOLI, STAGIONI_FILTRO, Database  # ruoli, stagioni e archivio
from ui.form_capo import DialogoModificaCapo  # finestra per modificare un capo
from ui.stile import COLORI  # colori dell'interfaccia
from ui.widgets import ScrollableFrame, immagine  # area scorrevole e miniature

# SINTASSI — costante
# Il nome tutto maiuscolo è una convenzione Python per le costanti: valori che
# non dovrebbero cambiare durante l'esecuzione.
COLONNE = 4  # numero di capi mostrati per riga nella griglia


class ArmadioTab(ttk.Frame):
    """Scheda con le sezioni a sinistra e la griglia dei capi a destra."""

    def __init__(self, master, app):
        super().__init__(master, padding=(16, 12))  # scheda con un piccolo margine
        self.app = app  # finestra principale, serve per aggiornare le altre schede
        self.db: Database = app.db  # archivio condiviso
        self._sezioni = []  # sezioni lette dal database
        self._job_ricerca = None  # timer che ritarda la ricerca mentre si scrive

        self.var_sezione = tk.StringVar(value="Tutte le sezioni")  # filtro per sezione
        self.var_stagione = tk.StringVar(value="Tutte le stagioni")  # filtro per stagione
        self.var_cerca = tk.StringVar()  # testo di ricerca libera

        self.columnconfigure(1, weight=1)  # la griglia occupa tutto lo spazio disponibile
        self.rowconfigure(1, weight=1)
        self._costruisci()  # crea i widget della scheda
        self.ricarica()  # carica sezioni e capi

    # ---------------------------------------------------------------- layout
    def _costruisci(self) -> None:
        """Crea i widget della scheda: sezioni, filtri e griglia."""
        testata = ttk.Frame(self)  # contenitore del titolo
        testata.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(testata, text="Il tuo armadio", style="Titolo.TLabel"
                  ).pack(anchor="w")  # titolo della scheda
        ttk.Label(
            testata,
            text="Scegli una sezione, cerca un capo e clicca sulla foto per i dettagli.",
            style="Sottotitolo.TLabel",
        ).pack(anchor="w")  # istruzioni brevi

        pannello = ttk.LabelFrame(self, text="Sezioni", padding=10)  # riquadro delle sezioni
        pannello.grid(row=1, column=0, sticky="ns", padx=(0, 12))
        pannello.rowconfigure(0, weight=1)

        contenitore = ttk.Frame(pannello)  # contiene elenco e barra di scorrimento
        contenitore.grid(row=0, column=0, sticky="nsew")
        # SINTASSI — `tk.Listbox`
        # `exportselection=False` mantiene la selezione visibile anche quando
        # il focus passa a un altro widget; senza questa opzione Tkinter
        # deseleziona l'elenco appena clicchi altrove.
        self.lista_sezioni = tk.Listbox(
            contenitore, width=22, height=15, exportselection=False,
            activestyle="none", font=("Segoe UI", 10), bg="white",
            fg=COLORI["testo"], selectbackground=COLORI["primario"],
            selectforeground="white", highlightthickness=1,
            highlightbackground=COLORI["bordo"], relief="flat", bd=0,
        )  # elenco delle sezioni
        self.lista_sezioni.pack(side="left", fill="both", expand=True)
        barra = ttk.Scrollbar(contenitore, orient="vertical",
                              command=self.lista_sezioni.yview)  # barra di scorrimento dell'elenco
        barra.pack(side="right", fill="y")
        self.lista_sezioni.configure(yscrollcommand=barra.set)  # collega elenco e barra
        self.lista_sezioni.bind("<<ListboxSelect>>", self._selezione_lista)  # reagisce al clic su una sezione

        ttk.Button(pannello, text="Nuova sezione", style="Secondario.TButton",
                   command=self._nuova_sezione).grid(row=1, column=0,
                                                     sticky="ew", pady=(8, 2))  # crea una sezione
        ttk.Button(pannello, text="Rinomina", style="Secondario.TButton",
                   command=self._rinomina_sezione).grid(row=2, column=0,
                                                        sticky="ew", pady=2)  # rinomina la sezione scelta
        ttk.Button(pannello, text="Elimina", style="Pericolo.TButton",
                   command=self._elimina_sezione).grid(row=3, column=0,
                                                       sticky="ew", pady=2)  # elimina la sezione scelta
        ttk.Label(pannello, text="La sezione scelta filtra i capi.",
                  style="Tenue.TLabel", wraplength=170).grid(
            row=4, column=0, sticky="w", pady=(8, 0))  # spiega il funzionamento del filtro

        destra = ttk.Frame(self)  # parte destra con filtri e griglia
        destra.grid(row=1, column=1, sticky="nsew")
        destra.columnconfigure(0, weight=1)
        destra.rowconfigure(1, weight=1)

        barra_filtri = ttk.Frame(destra)  # riga dei filtri
        barra_filtri.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(barra_filtri, text="Cerca").grid(row=0, column=0,
                                                   padx=(0, 4))  # etichetta ricerca
        entry = ttk.Entry(barra_filtri, textvariable=self.var_cerca, width=24)  # campo di ricerca
        entry.grid(row=0, column=1, padx=(0, 16))
        entry.bind("<KeyRelease>", lambda _e: self._programma_ricerca())  # cerca mentre si scrive
        ttk.Label(barra_filtri, text="Sezione").grid(row=0, column=2,
                                                     padx=(0, 4))  # etichetta filtro sezione
        self.combo_sezione = ttk.Combobox(
            barra_filtri, textvariable=self.var_sezione, state="readonly", width=18
        )  # menu del filtro sezione
        self.combo_sezione.grid(row=0, column=3, padx=(0, 16))
        self.combo_sezione.bind("<<ComboboxSelected>>", self._filtro_cambiato)  # aggiorna la griglia
        ttk.Label(barra_filtri, text="Stagione").grid(row=0, column=4,
                                                      padx=(0, 4))  # etichetta filtro stagione
        # SINTASSI — concatenazione di tuple
        # `("Tutte le stagioni",)` è una tupla di un solo elemento: la virgola
        # finale è obbligatoria, altrimenti sarebbero solo parentesi.
        # `+ STAGIONI_FILTRO` crea una nuova tupla con tutte le voci.
        self.combo_stagione = ttk.Combobox(
            barra_filtri, textvariable=self.var_stagione, state="readonly",
            width=16, values=("Tutte le stagioni",) + STAGIONI_FILTRO,
        )  # menu del filtro stagione
        self.combo_stagione.grid(row=0, column=5)
        self.combo_stagione.bind("<<ComboboxSelected>>",
                                 lambda _e: self._carica_capi())  # ricarica i capi al cambio
        ttk.Button(barra_filtri, text="Azzera", style="Secondario.TButton",
                   command=self._azzera_filtri).grid(row=0, column=6,
                                                     padx=(12, 0))  # pulisce tutti i filtri

        self.griglia = ScrollableFrame(destra)  # area scorrevole con le card dei capi
        self.griglia.grid(row=1, column=0, sticky="nsew")

    # ---------------------------------------------------------------- sezioni
    def ricarica(self) -> None:
        """Rilegge sezioni e capi e aggiorna tutta la scheda."""
        self._carica_sezioni()  # rilegge le sezioni
        self._carica_capi()  # rilegge e ridisegna i capi

    def _carica_sezioni(self) -> None:
        """Legge le sezioni dal database e aggiorna elenco e filtro."""
        self._sezioni = self.db.sezioni()  # legge le sezioni dal database
        nomi = [r["nome"] for r in self._sezioni]  # estrae i nomi
        self.lista_sezioni.delete(0, "end")  # svuota l'elenco
        for nome in nomi:  # reinserisce le sezioni aggiornate
            self.lista_sezioni.insert("end", nome)
        valori = ["Tutte le sezioni"] + nomi  # voci del filtro sezione
        self.combo_sezione.configure(values=valori)  # aggiorna il menu
        if self.var_sezione.get() not in valori:  # la sezione scelta non esiste più
            self.var_sezione.set("Tutte le sezioni")  # torna a «Tutte»
        self._evidenzia_lista()  # evidenzia la sezione attiva

    def _evidenzia_lista(self) -> None:
        """Evidenzia nell'elenco la sezione attualmente filtrata."""
        self.lista_sezioni.selection_clear(0, "end")  # toglie la selezione precedente
        for indice, riga in enumerate(self._sezioni):  # cerca la sezione attiva
            if riga["nome"] == self.var_sezione.get():
                self.lista_sezioni.selection_set(indice)  # la seleziona
                self.lista_sezioni.see(indice)  # la porta in vista
                break

    def _selezione_lista(self, _event=None) -> None:
        """Applica il filtro della sezione cliccata nell'elenco."""
        # SINTASSI — `curselection()`
        # Restituisce una tupla con gli indici delle righe selezionate
        # (di solito una sola). Se non c'è selezione restituisce una tupla
        # vuota, che in un `if` vale come False.
        selezione = self.lista_sezioni.curselection()  # sezione cliccata
        if not selezione:  # nessuna selezione
            return
        nome = self.lista_sezioni.get(selezione[0])  # nome della sezione
        self.var_sezione.set(nome)  # aggiorna il filtro
        self._carica_capi()  # mostra i capi della sezione

    def _filtro_cambiato(self, _event=None) -> None:
        """Aggiorna l'elenco delle sezioni e ricarica la griglia."""
        self._evidenzia_lista()  # allinea l'elenco a sinistra
        self._carica_capi()  # ricarica la griglia

    def _azzera_filtri(self) -> None:
        """Azzera ricerca e filtri, mostrando di nuovo tutti i capi."""
        self.var_cerca.set("")  # svuota la ricerca
        self.var_sezione.set("Tutte le sezioni")  # toglie il filtro sezione
        self.var_stagione.set("Tutte le stagioni")  # toglie il filtro stagione
        self._evidenzia_lista()  # toglie l'evidenziazione
        self._carica_capi()  # ricarica tutti i capi

    def _sezione_scelta(self):
        """Restituisce la sezione selezionata oppure None."""
        selezione = self.lista_sezioni.curselection()  # sezione selezionata nell'elenco
        if not selezione:  # nessuna sezione scelta
            messagebox.showinfo(
                "Nessuna sezione",
                "Seleziona prima una sezione nell'elenco a sinistra.",
                parent=self.winfo_toplevel(),
            )  # avvisa l'utente
            return None
        return self._sezioni[selezione[0]]  # restituisce la riga della sezione

    def _nuova_sezione(self) -> None:
        """Chiede il nome e crea una nuova sezione."""
        # SINTASSI — `simpledialog.askstring`
        # Mostra una piccola finestra con un campo di testo. Restituisce la
        # stringa scritta oppure None se l'utente preme Annulla. Per questo
        # controlliamo `if nome is None`.
        nome = simpledialog.askstring("Nuova sezione", "Nome della sezione:",
                                      parent=self.winfo_toplevel())  # chiede il nome
        if nome is None:  # l'utente ha annullato
            return
        try:
            self.db.aggiungi_sezione(nome)  # salva la nuova sezione
        except ValueError as exc:  # nome vuoto o duplicato
            messagebox.showerror("Sezione non valida", str(exc),
                                 parent=self.winfo_toplevel())  # mostra l'errore
            return
        self.app.dati_cambiati()  # aggiorna tutte le schede
        self.var_sezione.set(nome.strip())  # seleziona la nuova sezione
        self._carica_sezioni()  # aggiorna l'elenco
        self._carica_capi()  # aggiorna la griglia
        self.app.messaggio(f"Sezione «{nome.strip()}» creata.")  # conferma all'utente

    def _rinomina_sezione(self) -> None:
        """Chiede un nuovo nome e rinomina la sezione scelta."""
        riga = self._sezione_scelta()  # sezione da rinominare
        if riga is None:
            return
        nome = simpledialog.askstring("Rinomina sezione", "Nuovo nome:",
                                      initialvalue=riga["nome"],
                                      parent=self.winfo_toplevel())  # chiede il nuovo nome
        if nome is None or nome.strip() == riga["nome"]:  # annullato o nome invariato
            return
        try:
            self.db.rinomina_sezione(riga["id"], nome)  # salva il nuovo nome
        except ValueError as exc:  # nome vuoto o duplicato
            messagebox.showerror("Sezione non valida", str(exc),
                                 parent=self.winfo_toplevel())  # mostra l'errore
            return
        self.var_sezione.set(nome.strip())  # aggiorna il filtro
        self.app.dati_cambiati()  # aggiorna le altre schede
        self.app.messaggio("Sezione rinominata.")  # conferma all'utente

    def _elimina_sezione(self) -> None:
        """Elimina la sezione scelta, dopo aver chiesto conferma."""
        riga = self._sezione_scelta()  # sezione da eliminare
        if riga is None:
            return
        # SINTASSI — `messagebox.askyesno`
        # Mostra una domanda con i pulsanti Sì/No e restituisce True o False.
        # Il `not` davanti significa: «se l'utente NON ha confermato, esci».
        if not messagebox.askyesno(
            "Eliminare la sezione?",
            f"Vuoi eliminare la sezione «{riga['nome']}»?",
            parent=self.winfo_toplevel(),
        ):  # chiede conferma prima di eliminare
            return
        try:
            self.db.elimina_sezione(riga["id"])  # elimina la sezione vuota
        except ValueError as exc:  # la sezione contiene ancora capi
            messagebox.showerror("Impossibile eliminare", str(exc),
                                 parent=self.winfo_toplevel())  # spiega il motivo
            return
        self.var_sezione.set("Tutte le sezioni")  # torna a mostrare tutto
        self.app.dati_cambiati()  # aggiorna le altre schede
        self.app.messaggio("Sezione eliminata.")  # conferma all'utente

    # ------------------------------------------------------------------ capi
    def _programma_ricerca(self) -> None:
        """Ritarda la ricerca mentre l'utente scrive (debounce)."""
        # SINTASSI — debounce con `after`
        # Ogni tasto premuto annulla il timer precedente e ne crea uno nuovo.
        # La ricerca parte solo quando l'utente smette di scrivere per 250 ms:
        # così non eseguiamo una query per ogni singola lettera.
        if self._job_ricerca:  # se c'era già una ricerca in attesa
            self.after_cancel(self._job_ricerca)  # annulla il timer precedente
        self._job_ricerca = self.after(250, self._carica_capi)  # cerca dopo 250 ms dall'ultimo tasto

    def _carica_capi(self) -> None:
        """Legge i capi con i filtri attivi e ridisegna la griglia."""
        sezione_id = None  # nessun filtro sezione all'inizio
        for riga in self._sezioni:  # cerca l'id della sezione scelta
            if riga["nome"] == self.var_sezione.get():
                sezione_id = riga["id"]
                break
        stagione = self.var_stagione.get()  # stagione scelta nel filtro
        if stagione == "Tutte le stagioni":  # il filtro «Tutte» significa nessun filtro
            stagione = None
        righe = self.db.capi(sezione_id=sezione_id, stagione=stagione,
                             testo=self.var_cerca.get())  # legge i capi filtrati
        self._disegna_griglia(righe)  # aggiorna la griglia

    def _disegna_griglia(self, righe) -> None:
        """Svuota la griglia e ricrea una card per ogni capo."""
        for figlio in self.griglia.contenuto.winfo_children():  # svuota la griglia attuale
            figlio.destroy()
        for colonna in range(COLONNE):  # imposta le colonne della griglia
            self.griglia.contenuto.columnconfigure(colonna, weight=1)

        if not righe:  # nessun capo da mostrare
            self._disegna_vuoto()  # mostra il messaggio «armadio vuoto» o «nessun risultato»
            return

        for indice, riga in enumerate(righe):  # crea una card per ogni capo
            card = self._crea_card(riga)  # costruisce la card
            # SINTASSI — `//` e `%` per la griglia
            # Con 4 colonne: indice 0..3 -> riga 0; 4..7 -> riga 1; ecc.
            # `indice // 4` dà la riga, `indice % 4` dà la colonna.
            card.grid(row=indice // COLONNE, column=indice % COLONNE,
                      padx=6, pady=6, sticky="n")  # posiziona la card nella griglia
        self.griglia.collega_rotella()  # attiva la rotella del mouse sulle nuove card

    def _disegna_vuoto(self) -> None:
        """Mostra un messaggio quando l'armadio o i filtri non trovano capi."""
        riquadro = ttk.Frame(self.griglia.contenuto, padding=50)  # contenitore del messaggio
        riquadro.grid(row=0, column=0, columnspan=COLONNE, pady=30)
        if self.db.conta_capi() == 0:  # l'armadio non ha ancora capi
            titolo = "L'armadio è ancora vuoto"
            testo = "Aggiungi il primo capo dalla scheda «Aggiungi capo»."
        else:  # ci sono capi ma i filtri non trovano risultati
            titolo = "Nessun capo trovato"
            testo = "Prova a cambiare sezione, stagione o testo di ricerca."
        ttk.Label(riquadro, text=titolo, style="Titolo.TLabel").pack()  # titolo del messaggio
        ttk.Label(riquadro, text=testo, style="Tenue.TLabel").pack(pady=(6, 0))  # suggerimento

    def _crea_card(self, riga) -> tk.Frame:
        """Crea la card cliccabile di un capo con foto e dettagli."""
        card = tk.Frame(self.griglia.contenuto, bg=COLORI["superficie"],
                        highlightbackground=COLORI["bordo"],
                        highlightthickness=1, cursor="hand2")  # card bianca cliccabile
        foto = immagine(self.db.percorso_foto(riga["foto"]), (150, 150))  # miniatura del capo
        etichetta_foto = tk.Label(card, image=foto, bg=COLORI["superficie"],
                                  bd=0, cursor="hand2")  # spazio della foto
        etichetta_foto.image = foto  # evita che Tk elimini l'immagine dalla memoria
        etichetta_foto.pack(padx=10, pady=(10, 5))
        nome = tk.Label(card, text=riga["nome"], bg=COLORI["superficie"],
                        fg=COLORI["testo"], font=("Segoe UI", 10, "bold"),
                        wraplength=150, justify="center", cursor="hand2")  # nome del capo
        nome.pack(padx=10)
        dettagli = tk.Label(
            card, text=f"{riga['sezione']} · {riga['stagione']}",
            bg=COLORI["superficie"], fg=COLORI["tenue"],
            font=("Segoe UI", 8), wraplength=150, justify="center",
            cursor="hand2",
        )  # sezione e stagione del capo
        dettagli.pack(padx=10, pady=(2, 10))

        # SINTASSI — lambda con valore catturato
        # Se scrivessimo `lambda _e: self._apri_dettaglio(riga)`, tutte le
        # lambda userebbero l'ultimo valore di `riga` (late binding). Il
        # parametro `r=riga` crea una copia del valore attuale per ogni card.
        for widget in (card, etichetta_foto, nome, dettagli):  # rende cliccabili tutti gli elementi
            widget.bind("<Button-1>", lambda _e, r=riga: self._apri_dettaglio(r))
        # SINTASSI — eventi del mouse
        # `<Enter>` scatta quando il mouse entra nel widget, `<Leave>` quando
        # esce. Qui cambiamo solo il colore del bordo per darlo «vivo».
        card.bind("<Enter>", lambda _e: card.configure(
            highlightbackground=COLORI["primario"]))  # bordo colorato al passaggio del mouse
        card.bind("<Leave>", lambda _e: card.configure(
            highlightbackground=COLORI["bordo"]))  # bordo normale quando il mouse esce
        return card  # restituisce la card pronta

    def _apri_dettaglio(self, riga) -> None:
        """Apre la finestra di dettaglio del capo cliccato."""
        capo = self.db.capo(riga["id"])  # rilegge il capo aggiornato dal database
        if capo is None:  # il capo è stato eliminato nel frattempo
            self.ricarica()  # aggiorna la griglia
            return
        DettaglioCapo(self.winfo_toplevel(), self.db, capo, self.app)  # apre la finestra di dettaglio


# SINTASSI — seconda finestra modale
# `tk.Toplevel` crea una finestra separata. `transient` + `grab_set` la
# rendono un dialogo che resta sopra la finestra principale e blocca i clic
# sulle altre finestre finché non viene chiusa.
class DettaglioCapo(tk.Toplevel):
    """Finestra modale con la foto grande e i dettagli di un capo."""

    def __init__(self, master, db: Database, capo, app):
        super().__init__(master)  # crea la finestra di dettaglio
        self.db = db  # archivio condiviso
        self.capo = capo  # capo mostrato
        self.app = app  # finestra principale
        self.title(capo["nome"])  # titolo con il nome del capo
        self.configure(bg=COLORI["superficie"])  # sfondo bianco
        self.resizable(False, False)  # dimensione fissa
        self.transient(master)  # resta sopra la finestra principale
        self.grab_set()  # blocca le altre finestre finché è aperta

        foto = immagine(db.percorso_foto(capo["foto"]), (360, 360))  # foto ingrandita
        etichetta = tk.Label(self, image=foto, bg=COLORI["superficie"], bd=0)  # spazio della foto
        etichetta.image = foto  # evita che Tk elimini l'immagine dalla memoria
        etichetta.pack(padx=24, pady=(24, 8))

        tk.Label(self, text=capo["nome"], bg=COLORI["superficie"],
                 fg=COLORI["testo"], font=("Segoe UI", 15, "bold"),
                 wraplength=360).pack(padx=24)  # nome del capo
        tk.Label(self, text=f"{capo['sezione']} · {RUOLI.get(capo['ruolo'], 'Altro')}",
                 bg=COLORI["superficie"], fg=COLORI["tenue"],
                 font=("Segoe UI", 10)).pack(padx=24, pady=(2, 10))  # sezione e ruolo

        info = tk.Frame(self, bg=COLORI["superficie"])  # tabella delle informazioni
        info.pack(padx=24, fill="x")
        # SINTASSI — `valore or "—"` e slicing
        # Se `capo["colore"]` è una stringa vuota (falsa), `or` usa "—".
        # `(capo["creato"] or "")[:10]` prende i primi 10 caratteri della
        # data, cioè "AAAA-MM-GG" da un timestamp completo.
        righe = [  # coppie etichetta/valore da mostrare
            ("Colore", capo["colore"] or "—"),
            ("Stagione", capo["stagione"]),
            ("Occasione", capo["occasione"]),
            ("Aggiunto il", (capo["creato"] or "")[:10]),
        ]
        for indice, (voce, valore) in enumerate(righe):  # crea una riga per ogni informazione
            tk.Label(info, text=voce, bg=COLORI["superficie"],
                     fg=COLORI["tenue"], font=("Segoe UI", 9)).grid(
                row=indice, column=0, sticky="w", padx=(0, 18), pady=1)  # nome del dato
            tk.Label(info, text=valore, bg=COLORI["superficie"],
                     fg=COLORI["testo"], font=("Segoe UI", 9)).grid(
                row=indice, column=1, sticky="w", pady=1)  # valore del dato

        pulsanti = ttk.Frame(self, style="Card.TFrame", padding=(24, 18, 24, 20))  # barra dei pulsanti
        pulsanti.pack(fill="x")
        ttk.Button(pulsanti, text="Elimina", style="Pericolo.TButton",
                   command=self._elimina).pack(side="left")  # elimina il capo
        ttk.Button(pulsanti, text="Chiudi", style="Secondario.TButton",
                   command=self.destroy).pack(side="right")  # chiude la finestra
        ttk.Button(pulsanti, text="Modifica", style="Accent.TButton",
                   command=self._modifica).pack(side="right", padx=(0, 8))  # modifica il capo

        self.bind("<Escape>", lambda _e: self.destroy())  # Esc chiude la finestra
        self.update_idletasks()  # calcola le dimensioni reali
        genitore = master.winfo_toplevel()  # finestra principale
        x = genitore.winfo_rootx() + (genitore.winfo_width() - self.winfo_width()) // 2  # centro orizzontale
        y = genitore.winfo_rooty() + (genitore.winfo_height() - self.winfo_height()) // 2  # centro verticale
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")  # sposta la finestra

    def _modifica(self) -> None:
        """Apre il form di modifica del capo."""
        DialogoModificaCapo(self, self.db, self.capo, self._dopo_modifica)  # apre il form di modifica

    def _dopo_modifica(self) -> None:
        """Aggiorna l'app e chiude il dettaglio dopo la modifica."""
        self.app.dati_cambiati()  # aggiorna tutte le schede
        self.app.messaggio("Capo modificato.")  # conferma all'utente
        self.destroy()  # chiude il dettaglio

    def _elimina(self) -> None:
        """Elimina il capo dopo la conferma dell'utente."""
        if not messagebox.askyesno(
            "Eliminare il capo?",
            f"Vuoi eliminare «{self.capo['nome']}»?\n"
            "Verrà tolto anche dai look e dal diario.",
            parent=self,
        ):  # chiede conferma prima di eliminare
            return
        self.db.elimina_capo(self.capo["id"])  # elimina capo, foto e collegamenti
        self.app.dati_cambiati()  # aggiorna tutte le schede
        self.app.messaggio("Capo eliminato.")  # conferma all'utente
        self.destroy()  # chiude il dettaglio
