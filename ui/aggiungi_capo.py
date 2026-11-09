"""Scheda Aggiungi capo."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from tkinter import messagebox, ttk  # messaggi di errore e widget

from ui.form_capo import FormCapo  # form condiviso per i dati del capo
from ui.stile import COLORI  # colori dell'interfaccia


# SINTASSI — `super().__init__(...)`
# Chiama il costruttore della classe madre (`ttk.Frame`), che crea il widget
# vero. `padding=(16, 12)` è lo spazio interno: 16 px a sinistra/destra e
# 12 px sopra/sotto.
class AggiungiCapoTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=(16, 12))  # scheda con un piccolo margine
        self.app = app  # finestra principale, serve per aggiornare le altre schede
        self.db = app.db  # archivio condiviso

        testata = ttk.Frame(self)  # contenitore del titolo
        testata.pack(fill="x", pady=(0, 10))
        ttk.Label(testata, text="Aggiungi un capo", style="Titolo.TLabel"
                  ).pack(anchor="w")  # titolo della scheda
        ttk.Label(
            testata,
            text="Scegli la foto, compila i dati e salva: il capo comparirà subito nell'armadio.",
            style="Sottotitolo.TLabel",
        ).pack(anchor="w")  # istruzioni brevi

        card = tk.Frame(self, bg=COLORI["superficie"],
                        highlightbackground=COLORI["bordo"], highlightthickness=1)  # card bianca del form
        card.pack(fill="both", expand=True)

        self.form = FormCapo(card, self.db)  # crea i campi vuoti per un nuovo capo
        self.form.pack(fill="both", expand=True)

        pulsanti = ttk.Frame(card, style="Card.TFrame",
                             padding=(24, 0, 24, 20))  # barra dei pulsanti
        pulsanti.pack(fill="x")
        ttk.Button(pulsanti, text="Svuota form", style="Secondario.TButton",
                   command=self._svuota).pack(side="right")  # pulisce i campi
        ttk.Button(pulsanti, text="Salva capo", style="Accent.TButton",
                   command=self._salva).pack(side="right", padx=(0, 8))  # salva il nuovo capo

        # SINTASSI — `focus_set`
        # Sposta il focus della tastiera sul campo: l'utente può scrivere
        # subito il nome senza doverci cliccare sopra.
        self.form.entry_nome.focus_set()  # mette il cursore sul campo nome

    def ricarica(self) -> None:
        """Aggiorna l'elenco delle sezioni nel form."""
        self.form.ricarica()  # aggiorna l'elenco delle sezioni nel form

    def _svuota(self) -> None:
        """Svuota il form e riporta il cursore sul campo nome."""
        self.form.reset()  # riporta i campi ai valori iniziali
        self.form.entry_nome.focus_set()  # riporta il cursore sul nome
        self.app.messaggio("Form svuotato.")  # conferma all'utente

    def _salva(self) -> None:
        """Legge il form, salva il nuovo capo e aggiorna l'app."""
        try:
            dati = self.form.raccogli()  # legge e controlla i campi
            foto = self.form.prepara_foto()  # importa la foto scelta, se c'è
            # SINTASSI — `**dati`
            # Il dizionario `dati` viene «aperto» in argomenti nominati:
            # `aggiungi_capo(nome=..., sezione_id=..., ruolo=..., ...)`.
            self.db.aggiungi_capo(foto=foto, **dati)  # salva il capo nel database
        except ValueError as exc:  # dati obbligatori mancanti o non validi
            messagebox.showerror("Dati non validi", str(exc),
                                 parent=self.winfo_toplevel())  # spiega l'errore
            return
        self.form.reset()  # svuota il form dopo il salvataggio
        self.form.entry_nome.focus_set()  # prepara l'inserimento del capo successivo
        self.app.dati_cambiati()  # aggiorna armadio, look, diario e conteggi
        self.app.messaggio(f"Capo «{dati['nome']}» aggiunto all'armadio.")  # conferma all'utente
