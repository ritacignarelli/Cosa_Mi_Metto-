"""Finestra principale di «Cosa Mi Metto?» con schede e barra di stato."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from tkinter import ttk  # widget con stile moderno

from database import Database  # archivio SQLite dell'applicazione
from ui.aggiungi_capo import AggiungiCapoTab  # scheda per aggiungere un capo
from ui.armadio import ArmadioTab  # scheda con l'armadio
from ui.diario import DiarioTab  # scheda con il diario
from ui.idee import IdeeTab  # scheda con i suggerimenti
from ui.look import LookTab  # scheda per comporre i look
from ui.stile import COLORI, applica_stile  # colori e tema dell'interfaccia


# SINTASSI — ereditarietà da `tk.Tk`
# `App` è la finestra principale dell'applicazione: eredita tutto da `tk.Tk`
# e aggiunge schede, barra di stato e gestione dei dati.
class App(tk.Tk):
    """Finestra principale dell'applicazione, con schede e barra di stato."""

    def __init__(self, db: Database | None = None):
        # `super().__init__()` chiama il costruttore di tk.Tk, che crea davvero
        # la finestra. Senza questa riga non esisterebbe nessuna finestra.
        super().__init__()  # crea la finestra Tkinter
        self.db = db or Database()  # usa l'archivio ricevuto oppure ne apre uno nuovo
        self._job_messaggio = None  # riferimento al timer che svuota il messaggio
        self.title("Cosa Mi Metto? — Armadio digitale")  # titolo della finestra
        self.minsize(1024, 680)  # dimensione minima per non schiacciare i contenuti
        applica_stile(self)  # applica colori e stili comuni
        self._centra()  # posiziona la finestra al centro dello schermo
        # SINTASSI — `protocol("WM_DELETE_WINDOW", ...)`
        # Il gestore della finestra (Windows/Linux) manda questo messaggio
        # quando l'utente clicca la X. Così, invece di chiudere subito,
        # chiamiamo `_chiudi`, che chiude prima il database.
        self.protocol("WM_DELETE_WINDOW", self._chiudi)  # intercetta la chiusura della finestra

        self._costruisci_intestazione()  # crea la barra scura in alto

        self._barra_stato = tk.Frame(self, bg=COLORI["grigio"])  # barra in basso
        self._barra_stato.pack(side="bottom", fill="x")
        self.lbl_messaggio = tk.Label(
            self._barra_stato, text="", bg=COLORI["grigio"],
            fg=COLORI["tenue"], font=("Segoe UI", 9), anchor="w",
        )  # messaggio temporaneo a sinistra
        self.lbl_messaggio.pack(side="left", padx=14, pady=6)
        self.lbl_conteggi = tk.Label(
            self._barra_stato, text="", bg=COLORI["grigio"],
            fg=COLORI["testo"], font=("Segoe UI", 9, "bold"), anchor="e",
        )  # conteggio di capi e look a destra
        self.lbl_conteggi.pack(side="right", padx=14, pady=6)

        # SINTASSI — `ttk.Notebook`
        # È il contenitore che mostra più schede una per volta. Ogni scheda
        # viene aggiunta con `.add(widget, text="Nome")`.
        self.notebook = ttk.Notebook(self)  # contenitore con le schede in alto
        self.notebook.pack(fill="both", expand=True)
        self.tabs = {}  # dizionario nome scheda -> widget della scheda
        for nome, classe in (  # elenco delle schede nell'ordine in cui compaiono
            ("Armadio", ArmadioTab),
            ("Aggiungi capo", AggiungiCapoTab),
            ("Look", LookTab),
            ("Idee", IdeeTab),
            ("Diario", DiarioTab),
        ):
            scheda = classe(self.notebook, self)  # crea la scheda passando la finestra principale
            self.notebook.add(scheda, text=nome)  # aggiunge la scheda al notebook
            self.tabs[nome] = scheda  # memorizza la scheda per poterla ricaricare

        self.aggiorna_stato()  # mostra subito i conteggi
        self.messaggio("Benvenuta! Inizia aggiungendo i capi nella scheda «Aggiungi capo».")  # messaggio iniziale

    def _centra(self) -> None:
        """Posiziona la finestra al centro dello schermo."""
        larghezza, altezza = 1200, 780  # dimensione iniziale della finestra
        # SINTASSI — `//` è la divisione intera: 5 // 2 fa 2, non 2.5.
        # `max(..., 0)` evita coordinate negative su schermi piccoli.
        x = max((self.winfo_screenwidth() - larghezza) // 2, 0)  # coordinata orizzontale centrale
        y = max((self.winfo_screenheight() - altezza) // 2 - 20, 0)  # coordinata verticale un po' più in alto
        # SINTASSI — la stringa di `geometry` ha il formato "LARGHEZZAxALTEZZA+X+Y".
        self.geometry(f"{larghezza}x{altezza}+{x}+{y}")  # applica dimensione e posizione

    def _costruisci_intestazione(self) -> None:
        """Crea la barra scura in alto con titolo e sottotitolo."""
        intestazione = tk.Frame(self, bg=COLORI["intestazione"])  # barra scura in alto
        intestazione.pack(side="top", fill="x")
        testo = tk.Frame(intestazione, bg=COLORI["intestazione"])  # contenitore del titolo
        testo.pack(side="left", padx=20, pady=12)
        tk.Label(testo, text="Cosa Mi Metto?", bg=COLORI["intestazione"],
                 fg=COLORI["testo_chiaro"], font=("Segoe UI", 20, "bold")
                 ).pack(anchor="w")  # titolo dell'applicazione
        tk.Label(
            testo,
            text="Assistente personale per armadio, abbinamenti e diario",
            bg=COLORI["intestazione"], fg="#a1a1aa", font=("Segoe UI", 9),
        ).pack(anchor="w")  # sottotitolo
        tk.Label(
            intestazione, text="Progetto Python · 2026/2027",
            bg=COLORI["intestazione"], fg="#a1a1aa", font=("Segoe UI", 9),
        ).pack(side="right", padx=20)  # riferimento al progetto a destra

    # --------------------------------------------------------------- eventi
    def dati_cambiati(self) -> None:
        """Avvisa tutte le schede che i dati sono cambiati e le ricarica."""
        # SINTASSI — `getattr` e `callable`
        # Non tutte le schede hanno `ricarica`. `getattr(scheda, "ricarica",
        # None)` restituisce il metodo se esiste, altrimenti None.
        # `callable(...)` controlla che sia davvero una funzione chiamabile.
        for scheda in self.tabs.values():  # aggiorna tutte le schede aperte
            ricarica = getattr(scheda, "ricarica", None)  # cerca il metodo di ricarica
            if callable(ricarica):
                ricarica()  # ricarica i dati della scheda
        self.aggiorna_stato()  # aggiorna i conteggi in basso

    def aggiorna_stato(self) -> None:
        """Aggiorna il conteggio di capi e look nella barra in basso."""
        self.lbl_conteggi.configure(
            text=f"{self.db.conta_capi()} capi  ·  {self.db.conta_look()} look"
        )  # scrive il numero di capi e di look salvati

    def messaggio(self, testo: str) -> None:
        """Mostra un messaggio temporaneo nella barra di stato."""
        # SINTASSI — `after` / `after_cancel`
        # `after(millisecondi, funzione)` programma una funzione per il futuro
        # senza bloccare l'interfaccia. Restituisce un id che permette di
        # annullare il timer con `after_cancel(id)`.
        if self._job_messaggio:  # se c'era un messaggio precedente
            self.after_cancel(self._job_messaggio)  # annulla il timer precedente
            self._job_messaggio = None
        self.lbl_messaggio.configure(text=testo)  # mostra il nuovo messaggio
        if testo:  # solo se c'è qualcosa da mostrare
            self._job_messaggio = self.after(8000, self._svuota_messaggio)  # lo cancella dopo 8 secondi

    def _svuota_messaggio(self) -> None:
        """Cancella il messaggio quando scade il timer."""
        self._job_messaggio = None  # il timer è scaduto
        self.lbl_messaggio.configure(text="")  # nasconde il messaggio

    def _chiudi(self) -> None:
        """Chiude il database e poi la finestra."""
        # SINTASSI — `try/finally`
        # Il blocco `finally` viene eseguito SEMPRE, anche se `db.chiudi()`
        # solleva un errore. Così la finestra si chiude comunque e il programma
        # non resta bloccato.
        try:
            self.db.chiudi()  # chiude il database prima di uscire
        finally:
            self.destroy()  # chiude comunque la finestra
