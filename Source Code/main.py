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
from PIL import Image, ImageTk, ImageSequence
import requests
import webbrowser

# ============================
#  CARICAMENTO TRADUZIONI JSON
# ============================

TRANSLATION_FILE = "translations.json"

def load_translations():
    if not os.path.exists(TRANSLATION_FILE):
        # Utilizza una traduzione base se il file non è trovato per evitare crash immediati
        print("translations.json non trovato. Uso traduzione di default (italiano).")
        return {"it": {"language_name": "Italiano", "app_name": "App Trascrizione", "setup_title": "Setup Modello", "setup_prompt": "Seleziona la lingua per scaricare il modello di riconoscimento vocale Vosk.", "status_verify": "Verifica stato del modello...", "status_found": "Modello '%s' trovato.", "status_not_found": "Modello '%s' non trovato.", "status_downloading": "Download Modello '%s'...", "status_download_progress": "Scaricati %.2f MB di %.2f MB", "status_extracting": "Estrazione file...", "status_loading": "Caricamento modello '%s'...", "error_download_extract": "Errore download/estrazione: %s", "error_model_load": "Errore caricamento modello da %s: %s", "btn_start": "Avvia", "btn_retry": "Riprova", "btn_download_start": "Scarica e Avvia", "app_title": " - Riconoscimento Vocale (%s)", "lang_active": "Lingua attiva: %s", "select_file_prompt": "Seleziona un file audio:", "btn_browse": "Sfoglia", "btn_transcribe": "Trascrivi", "status_ready": "Pronto per trascrivere.", "status_transcribing": "In Trascrizione...", "status_converting_wait": "Conversione audio (%s) in corso. Attesa stimata: %s", "status_listening": "Ascolto e Riconoscimento...", "status_transcribed": "Riconosciuto: ... %s", "status_complete": "Trascrizione completata.", "error_select_file": "Seleziona un file audio!", "error_critical": "Errore Critico Trascrizione.", "result_title": "Risultato Trascrizione:", "result_footer": " (Fine della trascrizione)", "time_sec": "sec", "time_min_sec": "min e %s sec", "time_audio_format": "%d min e %d sec", "ai_processing": "Elaborazione AI...", "ai_done": "Elaborazione AI completata.", "ai_error": "Errore elaborazione AI."}}
    
    with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

TRANSLATIONS = load_translations()

# ============================
#  RILEVAZIONE AUTOMATICA LINGUA OS
# ============================

def get_system_language_code():
    try:
        # Usa getlocale() invece di getdefaultlocale()
        lang = locale.getlocale()[0]
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
    TRANSLATIONS.get("it", {}).get("language_name", "Italiano"): "it",
    TRANSLATIONS.get("en", {}).get("language_name", "English"): "en",
    TRANSLATIONS.get("cn", {}).get("language_name", "Chinese"): "cn",
    TRANSLATIONS.get("ru", {}).get("language_name", "Russian"): "ru",
    TRANSLATIONS.get("fr", {}).get("language_name", "French"): "fr",
    TRANSLATIONS.get("de", {}).get("language_name", "German"): "de",
    TRANSLATIONS.get("es", {}).get("language_name", "Spanish"): "es",
    TRANSLATIONS.get("pt", {}).get("language_name", "Portuguese"): "pt"
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
#  LOGHI
# ============================

GLOBAL_LOGO_IMAGES = {"ui": None, "icon": None}

def load_app_logo(master):
    try:
        img = Image.open("logo.png").convert("RGBA")
        ui = img.resize((120, 120))
        icon = img.resize((32, 32))
        
        # Usa CTkImage invece di ImageTk.PhotoImage
        GLOBAL_LOGO_IMAGES["ui"] = ctk.CTkImage(ui, size=(120, 120))
        GLOBAL_LOGO_IMAGES["icon"] = ctk.CTkImage(icon, size=(32, 32))
        
        # Per l'icona della finestra usa ancora PhotoImage
        master.iconphoto(True, ImageTk.PhotoImage(icon))
    except:
        print("logo.png non trovato.")
# =============================================================
# ============== CLASSE PER GIF ANIMATE =======================
# =============================================================

class GifLoader:
    def __init__(self, master, filename, size=(50, 50)):
        self.master = master
        self.filename = filename
        self.size = size
        self.frames = []
        self.frame_index = 0
        self.delay = 0
        self.running = False
        self.label = None
        self.after_id = None

        try:
            img = Image.open(filename)
            for frame in ImageSequence.Iterator(img):
                # Usa CTkImage invece di ImageTk.PhotoImage
                ctk_frame = ctk.CTkImage(
                    frame.resize(size).convert("RGBA"), 
                    size=size # Mantiene la dimensione specificata
                )
                self.frames.append(ctk_frame)
            
            self.delay = img.info.get('duration', 100)
        except Exception as e:
            print(f"Errore nel caricamento della GIF {filename}: {e}")
            self.frames = []

    def start_animation(self, row, column, sticky="ne", padx=10, pady=10):
        if not self.frames:
            return
            
        if self.label is None:
            self.label = ctk.CTkLabel(self.master, text="", corner_radius=10, fg_color="transparent")
            
        self.label.configure(image=self.frames[self.frame_index])
        self.label.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)
        
        self.running = True
        self._animate()

    def _animate(self):
        if not self.running:
            return

        # Passa alla frame successiva
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.label.configure(image=self.frames[self.frame_index])

        # Riprogramma la prossima chiamata
        self.after_id = self.master.after(self.delay, self._animate)

    def stop_animation(self):
        if self.running and self.after_id:
            self.master.after_cancel(self.after_id)
        self.running = False
        if self.label:
            self.label.grid_forget()

# =============================================================
# ============== FINESTRA DI SETUP (CUSTOMTKINTER) ============
# =============================================================

class ModelSetupWindow:
    def __init__(self, master):
        self.master = master
        load_app_logo(master)
        
        self.gif_loader = GifLoader(master, "loader.gif", size=(50, 50)) 

        master.title(T["app_name"] + " - " + T["setup_title"])
        master.geometry("480x380")
        master.resizable(False, False)

        # Frame principale - USA GRID PER TUTTO
        self.main_frame = ctk.CTkFrame(master, corner_radius=12)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configura la griglia del master
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)
        
        # Configura la griglia del main_frame
        self.main_frame.grid_rowconfigure(0, weight=0) # Titolo
        self.main_frame.grid_rowconfigure(1, weight=0) # Combo
        self.main_frame.grid_rowconfigure(2, weight=0) # Progress
        self.main_frame.grid_rowconfigure(3, weight=0) # Status
        self.main_frame.grid_rowconfigure(4, weight=0) # Button
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Titolo
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text=T["setup_prompt"],
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.grid(row=0, column=0, pady=(10, 15), sticky="n")

        # Lista lingue
        lang_names = [TRANSLATIONS[key]["language_name"] for key in TRANSLATIONS if "language_name" in TRANSLATIONS[key]]
        default_lang_name = TRANSLATIONS[DEFAULT_LANGUAGE_CODE]["language_name"]

        self.language_var = ctk.StringVar(value=default_lang_name)

        self.language_combo = ctk.CTkOptionMenu(
            self.main_frame, # Usa CTkOptionMenu
            values=lang_names,
            variable=self.language_var,
            height=40,
            font=("Segoe UI", 14),
            command=self.check_model_status
        )
        self.language_combo.grid(row=1, column=0, pady=10, sticky="ew", padx=10)

        # Barra progresso
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.grid(row=2, column=0, pady=15, sticky="ew", padx=10)
        self.progress_bar.set(0)

        # Stato
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text=T["status_verify"],
            font=("Segoe UI", 13, "italic")
        )
        self.status_label.grid(row=3, column=0, pady=(0, 10), sticky="n")

        # Bottone azione
        self.action_button = ctk.CTkButton(
            self.main_frame,
            text=T["btn_start"],
            command=self.start_model_setup,
            height=42,
            font=("Segoe UI", 14, "bold")
        )
        self.action_button.grid(row=4, column=0, pady=10, sticky="ew", padx=20)

        # Avvio controllo iniziale stato modello
        self.check_model_status() 

    # -----------------------------------------------------------
    # Controllo stato del modello
    # -----------------------------------------------------------
    def check_model_status(self, event=None):
        lang_ui = self.language_var.get() # lingua selezionata nell'UI

        # trova il codice modello dal nome lingua UI
        selected_code = None
        for code, data in TRANSLATIONS.items():
            if data.get("language_name") == lang_ui:
                selected_code = code
                break
        
        if selected_code is None:
             # Caso di fallback se il nome lingua non è nel mapping
             for name, code in MODEL_MAPPING.items():
                 if name == lang_ui:
                     selected_code = code
                     break
             if selected_code is None: return # Non fare nulla se non trova il codice

        model_code = selected_code
        model_path = MODEL_CONFIG[model_code]["folder"]

        if os.path.exists(model_path):
            self.status_label.configure(text=T["status_found"] % lang_ui)
            self.progress_bar.set(1)
            self.action_button.configure(text=T["btn_start"], state="normal")
        else:
            self.status_label.configure(text=T["status_not_found"] % lang_ui)
            self.progress_bar.set(0)
            self.action_button.configure(text=T["btn_download_start"], state="normal")

    # -----------------------------------------------------------
    # Avvio installazione modello
    # -----------------------------------------------------------
    def start_model_setup(self):
        lang_ui = self.language_var.get()
        
        model_code = MODEL_MAPPING.get(lang_ui)
        if not model_code:
            messagebox.showerror("Errore", "Lingua non mappata correttamente.")
            return

        config = MODEL_CONFIG[model_code]

        self.lang_code = model_code
        self.TL = TRANSLATIONS.get(model_code, TRANSLATIONS["it"])

        self.action_button.configure(state="disabled")
        self.language_combo.configure(state="disabled")
        
        # MODIFICA QUESTA RIGA - usa grid sul main_frame invece che sul master
        self.gif_loader.start_animation(row=0, column=0, sticky="ne", padx=10, pady=10)

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

                    self.master.after_idle(lambda v=perc: self.progress_bar.set(v))
                    self.master.after_idle(lambda:
                        self.status_label.configure(
                            text=self.TL["status_download_progress"] % (mb1, mb2)
                        )
                    )

            self.master.after_idle(lambda:
                self.status_label.configure(text=self.TL["status_extracting"])
            )

            # Estrazione
            with zipfile.ZipFile(buffer) as z:
                # Trova la cartella di livello superiore all'interno dello zip (es. 'vosk-model-small-it-0.22')
                top_level_dirs = {n.split('/')[0] for n in z.namelist() if '/' in n}
                if len(top_level_dirs) != 1:
                    raise Exception("Formato ZIP inatteso.")
                folder_name_in_zip = next(iter(top_level_dirs))
                
                os.makedirs(folder, exist_ok=True)
                z.extractall(folder)
                
                # Sposta i contenuti se la cartella estratta è annidata (standard Vosk)
                extracted = os.path.join(folder, folder_name_in_zip)
                if os.path.isdir(extracted):
                    for f in os.listdir(extracted):
                        os.rename(os.path.join(extracted, f), os.path.join(folder, f))
                    os.rmdir(extracted)


            self.master.after_idle(lambda:
                self._load_model_and_start_app(folder, lang_ui)
            )

        except Exception as e:
            msg = self.TL["error_download_extract"] % str(e)
            self.master.after_idle(lambda: messagebox.showerror("Errore", msg))
            
            # Reset UI
            self.master.after_idle(lambda:
                self.action_button.configure(state="normal", text=self.TL["btn_retry"])
            )
            self.master.after_idle(lambda: self.language_combo.configure(state="normal"))
            self.gif_loader.stop_animation() # Ferma GIF


    # -----------------------------------------------------------
    # Caricamento modello + apertura app
    # -----------------------------------------------------------
    def _load_model_and_start_app(self, folder, lang_ui):
        try:
            model = Model(folder)

            self.master.after_idle(self.master.withdraw)
            self.gif_loader.stop_animation() # Ferma GIF prima di nascondere

            root_app = ctk.CTkToplevel(self.master)
            TranscriberApp(root_app, model, lang_ui, self.lang_code)

        except Exception as e:
            msg = self.TL["error_model_load"] % (folder, str(e))
            self.master.after_idle(lambda:
                messagebox.showerror("Errore", msg)
            )
            # Reset UI
            self.master.after_idle(lambda:
                self.action_button.configure(state="normal", text=self.TL["btn_retry"])
            )
            self.master.after_idle(lambda: self.language_combo.configure(state="normal"))
            self.gif_loader.stop_animation() # Ferma GIF

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
        self.ai_processing = False

        load_app_logo(master)
        
        # Inizializza il loader GIF per l'app principale
        self.gif_loader = GifLoader(master, "loader.gif", size=(50, 50)) 

        master.title(self.T["app_name"] + self.T["app_title"] % lang_ui)
        master.geometry("900x650")
        master.minsize(800, 600)

        # Griglia finestra
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(master, corner_radius=12)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Imposta griglia interna
        self.main_frame.grid_rowconfigure(0, weight=0)  # Logo/titolo
        self.main_frame.grid_rowconfigure(1, weight=0)  # Seleziona file
        self.main_frame.grid_rowconfigure(2, weight=0)  # File frame
        self.main_frame.grid_rowconfigure(3, weight=0)  # Bottone trascrizione
        self.main_frame.grid_rowconfigure(4, weight=0)  # Progress bar
        self.main_frame.grid_rowconfigure(5, weight=0)  # Status
        self.main_frame.grid_rowconfigure(6, weight=0)  # Titolo risultato
        self.main_frame.grid_rowconfigure(7, weight=1)  # Textbox (espandibile)
        self.main_frame.grid_rowconfigure(8, weight=0)  # Bottoni finali
        self.main_frame.grid_columnconfigure(0, weight=1)

        # =======================
        # LOGO + TITOLO
        # =======================
        logo_title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        logo_title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        logo_title_frame.grid_columnconfigure(0, weight=0) # Per l'immagine del logo
        logo_title_frame.grid_columnconfigure(1, weight=1) # Per il testo

        if GLOBAL_LOGO_IMAGES["ui"]:
            ctk.CTkLabel(
                logo_title_frame,
                image=GLOBAL_LOGO_IMAGES["ui"],
                text=""
            ).grid(row=0, column=0, rowspan=2, padx=(0, 20), sticky="nw")

        ctk.CTkLabel(
            logo_title_frame,
            text=self.T["app_name"],
            font=("Segoe UI", 34, "bold")
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            logo_title_frame,
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
            text=self.T["ai_processing"],
            font=("Segoe UI", 15),
            height=44,
            state="disabled",
            command=self.use_ai_system
        )
        self.ai_button.grid(row=0, column=0, sticky="ew", padx=5)

        # COPY
        self.copy_button = ctk.CTkButton(
            bottom_frame,
            text=self.T["btn_copy"],
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

        if self.transcribing or self.ai_processing:
            return

        self.transcribing = True
        self.progress_var.set(0)
        self.text_box.delete("1.0", "end")

        # disabilita bottoni
        self.ai_button.configure(state="disabled")
        self.copy_button.configure(state="disabled")
        self.transcribe_button.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        
        # Avvia l'animazione GIF
        self.gif_loader.start_animation(row=0, column=0, sticky="ne", padx=10, pady=10)

        self.status_label.configure(
            text=self.T["status_transcribing"],
            text_color="#ffaa00"
        )
        self.transcribe_button.configure(text=self.T["status_transcribing"])

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

        try:
            # 1) Conversione audio
            audio = AudioSegment.from_file(filepath)

            duration_sec = len(audio) / 1000
            estimated_wait = max(duration_sec * 2.5, 5)

            if estimated_wait < 60:
                wait_str = f"{int(estimated_wait)} {self.T['time_sec']}"
            else:
                minutes = int(estimated_wait // 60)
                seconds = int(estimated_wait % 60)
                wait_str = self.T['time_min_sec'] % seconds
                
            audio_minutes = int(duration_sec // 60)
            audio_seconds = int(duration_sec % 60)
            audio_dur_str = self.T['time_audio_format'] % (audio_minutes, audio_seconds)

            msg = self.T['status_converting_wait'] % (audio_dur_str, wait_str)
            self.master.after_idle(lambda:
                self.status_label.configure(text=msg, text_color="#ffaa00")
            )

            # converti
            audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
            audio.export(temp_wav_file, format="wav")

            # 2) Setup riconoscitore Vosk
            rec = KaldiRecognizer(self.model, 16000)

            # 3) Lettura file WAV
            self.master.after_idle(lambda:
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

                            self.master.after_idle(lambda t=punct + " ":
                                self.text_box.insert("end", t)
                            )

                            short = punct[-40:].strip() if len(punct) > 40 else punct
                            self.master.after_idle(lambda s=short:
                                self.status_label.configure(
                                    text=self.T["status_transcribed"] % s,
                                    text_color="#22bb55"
                                )
                            )

                    bytes_read += len(data)
                    # Non includiamo l'header nel calcolo della percentuale
                    perc = (bytes_read) / (total_size - 44) if total_size > 44 else 0 
                    self.master.after_idle(lambda v=perc: self.progress_bar.set(v))

            # 4) Finale
            final_res = json.loads(rec.FinalResult())
            final_text = final_res.get("text", "")
            final_punct = self.add_simple_punctuation(final_text)

            self.master.after_idle(lambda:
                self.text_box.insert("end", final_punct + self.T["result_footer"])
            )
            self.master.after_idle(lambda:
                self.status_label.configure(text=self.T["status_complete"], text_color="#0095ff")
            )

        except Exception as e:
            print("Errore trascrizione:", e)
            self.master.after_idle(lambda:
                messagebox.showerror("Errore", f"Errore trascrizione: {e}")
            )
            self.master.after_idle(lambda:
                self.status_label.configure(text=self.T["error_critical"], text_color="#ff4444")
            )

        finally:
            if os.path.exists(temp_wav_file):
                try:
                    os.remove(temp_wav_file)
                except:
                    pass

            self.transcribing = False
            self.master.after_idle(lambda:
                self.transcribe_button.configure(state="normal", text=self.T["btn_transcribe"])
            )
            self.master.after_idle(lambda: self.browse_btn.configure(state="normal"))
            self.master.after_idle(lambda: self.progress_bar.set(1))
            self.gif_loader.stop_animation()

            # abilita pulsanti finali
            self.master.after_idle(lambda:
                self.copy_button.configure(state="normal")
            )
            self.master.after_idle(lambda:
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
        win.geometry("420x300")
        win.grab_set()
        win.resizable(False, False)

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
        ).pack(pady=5)

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

        if self.ai_processing or self.transcribing:
             return

        self.ai_processing = True

        self.ai_button.configure(state="disabled")
        self.copy_button.configure(state="disabled")
        self.transcribe_button.configure(state="disabled")
        
        # Avvia l'animazione GIF
        self.gif_loader.start_animation(row=0, column=0, sticky="ne", padx=10, pady=10)

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
                        "NON andare a capo. Rispondi SOLO con il testo corretto.\n"
                        f"Testo: {testo_originale}"
                    }]
                }]
            }

            r = requests.post(url, json=payload)
            r.raise_for_status()

            data = r.json()
            if 'candidates' not in data or not data['candidates']:
                 raise Exception(f"Risposta API non valida o bloccata. {data}")
            
            risposta = data["candidates"][0]["content"]["parts"][0]["text"]

            # Salvataggio
            with open("fine_ai.txt", "w", encoding="utf-8") as f:
                f.write(risposta)

            # Aggiornamento UI
            self.master.after_idle(lambda:
                self.text_box.delete("1.0", "end")
            )
            self.master.after_idle(lambda:
                self.text_box.insert("end", risposta)
            )
            self.master.after_idle(lambda:
                self.status_label.configure(text=self.T["ai_done"], text_color="#22bb55")
            )

        except Exception as e:
            print("Errore AI:", e)

            # Salvataggio di emergenza
            with open("temp_ai_error.txt", "w", encoding="utf-8") as f:
                 f.write(testo_originale)

            self.master.after_idle(lambda:
                messagebox.showerror("Errore AI", f"Qualcosa è andato storto ({e}), la trascrizione originale è salvata in temp_ai_error.txt")
            )
            self.master.after_idle(lambda:
                self.status_label.configure(text=self.T["ai_error"], text_color="#ff4444")
            )

        finally:
            self.ai_processing = False
            self.gif_loader.stop_animation()
            
            self.master.after_idle(lambda:
                self.ai_button.configure(state="normal")
            )
            self.master.after_idle(lambda:
                self.copy_button.configure(state="normal")
            )
            self.master.after_idle(lambda:
                self.transcribe_button.configure(state="normal")
            )


# =============================================================
# ========================= MAIN ==============================
# =============================================================

if __name__ == "__main__":
    # Verifica che PIL sia installato per la GIF
    try:
        from PIL import Image, ImageTk, ImageSequence
    except ImportError:
        print("Errore: La libreria 'Pillow' (PIL) non è installata. Non è possibile usare GIF animate.")

    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    ModelSetupWindow(root)
    root.mainloop()
