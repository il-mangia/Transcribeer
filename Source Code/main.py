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
from PIL import Image, ImageTk
import requests
import webbrowser

# ============================
#  CARICAMENTO TRADUZIONI JSON
# ============================

TRANSLATION_FILE = "translations.json"

def load_translations():
    if not os.path.exists(TRANSLATION_FILE):
        raise FileNotFoundError("translations.json non trovato!")
    with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

TRANSLATIONS = load_translations()

# ============================
#  RILEVAZIONE AUTOMATICA LINGUA OS
# ============================

def get_system_language_code():
    try:
        lang = locale.getdefaultlocale()[0]
        if not lang:
            return "it"
        lang = lang.split("_")[0].lower()
        if lang in TRANSLATIONS:
            return lang
        # mapping lingue simili
        if lang.startswith("en"): return "en"
        if lang.startswith("it"): return "it"
        if lang.startswith("fr"): return "fr"
        if lang.startswith("es"): return "es"
        if lang.startswith("pt"): return "pt"
        if lang.startswith("de"): return "de"
        if lang.startswith("ru"): return "ru"
        if lang.startswith("zh") or lang.startswith("cn"): return "cn"
    except:
        pass
    return "it"

DEFAULT_LANGUAGE_CODE = get_system_language_code()
T = TRANSLATIONS.get(DEFAULT_LANGUAGE_CODE, TRANSLATIONS["it"])

# ============================
#  MODEL MAPPING (UI → codice interno)
# ============================

MODEL_MAPPING = {
    TRANSLATIONS["it"]["language_name"]: "it",
    TRANSLATIONS["en"]["language_name"]: "en",
    TRANSLATIONS["cn"]["language_name"]: "cn",
    TRANSLATIONS["ru"]["language_name"]: "ru",
    TRANSLATIONS["fr"]["language_name"]: "fr",
    TRANSLATIONS["de"]["language_name"]: "de",
    TRANSLATIONS["es"]["language_name"]: "es",
    TRANSLATIONS["pt"]["language_name"]: "pt"
}

# ============================
#  MODEL CONFIG (link download)
# ============================

MODEL_CONFIG = {
    "it": {
        "folder": "model_it",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip"
    },
    "en": {
        "folder": "model_en",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    },
    "cn": {
        "folder": "model_cn",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"
    },
    "ru": {
        "folder": "model_ru",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
    },
    "fr": {
        "folder": "model_fr",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"
    },
    "de": {
        "folder": "model_de",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-de-zamia-0.3.zip"
    },
    "es": {
        "folder": "model_es",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
    },
    "pt": {
        "folder": "model_pt",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
    }
}

# ============================
#  GESTIONE SETTINGS (API KEY)
# ============================

SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"gemini_api_key": ""}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"gemini_api_key": ""}

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ============================
#   LOGHI
# ============================

GLOBAL_LOGO_IMAGES = {"ui": None, "icon": None}

def load_app_logo(master):
    try:
        img = Image.open("logo.png").convert("RGBA")
        ui = img.resize((120, 120))
        icon = img.resize((32, 32))
        GLOBAL_LOGO_IMAGES["ui"] = ImageTk.PhotoImage(ui)
        GLOBAL_LOGO_IMAGES["icon"] = ImageTk.PhotoImage(icon)
        master.iconphoto(True, GLOBAL_LOGO_IMAGES["icon"])
    except:
        print("logo.png non trovato.")
# =============================================================
# ============== FINESTRA DI SETUP (CUSTOMTKINTER) ============
# =============================================================

class ModelSetupWindow:
    def __init__(self, master):
        self.master = master
        load_app_logo(master)

        master.title(T["app_name"] + " - " + T["setup_title"])
        master.geometry("480x380")

        # Frame principale
        self.main_frame = ctk.CTkFrame(master, corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titolo
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text=T["setup_prompt"],
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(pady=(10, 15))

        # Lista lingue disponibili dalla traduzione JSON
        lang_names = [TRANSLATIONS[key]["language_name"] for key in TRANSLATIONS]
        default_lang_name = TRANSLATIONS[DEFAULT_LANGUAGE_CODE]["language_name"]

        self.language_var = ctk.StringVar(value=default_lang_name)

        self.language_combo = ctk.CTkOptionMenu(
            self.main_frame,
            values=lang_names,
            variable=self.language_var,
            height=40,
            font=("Segoe UI", 14),
            command=self.check_model_status
        )
        self.language_combo.pack(pady=10, fill="x", padx=10)

        # Barra progresso
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(pady=15, fill="x", padx=10)
        self.progress_bar.set(0)

         # ========== LOADER ANIMATO ==========
        self.loader_frames = []
        self.loader_label = ctk.CTkLabel(self.main_frame, text="")
        try:
            import PIL.ImageSequence as ImageSequence
            gif = Image.open("loader.gif")  # assicurati che il file si chiami così
            for frame in ImageSequence.Iterator(gif):
                fr = frame.copy().resize((64, 64), Image.LANCZOS)
                self.loader_frames.append(ImageTk.PhotoImage(fr))
        except Exception as e:
            print("Errore GIF loader:", e)
            self.loader_frames = []

        self.loader_running = False
        self.loader_index = 0

        # Stato
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text=T["status_verify"],
            font=("Segoe UI", 13, "italic")
        )
        self.status_label.pack(pady=(0, 10))

        # Bottone azione
        self.action_button = ctk.CTkButton(
            self.main_frame,
            text=T["btn_start"],
            command=self.start_model_setup,
            height=42,
            font=("Segoe UI", 14, "bold")
        )
        self.action_button.pack(pady=10, fill="x", padx=20)

        # Avvio controllo iniziale
        self.check_model_status()

    # -----------------------------------------------------------
    # Controllo stato del modello
    # -----------------------------------------------------------
    def check_model_status(self, event=None):
        lang_ui = self.language_var.get()

        # trova il codice modello dal nome lingua UI
        for code, data in TRANSLATIONS.items():
            if data["language_name"] == lang_ui:
                selected_code = code
                break

        # mapping UI → modello Vosk
        model_code = MODEL_MAPPING[lang_ui]
        model_path = MODEL_CONFIG[model_code]["folder"]

        if os.path.exists(model_path):
            self.status_label.configure(text=T["status_found"] % lang_ui)
            self.progress_bar.set(1)
            self.action_button.configure(text=T["btn_start"])
        else:
            self.status_label.configure(text=T["status_not_found"] % lang_ui)
            self.progress_bar.set(0)
            self.action_button.configure(text=T["btn_download_start"])

    # -----------------------------------------------------------
    # Avvio installazione modello
    # -----------------------------------------------------------
    def start_model_setup(self):
        lang_ui = self.language_var.get()

        # trova codice config
        model_code = MODEL_MAPPING[lang_ui]
        config = MODEL_CONFIG[model_code]

        self.lang_code = model_code
        self.TL = TRANSLATIONS.get(model_code, TRANSLATIONS["it"])

        self.action_button.configure(state="disabled")

        if os.path.exists(config["folder"]):
            self.status_label.configure(text=self.TL["status_loading"] % lang_ui)
            threading.Thread(
                target=self._load_model_and_start_app,
                args=(config["folder"], lang_ui),
                daemon=True
            ).start()
        else:
            self.status_label.configure(text=self.TL["status_downloading"] % lang_ui)
            threading.Thread(
                target=self._download_and_extract,
                args=(config, lang_ui),
                daemon=True
            ).start()

    # -----------------------------------------------------------
    # Download + estrazione
    # -----------------------------------------------------------
    def _download_and_extract(self, config, lang_ui):
        url = config["url"]
        folder = config["folder"]

        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()

            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            buffer = io.BytesIO()

            for chunk in r.iter_content(8192):
                if chunk:
                    buffer.write(chunk)
                    downloaded += len(chunk)

                    perc = downloaded / total if total else 0
                    mb1 = downloaded / 1024 / 1024
                    mb2 = total / 1024 / 1024

                    self.master.after(0, lambda v=perc: self.progress_bar.set(v))
                    self.master.after(0, lambda:
                        self.status_label.configure(
                            text=self.TL["status_download_progress"] % (mb1, mb2)
                        )
                    )

            self.master.after(0, lambda:
                self.status_label.configure(text=self.TL["status_extracting"])
            )

            # Estrazione
            with zipfile.ZipFile(buffer) as z:
                folder_name = next(n.split('/')[0] for n in z.namelist() if '/' in n)
                os.makedirs(folder, exist_ok=True)
                z.extractall(folder)

                extracted = os.path.join(folder, folder_name)

                for f in os.listdir(extracted):
                    os.rename(os.path.join(extracted, f), os.path.join(folder, f))

                os.rmdir(extracted)

            self.master.after(0, lambda:
                self._load_model_and_start_app(folder, lang_ui)
            )

        except Exception as e:
            msg = self.TL["error_download_extract"] % str(e)
            self.master.after(0, lambda: messagebox.showerror("Errore", msg))
            self.master.after(0, lambda:
                self.action_button.configure(state="normal", text=self.TL["btn_retry"])
            )

    # -----------------------------------------------------------
    # Caricamento modello + apertura app
    # -----------------------------------------------------------
    def _load_model_and_start_app(self, folder, lang_ui):
        try:
            model = Model(folder)

            self.master.withdraw()

            root_app = ctk.CTkToplevel(self.master)
            TranscriberApp(root_app, model, lang_ui, self.lang_code)

        except Exception as e:
            msg = self.TL["error_model_load"] % (folder, str(e))
            self.master.after(0, lambda:
                messagebox.showerror("Errore", msg)
            )
            self.master.after(0, lambda:
                self.action_button.configure(state="normal", text=self.TL["btn_retry"])
            )
# =============================================================
# ================== FINESTRA PRINCIPALE CTk ==================
# =============================================================

class TranscriberApp:
    def __init__(self, master, model_instance, lang_ui, lang_code):
        self.master = master
        self.model = model_instance
        self.lang_ui = lang_ui
        self.lang_code = lang_code
        self.T = TRANSLATIONS.get(lang_code, TRANSLATIONS["it"])

        self.transcribing = False

        load_app_logo(master)

        master.title(self.T["app_name"] + self.T["app_title"] % lang_ui)
        master.geometry("900x650")

        # Griglia finestra
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(master, corner_radius=12)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Imposta griglia interna
        for r in range(12):
            self.main_frame.grid_rowconfigure(r, weight=0 if r < 8 else 1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # =======================
        # LOGO + TITOLO
        # =======================
        logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="w", pady=(0, 15))

        if GLOBAL_LOGO_IMAGES["ui"]:
            ctk.CTkLabel(
                logo_frame,
                image=GLOBAL_LOGO_IMAGES["ui"],
                text=""
            ).grid(row=0, column=0, padx=(0, 20))

        ctk.CTkLabel(
            logo_frame,
            text=self.T["app_name"],
            font=("Segoe UI", 34, "bold")
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            logo_frame,
            text=self.T["lang_active"] % lang_ui,
            font=("Segoe UI", 14),
            text_color="#0095ff"
        ).grid(row=1, column=1, sticky="nw")

        # =======================
        # SELEZIONE FILE
        # =======================
        ctk.CTkLabel(
            self.main_frame,
            text=self.T["select_file_prompt"],
            font=("Segoe UI", 16, "bold")
        ).grid(row=1, column=0, sticky="w", padx=5)

        file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        file_frame.grid(row=2, column=0, sticky="ew", pady=(5, 10))
        file_frame.grid_columnconfigure(0, weight=1)

        self.file_path = tk.StringVar()

        self.file_entry = ctk.CTkEntry(
            file_frame,
            textvariable=self.file_path,
            font=("Segoe UI", 14),
            height=40
        )
        self.file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            file_frame,
            text=self.T["btn_browse"],
            font=("Segoe UI", 14, "bold"),
            width=120,
            height=40,
            command=self.select_file
        )
        self.browse_btn.grid(row=0, column=1)

        # =======================
        # BOTTONE TRASCRIZIONE
        # =======================
        self.transcribe_button = ctk.CTkButton(
            self.main_frame,
            text=self.T["btn_transcribe"],
            font=("Segoe UI", 18, "bold"),
            height=50,
            command=self.start_transcription
        )
        self.transcribe_button.grid(row=3, column=0, sticky="ew", pady=(5, 15))

        # =======================
        # BARRA PROGRESSO
        # =======================
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            variable=self.progress_var
        )
        self.progress_bar.grid(row=4, column=0, sticky="ew", pady=(10, 10))
        self.progress_bar.set(0)

        # =======================
        # STATO
        # =======================
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text=self.T["status_ready"],
            font=("Segoe UI", 14, "italic"),
            text_color="#0095ff"
        )
        self.status_label.grid(row=5, column=0, sticky="w", padx=5)

        # =======================
        # RISULTATO (TEXTBOX)
        # =======================
        ctk.CTkLabel(
            self.main_frame,
            text=self.T["result_title"],
            font=("Segoe UI", 17, "bold")
        ).grid(row=6, column=0, sticky="w", padx=5, pady=(10, 5))

        self.text_box = ctk.CTkTextbox(
            self.main_frame,
            corner_radius=10,
            font=("Segoe UI", 15),
            wrap="word"
        )
        self.text_box.grid(row=7, column=0, sticky="nsew", padx=5, pady=(5, 5))

        # --- abilita la griglia a crescere ---
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(7, weight=1)

        # =======================
        # BOTTONI FINALI
        # =======================
        bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_frame.grid(row=8, column=0, sticky="ew", pady=(10, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        # AI
        self.ai_button = ctk.CTkButton(
            bottom_frame,
            text="AI",
            font=("Segoe UI", 15),
            height=44,
            state="disabled",
            command=self.use_ai_system
        )
        self.ai_button.grid(row=0, column=0, sticky="ew", padx=5)

        # COPY
        self.copy_button = ctk.CTkButton(
            bottom_frame,
            text="Copy",
            font=("Segoe UI", 15),
            height=44,
            state="disabled",
            command=self.copy_text
        )
        self.copy_button.grid(row=0, column=1, sticky="ew", padx=10)
    # ---------------------------------------------------------
    # FILE PICKER
    # ---------------------------------------------------------
    def select_file(self):
        types = [("Audio files", "*.mp3 *.wav *.m4a *.ogg *.flac")]
        f = filedialog.askopenfilename(filetypes=types)
        if f:
            self.file_path.set(f)
            self.text_box.delete("1.0", "end")
            self.status_label.configure(text=self.T["status_ready"], text_color="#0095ff")

    # ---------------------------------------------------------
    # COPY TEXT
    # ---------------------------------------------------------
    def copy_text(self):
        txt = self.text_box.get("1.0", "end")
        self.master.clipboard_clear()
        self.master.clipboard_append(txt)

    # ---------------------------------------------------------
    # ANIMATE LOADER
    # ---------------------------------------------------------
    def animate_loader(self):
        if not self.loader_running:
            return
        if self.loader_frames:
            self.loader_label.configure(image=self.loader_frames[self.loader_index])
            self.loader_index = (self.loader_index + 1) % len(self.loader_frames)
        self.master.after(70, self.animate_loader)


    # ---------------------------------------------------------
    # START TRANSCRIPTION
    # ---------------------------------------------------------
    def start_transcription(self):
        fp = self.file_path.get()
        if not fp:
            self.status_label.configure(
                text=self.T["error_select_file"],
                text_color="#ff4444"
            )
            return

        if self.transcribing:
            return

        self.transcribing = True
        self.progress_var.set(0)
        self.text_box.delete("1.0", "end")

        # disabilita bottoni
        self.ai_button.configure(state="disabled")
        self.copy_button.configure(state="disabled")
        self.transcribe_button.configure(state="disabled")

        self.status_label.configure(
            text=self.T["status_transcribing"],
            text_color="#ffaa00"
        )
        self.transcribe_button.configure(text=self.T["status_transcribing"])

        # Mostra il loader
        self.loader_running = True
        self.loader_label.grid(row=5, column=0, sticky="e", padx=10)
        self.animate_loader()

        threading.Thread(
            target=self.transcribe_audio_threaded,
            args=(fp,),
            daemon=True
        ).start()

    # ---------------------------------------------------------
    # PUNTEGGIATURA EASY
    # ---------------------------------------------------------
    def add_simple_punctuation(self, t):
        if not t:
            return t
        t = t.strip()
        if not t:
            return t
        t = t[0].upper() + t[1:]
        if len(t.split()) > 3 and t[-1] not in ".?!":
            t += "."
        return t

    # ---------------------------------------------------------
    # MAIN TRANSCRIPTION FUNCTION (THREAD)
    # ---------------------------------------------------------
    def transcribe_audio_threaded(self, filepath):
        temp_wav_file = "temp_audio_16k.wav"
        self.loader_running = False
        self.loader_label.grid_forget()
        try:
            # 1) Conversione audio
            audio = AudioSegment.from_file(filepath)

            duration_ms = len(audio)
            duration_sec = duration_ms / 1000

            estimated_wait = max(duration_sec * 2.5, 5)

            if estimated_wait < 60:
                wait_str = f"{int(estimated_wait)} {self.T['time_sec']}"
            else:
                minutes = int(estimated_wait // 60)
                seconds = int(estimated_wait % 60)
                wait_str = f"{minutes} {self.T['time_min_sec'] % seconds}"

            audio_minutes = int(duration_sec // 60)
            audio_seconds = int(duration_sec % 60)
            audio_dur_str = self.T['time_audio_format'] % (audio_minutes, audio_seconds)

            msg = self.T['status_converting_wait'] % (audio_dur_str, wait_str)
            self.master.after(0, lambda:
                self.status_label.configure(text=msg, text_color="#ffaa00")
            )

            # converti
            audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
            audio.export(temp_wav_file, format="wav")

            # 2) Setup riconoscitore Vosk
            rec = KaldiRecognizer(self.model, 16000)

            # 3) Lettura file WAV
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["status_listening"], text_color="#22bb55")
            )

            total_size = os.path.getsize(temp_wav_file)
            bytes_read = 0

            with open(temp_wav_file, "rb") as wf:
                wf.read(44)  # salta header WAV
                CHUNK = 80000

                while True:
                    data = wf.read(CHUNK)
                    if not data:
                        break

                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text_piece = result.get("text", "")

                        if text_piece:
                            punct = self.add_simple_punctuation(text_piece)

                            self.master.after(0, lambda t=punct + " ":
                                self.text_box.insert("end", t)
                            )

                            short = punct[-40:].strip() if len(punct) > 40 else punct
                            self.master.after(0, lambda s=short:
                                self.status_label.configure(
                                    text=self.T["status_transcribed"] % s,
                                    text_color="#22bb55"
                                )
                            )

                    bytes_read += len(data)
                    perc = bytes_read / total_size
                    self.master.after(0, lambda v=perc: self.progress_bar.set(v))

            # 4) Finale
            final_res = json.loads(rec.FinalResult())
            final_text = final_res.get("text", "")
            final_punct = self.add_simple_punctuation(final_text)

            self.master.after(0, lambda:
                self.text_box.insert("end", final_punct + self.T["result_footer"])
            )
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["status_complete"], text_color="#0095ff")
            )

        except Exception as e:
            print("Errore trascrizione:", e)
            self.master.after(0, lambda:
                messagebox.showerror("Errore", f"Errore trascrizione: {e}")
            )
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["error_critical"], text_color="#ff4444")
            )

        finally:
            if os.path.exists(temp_wav_file):
                os.remove(temp_wav_file)

            self.transcribing = False
            self.master.after(0, lambda:
                self.transcribe_button.configure(state="normal", text=self.T["btn_transcribe"])
            )
            self.master.after(0, lambda: self.progress_bar.set(1))

            # abilita pulsanti finali
            self.master.after(0, lambda:
                self.copy_button.configure(state="normal")
            )
            self.master.after(0, lambda:
                self.ai_button.configure(state="normal")
            )
    # =========================================================
    # ====================== SISTEMA AI ========================
    # =========================================================

    def use_ai_system(self):
        """Avvia la finestra per usare AI con Gemini."""
        settings = load_settings()
        api_key = settings.get("gemini_api_key", "")

        if not api_key:
            self.open_api_window()
        else:
            self.process_with_ai(api_key)

    # ---------------------------------------------------------
    # Finestra per inserire la API
    # ---------------------------------------------------------
    def open_api_window(self):
        win = ctk.CTkToplevel(self.master)
        win.title("Gemini API Key")
        win.geometry("420x260")
        win.grab_set()

        ctk.CTkLabel(
            win,
            text="Inserisci la tua API Key Gemini:",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=15)

        api_var = ctk.StringVar()

        entry = ctk.CTkEntry(
            win,
            textvariable=api_var,
            width=350,
            height=40,
            font=("Segoe UI", 14)
        )
        entry.pack(pady=10)

        def salva_api():
            key = api_var.get().strip()
            if not key:
                messagebox.showerror("Errore", "Inserisci una API key valida.")
                return

            settings = load_settings()
            settings["gemini_api_key"] = key
            save_settings(settings)
            win.destroy()
            self.process_with_ai(key)

        ctk.CTkButton(
            win,
            text="Salva",
            height=40,
            command=salva_api,
            font=("Segoe UI", 14)
        ).pack(pady=10)

        def apri_google():
            webbrowser.open("https://aistudio.google.com/api-keys")

        ctk.CTkButton(
            win,
            text="Ottieni API Gemini",
            height=40,
            fg_color="#008cff",
            command=apri_google
        ).pack(pady=10)

    # ---------------------------------------------------------
    # Avvia processo AI
    # ---------------------------------------------------------
    def process_with_ai(self, api_key):
        testo_originale = self.text_box.get("1.0", "end").strip()

        if not testo_originale:
            messagebox.showinfo("Info", "Non c'è testo da migliorare.")
            return

        self.ai_button.configure(state="disabled")
        self.status_label.configure(text=self.T["ai_processing"], text_color="#ffaa00")

        threading.Thread(
            target=self._ai_thread,
            args=(api_key, testo_originale),
            daemon=True
        ).start()

    # ---------------------------------------------------------
    # Thread AI con Gemini
    # ---------------------------------------------------------
    def _ai_thread(self, api_key, testo_originale):

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

            payload = {
                "contents": [{
                    "parts": [{
                        "text":
                        "Migliora la punteggiatura e la naturalezza di questo testo.\n"
                        "Non cambiare significato, non aggiungere nulla.\n"
                        "NON andare a capo.\n"
                        "Rispondi SOLO con il testo corretto.\n"
                        f"Testo: {testo_originale}"
                    }]
                }]
            }

            r = requests.post(url, json=payload)
            r.raise_for_status()

            data = r.json()
            risposta = data["candidates"][0]["content"]["parts"][0]["text"]

            # Salvataggio
            with open("fine_ai.txt", "w", encoding="utf-8") as f:
                f.write(risposta)

            # Aggiornamento UI
            self.master.after(0, lambda:
                self.text_box.delete("1.0", "end")
            )
            self.master.after(0, lambda:
                self.text_box.insert("end", risposta)
            )
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["ai_done"], text_color="#22bb55")
            )

        except Exception as e:
            print("Errore AI:", e)

            with open("temp.txt", "w", encoding="utf-8") as f:
                f.write(testo_originale)

            self.master.after(0, lambda:
                messagebox.showerror("Errore AI", "Qualcosa è andato storto, la trascrizione è salvata in temp.txt")
            )
            self.master.after(0, lambda:
                self.status_label.configure(text=self.T["ai_error"], text_color="#ff4444")
            )

        finally:
            self.master.after(0, lambda:
                self.ai_button.configure(state="normal")
            )


# =============================================================
# ========================= MAIN ==============================
# =============================================================

if __name__ == "__main__":
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    ModelSetupWindow(root)
    root.mainloop()
