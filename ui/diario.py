"""Scheda Diario: cosa ho indossato e capi più/mai usati."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from datetime import date  # serve per la data di oggi
from tkinter import messagebox, ttk  # messaggi e widget

from ui.stile import COLORI  # colori dell'interfaccia


class DiarioTab(ttk.Frame):
    """Scheda per segnare i capi indossati e vedere le statistiche."""

    def __init__(self, master, app):
        super().__init__(master, padding=(16, 12))  # scheda con un piccolo margine
        self.app = app  # finestra principale, serve per aggiornare le altre schede
        self.db = app.db  # archivio condiviso
        self._capi = []  # capi disponibili per il diario
        self._mappa_capi: dict[str, int] = {}  # testo del menu -> id del capo
        self._voci = []  # voci del giorno mostrate nell'elenco
        # SINTASSI — `date.today().isoformat()`
        # `today()` restituisce la data di oggi; `isoformat()` la scrive come
        # "AAAA-MM-GG", il formato che usa anche SQLite.
        self.var_data = tk.StringVar(value=date.today().isoformat())  # data di oggi
        self.var_capo = tk.StringVar(value="— scegli un capo —")  # capo scelto
        self._costruisci()  # crea i widget della scheda
        self.ricarica()  # carica capi, giorno corrente e statistiche

    def _costruisci(self) -> None:
        """Crea i widget della scheda Diario."""
        testata = ttk.Frame(self)  # contenitore del titolo
        testata.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(testata, text="Diario dell'indossato", style="Titolo.TLabel"
                  ).pack(anchor="w")  # titolo della scheda
        ttk.Label(
            testata,
            text="Segna cosa hai indossato ogni giorno e scopri i capi più usati e quelli mai usati.",
            style="Sottotitolo.TLabel",
        ).pack(anchor="w")  # istruzioni brevi

        self.columnconfigure(1, weight=1)  # la parte destra si allarga
        self.rowconfigure(1, weight=1)

        card = tk.Frame(self, bg=COLORI["superficie"],
                        highlightbackground=COLORI["bordo"],
                        highlightthickness=1)  # card con i comandi del diario
        card.grid(row=1, column=0, sticky="ns", padx=(0, 12))
        dentro = ttk.Frame(card, style="Card.TFrame", padding=18)  # contenuto della card
        dentro.pack(fill="both", expand=True)
        ttk.Label(dentro, text="Segna cosa indossi", style="CardTitolo.TLabel"
                  ).pack(anchor="w", pady=(0, 10))  # titolo della card

        ttk.Label(dentro, text="Data (AAAA-MM-GG)", style="Card.TLabel"
                  ).pack(anchor="w", pady=(4, 2))  # etichetta della data
        riga_data = ttk.Frame(dentro, style="Card.TFrame")  # riga con data e pulsanti
        riga_data.pack(fill="x")
        entry_data = ttk.Entry(riga_data, textvariable=self.var_data, width=13)  # campo della data
        entry_data.pack(side="left")
        entry_data.bind("<Return>", lambda _e: self._mostra_giorno(avvisa=True))  # Invio mostra il giorno
        ttk.Button(riga_data, text="Oggi", style="Secondario.TButton",
                   command=self._oggi).pack(side="left", padx=(6, 0))  # imposta la data di oggi
        ttk.Button(riga_data, text="Mostra", style="Secondario.TButton",
                   command=lambda: self._mostra_giorno(avvisa=True)
                   ).pack(side="left", padx=(6, 0))  # mostra i capi della data scritta

        ttk.Label(dentro, text="Capo indossato", style="Card.TLabel"
                  ).pack(anchor="w", pady=(14, 2))  # etichetta del capo
        self.combo_capo = ttk.Combobox(
            dentro, textvariable=self.var_capo, state="readonly", width=32
        )  # menu dei capi disponibili
        self.combo_capo.pack(fill="x")
        ttk.Button(dentro, text="Segna come indossato", style="Accent.TButton",
                   command=self._aggiungi).pack(fill="x", pady=(10, 18))  # registra il capo nel diario

        self.frame_giorno = ttk.LabelFrame(dentro, text="Capi del giorno",
                                           padding=8)  # riquadro dei capi del giorno
        self.frame_giorno.pack(fill="both", expand=True)
        contenitore = ttk.Frame(self.frame_giorno)  # contiene elenco e barra
        contenitore.pack(fill="both", expand=True)
        self.lista_giorno = tk.Listbox(
            contenitore, exportselection=False, activestyle="none",
            font=("Segoe UI", 10), bg="white", fg=COLORI["testo"],
            selectbackground=COLORI["primario"], selectforeground="white",
            highlightthickness=1, highlightbackground=COLORI["bordo"],
            relief="flat", bd=0, height=8,
        )  # elenco dei capi indossati nella data scelta
        self.lista_giorno.pack(side="left", fill="both", expand=True)
        barra = ttk.Scrollbar(contenitore, orient="vertical",
                              command=self.lista_giorno.yview)  # barra di scorrimento
        barra.pack(side="right", fill="y")
        self.lista_giorno.configure(yscrollcommand=barra.set)  # collega elenco e barra
        ttk.Button(self.frame_giorno, text="Rimuovi selezionato",
                   style="Secondario.TButton", command=self._rimuovi
                   ).pack(fill="x", pady=(8, 0))  # elimina la voce scelta

        destra = ttk.Frame(self)  # parte destra con le statistiche
        destra.grid(row=1, column=1, sticky="nsew")
        destra.columnconfigure(0, weight=1)
        destra.rowconfigure(0, weight=3)  # la tabella dei più usati è più alta
        destra.rowconfigure(1, weight=2)

        self.frame_piu = ttk.LabelFrame(destra, text="Capi più indossati",
                                        padding=8)  # riquadro dei capi più usati
        self.frame_piu.grid(row=0, column=0, sticky="nsew")
        # SINTASSI — `ttk.Treeview`
        # `columns` elenca le colonne; `show="headings"` nasconde la colonna
        # ad albero e mostra solo le intestazioni. È il modo più semplice per
        # creare una tabella in Tkinter.
        self.tabella = ttk.Treeview(
            self.frame_piu, columns=("capo", "volte"), show="headings", height=9
        )  # tabella con capo e numero di utilizzi
        self.tabella.heading("capo", text="Capo")  # intestazione della colonna capo
        self.tabella.heading("volte", text="Volte")  # intestazione della colonna utilizzi
        self.tabella.column("capo", width=360, anchor="w")  # colonna larga per il nome
        self.tabella.column("volte", width=70, anchor="center", stretch=False)  # colonna stretta per il numero
        self.tabella.pack(fill="both", expand=True)

        self.frame_mai = ttk.LabelFrame(destra, text="Capi mai indossati",
                                        padding=8)  # riquadro dei capi mai usati
        self.frame_mai.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        contenitore_mai = ttk.Frame(self.frame_mai)  # contiene elenco e barra
        contenitore_mai.pack(fill="both", expand=True)
        self.lista_mai = tk.Listbox(
            contenitore_mai, activestyle="none", font=("Segoe UI", 10),
            bg="white", fg=COLORI["testo"], highlightthickness=1,
            highlightbackground=COLORI["bordo"], relief="flat", bd=0,
            height=6,
        )  # elenco dei capi mai indossati
        self.lista_mai.pack(side="left", fill="both", expand=True)
        barra_mai = ttk.Scrollbar(contenitore_mai, orient="vertical",
                                  command=self.lista_mai.yview)  # barra di scorrimento
        barra_mai.pack(side="right", fill="y")
        self.lista_mai.configure(yscrollcommand=barra_mai.set)  # collega elenco e barra

    # ------------------------------------------------------------------ dati
    def ricarica(self) -> None:
        """Rilegge capi, giorno corrente e statistiche."""
        precedente = self._mappa_capi.get(self.var_capo.get())  # ricorda il capo scelto
        self._capi = self.db.capi()  # rilegge tutti i capi
        self._mappa_capi = {}  # ricostruisce la mappa testo -> id
        voci = []  # voci del menu dei capi
        for capo in self._capi:  # crea una voce per ogni capo
            testo = f"{capo['nome']} ({capo['sezione']})"  # testo mostrato nel menu
            if testo in self._mappa_capi:  # due capi con lo stesso nome e sezione
                testo += f" · #{capo['id']}"  # distingue aggiungendo l'id
            voci.append(testo)
            self._mappa_capi[testo] = capo["id"]
        self.combo_capo.configure(values=["— scegli un capo —"] + voci)  # aggiorna il menu
        scelta = "— scegli un capo —"  # valore predefinito
        for testo, capo_id in self._mappa_capi.items():  # cerca di mantenere il capo scelto prima
            if capo_id == precedente:
                scelta = testo
                break
        self.var_capo.set(scelta)  # ripristina la scelta
        self._mostra_giorno()  # mostra i capi della data corrente
        self._aggiorna_statistiche()  # aggiorna i più usati e i mai usati

    def _data_valida(self, avvisa: bool) -> str | None:
        """Controlla la data scritta e, se richiesto, mostra un avviso."""
        testo = self.var_data.get().strip()  # legge la data scritta
        try:
            # SINTASSI — `date.fromisoformat`
            # Converte una stringa "AAAA-MM-GG" in un oggetto data. Se il
            # formato è sbagliato solleva `ValueError`, che intercettiamo
            # subito sotto.
            date.fromisoformat(testo)  # controlla il formato AAAA-MM-GG
        except ValueError:  # data non valida
            if avvisa:  # mostra l'errore solo se richiesto
                messagebox.showerror(
                    "Data non valida",
                    "Scrivi la data nel formato AAAA-MM-GG, per esempio 2026-10-28.",
                    parent=self.winfo_toplevel(),
                )  # spiega il formato corretto
            return None
        return testo  # restituisce la data valida

    def _oggi(self) -> None:
        """Imposta la data di oggi e mostra i capi indossati."""
        self.var_data.set(date.today().isoformat())  # imposta la data di oggi
        self._mostra_giorno()  # mostra i capi indossati oggi

    def _mostra_giorno(self, avvisa: bool = False) -> None:
        """Mostra i capi indossati nella data scelta."""
        data_iso = self._data_valida(avvisa)  # controlla la data
        self.lista_giorno.delete(0, "end")  # svuota l'elenco
        self._voci = []  # nessuna voce caricata
        if not data_iso:  # data non valida
            self.frame_giorno.configure(text="Capi del giorno")  # ripristina il titolo
            return
        self._voci = self.db.voci_diario(data_iso)  # legge i capi indossati nella data
        for voce in self._voci:  # inserisce una riga per ogni capo
            self.lista_giorno.insert("end", f"{voce['nome']} — {voce['sezione']}")
        self.frame_giorno.configure(
            text=f"Capi del giorno · {data_iso} ({len(self._voci)})"
        )  # aggiorna il titolo con data e conteggio

    def _capo_scelto(self) -> int | None:
        """Restituisce l'id del capo scelto nel menu, oppure None."""
        if self.var_capo.get() == "— scegli un capo —":  # nessun capo scelto
            return None
        return self._mappa_capi.get(self.var_capo.get())  # id del capo scelto

    def _aggiungi(self) -> None:
        """Segna il capo scelto come indossato nella data indicata."""
        data_iso = self._data_valida(avvisa=True)  # controlla la data
        if not data_iso:
            return
        capo_id = self._capo_scelto()  # capo da segnare
        if capo_id is None:  # nessun capo scelto
            messagebox.showinfo("Nessun capo scelto",
                                "Scegli il capo che hai indossato.",
                                parent=self.winfo_toplevel())  # avvisa l'utente
            return
        try:
            self.db.aggiungi_voce_diario(data_iso, capo_id)  # salva la voce nel diario
        except ValueError as exc:  # capo già segnato o non più esistente
            messagebox.showwarning("Non aggiunto", str(exc),
                                   parent=self.winfo_toplevel())  # spiega il motivo
            return
        self._mostra_giorno()  # aggiorna l'elenco del giorno
        self._aggiorna_statistiche()  # aggiorna i più usati e i mai usati
        self.app.aggiorna_stato()  # aggiorna la barra di stato
        self.app.messaggio("Capo segnato nel diario.")  # conferma all'utente

    def _rimuovi(self) -> None:
        """Rimuove dal diario la voce selezionata."""
        # SINTASSI — `curselection()`
        # Restituisce una tupla con gli indici selezionati. Se l'utente non
        # ha cliccato nulla, la tupla è vuota e `not selezione` è True.
        selezione = self.lista_giorno.curselection()  # voce selezionata
        if not selezione:  # nessuna selezione
            messagebox.showinfo("Nessuna voce",
                                "Seleziona la voce da rimuovere.",
                                parent=self.winfo_toplevel())  # avvisa l'utente
            return
        voce = self._voci[selezione[0]]  # voce corrispondente
        self.db.elimina_voce_diario(voce["id"])  # elimina la voce dal diario
        self._mostra_giorno()  # aggiorna l'elenco
        self._aggiorna_statistiche()  # aggiorna le statistiche
        self.app.aggiorna_stato()  # aggiorna la barra di stato

    def _aggiorna_statistiche(self) -> None:
        """Aggiorna le tabelle dei capi più usati e mai usati."""
        piu_usati = self.db.capi_piu_usati(10)  # primi dieci capi più indossati
        self.tabella.delete(*self.tabella.get_children())  # svuota la tabella
        for riga in piu_usati:  # inserisce una riga per ogni capo
            self.tabella.insert(
                "", "end",
                values=(f"{riga['nome']} ({riga['sezione']})", riga["volte"]),
            )
        self.frame_piu.configure(
            text=f"Capi più indossati ({len(piu_usati)})")  # aggiorna il titolo con il conteggio

        mai_usati = self.db.capi_mai_usati()  # capi senza nessuna voce nel diario
        self.lista_mai.delete(0, "end")  # svuota l'elenco
        for riga in mai_usati:  # inserisce una riga per ogni capo mai usato
            self.lista_mai.insert("end", f"{riga['nome']} — {riga['sezione']}")
        if not mai_usati:  # nessun capo mai usato
            self.lista_mai.insert("end", "Nessun capo: li hai indossati tutti.")
        self.frame_mai.configure(
            text=f"Capi mai indossati ({len(mai_usati)})"
        )  # aggiorna il titolo con il conteggio
