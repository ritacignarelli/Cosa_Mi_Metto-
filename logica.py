"""Regole dell'applicazione: importazione foto e proposta «Sorprendimi»."""
# SINTASSI — `from __future__ import annotations`
# Le annotazioni dei tipi (`str | Path`, `dict[str, list]`, `-> str`) servono
# a documentare che cosa accetta e restituisce una funzione. Con questa riga
# non vengono valutate subito, quindi possiamo usarle anche su Python meno
# recente. Non cambiano il comportamento del programma.
from __future__ import annotations  # permette di usare le annotazioni dei tipi anche su Python meno recente

import random  # serve per scegliere i capi a caso nella proposta automatica
import uuid  # genera un nome unico per ogni foto importata
from pathlib import Path  # gestisce i percorsi dei file

from PIL import Image, ImageOps, UnidentifiedImageError  # Pillow: apertura, rotazione e ridimensionamento foto

from database import (Database, RUOLI, RUOLI_OPZIONALI, RUOLI_RICHIESTI,
                      RUOLI_ORDINE)  # costanti e archivio usati dalla logica

# LOGICA — 1600 px è un buon compromesso: la foto resta nitida sullo schermo
# ma il file non diventa enorme. Il ridimensionamento avviene una volta sola,
# al momento dell'importazione.
LATO_MASSIMO = 1600  # lato massimo (in pixel) delle foto salvate


# SINTASSI — `Image.Image` è il tipo di un'immagine Pillow.
# Il nome che inizia con `_` (`_su_rgb`) è una convenzione Python: significa
# «funzione interna», che non dovrebbe essere usata dagli altri moduli.
def _su_rgb(img: Image.Image) -> Image.Image:
    """Converte un'immagine in RGB, mettendo uno sfondo bianco se è trasparente."""
    if img.mode in ("RGBA", "LA", "P"):  # immagini con trasparenza o con palette
        rgba = img.convert("RGBA")  # porta l'immagine in RGBA
        sfondo = Image.new("RGB", rgba.size, (255, 255, 255))  # crea uno sfondo bianco
        sfondo.paste(rgba, mask=rgba.getchannel("A"))  # incolla l'immagine rispettando la trasparenza
        return sfondo  # restituisce l'immagine senza trasparenza
    return img.convert("RGB")  # converte direttamente in RGB


def importa_foto(db: Database, sorgente: str | Path) -> str:
    """Valida la foto, la ridimensiona e ne salva una copia in data/foto.

    Restituisce il nome del file da memorizzare nel database.
    """
    src = Path(sorgente)  # percorso del file scelto dall'utente
    if not src.is_file():  # controlla che il file esista ancora
        raise ValueError("Il file selezionato non esiste più.")
    try:
        # SINTASSI — `with Image.open(src) as originale:`
        # `with` è un context manager: apre il file e lo chiude automaticamente
        # quando si esce dal blocco, anche se c'è un errore. Evita di lasciare
        # file aperti e di dimenticare `close()`.
        with Image.open(src) as originale:  # apre la foto scelta
            img = ImageOps.exif_transpose(originale)  # corregge l'orientamento delle foto da smartphone
            img.load()  # legge davvero i pixel dal file
            # SINTASSI — `thumbnail` modifica l'immagine «sul posto» e mantiene
            # le proporzioni: il lato più lungo diventa al massimo 1600 px.
            # `Image.Resampling.LANCZOS` è l'algoritmo di ridimensionamento,
            # scelto perché mantiene una buona qualità.
            img.thumbnail((LATO_MASSIMO, LATO_MASSIMO), Image.Resampling.LANCZOS)  # riduce la foto mantenendo le proporzioni
            img = _su_rgb(img)  # converte la foto in RGB per salvarla in JPEG
    # SINTASSI — `raise ... from exc`
    # Intercettiamo più tipi di errore e ne lanciamo uno solo, con un
    # messaggio comprensibile per l'utente. `from exc` conserva l'errore
    # originale come causa, così il dettaglio tecnico non va perso.
    except (UnidentifiedImageError, OSError, ValueError) as exc:  # file non immagine o danneggiato
        raise ValueError(
            "Il file selezionato non è un'immagine valida o è danneggiato."
        ) from exc

    # SINTASSI — `uuid.uuid4().hex`
    # `uuid4()` genera un identificativo casuale; `.hex` lo trasforma in una
    # stringa di 32 caratteri esadecimali. Usiamo questo nome per non
    # sovrascrivere mai foto con lo stesso nome.
    nome = f"{uuid.uuid4().hex}.jpg"  # nome unico per evitare sovrascritture
    try:
        img.save(db.foto_dir / nome, "JPEG", quality=88, optimize=True)  # salva una copia ottimizzata in data/foto
    except OSError as exc:  # problemi di scrittura sul disco
        raise ValueError("Non è stato possibile salvare la copia della foto.") from exc
    return nome  # restituisce solo il nome del file, non il percorso completo


def valida_selezione(selezione: dict[str, int | None]) -> None:
    """Controlla che il look contenga i ruoli obbligatori."""
    if not selezione:  # nessun capo scelto
        raise ValueError("Scegli almeno un capo per creare il look.")
    # SINTASSI — list comprehension
    # `[espressione for elemento in sequenza if condizione]` crea una lista
    # in una sola riga. Qui produce le etichette dei ruoli obbligatori che
    # mancano. `selezione.get(ruolo)` restituisce None se il ruolo non c'è;
    # `not None` è True, quindi il ruolo viene considerato mancante.
    mancanti = [  # ruoli obbligatori che non sono stati scelti
        RUOLI[ruolo].lower()  # usa l'etichetta leggibile nel messaggio
        for ruolo in RUOLI_RICHIESTI
        if not selezione.get(ruolo)
    ]
    if mancanti:  # se manca almeno un ruolo obbligatorio
        raise ValueError(
            "Per salvare il look scegli anche: " + ", ".join(mancanti) + "."
        )


def _raggruppa(righe) -> dict[str, list]:
    """Raggruppa i capi per ruolo, pronti per comporre un look."""
    # SINTASSI — dict comprehension
    # `{chiave: valore for elemento in sequenza}` costruisce un dizionario.
    # Qui crea una lista vuota per ogni ruolo conosciuto.
    gruppi: dict[str, list] = {ruolo: [] for ruolo in RUOLI_ORDINE}  # prepara una lista vuota per ogni ruolo
    for riga in righe:  # distribuisce i capi nel gruppo del loro ruolo
        # SINTASSI — `setdefault`
        # Se la chiave non esiste, inserisce `[]` e restituisce quella lista.
        # Poi `.append(riga)` aggiunge il capo. In pratica: «prendi la lista
        # del ruolo, creala se manca, e aggiungi l'elemento».
        gruppi.setdefault(riga["ruolo"], []).append(riga)
    return gruppi  # restituisce i capi raggruppati per ruolo


# SINTASSI — `set[int]` è un insieme di numeri interi. Un set non ammette
# duplicati ed è perfetto per rispondere alla domanda «questo id è già stato
# usato?» in modo veloce.
def _componi(gruppi: dict[str, list], escludi: set[int]):
    """Sceglie un capo per ogni ruolo, evitando quelli già proposti."""
    scelti: dict[str, object] = {}  # capi scelti, uno per ruolo
    mancanti: list[str] = []  # ruoli per cui non ci sono capi
    for ruolo in RUOLI_RICHIESTI:  # sceglie i tre ruoli obbligatori
        disponibili = gruppi.get(ruolo, [])  # capi disponibili per questo ruolo
        if not disponibili:  # nessun capo per il ruolo obbligatorio
            mancanti.append(RUOLI[ruolo])  # annota il ruolo mancante
            continue  # passa al ruolo successivo
        alternativa = [c for c in disponibili if c["id"] not in escludi]  # evita i capi della proposta precedente
        # SINTASSI — `alternativa or disponibili`
        # In Python `or` non restituisce True/False: restituisce il primo
        # valore «vero». Se `alternativa` non è vuota usa quella; se è vuota
        # (cioè tutti i capi erano da escludere) usa l'intera lista.
        # `random.choice` sceglie un elemento a caso da una sequenza non vuota.
        scelti[ruolo] = random.choice(alternativa or disponibili)  # sceglie a caso, o riusa tutti se non ci sono alternative
    if mancanti:  # se manca un ruolo obbligatorio la proposta non è valida
        return None, mancanti
    for ruolo in RUOLI_OPZIONALI:  # aggiunge borsa e accessorio solo se disponibili
        disponibili = gruppi.get(ruolo, [])
        if disponibili:
            alternativa = [c for c in disponibili if c["id"] not in escludi]  # preferisce capi non ancora proposti
            scelti[ruolo] = random.choice(alternativa or disponibili)
    return scelti, []  # proposta completa e nessun ruolo mancante


def suggerisci_look(db: Database, stagione: str, occasione: str,
                    escludi: set[int] | None = None):
    """Propone un look completo. Restituisce (capi_per_ruolo, avviso)."""
    # SINTASSI — default `None` + `or set()`
    # Non usiamo `escludi=set()` come valore predefinito perché in Python il
    # valore predefinito viene creato una sola volta e sarebbe condiviso tra
    # tutte le chiamate. Con `None` ne creiamo uno nuovo ogni volta.
    escludi = escludi or set()  # insieme dei capi da evitare (proposta precedente)
    gruppi = _raggruppa(db.capi_per_suggerimento(stagione, occasione))  # cerca i capi adatti a stagione e occasione
    scelti, mancanti = _componi(gruppi, escludi)  # prova a comporre il look
    if scelti:  # proposta trovata
        return scelti, ""

    # Riprova ignorando l'occasione, così una selezione troppo stretta
    # non blocca l'utente che ha comunque capi adatti alla stagione.
    gruppi = _raggruppa(db.capi_per_suggerimento(stagione))  # seconda ricerca senza filtro occasione
    scelti, mancanti = _componi(gruppi, escludi)  # riprova a comporre il look
    if scelti:  # proposta trovata con i soli capi della stagione
        return scelti, (
            "Non c'erano abbastanza capi per l'occasione scelta: "
            "ho usato capi della stessa stagione."
        )
    # SINTASSI — `", ".join(lista)`
    # Unisce gli elementi della lista in un'unica stringa, mettendo `, ` tra
    # uno e l'altro. È l'opposto di `stringa.split(", ")`.
    raise ValueError(  # nessuna combinazione possibile: spiega cosa manca
        "Non ci sono abbastanza capi per creare un look. Mancano: "
        + ", ".join(mancanti).lower()
        + ". Aggiungili nella scheda «Aggiungi capo»."
    )
