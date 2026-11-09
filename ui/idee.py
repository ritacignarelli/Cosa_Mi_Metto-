"""Scheda Idee: proposta automatica di un look con «Sorprendimi»."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from tkinter import messagebox, simpledialog, ttk  # messaggi, richiesta del nome e widget

from database import OCCASIONI, STAGIONI_FILTRO  # stagioni e occasioni disponibili
from logica import suggerisci_look, valida_selezione  # algoritmo della proposta e controllo del look
from ui.stile import COLORI  # colori dell'interfaccia
from ui.widgets import AnteprimaLook  # anteprima con le foto affiancate


class IdeeTab(ttk.Frame):
    """Scheda che propone un look automatico con il pulsante «Sorprendimi»."""

    def __init__(self, master, app):
        super().__init__(master, padding=(16, 12))  # scheda con un piccolo margine
        self.app = app  # finestra principale, serve per aggiornare le altre schede
        self.db = app.db  # archivio condiviso
        # SINTASSI — `dict | None`
        # Il tipo «unione» si legge: «un dizionario oppure None». All'inizio
        # None significa «nessuna proposta ancora generata».
        self._suggerimento: dict | None = None  # ultima proposta mostrata
        # SINTASSI — `StringVar(value=...)`
        # Crea la variabile già con un valore iniziale: la stagione parte da
        # "Estate". `OCCASIONI[0]` prende il primo elemento della tupla.
        self.var_stagione = tk.StringVar(value="Estate")  # stagione scelta per la proposta
        self.var_occasione = tk.StringVar(value=OCCASIONI[0])  # occasione scelta per la proposta
        self._costruisci()  # crea i widget della scheda

    def _costruisci(self) -> None:
        """Crea i widget della scheda Idee."""
        testata = ttk.Frame(self)  # contenitore del titolo
        testata.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(testata, text="Idee per te", style="Titolo.TLabel"
                  ).pack(anchor="w")  # titolo della scheda
        ttk.Label(
            testata,
            text="Scegli stagione e occasione, poi lascia che l'app proponga un abbinamento.",
            style="Sottotitolo.TLabel",
        ).pack(anchor="w")  # istruzioni brevi

        self.columnconfigure(1, weight=1)  # la parte destra si allarga
        self.rowconfigure(1, weight=1)

        card = tk.Frame(self, bg=COLORI["superficie"],
                        highlightbackground=COLORI["bordo"],
                        highlightthickness=1)  # card con i menu di scelta
        card.grid(row=1, column=0, sticky="ns", padx=(0, 12))
        dentro = ttk.Frame(card, style="Card.TFrame", padding=18)  # contenuto della card
        dentro.pack(fill="both", expand=True)
        ttk.Label(dentro, text="Cosa ti serve?", style="CardTitolo.TLabel"
                  ).pack(anchor="w", pady=(0, 10))  # titolo della card

        ttk.Label(dentro, text="Stagione", style="Card.TLabel"
                  ).pack(anchor="w", pady=(5, 2))  # etichetta della stagione
        ttk.Combobox(dentro, textvariable=self.var_stagione, state="readonly",
                     values=list(STAGIONI_FILTRO), width=24).pack(fill="x")  # menu delle stagioni
        ttk.Label(dentro, text="Occasione", style="Card.TLabel"
                  ).pack(anchor="w", pady=(12, 2))  # etichetta dell'occasione
        ttk.Combobox(dentro, textvariable=self.var_occasione, state="readonly",
                     values=list(OCCASIONI), width=24).pack(fill="x")  # menu delle occasioni

        # SINTASSI — `command=self._sorprendimi`
        # Non stiamo chiamando la funzione: stiamo passando il suo nome. Tkinter
        # la chiamerà quando l'utente preme il pulsante. Se scrivessimo
        # `self._sorprendimi()`, la funzione partirebbe subito, alla creazione
        # della schermata.
        ttk.Button(dentro, text="Sorprendimi", style="Accent.TButton",
                   command=self._sorprendimi).pack(fill="x", pady=(22, 8))  # genera la proposta
        ttk.Label(
            dentro,
            text="L'app sceglie parte superiore, parte inferiore e scarpe.\n"
                 "Se ci sono, aggiunge anche borsa e accessorio.",
            style="CardTenue.TLabel", justify="left",
        ).pack(anchor="w")  # spiega come viene composta la proposta

        destra = ttk.LabelFrame(self, text="Proposta", padding=10)  # riquadro della proposta
        destra.grid(row=1, column=1, sticky="nsew")
        destra.columnconfigure(0, weight=1)
        destra.rowconfigure(0, weight=1)

        self.anteprima = AnteprimaLook(destra, self.db)  # cinque riquadri affiancati
        self.anteprima.grid(row=0, column=0, sticky="n", pady=(10, 6))

        self.lbl_esito = ttk.Label(
            destra,
            text="Premi «Sorprendimi» per ricevere una proposta.",
            style="Tenue.TLabel", wraplength=780, justify="center",
        )  # messaggio con l'esito della proposta
        self.lbl_esito.grid(row=1, column=0, pady=(0, 10))

        self.btn_salva = ttk.Button(destra, text="Salva come look",
                                    style="Accent.TButton",
                                    command=self._salva, state="disabled")  # salvataggio della proposta
        self.btn_salva.grid(row=2, column=0, pady=(0, 10))
        self.anteprima.mostra({})  # all'inizio mostra solo i segnaposto

    def ricarica(self) -> None:
        """Aggiorna la proposta se i capi sono cambiati nel frattempo."""
        if not self._suggerimento:  # nessuna proposta da aggiornare
            return
        aggiornati = {}  # proposta riletta dal database
        for ruolo, capo in self._suggerimento.items():  # controlla ogni capo della proposta
            fresco = self.db.capo(capo["id"])  # rilegge il capo aggiornato
            if fresco is None:  # se un capo è stato eliminato
                self._azzera()  # cancella la proposta
                return
            aggiornati[ruolo] = fresco
        self._suggerimento = aggiornati  # usa i dati aggiornati
        self.anteprima.mostra(aggiornati)  # aggiorna le foto

    def _sorprendimi(self) -> None:
        """Chiede una nuova proposta e la mostra nell'anteprima."""
        escludi = set()  # capi da evitare nella nuova proposta
        if self._suggerimento:  # se c'era già una proposta
            # SINTASSI — set comprehension
            # `{espressione for elemento in ...}` crea un insieme. Qui raccoglie
            # gli id dei capi già proposti, così il pulsante «Sorprendimi»
            # mostra qualcosa di diverso al secondo clic.
            escludi = {capo["id"] for capo in self._suggerimento.values()}  # evita di riproporre gli stessi capi
        try:
            scelti, avviso = suggerisci_look(
                self.db, self.var_stagione.get(), self.var_occasione.get(),
                escludi=escludi,
            )  # chiede una nuova proposta
        except ValueError as exc:  # non ci sono abbastanza capi
            messagebox.showwarning("Non ci sono abbastanza capi", str(exc),
                                   parent=self.winfo_toplevel())  # spiega cosa manca
            return
        self._suggerimento = scelti  # memorizza la proposta
        self.anteprima.mostra(scelti)  # mostra le foto
        # SINTASSI — `configure(state="normal")`
        # Un pulsante ttk può essere "normal", "disabled" o "active". Qui lo
        # riattiviamo dopo aver trovato una proposta valida.
        self.btn_salva.configure(state="normal")  # abilita il salvataggio
        # SINTASSI — `avviso or (...)`
        # Se `avviso` è una stringa vuota (falsa), usa il testo tra parentesi.
        # Se contiene un messaggio di ripiego, mostra quello.
        testo = avviso or (
            f"Proposta per {self.var_stagione.get().lower()} · "
            f"{self.var_occasione.get().lower()}. "
            "Non ti piace? Premi di nuovo «Sorprendimi»."
        )  # messaggio normale oppure avviso di ripiego
        self.lbl_esito.configure(text=testo)  # mostra il messaggio

    def _salva(self) -> None:
        """Salva la proposta corrente come look."""
        if not self._suggerimento:  # nessuna proposta da salvare
            return
        # SINTASSI — `askstring`
        # Restituisce il testo scritto oppure None se l'utente annulla.
        nome = simpledialog.askstring("Salva look", "Nome del look:",
                                      parent=self.winfo_toplevel())  # chiede il nome del look
        if nome is None:  # l'utente ha annullato
            return
        selezione = {ruolo: capo["id"]
                     for ruolo, capo in self._suggerimento.items()}  # id dei capi proposti
        try:
            valida_selezione(selezione)  # controlla i ruoli obbligatori
            self.db.salva_look(nome, selezione)  # salva il look
        except ValueError as exc:  # nome vuoto, look incompleto o capo eliminato
            messagebox.showerror("Look non salvato", str(exc),
                                 parent=self.winfo_toplevel())  # spiega l'errore
            return
        self.app.dati_cambiati()  # aggiorna le altre schede
        self.app.messaggio(f"Look «{nome.strip()}» salvato.")  # conferma all'utente

    def _azzera(self) -> None:
        """Cancella la proposta e disabilita il salvataggio."""
        self._suggerimento = None  # cancella la proposta
        self.anteprima.mostra({})  # torna ai segnaposto
        # SINTASSI — `state="disabled"`
        # Disattiva il pulsante: diventa grigio e non può essere cliccato.
        self.btn_salva.configure(state="disabled")  # disabilita il salvataggio
        self.lbl_esito.configure(
            text="Premi «Sorprendimi» per ricevere una proposta.")  # ripristina il messaggio iniziale
