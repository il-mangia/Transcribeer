import tkinter as tk
from ui import UI
from transcriber import Transcriber
from tkinter import filedialog

def main():
    root = tk.Tk()

    ui = UI(
        root,
        start_cb=lambda: start_transcription(ui),
        save_cb=lambda: save_text(ui)
    )

    root.mainloop()

def start_transcription(ui):
    file_path, lang = ui.get_params()

    if not file_path:
        ui.log("⚠ Seleziona un file.")
        return

    worker = Transcriber(ui, file_path, ui.strings, lang)
    worker.start()

def save_text(ui):
    text = ui.out.get("1.0", "end").strip()

    if not text:
        ui.log("⚠ Niente da salvare.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text", "*.txt")]
    )

    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        ui.log("💾 Salvato con successo.")

if __name__ == "__main__":
    main()
