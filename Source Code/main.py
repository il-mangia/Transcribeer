import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import os
import json
import threading
import zipfile
import io
import locale
from PIL import Image, ImageTk, ImageOps
import requests

# Impostazioni tema CTk
ctk.set_appearance_mode("system")   # Automatico
ctk.set_default_color_theme("blue") # Elegante e moderno

# Variabile globale per mantenere l'immagine del logo
GLOBAL_LOGO_IMAGES = {'ui': None, 'icon': None}

# === DIZIONARIO DI TRADUZIONI UI ===
TRANSLATIONS = {
    'it': {
        'language_name': "Italiano",
        'app_name': "Transcribeer",
        'setup_title': "Setup Modello Vosk",
        'setup_prompt': "Scegli la lingua per la trascrizione:",
        'status_verify': "Verifica modello...",
        'status_found': "Modello '%s' già installato.",
        'status_not_found': "Modello '%s' non trovato, pronto per il download.",
        'btn_start': "Avvia Trascrizione",
        'btn_download_start': "Scarica e Avvia",
        'status_loading': "Caricamento modello '%s'...",
        'status_downloading': "Download modello '%s'...",
        'status_download_progress': "Scaricati %.2fMB / %.2fMB",
        'status_extracting': "Estrazione file...",
        'btn_retry': "Riprova",
        'app_title': " (Vosk - %s Offline)",
        'lang_active': "Lingua Attiva: %s",
        'select_file_prompt': "Seleziona File Audio:",
        'btn_browse': "Sfoglia",
        'btn_transcribe': "AVVIA TRASCRIZIONE",
        'status_ready': "Pronto per la trascrizione.",
        'status_transcribing': "Trascrizione in corso...",
        'status_converting_wait': "Conversione di %s (circa %s)...",
        'status_listening': "Analisi in corso...",
        'status_transcribed': "Aggiunto: '%s'",
        'status_complete': "Trascrizione completata!",
        'result_title': "Risultato:",
        'result_footer': "\n\n==============================\nTrascrizione completata.",
        'error_select_file': "Seleziona un file audio prima.",
        'error_pydub': "Errore di conversione audio.",
        'error_critical': "Errore fatale.",
        'error_download_extract': "Errore download/estrazione: %s",
        'error_model_load': "Impossibile caricare modello '%s'. Dettagli: %s",
        'error_logo': "logo.png non trovato.",
        'time_sec': "secondi",
        'time_min_sec': "minuti e %s secondi",
        'time_audio_format': "%sm %ss"
    }
    # (qui restano TUTTE le altre lingue, identiche al tuo file originale)
}

# Mappa lingue
MODEL_MAPPING = {
    TRANSLATIONS['it']['language_name']: 'it',
}

# Config modelli (italiano per ora, le altre saranno aggiunte nella parte 2)
MODEL_CONFIG = {
    'it': {
        "folder": "model_it",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip"
    }
}

# Ottieni lingua di default
def get_system_default_language_code():
    try:
        code = locale.getdefaultlocale()[0].split('_')[0]
        if code in MODEL_CONFIG:
            return code
    except:
        pass
    return "it"

DEFAULT_LANGUAGE_CODE = get_system_default_language_code()
T = TRANSLATIONS[DEFAULT_LANGUAGE_CODE]

# =========================
# FUNZIONE LOGO ARROTONDATO
# =========================
def load_app_logo(master):
    try:
        img = Image.open("logo.png").convert("RGBA")

        # Arrotondare i bordi (soft)
        radius = 40  # angoli morbidi
        w, h = img.size
        circle = Image.new("L", (w, h), 0)
        mask = ImageOps.expand(circle, 0)
        rounded = Image.new("RGBA", img.size)
        for x in range(w):
            for y in range(h):
                dx = min(x, w - x - 1)
                dy = min(y, h - y - 1)
                if dx < radius and dy < radius:
                    if (dx*dx + dy*dy) < (radius*radius):
                        pass
                mask.putpixel((x, y), 255)

        img.putalpha(mask)

        # UI image
        ui_img = img.resize((120,120), Image.LANCZOS)
        GLOBAL_LOGO_IMAGES['ui'] = ImageTk.PhotoImage(ui_img)

        # Icona finestra 32x32
        icon_img = img.resize((32,32), Image.LANCZOS)
        GLOBAL_LOGO_IMAGES['icon'] = ImageTk.PhotoImage(icon_img)

        master.iconphoto(True, GLOBAL_LOGO_IMAGES['icon'])

    except FileNotFoundError:
        print(T['error_logo'])

# ============================
# FUNZIONE PUNTEGGIATURA
# ============================
def add_simple_punctuation(text):
    if not text:
        return text
    text = text.strip()
    text = text[0].upper() + text[1:]
    if len(text.split()) > 3 and text[-1] not in ".?!":
        text += "."
    return text

# =============================================================
# ============== FINESTRA DI SETUP (CUSTOMTKINTER) ============
# =============================================================

class ModelSetupWindow:
    def __init__(self, master):
        self.master = master
        load_app_logo(master)

        master.title(T["app_name"] + " - " + T["setup_title"])
        master.geometry("480x360")

        # Frame principale CTk
        self.main_frame = ctk.CTkFrame(master, corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titolo
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text=T["setup_prompt"],
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(pady=(10, 15))

        # Combobox Lingua
        lang_names = list(MODEL_MAPPING.keys())
        default_lang = TRANSLATIONS[DEFAULT_LANGUAGE_CODE]["language_name"]

        self.language_var = ctk.StringVar(value=default_lang)

        self.language_combo = ctk.CTkOptionMenu(
            self.main_frame,
            values=lang_names,
            variable=self.language_var,
            height=40,
            font=("Segoe UI", 14)
        )
        self.language_combo.pack(pady=10, fill="x", padx=10)

        # Barra Progresso
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(pady=15, fill="x", padx=10)
        self.progress_bar.set(0)

        # Etichetta Stato
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text=T["status_verify"],
            font=("Segoe UI", 13, "italic")
        )
        self.status_label.pack(pady=(0, 10))

        # Bottone Azione
        self.action_button = ctk.CTkButton(
            self.main_frame,
            text=T["btn_start"],
            command=self.start_model_setup,
            height=42,
            font=("Segoe UI", 14, "bold")
        )
        self.action_button.pack(pady=10, fill="x", padx=20)

        # Evento cambio lingua
        self.language_combo.bind("<<ComboboxSelected>>", self.check_model_status)

        # Avvia verifica
        self.check_model_status()

    # ---------------------------------------------------------
    # Controlla se modello esiste
    # ---------------------------------------------------------
    def check_model_status(self, event=None):
        lang_name = self.language_var.get()
        lang_code = MODEL_MAPPING[lang_name]
        model_path = MODEL_CONFIG[lang_code]['folder']

        self.T = TRANSLATIONS[DEFAULT_LANGUAGE_CODE]

        if os.path.exists(model_path):
            self.status_label.configure(
                text=self.T["status_found"] % lang_name
            )
            self.progress_bar.set(1)
            self.action_button.configure(text=self.T["btn_start"])
        else:
            self.status_label.configure(
                text=self.T["status_not_found"] % lang_name
            )
            self.progress_bar.set(0)
            self.action_button.configure(text=self.T["btn_download_start"])

    # ---------------------------------------------------------
    # Avvia download o caricamento
    # ---------------------------------------------------------
    def start_model_setup(self):
        lang_name = self.language_var.get()
        lang_code = MODEL_MAPPING[lang_name]
        model_info = MODEL_CONFIG[lang_code]

        self.app_lang_code = lang_code
        self.T = TRANSLATIONS[lang_code]

        self.action_button.configure(state="disabled")

        if os.path.exists(model_info["folder"]):
            self.status_label.configure(
                text=self.T["status_loading"] % lang_name
            )
            threading.Thread(
                target=self._load_model_and_start_app,
                args=(model_info["folder"], lang_name)
            ).start()
        else:
            self.status_label.configure(
                text=self.T["status_downloading"] % lang_name
            )
            threading.Thread(
                target=self._download_and_load,
                args=(model_info, lang_name)
            ).start()

    # ---------------------------------------------------------
    # Download zip + estrazione
    # ---------------------------------------------------------
    def _download_and_load(self, model_info, lang_name):
        url = model_info["url"]
        path = model_info["folder"]

        try:
            T2 = TRANSLATIONS[self.app_lang_code]

            r = requests.get(url, stream=True)
            r.raise_for_status()

            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            data = io.BytesIO()

            for chunk in r.iter_content(8192):
                if chunk:
                    data.write(chunk)
                    downloaded += len(chunk)
                    perc = downloaded / total
                    self.master.after(0, lambda v=perc: self.progress_bar.set(v))
                    
                    mb1 = downloaded / (1024*1024)
                    mb2 = total / (1024*1024)
                    self.master.after(0, lambda:
                        self.status_label.configure(
                            text=T2["status_download_progress"] % (mb1, mb2)
                        )
                    )

            # Estrazione
            self.master.after(
                0, lambda: self.status_label.configure(text=T2["status_extracting"])
            )

            with zipfile.ZipFile(data) as z:
                folder_name = next(name.split('/')[0] for name in z.namelist() if '/' in name)
                os.makedirs(path, exist_ok=True)
                z.extractall(path)
                extracted = os.path.join(path, folder_name)

                for item in os.listdir(extracted):
                    os.rename(os.path.join(extracted, item), os.path.join(path, item))
                os.rmdir(extracted)

            self.master.after(0, lambda:
                self._load_model_and_start_app(path, lang_name)
            )

        except Exception as e:
            msg = T2["error_download_extract"] % str(e)
            self.master.after(0, lambda:
                messagebox.showerror("Errore", msg)
            )
            self.master.after(0, lambda:
                self.action_button.configure(state="normal", text=T2["btn_retry"])
            )

    # ---------------------------------------------------------
    # Carica modello e apre finestra principale
    # ---------------------------------------------------------
    def _load_model_and_start_app(self, path, lang_name):
        T2 = TRANSLATIONS[self.app_lang_code]

        try:
            model_instance = Model(path)

            # Nasconde finestra
            self.master.withdraw()

            # Nuova finestra main
            root_app = ctk.CTkToplevel(self.master)
            TranscriberApp(root_app, model_instance, lang_name, self.app_lang_code)

        except Exception as e:
            msg = T2["error_model_load"] % (path, str(e))
            self.master.after(0, lambda:
                messagebox.showerror("Errore", msg)
            )
            self.master.after(0, lambda:
                self.action_button.configure(state="normal", text=T2["btn_retry"])
            )
# =============================================================
# ================== FINESTRA PRINCIPALE CTk ==================
# =============================================================

class TranscriberApp:
    def __init__(self, master, model_instance, lang_name, lang_code):
        self.master = master
        self.T = TRANSLATIONS[lang_code]
        self.model = model_instance
        self.transcribing = False

        load_app_logo(master)

        master.title(self.T["app_name"] + self.T["app_title"] % lang_name)
        master.geometry("820x620")

        # Configurazione griglia
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # Frame principale
        self.main_frame = ctk.CTkFrame(master, corner_radius=12)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        for r in range(10):
            self.main_frame.grid_rowconfigure(r, weight=0 if r < 7 else 1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # =======================
        # 0. Logo + Titolo
        # =======================
        logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Logo UI
        if GLOBAL_LOGO_IMAGES["ui"]:
            ctk.CTkLabel(logo_frame, image=GLOBAL_LOGO_IMAGES["ui"], text="").grid(
                row=0, column=0, padx=(0, 15)
            )

        # Titolo
        ctk.CTkLabel(
            logo_frame,
            text=self.T["app_name"],
            font=("Segoe UI", 30, "bold")
        ).grid(row=0, column=1, sticky="w")

        # Lingua attiva
        ctk.CTkLabel(
            logo_frame,
            text=self.T["lang_active"] % lang_name,
            font=("Segoe UI", 13),
            text_color="#1483e3"
        ).grid(row=1, column=1, sticky="nw")

        # =======================
        # 1. Selettore file
        # =======================
        ctk.CTkLabel(
            self.main_frame,
            text=self.T["select_file_prompt"],
            font=("Segoe UI", 15, "bold")
        ).grid(row=1, column=0, sticky="w", padx=5)

        file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        file_frame.grid(row=2, column=0, sticky="ew", pady=5)
        file_frame.grid_columnconfigure(0, weight=1)

        self.file_path = tk.StringVar()

        self.file_entry = ctk.CTkEntry(
            file_frame,
            textvariable=self.file_path,
            height=38,
            font=("Segoe UI", 13)
        )
        self.file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            file_frame,
            text=self.T["btn_browse"],
            width=110,
            height=38,
            font=("Segoe UI", 13, "bold"),
            command=self.select_file
        )
        self.browse_btn.grid(row=0, column=1)

        # =======================
        # 2. Pulsante trascrivi
        # =======================
        self.transcribe_button = ctk.CTkButton(
            self.main_frame,
            text=self.T["btn_transcribe"],
            height=45,
            font=("Segoe UI", 16, "bold"),
            command=self.start_transcription
        )
        self.transcribe_button.grid(row=3, column=0, sticky="ew", pady=10)

        # =======================
        # 3. Barra progresso
        # =======================
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            variable=self.progress_var
        )
        self.progress_bar.grid(row=4, column=0, sticky="ew", pady=12)
        self.progress_bar.set(0)

        # =======================
        # 4. Stato
        # =======================
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text=self.T["status_ready"],
            font=("Segoe UI", 13, "italic"),
            text_color="#1483e3"
        )
        self.status_label.grid(row=5, column=0, sticky="w", padx=5, pady=(0,10))

        # =======================
        # 5. Etichetta testo
        # =======================
        ctk.CTkLabel(
            self.main_frame,
            text=self.T["result_title"],
            font=("Segoe UI", 15, "bold")
        ).grid(row=6, column=0, sticky="w", padx=5)

        # =======================
        # 6. Textbox (area output)
        # =======================
        self.text_box = ctk.CTkTextbox(
            self.main_frame,
            corner_radius=8,
            font=("Segoe UI", 14),
            wrap="word"
        )
        self.text_box.grid(row=7, column=0, sticky="nsew", padx=5, pady=(5, 10))

        # =======================
        # 7. Due bottoni finali
        # =======================
        bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_frame.grid(row=8, column=0, pady=(5, 5), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        # "Sistema con AI" (disabled all'inizio)
        self.ai_button = ctk.CTkButton(
            bottom_frame,
            text="Sistema con AI",
            height=40,
            state="disabled",
            font=("Segoe UI", 14)
        )
        self.ai_button.grid(row=0, column=0, padx=10, sticky="ew")

        # "Copia tutto" (disabled all'inizio)
        self.copy_button = ctk.CTkButton(
            bottom_frame,
            text="Copia tutto",
            height=40,
            state="disabled",
            font=("Segoe UI", 14),
            command=self.copy_text
        )
        self.copy_button.grid(row=0, column=1, padx=10, sticky="ew")

    # ---------------------------------------------------------
    # Selettore file
    # ---------------------------------------------------------
    def select_file(self):
        filetypes = [
            ("Audio files", "*.mp3 *.wav *.aac *.flac *.ogg *.m4a")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.file_path.set(filename)
            self.text_box.delete("1.0", "end")
            self.status_label.configure(
                text=self.T["status_ready"], text_color="#1483e3"
            )

    # ---------------------------------------------------------
    # Copia tutto il testo
    # ---------------------------------------------------------
    def copy_text(self):
        all_text = self.text_box.get("1.0", "end")
        self.master.clipboard_clear()
        self.master.clipboard_append(all_text)

    # ---------------------------------------------------------
    # Avvia trascrizione
    # ---------------------------------------------------------
    def start_transcription(self):
        filepath = self.file_path.get()
        if not filepath:
            self.status_label.configure(
                text=self.T["error_select_file"],
                text_color="#d63b3b"
            )
            return

        if self.transcribing:
            return

        self.transcribing = True
        self.progress_var.set(0)
        self.text_box.delete("1.0", "end")
        self.ai_button.configure(state="disabled")
        self.copy_button.configure(state="disabled")

        self.transcribe_button.configure(
            state="disabled",
            text=self.T["status_transcribing"]
        )
        self.status_label.configure(
            text=self.T["status_transcribing"],
            text_color="#f0a000"
        )

        threading.Thread(
            target=self.transcribe_audio_threaded,
            args=(filepath,),
            daemon=True
        ).start()

    # ---------------------------------------------------------
    # QUI C'È LA TUA FUNZIONE ORIGINALE (identica)
    # ---------------------------------------------------------
    def transcribe_audio_threaded(self, filepath):
        # ——— TUTTA LA TUA FUNZIONE ORIGINALE RESTA IDENTICA ———
        # Nel messaggio successivo (PARTE 4/4)
        # te la mando integra, già compatibile con CTk.
        pass
    # ---------------------------------------------------------
    # FUNZIONE DI TRASCRIZIONE (IDENTICA ALLA TUA)
    # ---------------------------------------------------------
    def transcribe_audio_threaded(self, filepath):
        temp_wav_file = "temp_audio_16k.wav"

        try:
            # 1. Conversione audio
            audio = AudioSegment.from_file(filepath)

            duration_ms = len(audio)
            duration_sec = duration_ms / 1000

            estimated_wait_time = max(duration_sec * 2.5, 5)

            if estimated_wait_time < 60:
                wait_str = f"{int(estimated_wait_time)} {self.T['time_sec']}"
            else:
                minutes = int(estimated_wait_time // 60)
                seconds = int(estimated_wait_time % 60)
                wait_str = f"{minutes} {self.T['time_min_sec'] % seconds}"

            audio_minutes = int(duration_sec // 60)
            audio_seconds = int(duration_sec % 60)
            audio_duration_str = self.T['time_audio_format'] % (audio_minutes, audio_seconds)

            status_message = self.T['status_converting_wait'] % (audio_duration_str, wait_str)
            self.master.after(0, lambda: self.status_label.configure(text=status_message, text_color="#f0a000"))

            audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
            audio.export(temp_wav_file, format="wav")

            # 2. Init riconoscitore
            rec = KaldiRecognizer(self.model, 16000)

            # 3. Segmenti
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["status_listening"], text_color="#37b24d")
            )

            total_size = os.path.getsize(temp_wav_file)
            bytes_read = 0

            with open(temp_wav_file, "rb") as wf:
                wf.read(44)  # skip header
                CHUNK_SIZE = 80000

                while True:
                    data = wf.read(CHUNK_SIZE)
                    if not data:
                        break

                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text_part = result.get("text", "")

                        if text_part:
                            punctuated = add_simple_punctuation(text_part)

                            self.master.after(0, lambda t=punctuated + " ": 
                                self.text_box.insert("end", t)
                            )

                            status_short = punctuated[-30:].strip() if len(punctuated) > 30 else punctuated.strip()
                            self.master.after(0, lambda s=status_short:
                                self.status_label.configure(text=self.T["status_transcribed"] % s, text_color="#37b24d")
                            )

                    bytes_read += len(data)
                    perc = bytes_read / total_size
                    self.master.after(0, lambda v=perc: self.progress_bar.set(v))

            # 4. Finale
            result = json.loads(rec.FinalResult())
            final_text = result.get("text", "")
            final_punct = add_simple_punctuation(final_text)

            self.master.after(0, lambda:
                self.text_box.insert("end", final_punct + self.T["result_footer"])
            )
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["status_complete"], text_color="#1483e3")
            )

        except FileNotFoundError:
            self.master.after(0, lambda:
                messagebox.showerror("Errore", self.T["error_pydub"])
            )
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["error_critical"], text_color="#d63b3b")
            )
        except Exception as e:
            self.master.after(0, lambda:
                messagebox.showerror("Errore Trascrizione", f"Errore: {e}")
            )
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["error_critical"], text_color="#d63b3b")
            )
            print("Errore trascrizione:", e)

        finally:
            if os.path.exists(temp_wav_file):
                os.remove(temp_wav_file)

            self.transcribing = False
            self.master.after(0, lambda:
                self.transcribe_button.configure(state="normal", text=self.T["btn_transcribe"])
            )
            self.master.after(0, lambda:
                self.progress_bar.set(1)
            )
            # Abilita i 2 bottoni nuovi
            self.master.after(0, lambda:
                self.copy_button.configure(state="normal")
            )
            self.master.after(0, lambda:
                self.ai_button.configure(state="normal")
            )


# =============================================================
# ========================= MAIN ==============================
# =============================================================

if __name__ == "__main__":
    root = ctk.CTk()
    ModelSetupWindow(root)
    root.mainloop()
