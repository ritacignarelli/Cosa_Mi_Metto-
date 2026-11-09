"""Tema grafico comune a tutte le schede."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from tkinter import ttk  # widget con stile moderno

# SINTASSI — i colori sono stringhe esadecimali nel formato "#RRGGBB":
# i primi due caratteri sono il rosso, poi verde e blu. Tkinter accetta
# direttamente questi codici.
COLORI = {  # tavolozza unica usata da tutta l'interfaccia
    "sfondo": "#f4f4f5",  # grigio chiarissimo per lo sfondo
    "superficie": "#ffffff",  # bianco per le card
    "testo": "#18181b",  # quasi nero per i testi
    "tenue": "#71717a",  # grigio per le informazioni secondarie
    "bordo": "#e4e4e7",  # grigio chiaro per i bordi
    "primario": "#4f46e5",  # indaco per i pulsanti principali
    "primario_scuro": "#4338ca",  # indaco più scuro al passaggio del mouse
    "pericolo": "#dc2626",  # rosso per le azioni di eliminazione
    "pericolo_scuro": "#b91c1c",  # rosso più scuro al passaggio del mouse
    "intestazione": "#111827",  # blu molto scuro per la barra superiore
    "testo_chiaro": "#f9fafb",  # bianco per il testo sull'intestazione
    "grigio": "#e5e7eb",  # grigio per la barra di stato
}


# SINTASSI — `isinstance(oggetto, (Tipo1, Tipo2))`
# Controlla se l'oggetto è di uno dei tipi elencati nella tupla. `tk.Misc` è
# la classe base comune a tutti i widget Tkinter; qui distinguiamo le vere
# finestre (Tk, Toplevel) dai semplici contenitori.
def applica_stile(finestra: tk.Misc) -> None:
    """Applica colori, font e stili comuni a tutta l'interfaccia."""
    if isinstance(finestra, (tk.Tk, tk.Toplevel)):  # solo le finestre vere hanno uno sfondo proprio
        finestra.configure(bg=COLORI["sfondo"])  # imposta il colore di sfondo

    # SINTASSI — `ttk.Style`
    # È il «foglio di stile» di Tkinter: si crea una volta e poi si usano i
    # nomi di stile (es. "Accent.TButton") nei widget.
    stile = ttk.Style(finestra)  # crea il gestore degli stili ttk
    try:
        stile.theme_use("clam")  # usa il tema «clam», più personalizzabile
    except tk.TclError:
        # `tk.TclError` è l'errore che Tkinter solleva quando un comando Tcl
        # non è disponibile. Se il tema manca, non blocchiamo l'app.
        pass  # se il tema non è disponibile mantiene quello predefinito

    base = ("Segoe UI", 10)  # font di base dell'applicazione
    # SINTASSI — il selettore "." indica lo stile globale, cioè le impostazioni
    # predefinite per tutti i widget ttk.
    stile.configure(".", background=COLORI["sfondo"],
                    foreground=COLORI["testo"], font=base)  # stile valido per tutti i widget
    stile.configure("TFrame", background=COLORI["sfondo"])  # sfondo dei contenitori
    stile.configure("Sfondo.TFrame", background=COLORI["sfondo"])  # variante esplicita per lo sfondo
    stile.configure("Card.TFrame", background=COLORI["superficie"])  # contenitori bianchi
    stile.configure("TLabel", background=COLORI["sfondo"],
                    foreground=COLORI["testo"])  # testo normale
    stile.configure("Card.TLabel", background=COLORI["superficie"],
                    foreground=COLORI["testo"])  # testo sopra una card bianca
    stile.configure("Tenue.TLabel", background=COLORI["sfondo"],
                    foreground=COLORI["tenue"])  # testo secondario
    stile.configure("CardTenue.TLabel", background=COLORI["superficie"],
                    foreground=COLORI["tenue"])  # testo secondario sopra una card
    stile.configure("Titolo.TLabel", background=COLORI["sfondo"],
                    foreground=COLORI["testo"], font=("Segoe UI", 17, "bold"))  # titolo di sezione
    stile.configure("Sottotitolo.TLabel", background=COLORI["sfondo"],
                    foreground=COLORI["tenue"], font=("Segoe UI", 10))  # sottotitolo esplicativo
    stile.configure("CardTitolo.TLabel", background=COLORI["superficie"],
                    foreground=COLORI["testo"], font=("Segoe UI", 12, "bold"))  # titolo dentro una card

    stile.configure("TNotebook", background=COLORI["sfondo"], borderwidth=0,
                    tabmargins=(14, 10, 14, 0))  # contenitore delle schede
    stile.configure("TNotebook.Tab", background=COLORI["grigio"],
                    foreground=COLORI["tenue"], padding=(18, 9),
                    font=("Segoe UI", 10))  # scheda non selezionata
    # SINTASSI — `stile.map`
    # `map` dice: «quando il widget si trova in questo stato, usa questo
    # colore». Gli stati più comuni sono "active" (mouse sopra), "disabled"
    # (pulsante disattivato), "selected" (scheda scelta) e "readonly".
    stile.map("TNotebook.Tab",
              background=[("selected", COLORI["superficie"])],
              foreground=[("selected", COLORI["primario"])])  # scheda selezionata

    stile.configure("Accent.TButton", background=COLORI["primario"],
                    foreground="white", padding=(14, 7), borderwidth=0,
                    focusthickness=0)  # pulsante principale
    stile.map("Accent.TButton",
              background=[("active", COLORI["primario_scuro"]),
                          ("disabled", "#c7d2fe")],
              foreground=[("disabled", "#ffffff")])  # colori per mouse sopra e pulsante disabilitato
    stile.configure("Secondario.TButton", background=COLORI["superficie"],
                    foreground=COLORI["testo"], padding=(12, 6),
                    bordercolor=COLORI["bordo"], focusthickness=0)  # pulsante secondario
    stile.map("Secondario.TButton",
              background=[("active", COLORI["grigio"])])  # grigio al passaggio del mouse
    stile.configure("Pericolo.TButton", background=COLORI["pericolo"],
                    foreground="white", padding=(12, 6), borderwidth=0,
                    focusthickness=0)  # pulsante per eliminare
    stile.map("Pericolo.TButton",
              background=[("active", COLORI["pericolo_scuro"])])  # rosso più scuro al passaggio del mouse

    stile.configure("TEntry", fieldbackground="white",
                    bordercolor=COLORI["bordo"], padding=5)  # campi di testo
    stile.configure("TCombobox", padding=4)  # menu a tendina
    stile.map("TCombobox",
              fieldbackground=[("readonly", "white")],
              selectbackground=[("readonly", "white")],
              selectforeground=[("readonly", COLORI["testo"])])  # aspetto del menu quando è bloccato
    stile.configure("TLabelframe", background=COLORI["sfondo"],
                    bordercolor=COLORI["bordo"], borderwidth=1)  # riquadri con titolo
    stile.configure("TLabelframe.Label", background=COLORI["sfondo"],
                    foreground=COLORI["testo"], font=("Segoe UI", 10, "bold"))  # titolo del riquadro
    stile.configure("Treeview", background="white", fieldbackground="white",
                    foreground=COLORI["testo"], rowheight=25,
                    bordercolor=COLORI["bordo"])  # tabelle
    stile.configure("Treeview.Heading", background=COLORI["grigio"],
                    foreground=COLORI["testo"], font=("Segoe UI", 9, "bold"))  # intestazioni delle tabelle
    stile.configure("TScrollbar", background=COLORI["grigio"],
                    troughcolor=COLORI["sfondo"], borderwidth=0)  # barre di scorrimento
