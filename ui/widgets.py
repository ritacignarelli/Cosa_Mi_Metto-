"""Componenti riutilizzabili: miniature, area scorrevole, anteprima look."""
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import tkinter as tk  # toolkit grafico incluso in Python
from pathlib import Path  # gestisce i percorsi delle foto
from tkinter import ttk  # widget con stile moderno

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk  # Pillow: immagini, disegno, font e conversione per Tk

from database import RUOLI, RUOLI_LOOK  # etichette e ruoli usati nell'anteprima
from ui.stile import COLORI  # colori comuni dell'interfaccia

# SINTASSI — dizionario a livello di modulo
# `_CACHE` esiste una sola volta per tutto il programma. La chiave è una tupla
# (percorso, dimensione, testo) e il valore è la PhotoImage già pronta.
# Serve a non rileggere e ridisegnare la stessa foto ogni volta.
_CACHE: dict[tuple, ImageTk.PhotoImage] = {}  # tiene in memoria le miniature già create


# SINTASSI — `ImageFont.truetype(nome, dimensione)`
# Carica un font dal sistema. Se il file non esiste solleva `OSError`: in quel
# caso proviamo il font successivo e, alla fine, usiamo quello predefinito.
def _font(dimensione: int):
    """Carica un font adatto al sistema, con ripiego su quello di Pillow."""
    for nome in ("segoeui.ttf", "DejaVuSans.ttf", "Arial.ttf"):  # prova alcuni font comuni
        try:
            return ImageFont.truetype(nome, dimensione)  # usa il primo font disponibile
        except OSError:
            continue  # se il font non c'è passa al successivo
    return ImageFont.load_default()  # ultima alternativa: font predefinito di Pillow


# SINTASSI — `tuple[int, int]`
# Indica una tupla di due numeri interi, per esempio (150, 150). Le annotazioni
# sono solo una guida: Python non controlla che la tupla sia davvero lunga due.
def _segnaposto(dimensione: tuple[int, int], testo: str) -> ImageTk.PhotoImage:
    """Disegna un riquadro grigio con un testo, usato quando manca la foto."""
    img = Image.new("RGB", dimensione, COLORI["grigio"])  # immagine grigia delle dimensioni richieste
    # `ImageDraw.Draw` crea un «pennello» per disegnare testo e forme sopra
    # un'immagine Pillow.
    disegno = ImageDraw.Draw(img)  # oggetto per disegnare sopra l'immagine
    font = _font(13)  # font del testo segnaposto
    righe = testo.split("\n")  # permette testi su più righe
    altezza = 17  # altezza di una riga di testo
    y = (dimensione[1] - altezza * len(righe)) / 2  # centra verticalmente il testo
    for riga in righe:  # disegna una riga alla volta
        larghezza = disegno.textlength(riga, font=font)  # misura la larghezza della riga
        disegno.text(((dimensione[0] - larghezza) / 2, y), riga,
                     fill=COLORI["tenue"], font=font)  # centra la riga orizzontalmente
        y += altezza  # passa alla riga successiva
    return ImageTk.PhotoImage(img)  # converte l'immagine in un formato usabile da Tk


# SINTASSI — espressione condizionale
# `str(percorso) if percorso else None` significa: «se percorso esiste, usa
# str(percorso); altrimenti usa None». È un `if` scritto in una sola riga.
def immagine(percorso: Path | str | None, dimensione: tuple[int, int],
             testo_vuoto: str = "Nessuna\nfoto") -> ImageTk.PhotoImage:
    """Crea (o riusa dalla cache) una miniatura pronta per Tkinter."""
    chiave = (str(percorso) if percorso else None, dimensione, testo_vuoto)  # identifica la miniatura in cache
    if chiave in _CACHE:  # se è già stata creata
        return _CACHE[chiave]  # riusa la stessa immagine, più veloce

    foto = None  # immagine da mostrare, all'inizio vuota
    if percorso:  # se esiste un percorso di foto
        try:
            with Image.open(percorso) as originale:  # apre il file della foto
                img = ImageOps.exif_transpose(originale)  # corregge l'orientamento della foto
                # SINTASSI — `ImageOps.fit` è diverso da `thumbnail`:
                # `fit` ritaglia e ridimensiona per riempire ESATTAMENTE il
                # riquadro richiesto, anche se questo taglia i bordi. Per le
                # miniature quadrate è l'effetto che vogliamo.
                img = ImageOps.fit(img, dimensione, Image.Resampling.LANCZOS)  # ritaglia e ridimensiona riempiendo il riquadro
                if img.mode in ("RGBA", "LA", "P"):  # se c'è trasparenza
                    rgba = img.convert("RGBA")  # converte in RGBA
                    sfondo = Image.new("RGB", dimensione, "white")  # sfondo bianco
                    sfondo.paste(rgba, mask=rgba.getchannel("A"))  # applica la trasparenza
                    img = sfondo  # usa l'immagine con sfondo bianco
                else:
                    img = img.convert("RGB")  # conversione normale in RGB
                # SINTASSI — `ImageTk.PhotoImage`
                # Pillow lavora con oggetti Image; Tkinter capisce solo
                # PhotoImage. Questa classe fa la conversione.
                foto = ImageTk.PhotoImage(img)  # prepara l'immagine per Tk
        except (OSError, ValueError):  # file mancante o non leggibile
            foto = None  # userà il segnaposto
    if foto is None:  # nessuna foto valida
        foto = _segnaposto(dimensione, testo_vuoto)  # disegna il riquadro «Nessuna foto»

    if len(_CACHE) > 400:  # evita che la cache cresca troppo
        _CACHE.clear()  # svuota la cache quando supera 400 immagini
    _CACHE[chiave] = foto  # salva la nuova miniatura in cache
    return foto  # restituisce l'immagine pronta per Tk


# SINTASSI — ereditarietà
# `class ScrollableFrame(ttk.Frame)` crea una classe che È un ttk.Frame, ma
# con funzionalità in più. `super().__init__(...)` chiama il costruttore
# della classe madre, che prepara il vero frame Tkinter.
class ScrollableFrame(ttk.Frame):
    """Area con barra di scorrimento verticale e rotella del mouse."""

    def __init__(self, master, **kwargs):
        super().__init__(master, style="Sfondo.TFrame", **kwargs)  # contenitore esterno
        # `**kwargs` raccoglie tutte le parole chiave passate al costruttore
        # (per esempio padding=...) e le inoltra al frame della classe madre.
        self.canvas = tk.Canvas(self, bg=COLORI["sfondo"],
                                highlightthickness=0, bd=0)  # tela su cui scorre il contenuto
        self.barra = ttk.Scrollbar(self, orient="vertical",
                                   command=self.canvas.yview)  # barra di scorrimento verticale
        self.canvas.configure(yscrollcommand=self.barra.set)  # collega la tela alla barra
        self.barra.pack(side="right", fill="y")  # barra a destra
        self.canvas.pack(side="left", fill="both", expand=True)  # tela a sinistra

        self.contenuto = ttk.Frame(self.canvas, style="Sfondo.TFrame")  # frame interno con i widget
        # SINTASSI — `create_window`
        # Una Canvas non può contenere widget normali. `create_window` crea
        # un «buco» nella tela dentro cui viene inserito `self.contenuto`.
        # `anchor="nw"` lo aggancia in alto a sinistra.
        self._finestra = self.canvas.create_window(
            (0, 0), window=self.contenuto, anchor="nw"
        )  # inserisce il frame dentro la tela
        self.contenuto.bind("<Configure>", self._aggiorna_area)  # aggiorna l'area scorrevole quando cambia il contenuto
        self.canvas.bind("<Configure>", self._aggiorna_larghezza)  # adatta la larghezza alla finestra

    def _aggiorna_area(self, _event=None) -> None:
        """Aggiorna l'area scorrevole quando cambia il contenuto."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))  # dice alla tela quanto è grande il contenuto

    def _aggiorna_larghezza(self, event) -> None:
        """Adatta la larghezza del contenuto a quella della finestra."""
        self.canvas.itemconfigure(self._finestra, width=event.width)  # il contenuto usa tutta la larghezza disponibile

    def _rotella(self, event) -> None:
        """Gestisce la rotella del mouse su Windows, macOS e Linux."""
        # SINTASSI — `getattr(event, "num", None)`
        # `event` è l'oggetto dell'evento. Su Windows non ha `num`, quindi
        # `getattr` restituisce il valore predefinito None invece di far
        # esplodere il programma con AttributeError.
        if getattr(event, "num", None) == 4:  # rotella su Linux: su
            passo = -1
        elif getattr(event, "num", None) == 5:  # rotella su Linux: giù
            passo = 1
        else:  # Windows e macOS usano il segno di event.delta
            passo = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(passo, "units")  # scorre di una riga

    def collega_rotella(self, widget=None) -> None:
        """Collega la rotella del mouse al contenuto e a tutti i suoi figli."""
        widget = widget or self.contenuto  # parte dal frame interno
        # SINTASSI — `bind(..., add="+")`
        # `bind` collega un evento a una funzione. Con `add="+"` aggiunge il
        # nuovo gestore senza cancellare quelli già presenti.
        widget.bind("<MouseWheel>", self._rotella, add="+")  # rotella su Windows/macOS
        widget.bind("<Button-4>", self._rotella, add="+")  # rotella su Linux: su
        widget.bind("<Button-5>", self._rotella, add="+")  # rotella su Linux: giù
        for figlio in widget.winfo_children():  # collega anche tutti i widget figli
            self.collega_rotella(figlio)


class AnteprimaLook(ttk.Frame):
    """Cinque riquadri affiancati con i capi del look."""

    def __init__(self, master, db):
        super().__init__(master, style="Sfondo.TFrame")  # contenitore dell'anteprima
        self.db = db  # archivio da cui leggere i percorsi delle foto
        # SINTASSI — tipo composto
        # `dict[str, tuple[tk.Frame, tk.Label, tk.Label]]` significa: un
        # dizionario che associa il nome del ruolo a una tupla di tre widget.
        self._slot: dict[str, tuple[tk.Frame, tk.Label, tk.Label]] = {}  # riquadri per ogni ruolo
        for colonna, ruolo in enumerate(RUOLI_LOOK):  # crea un riquadro per ogni ruolo del look
            self.columnconfigure(colonna, weight=1)  # colonne di larghezza uguale
            card = tk.Frame(self, bg=COLORI["superficie"],
                            highlightbackground=COLORI["bordo"],
                            highlightthickness=1)  # card bianca con bordo
            card.grid(row=0, column=colonna, padx=5, pady=4, sticky="n")  # posiziona la card
            tk.Label(card, text=RUOLI[ruolo].upper(), bg=COLORI["superficie"],
                     fg=COLORI["tenue"], font=("Segoe UI", 8, "bold")
                     ).pack(padx=8, pady=(8, 4))  # etichetta del ruolo
            etichetta = tk.Label(card, bg=COLORI["superficie"], bd=0)  # spazio per la foto
            etichetta.pack(padx=8)
            nome = tk.Label(card, text="—", bg=COLORI["superficie"],
                            fg=COLORI["testo"], font=("Segoe UI", 9),
                            wraplength=140, height=2, justify="center")  # nome del capo
            nome.pack(padx=8, pady=(4, 8))
            self._slot[ruolo] = (card, etichetta, nome)  # memorizza i widget del riquadro

    def mostra(self, selezione: dict[str, object]) -> None:
        """Mostra le foto e i nomi dei capi scelti per ogni ruolo."""
        for ruolo in RUOLI_LOOK:  # aggiorna tutti i ruoli, anche quelli vuoti
            _card, etichetta, nome = self._slot[ruolo]  # recupera i widget del riquadro
            capo = selezione.get(ruolo)  # capo scelto per questo ruolo, se c'è
            percorso = self.db.percorso_foto(capo["foto"]) if capo else None  # percorso della foto
            foto = immagine(percorso, (150, 150))  # crea o riusa la miniatura
            etichetta.configure(image=foto)  # mostra la foto
            # SINTASSI — riferimento all'immagine
            # Tkinter non tiene un riferimento Python alla PhotoImage: se la
            # variabile locale `foto` sparisce, l'immagine può essere
            # cancellata e il label resta vuoto. Salvandola come attributo
            # del label, resta viva finché esiste il label.
            etichetta.image = foto  # evita che Tk elimini l'immagine dalla memoria
            nome.configure(text=capo["nome"] if capo else "—")  # mostra il nome o un trattino
