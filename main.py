"""Avvio di «Cosa Mi Metto?»."""  # docstring del modulo

# SINTASSI — `from ... import ...`
# Prende solo la classe indicata da un modulo, senza importare tutto il file.
# È come dire: «dal file database prendimi la classe Database».
from database import Database  # importa la classe che gestisce l'archivio SQLite
from ui.finestra import App  # importa la finestra principale realizzata con Tkinter


# LOGICA — `main` è il punto di ingresso: apre i dati, crea la finestra e
# lascia il controllo a Tkinter, che gestisce clic, ridisegni e chiusura.
def main() -> None:  # punto di ingresso dell'applicazione
    db = Database()  # apre (o crea) il database e prepara la cartella delle foto
    app = App(db)  # costruisce la finestra principale passando l'archivio da usare
    app.mainloop()  # avvia il ciclo grafico e resta in ascolto fino alla chiusura


# SINTASSI — `if __name__ == "__main__":`
# `__name__` è una variabile speciale che Python mette in ogni file.
# Vale "__main__" quando il file viene eseguito direttamente (`python main.py`);
# vale il nome del modulo quando il file viene importato da un altro file.
# Così l'app parte solo se lanci questo file e non quando viene importato.
if __name__ == "__main__":  # controlla che il file sia stato lanciato direttamente
    main()  # esegue l'avvio dell'applicazione
