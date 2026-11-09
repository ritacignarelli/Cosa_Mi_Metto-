"""Scheda Look: composizione, anteprima e archivio dei look salvati."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from tkinter import messagebox, ttk  # messaggi e widget

from database import RUOLI, RUOLI_LOOK  # etichette e ruoli del look
from logica import valida_selezione  # controlla che i ruoli obbligatori siano presenti
from ui.stile import COLORI  # colori dell'interfaccia
from ui.widgets import AnteprimaLook  # anteprima con le foto affiancate


class LookTab(ttk.Frame):
    """Scheda per comporre, salvare e ricaricare i look."""

    def __init__(self, master, app):
        super().__init__(master, padding=(16, 12))  # scheda con un piccolo margine
        self.app = app  # finestra principale, serve per aggiornare le altre schede
        self.db = app.db  # archivio condiviso
        self._capi = []  # tutti i capi letti dal database
        self._per_id = {}  # id del capo -> riga completa, usato per l'anteprima
        # SINTASSI — dict comprehension annidata
        # `{r: {} for r in RUOLI_LOOK}` crea un dizionario che associa a ogni
        # ruolo un altro dizionario vuoto. Il tipo `dict[str, dict[str, int |
        # None]]` descrive questa struttura: ruolo -> (testo -> id o None).
        self._mappe: dict[str, dict[str, int | None]] = {r: {} for r in RUOLI_LOOK}  # testo del menu -> id del capo
        self._combo: dict[str, ttk.Combobox] = {}  # menu a tendina per ogni ruolo
        self._look = []  # look salvati mostrati nell'elenco
        self.var_nome = tk.StringVar()  # nome del look da salvare
        # SINTASSI — dict comprehension con valori creati al volo
        # Per ogni ruolo crea una StringVar separata, con il testo iniziale
        # «— nessuno —». Ogni menu avrà la sua variabile indipendente.
        self._vars = {ruolo: tk.StringVar(value="— nessuno —")
                      for ruolo in RUOLI_LOOK}  # valore scelto in ogni menu
        self._costruisci()  # crea i widget della scheda
        self.ricarica()  # carica capi e look salvati

    def _costruisci(self) -> None:
        """Crea i widget della scheda Look."""
        testata = ttk.Frame(self)  # contenitore del titolo
        testata.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(testata, text="I tuoi look", style="Titolo.TLabel"
                  ).pack(anchor="w")  # titolo della scheda
        ttk.Label(
            testata,
            text="Scegli un capo per ogni ruolo, guarda l'anteprima e salva il look.",
            style="Sottotitolo.TLabel",
        ).pack(anchor="w")  # istruzioni brevi

        self.columnconfigure(0, weight=0)  # la colonna sinistra ha larghezza fissa
        self.columnconfigure(1, weight=1)  # la destra si allarga
        self.rowconfigure(1, weight=1)

        card = tk.Frame(self, bg=COLORI["superficie"],
                        highlightbackground=COLORI["bordo"],
                        highlightthickness=1)  # card con i menu di scelta
        card.grid(row=1, column=0, sticky="ns", padx=(0, 12))
        dentro = ttk.Frame(card, style="Card.TFrame", padding=18)  # contenuto della card
        dentro.pack(fill="both", expand=True)

        ttk.Label(dentro, text="Componi un look", style="CardTitolo.TLabel"
                  ).pack(anchor="w", pady=(0, 10))  # titolo della card
        for ruolo in RUOLI_LOOK:  # crea un menu per ogni ruolo del look
            ttk.Label(dentro, text=RUOLI[ruolo], style="Card.TLabel"
                      ).pack(anchor="w", pady=(5, 2))  # etichetta del ruolo
            # SINTASSI — `textvariable`
            # Collega il menu alla StringVar: quando l'utente sceglie una voce,
            # la variabile si aggiorna automaticamente; se noi cambiamo la
            # variabile con `.set()`, il menu mostra la nuova scelta.
            combo = ttk.Combobox(dentro, textvariable=self._vars[ruolo],
                                 state="readonly", width=34)  # menu dei capi disponibili
            combo.pack(fill="x")
            combo.bind("<<ComboboxSelected>>", self._cambia)  # aggiorna l'anteprima alla scelta
            self._combo[ruolo] = combo  # memorizza il menu

        ttk.Label(dentro, text="Nome del look", style="Card.TLabel"
                  ).pack(anchor="w", pady=(14, 2))  # etichetta del nome
        ttk.Entry(dentro, textvariable=self.var_nome, width=34
                  ).pack(fill="x")  # campo per il nome del look
        ttk.Label(
            dentro,
            text="Obbligatori: parte superiore, parte inferiore e scarpe.\n"
                 "Borsa e accessorio sono facoltativi.",
            style="CardTenue.TLabel", justify="left",
        ).pack(anchor="w", pady=(8, 12))  # regole per salvare il look
        ttk.Button(dentro, text="Salva look", style="Accent.TButton",
                   command=self._salva).pack(fill="x", pady=(0, 4))  # salva il look
        ttk.Button(dentro, text="Pulisci", style="Secondario.TButton",
                   command=self._pulisci).pack(fill="x")  # svuota il form

        destra = ttk.Frame(self)  # parte destra con anteprima ed elenco
        destra.grid(row=1, column=1, sticky="nsew")
        destra.columnconfigure(0, weight=1)
        destra.rowconfigure(1, weight=1)

        anteprima = ttk.LabelFrame(destra, text="Anteprima", padding=8)  # riquadro dell'anteprima
        anteprima.grid(row=0, column=0, sticky="ew")
        self.anteprima = AnteprimaLook(anteprima, self.db)  # cinque riquadri affiancati
        self.anteprima.pack(anchor="center")

        salvati = ttk.LabelFrame(destra, text="Look salvati", padding=8)  # riquadro dei look salvati
        salvati.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        salvati.columnconfigure(0, weight=1)
        salvati.rowconfigure(0, weight=1)

        contenitore = ttk.Frame(salvati)  # contiene elenco e barra di scorrimento
        contenitore.grid(row=0, column=0, sticky="nsew")
        self.lista = tk.Listbox(
            contenitore, exportselection=False, activestyle="none",
            font=("Segoe UI", 10), bg="white", fg=COLORI["testo"],
            selectbackground=COLORI["primario"], selectforeground="white",
            highlightthickness=1, highlightbackground=COLORI["bordo"],
            relief="flat", bd=0, height=8,
        )  # elenco dei look salvati
        self.lista.pack(side="left", fill="both", expand=True)
        barra = ttk.Scrollbar(contenitore, orient="vertical",
                              command=self.lista.yview)  # barra di scorrimento
        barra.pack(side="right", fill="y")
        self.lista.configure(yscrollcommand=barra.set)  # collega elenco e barra
        # SINTASSI — `<Double-Button-1>`
        # Evento «doppio clic con il tasto sinistro». Il numero 1 indica il
        # pulsante sinistro del mouse; 2 sarebbe il centrale, 3 il destro.
        self.lista.bind("<Double-Button-1>", lambda _e: self._carica_look_scelto())  # doppio clic carica il look

        pulsanti = ttk.Frame(salvati)  # barra dei pulsanti dei look
        pulsanti.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(pulsanti, text="Carica nel form", style="Secondario.TButton",
                   command=self._carica_look_scelto).pack(side="left")  # riporta il look nel form
        ttk.Button(pulsanti, text="Elimina look", style="Pericolo.TButton",
                   command=self._elimina_look).pack(side="left", padx=(8, 0))  # elimina il look scelto

    # ------------------------------------------------------------------ dati
    def ricarica(self) -> None:
        """Rilegge i capi e i look salvati e aggiorna la scheda."""
        precedente = {ruolo: self._id_scelto(ruolo) for ruolo in RUOLI_LOOK}  # ricorda i capi già scelti
        self._capi = self.db.capi()  # rilegge tutti i capi
        self._per_id = {riga["id"]: riga for riga in self._capi}  # indice per id
        for ruolo in RUOLI_LOOK:  # ricostruisce il menu di ogni ruolo
            voci = ["— nessuno —"]  # voce per lasciare il ruolo vuoto
            mappa: dict[str, int | None] = {"— nessuno —": None}  # testo -> id
            for capo in self._capi:  # considera solo i capi del ruolo giusto
                if capo["ruolo"] != ruolo:
                    continue
                testo = f"{capo['nome']} ({capo['sezione']})"  # testo mostrato nel menu
                if testo in mappa:  # due capi con lo stesso nome e sezione
                    testo += f" · #{capo['id']}"  # distingue aggiungendo l'id
                voci.append(testo)
                mappa[testo] = capo["id"]
            self._mappe[ruolo] = mappa  # salva la corrispondenza
            self._combo[ruolo].configure(values=voci)  # aggiorna il menu
        for ruolo, capo_id in precedente.items():  # prova a mantenere le scelte precedenti
            self._imposta_id(ruolo, capo_id)
        self._aggiorna_anteprima()  # aggiorna le foto
        self._carica_lista()  # aggiorna l'elenco dei look salvati

    def _id_scelto(self, ruolo: str) -> int | None:
        """Restituisce l'id del capo scelto per un ruolo, oppure None."""
        # SINTASSI — `dict.get(chiave)`
        # Restituisce il valore associato alla chiave oppure None se la chiave
        # non esiste. Evita il KeyError che si avrebbe con `dizionario[chiave]`.
        return self._mappe[ruolo].get(self._vars[ruolo].get())  # id del capo scelto nel menu

    def _imposta_id(self, ruolo: str, capo_id: int | None) -> None:
        """Seleziona nel menu il testo corrispondente a un id."""
        for testo, identificativo in self._mappe[ruolo].items():  # cerca il testo corrispondente all'id
            if identificativo == capo_id:
                self._vars[ruolo].set(testo)  # seleziona il capo
                return
        self._vars[ruolo].set("— nessuno —")  # il capo non c'è più: svuota il ruolo

    def _selezione(self) -> dict[str, int]:
        """Restituisce solo i ruoli per cui è stato scelto un capo."""
        # LOGICA — costruiamo un dizionario «pulito»: dentro mettiamo solo i
        # ruoli che hanno davvero un capo. Così borsa e accessorio possono
        # restare fuori senza creare problemi al database.
        selezione = {}  # solo i ruoli con un capo scelto
        for ruolo in RUOLI_LOOK:
            capo_id = self._id_scelto(ruolo)  # id del capo nel menu
            if capo_id is not None:  # salta i ruoli vuoti
                selezione[ruolo] = capo_id
        return selezione  # restituisce la selezione pronta per il database

    def _righe_anteprima(self) -> dict:
        """Restituisce le righe complete dei capi scelti per l'anteprima."""
        return {ruolo: self._per_id.get(capo_id)
                for ruolo, capo_id in self._selezione().items()}  # righe complete dei capi scelti

    def _cambia(self, _event=None) -> None:
        """Aggiorna l'anteprima quando cambia un menu."""
        self._aggiorna_anteprima()  # mostra subito la nuova scelta

    def _aggiorna_anteprima(self) -> None:
        """Passa all'anteprima le foto dei capi scelti."""
        self.anteprima.mostra(self._righe_anteprima())  # passa le foto all'anteprima

    def _pulisci(self) -> None:
        """Svuota tutti i menu e il nome del look."""
        for ruolo in RUOLI_LOOK:  # svuota tutti i menu
            self._vars[ruolo].set("— nessuno —")
        self.var_nome.set("")  # svuota il nome del look
        self.lista.selection_clear(0, "end")  # toglie la selezione dall'elenco
        self._aggiorna_anteprima()  # riporta l'anteprima ai segnaposto

    # ------------------------------------------------------------------ look
    def _salva(self) -> None:
        """Controlla e salva il look composto nel form."""
        try:
            selezione = self._selezione()  # capi scelti
            valida_selezione(selezione)  # controlla i ruoli obbligatori
            self.db.salva_look(self.var_nome.get(), selezione)  # salva il look nel database
        except ValueError as exc:  # look incompleto o senza nome
            messagebox.showerror("Look incompleto", str(exc),
                                 parent=self.winfo_toplevel())  # spiega l'errore
            return
        nome = self.var_nome.get().strip()  # nome del look appena salvato
        self.app.dati_cambiati()  # aggiorna le altre schede
        self._pulisci()  # svuota il form
        self.app.messaggio(f"Look «{nome}» salvato.")  # conferma all'utente

    def _carica_lista(self) -> None:
        """Aggiorna l'elenco dei look salvati."""
        self._look = self.db.look_salvati()  # rilegge i look salvati
        self.lista.delete(0, "end")  # svuota l'elenco
        for riga in self._look:  # mostra nome e numero di capi
            self.lista.insert(
                "end", f"{riga['nome']}  —  {riga['n_capi']} capi"
            )

    def _look_scelto(self):
        """Restituisce il look selezionato oppure None."""
        selezione = self.lista.curselection()  # look selezionato nell'elenco
        if not selezione:  # nessuna selezione
            messagebox.showinfo("Nessun look",
                                "Seleziona prima un look dall'elenco.",
                                parent=self.winfo_toplevel())  # avvisa l'utente
            return None
        return self._look[selezione[0]]  # restituisce la riga del look

    def _carica_look_scelto(self) -> None:
        """Riporta nel form i capi del look selezionato."""
        riga = self._look_scelto()  # look da caricare
        if riga is None:
            return
        for ruolo in RUOLI_LOOK:  # svuota prima tutti i menu
            self._vars[ruolo].set("— nessuno —")
        for capo in self.db.capi_look(riga["id"]):  # inserisce i capi del look
            # SINTASSI — `in` su una tupla
            # `capo["ruolo"] in RUOLI_LOOK` è True se il ruolo è uno dei valori
            # presenti nella tupla RUOLI_LOOK.
            if capo["ruolo"] in RUOLI_LOOK:  # considera solo i ruoli mostrati nel form
                self._imposta_id(capo["ruolo"], capo["id"])
        self.var_nome.set(riga["nome"])  # riporta il nome del look
        self._aggiorna_anteprima()  # aggiorna le foto
        self.app.messaggio(f"Look «{riga['nome']}» caricato nel form.")  # conferma all'utente

    def _elimina_look(self) -> None:
        """Elimina il look selezionato dopo la conferma."""
        riga = self._look_scelto()  # look da eliminare
        if riga is None:
            return
        if not messagebox.askyesno(
            "Eliminare il look?",
            f"Vuoi eliminare il look «{riga['nome']}»?",
            parent=self.winfo_toplevel(),
        ):  # chiede conferma prima di eliminare
            return
        self.db.elimina_look(riga["id"])  # elimina il look
        self.app.dati_cambiati()  # aggiorna le altre schede
        self.app.messaggio("Look eliminato.")  # conferma all'utente
