import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import os
import json
import threading
import zipfile
import io
import locale

# Librerie esterne necessarie:
# - requests per il download
# - Pillow (PIL) per la gestione del logo/icona
try:
    import requests
    from PIL import Image, ImageTk
except ImportError as e:
    if 'requests' in str(e):
        print("ERRORE: La libreria 'requests' non è installata. Esegui: pip install requests")
    elif 'PIL' in str(e):
        print("ERRORE: La libreria 'Pillow' (PIL) non è installata. Esegui: pip install Pillow")
    exit()

# Variabile globale per mantenere il riferimento all'oggetto logo (necessario per Tkinter)
# Memorizzerà l'immagine preparata per l'uso come icona (piccola) e l'immagine grande per la UI.
GLOBAL_LOGO_IMAGES = {'icon': None, 'ui': None}

# === DIZIONARIO DI TRADUZIONI UI ===
TRANSLATIONS = {
    'it': {
        'language_name': "Italiano",
        'app_name': "Transcribeer", # Nuovo nome app
        'setup_title': "Setup Modello Vosk",
        'setup_prompt': "Scegli la lingua per la trascrizione:",
        'status_verify': "Verifica modello...",
        'status_found': "✅ Modello '%s' trovato in '%s'.",
        'status_not_found': "⚠️ Modello '%s' non trovato. Pronto per il download.",
        'btn_start': "Avvia Trascrizione",
        'btn_download_start': "Scarica e Avvia",
        'status_loading': "⏳ Caricamento modello '%s'...",
        'status_downloading': "⬇️ Avvio download di '%s'...",
        'status_download_progress': "⬇️ Scaricati: %.2f MB / Totale: %.2f MB",
        'status_extracting': "📦 Estrazione dei file...",
        'btn_retry': "Riprova",
        'app_title': " (Vosk - %s Offline)", # Modificato per usare app_name
        'lang_active': "Lingua Attiva: %s",
        'select_file_prompt': "Seleziona File Audio:",
        'btn_browse': "Sfoglia...",
        'btn_transcribe': "▶️ AVVIA TRASCRIZIONE",
        'status_ready': "Stato: Pronto per la trascrizione.",
        'status_transcribing': "Trascrizione in corso... (Attendere)",
        'status_converting_wait': "⚙️ Stato: Conversione audio di %s (attendere circa %s) ...", # Nuovo status con tempo
        'status_listening': "🎤 Stato: Inizio Trascrizione a segmenti e Aggiunta Punteggiatura...", # AGGIORNATO
        'status_transcribed': "✅ Trascritto: '%s'",
        'status_complete': "🎉 Trascrizione terminata con successo!",
        'result_title': "Trascrizione Risultante (Tempo Reale):",
        'result_footer': "\n\n==============================\nTrascrizione completata con successo.",
        'error_select_file': "❌ ERRORE: Selezionare un file audio prima di avviare.",
        'error_pydub': "Errore di pre-elaborazione. Assicurati che FFmpeg sia installato e configurato nel PATH se stai usando formati complessi (MP3, AAC, ecc.).",
        'error_critical': "❌ ERRORE FATALE: Controlla la console.",
        'error_download_extract': "❌ ERRORE FATALE durante Download/Estrazione: %s",
        'error_model_load': "❌ ERRORE: Impossibile caricare il modello da '%s'. Assicurati che i file siano integri.\nDettagli: %s",
        'error_logo': "❌ ERRORE: File 'logo.png' non trovato nella directory. L'icona non verrà visualizzata.",
        'time_sec': "secondi",
        'time_min_sec': "min e %s sec",
        'time_audio_format': "%sm %ss",
    },
    'en': {
        'language_name': "English (US)",
        'app_name': "Transcribeer",
        'setup_title': "Vosk Model Setup",
        'setup_prompt': "Choose the language for transcription:",
        'status_verify': "Verifying model...",
        'status_found': "✅ Model '%s' found in '%s'.",
        'status_not_found': "⚠️ Model '%s' not found. Ready for download.",
        'btn_start': "Start Transcription",
        'btn_download_start': "Download and Start",
        'status_loading': "⏳ Loading model '%s'...",
        'status_downloading': "⬇️ Starting download of '%s'...",
        'status_download_progress': "⬇️ Downloaded: %.2f MB / Total: %.2f MB",
        'status_extracting': "📦 Extracting files...",
        'btn_retry': "Retry",
        'app_title': " (Vosk - %s Offline)",
        'lang_active': "Active Language: %s",
        'select_file_prompt': "Select Audio File:",
        'btn_browse': "Browse...",
        'btn_transcribe': "▶️ START TRANSCRIPTION",
        'status_ready': "Status: Ready for transcription.",
        'status_transcribing': "Transcription in progress... (Please wait)",
        'status_converting_wait': "⚙️ Status: Converting audio of %s (wait approx. %s) ...",
        'status_listening': "🎤 Status: Starting segment transcription and Adding Punctuation...",
        'status_transcribed': "✅ Transcribed: '%s'",
        'status_complete': "🎉 Transcription successfully finished!",
        'result_title': "Resulting Transcription (Real-Time):",
        'result_footer': "\n\n==============================\nTranscription completed successfully.",
        'error_select_file': "❌ ERROR: Please select an audio file before starting.",
        'error_pydub': "Preprocessing error. Ensure FFmpeg is installed and configured in PATH if you are using complex formats (MP3, AAC, etc.).",
        'error_critical': "❌ FATAL ERROR: Check the console.",
        'error_download_extract': "❌ FATAL ERROR during Download/Extraction: %s",
        'error_model_load': "❌ ERROR: Could not load model from '%s'. Ensure files are intact.\nDetails: %s",
        'error_logo': "❌ ERROR: File 'logo.png' not found in directory. Icon will not be displayed.",
        'time_sec': "seconds",
        'time_min_sec': "min and %s sec",
        'time_audio_format': "%sm %ss",
    },
    'fr': {
        'language_name': "Français",
        'app_name': "Transcribeer",
        'setup_title': "Configuration du Modèle Vosk",
        'setup_prompt': "Choisissez la langue pour la transcription :",
        'status_verify': "Vérification du modèle...",
        'status_found': "✅ Modèle '%s' trouvé dans '%s'.",
        'status_not_found': "⚠️ Modèle '%s' non trouvé. Prêt pour le téléchargement.",
        'btn_start': "Démarrer la Transcription",
        'btn_download_start': "Télécharger et Démarrer",
        'status_loading': "⏳ Chargement du modèle '%s'...",
        'status_downloading': "⬇️ Démarrage du téléchargement de '%s'...",
        'status_download_progress': "⬇️ Téléchargés : %.2f Mo / Total : %.2f Mo",
        'status_extracting': "📦 Extraction des fichiers...",
        'btn_retry': "Réessayer",
        'app_title': " (Vosk - %s Hors Ligne)",
        'lang_active': "Langue Active : %s",
        'select_file_prompt': "Sélectionner le Fichier Audio :",
        'btn_browse': "Parcourir...",
        'btn_transcribe': "▶️ DÉMARRER LA TRANSCRIPTION",
        'status_ready': "Statut : Prêt pour la transcription.",
        'status_transcribing': "Transcription en cours... (Veuillez patienter)",
        'status_converting_wait': "⚙️ Statut : Conversion audio de %s (attendre env. %s) ...",
        'status_listening': "🎤 Statut : Début de la transcription par segment et Ajout de Ponctuation...",
        'status_transcribed': "✅ Transcrit : '%s'",
        'status_complete': "🎉 Transcription terminée avec succès !",
        'result_title': "Transcription Résultante (Temps Réel) :",
        'result_footer': "\n\n==============================\nTranscription terminée avec succès.",
        'error_select_file': "❌ ERREUR : Veuillez sélectionner un fichier audio avant de commencer.",
        'error_pydub': "Erreur de pré-traitement. Assurez-vous que FFmpeg est installé et configuré dans le PATH si vous utilisez des formats complexes (MP3, AAC, etc.).",
        'error_critical': "❌ ERREUR FATALE : Vérifiez la console.",
        'error_download_extract': "❌ ERREUR FATALE lors du téléchargement/extraction : %s",
        'error_model_load': "❌ ERREUR : Impossible de charger le modèle depuis '%s'. Assurez-vous que les fichiers sont intacts.\nDétails: %s",
        'error_logo': "❌ ERREUR : Fichier 'logo.png' non trouvé dans le répertoire. L'icône ne s'affichera pas.",
        'time_sec': "secondes",
        'time_min_sec': "min et %s sec",
        'time_audio_format': "%sm %ss",
    },
    'de': {
        'language_name': "Deutsch",
        'app_name': "Transcribeer",
        'setup_title': "Vosk Modell-Setup",
        'setup_prompt': "Wählen Sie die Sprache für die Transkription:",
        'status_verify': "Modell wird überprüft...",
        'status_found': "✅ Modell '%s' in '%s' gefunden.",
        'status_not_found': "⚠️ Modell '%s' nicht gefunden. Bereit zum Download.",
        'btn_start': "Transkription starten",
        'btn_download_start': "Herunterladen und Starten",
        'status_loading': "⏳ Lade Modell '%s'...",
        'status_downloading': "⬇️ Starte Download von '%s'...",
        'status_download_progress': "⬇️ Heruntergeladen: %.2f MB / Gesamt: %.2f MB",
        'status_extracting': "📦 Dateien werden extrahiert...",
        'btn_retry': "Wiederholen",
        'app_title': " (Vosk - %s Offline)",
        'lang_active': "Aktive Sprache: %s",
        'select_file_prompt': "Audio-Datei auswählen:",
        'btn_browse': "Durchsuchen...",
        'btn_transcribe': "▶️ TRANSKRIPTION STARTEN",
        'status_ready': "Status: Bereit zur Transkription.",
        'status_transcribing': "Transkription läuft... (Bitte warten)",
        'status_converting_wait': "⚙️ Status: Konvertiere Audio von %s (warte ca. %s) ...",
        'status_listening': "🎤 Status: Beginne Segmenttranskription und Füge Zeichensetzung hinzu...",
        'status_transcribed': "✅ Transkribiert: '%s'",
        'status_complete': "🎉 Transkription erfolgreich abgeschlossen!",
        'result_title': "Resultierende Transkription (Echtzeit):",
        'result_footer': "\n\n==============================\nTranskription erfolgreich abgeschlossen.",
        'error_select_file': "❌ FEHLER: Bitte wählen Sie eine Audiodatei aus, bevor Sie starten.",
        'error_pydub': "Fehler bei der Vorverarbeitung. Stellen Sie sicher, dass FFmpeg installiert und im PATH konfiguriert ist, wenn Sie komplexe Formate (MP3, AAC usw.) verwenden.",
        'error_critical': "❌ FATALER FEHLER: Überprüfen Sie die Konsole.",
        'error_download_extract': "❌ FATALER FEHLER beim Download/Extrahieren: %s",
        'error_model_load': "❌ FEHLER: Konnte Modell nicht von '%s' laden. Stellen Sie sicher, dass die Dateien intakt sind.\nDettails: %s",
        'error_logo': "❌ FEHLER: Datei 'logo.png' im Verzeichnis nicht gefunden. Das Symbol wird nicht angezeigt.",
        'time_sec': "Sekunden",
        'time_min_sec': "Min und %s Sek",
        'time_audio_format': "%sm %ss",
    },
    'es': {
        'language_name': "Español",
        'app_name': "Transcribeer",
        'setup_title': "Configuración del Modelo Vosk",
        'setup_prompt': "Elija el idioma para la transcripción:",
        'status_verify': "Verificando modelo...",
        'status_found': "✅ Modelo '%s' encontrado en '%s'.",
        'status_not_found': "⚠️ Modelo '%s' no encontrado. Listo para descargar.",
        'btn_start': "Iniciar Transcripción",
        'btn_download_start': "Descargar e Iniciar",
        'status_loading': "⏳ Cargando modelo '%s'...",
        'status_downloading': "⬇️ Iniciando descarga de '%s'...",
        'status_download_progress': "⬇️ Descargados: %.2f MB / Total: %.2f MB",
        'status_extracting': "📦 Extrayendo archivos...",
        'btn_retry': "Reintentar",
        'app_title': " (Vosk - %s sin Conexión)",
        'lang_active': "Idioma Activo: %s",
        'select_file_prompt': "Seleccionar Archivo de Audio:",
        'btn_browse': "Explorar...",
        'btn_transcribe': "▶️ INICIAR TRANSCRIPCIÓN",
        'status_ready': "Estado: Listo para la transcripción.",
        'status_transcribing': "Transcribiendo... (Espere por favor)",
        'status_converting_wait': "⚙️ Estado: Convirtiendo audio de %s (espere aprox. %s) ...",
        'status_listening': "🎤 Estado: Iniciando transcripción por segmento y Añadiendo Puntuación...",
        'status_transcribed': "✅ Transcrito: '%s'",
        'status_complete': "🎉 ¡Transcipción finalizada con éxito!",
        'result_title': "Transcripción Resultante (Tiempo Real):",
        'result_footer': "\n\n==============================\nTranscripción finalizada con éxito.",
        'error_select_file': "❌ ERROR: Seleccione un archivo de audio antes de comenzar.",
        'error_pydub': "Error de preprocesamiento. Asegúrese de que FFmpeg esté instalado y configurado en el PATH si está utilizando formatos complejos (MP3, AAC, etc.).",
        'error_critical': "❌ ERROR FATAL: Revise la consola.",
        'error_download_extract': "❌ ERROR FATAL durante la Descarga/Extracción: %s",
        'error_model_load': "❌ ERROR: No se pudo cargar el modelo desde '%s'. Asegúrese de que los archivos estén intactos.\nDettalles: %s",
        'error_logo': "❌ ERRORE: File 'logo.png' non trovato nella directory. L'icona non verrà visualizzata.",
        'time_sec': "segundos",
        'time_min_sec': "min y %s seg",
        'time_audio_format': "%sm %ss",
    }
}

# === Configurazione dei Modelli e URL di Download ===
MODEL_MAPPING = {
    TRANSLATIONS['it']['language_name']: 'it',
    TRANSLATIONS['en']['language_name']: 'en',
    TRANSLATIONS['fr']['language_name']: 'fr',
    TRANSLATIONS['de']['language_name']: 'de',
    TRANSLATIONS['es']['language_name']: 'es',
}

MODEL_CONFIG = {
    'it': {
        "folder": "model_it",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip"
    },
    'en': {
        "folder": "model_en",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    },
    'fr': {
        "folder": "model_fr",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"
    },
    'de': {
        "folder": "model_de",
        "url": "https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip"
    },
    'es': {
        "folder": "model_es",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
    }
}

# Tentativo di rilevare la lingua di default del sistema (locale)
def get_system_default_language_code():
    """Tenta di rilevare il codice lingua del sistema operativo e lo mappa ai codici supportati."""
    try:
        lang_code = locale.getdefaultlocale()[0].split('_')[0]
        if lang_code in MODEL_CONFIG:
            return lang_code
    except Exception:
        pass
    return 'it' # Default di fallback

DEFAULT_LANGUAGE_CODE = get_system_default_language_code()
T = TRANSLATIONS[DEFAULT_LANGUAGE_CODE] # Abbreviazione per il dizionario delle traduzioni attive

# Configurazione del look and feel
FONT_FAMILY = "Segoe UI" 
PADDING = 15
LOGO_SIZE = 80 # Dimensione del logo nell'interfaccia principale

# === FUNZIONE DI POST-ELABORAZIONE PER LA PUNTEGGIATURA ===
def add_simple_punctuation(text):
    """
    Simula l'aggiunta di punteggiatura e capitalizzazione di base.
    Vosk non fornisce la punteggiatura di default, quindi si esegue una post-elaborazione.
    """
    if not text:
        return text
    
    # 1. Pulizia e capitalizzazione
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]

    # 2. Aggiungi punteggiatura di fine frase se assente
    last_char = text[-1] if text else ''
    if last_char not in ['.', '?', '!', '...']:
        # Regola semplice: se la frase ha più di 3 parole, aggiungi un punto.
        if len(text.split()) > 3: 
            text += '.'
            
    # 3. Pulizia degli spazi intorno alla punteggiatura
    text = text.replace(' .', '.').replace(' ,', ',').replace(' ?', '?').replace(' !', '!')
    
    return text.replace('..', '.') # Evita doppi punti

# === FINE FUNZIONE DI POST-ELABORAZIONE ===

def load_app_logo(master):
    """Carica il logo.png, lo imposta come icona della finestra e memorizza il riferimento per la UI."""
    global GLOBAL_LOGO_IMAGES
    T_local = TRANSLATIONS[get_system_default_language_code()] # Usa le traduzioni dell'OS per l'errore

    if GLOBAL_LOGO_IMAGES['icon']:
        # Se l'immagine è già stata caricata per la root, usala per i Toplevel
        master.iconphoto(True, GLOBAL_LOGO_IMAGES['icon'])
        return

    try:
        # Carica l'immagine usando PIL
        img = Image.open("logo.png")
        
        # 1. Icona (32x32)
        icon_image_tk = ImageTk.PhotoImage(img.resize((32, 32), Image.LANCZOS))
        GLOBAL_LOGO_IMAGES['icon'] = icon_image_tk
        master.iconphoto(True, icon_image_tk) 
        
        # 2. Immagine UI (LOGO_SIZE x LOGO_SIZE)
        ui_image_tk = ImageTk.PhotoImage(img.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS))
        GLOBAL_LOGO_IMAGES['ui'] = ui_image_tk

    except FileNotFoundError:
        print(T_local['error_logo'])
    except Exception as e:
        print(f"Errore durante il caricamento del logo: {e}")

class ModelSetupWindow:
    """Finestra iniziale per la selezione della lingua e il download/caricamento del modello."""
    def __init__(self, master):
        self.master = master
        
        # Imposta l'icona e il titolo
        load_app_logo(master)
        master.title(T['app_name'] + " - " + T['setup_title'])
        master.geometry("400x300")
        
        # Configurazione del tema
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#e0e0e0')
        style.configure('TButton', font=(FONT_FAMILY, 10, 'bold'), padding=10, background='#4CAF50', foreground='white')
        style.map('TButton', background=[('active', '#45a049')])

        # Ottiene la lista dei nomi delle lingue da visualizzare nel Combobox
        lang_names = list(MODEL_MAPPING.keys())
        default_lang_name = TRANSLATIONS[DEFAULT_LANGUAGE_CODE]['language_name']
        self.language_var = tk.StringVar(value=default_lang_name)
        
        main_frame = ttk.Frame(master, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text=T['setup_prompt'], 
                  font=(FONT_FAMILY, 14, 'bold')).pack(pady=10)

        # Combo per la selezione della lingua
        self.language_combo = ttk.Combobox(main_frame, textvariable=self.language_var, 
                                           values=lang_names, state='readonly', 
                                           font=(FONT_FAMILY, 12))
        self.language_combo.pack(pady=10, fill='x')
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate", variable=self.progress_var)
        self.progress_bar.pack(pady=10, fill='x')
        
        self.status_label = ttk.Label(main_frame, text=T['status_verify'], 
                                      foreground='#007acc', font=(FONT_FAMILY, 10, 'italic'))
        self.status_label.pack(pady=5)
        
        self.action_button = ttk.Button(main_frame, text=T['btn_start'], command=self.start_model_setup)
        self.action_button.pack(pady=15)

        # Avvia la verifica iniziale al caricamento
        self.language_combo.bind("<<ComboboxSelected>>", self.check_model_status)
        self.check_model_status()

    def check_model_status(self, event=None):
        """Verifica se il modello selezionato è già installato e aggiorna la UI."""
        lang_name = self.language_var.get()
        lang_code = MODEL_MAPPING[lang_name]
        model_path = MODEL_CONFIG[lang_code]['folder']
        
        # Aggiorna le traduzioni in base alla lingua selezionata per i messaggi futuri
        self.T = TRANSLATIONS[DEFAULT_LANGUAGE_CODE] # Usa le traduzioni dell'OS per i messaggi di stato
        
        if os.path.exists(model_path) and os.path.isdir(model_path):
            status_text = self.T['status_found'] % (lang_name, model_path)
            self.status_label.config(text=status_text, foreground='#4CAF50')
            self.action_button.config(text=self.T['btn_start'], state=tk.NORMAL)
            self.progress_bar.stop()
            self.progress_var.set(100)
        else:
            status_text = self.T['status_not_found'] % lang_name
            self.status_label.config(text=status_text, foreground='#ff9800')
            self.action_button.config(text=self.T['btn_download_start'], state=tk.NORMAL)
            self.progress_bar.stop()
            self.progress_var.set(0)

    def start_model_setup(self):
        """Avvia il caricamento o il download del modello in un thread."""
        lang_name = self.language_var.get()
        lang_code = MODEL_MAPPING[lang_name]
        model_info = MODEL_CONFIG[lang_code]
        
        # La lingua attiva per l'applicazione finale sarà quella selezionata qui
        self.app_lang_code = lang_code
        self.T = TRANSLATIONS[lang_code]
        
        if os.path.exists(model_info['folder']):
            # Modello già installato, procedi al caricamento
            self.status_label.config(text=self.T['status_loading'] % lang_name, foreground='#007acc')
            self.action_button.config(state=tk.DISABLED)
            threading.Thread(target=self._load_model_and_start_app, args=(model_info['folder'], lang_name)).start()
        else:
            # Modello da scaricare
            self.status_label.config(text=self.T['status_downloading'] % lang_name, foreground='orange')
            self.action_button.config(state=tk.DISABLED)
            threading.Thread(target=self._download_and_load, args=(model_info, lang_name)).start()
            
    def _download_and_load(self, model_info, lang_name):
        """Scarica e estrae il modello in un thread."""
        url = model_info['url']
        path = model_info['folder']
        
        try:
            # Traduzioni da usare all'interno del thread
            T_thread = TRANSLATIONS[self.app_lang_code]
            
            # 1. Download del file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded_bytes = 0
            zip_bytes = io.BytesIO()
            
            self.master.after(0, lambda: self.progress_bar.config(mode='determinate'))
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    zip_bytes.write(chunk)
                    downloaded_bytes += len(chunk)
                    
                    # Aggiornamento Progresso
                    progress = (downloaded_bytes / total_size) * 100 if total_size else 0
                    self.master.after(0, lambda p=progress: self.progress_var.set(p))
                    
                    # Aggiornamento Stato in MB
                    total_mb = total_size / (1024*1024)
                    downloaded_mb = downloaded_bytes / (1024*1024)
                    status_text = T_thread['status_download_progress'] % (downloaded_mb, total_mb)
                    self.master.after(0, lambda d=status_text: self.status_label.config(text=d, foreground='orange'))
            
            # 2. Estrazione del file
            self.master.after(0, lambda: self.status_label.config(text=T_thread['status_extracting'], foreground='purple'))
            
            # Controlla il nome della cartella interna nel file zip (Vosk usa una struttura con doppia cartella)
            with zipfile.ZipFile(zip_bytes) as z:
                # Trova la cartella principale nel zip
                folder_name = next(name.split('/')[0] for name in z.namelist() if '/' in name)
                
                # Crea la cartella di destinazione
                os.makedirs(path, exist_ok=True)
                
                # Estrai tutti i file nella cartella temporanea (path è la cartella model_XX)
                z.extractall(path=path)
                
                # Rinomina la cartella estratta (es. vosk-model-small-it-0.22) al nome finale (model_it)
                extracted_path = os.path.join(path, folder_name)
                
                # Sposta i contenuti della cartella estratta alla cartella finale
                for item in os.listdir(extracted_path):
                    os.rename(os.path.join(extracted_path, item), os.path.join(path, item))
                
                # Rimuovi la cartella vuota
                os.rmdir(extracted_path)
            
            # 3. Caricamento e Avvio
            self.master.after(0, lambda: self._load_model_and_start_app(path, lang_name))

        except Exception as e:
            error_msg = T_thread['error_download_extract'] % str(e)
            self.master.after(0, lambda: messagebox.showerror("Errore Critico", error_msg))
            self.master.after(0, lambda: self.status_label.config(text=error_msg, foreground='red'))
            self.master.after(0, lambda: self.action_button.config(state=tk.NORMAL, text=T_thread['btn_retry']))
            print(error_msg)

    def _load_model_and_start_app(self, path, lang_name):
        """Tenta di caricare il modello e se ha successo, avvia l'app principale."""
        T_thread = TRANSLATIONS[self.app_lang_code]
        try:
            model_instance = Model(path)
            
            # Nascondi la finestra di setup
            self.master.withdraw()
            
            # Avvia l'app di trascrizione
            root_app = tk.Toplevel(self.master)
            TranscriberApp(root_app, model_instance, lang_name, self.app_lang_code)
            
        except Exception as e:
            error_msg = T_thread['error_model_load'] % (path, str(e))
            self.master.after(0, lambda: messagebox.showerror("Errore Caricamento Modello", error_msg))
            self.master.after(0, lambda: self.status_label.config(text=error_msg, foreground='red'))
            self.master.after(0, lambda: self.action_button.config(state=tk.NORMAL, text=T_thread['btn_retry']))


class TranscriberApp:
    """Finestra principale per l'interfaccia di trascrizione."""
    def __init__(self, master, model_instance, lang_name, lang_code):
        self.master = master
        self.T = TRANSLATIONS[lang_code] # Traduzioni per questa finestra
        
        # Imposta il titolo e l'icona
        load_app_logo(master)
        master.title(self.T['app_name'] + self.T['app_title'] % lang_name)
        
        self.model = model_instance # Modello Vosk già caricato
        self.transcribing = False
        
        # Configurazione del tema
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', font=(FONT_FAMILY, 10, 'bold'), padding=10, background='#4CAF50', foreground='white')
        style.map('TButton', background=[('active', '#45a049')])
        style.configure('TLabel', font=(FONT_FAMILY, 10))
        style.configure('TProgressbar', thickness=20)
        
        # Configurazione Layout responsive
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # Frame principale
        main_frame = ttk.Frame(master, padding=PADDING)
        main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Configurazione responsive del frame principale (10 righe)
        for i in range(10):
            # Le righe 0 (Logo+Titolo), 1-6 (Controlli) non si espandono. Le righe 7-9 (Area Testo) si espandono.
            main_frame.rowconfigure(i, weight=0 if i < 7 else 1) 
        main_frame.columnconfigure(0, weight=1)

        # Inizializzazione variabili
        self.file_path = tk.StringVar()
        self.progress_var = tk.DoubleVar()

        # === 0. Area Logo e Titolo ===
        logo_title_frame = ttk.Frame(main_frame)
        logo_title_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        logo_title_frame.columnconfigure(1, weight=1) # Colonna per il titolo si espande

        if GLOBAL_LOGO_IMAGES['ui']:
            # Logo visibile nell'interfaccia (usiamo il riferimento memorizzato)
            logo_label = ttk.Label(logo_title_frame, image=GLOBAL_LOGO_IMAGES['ui'])
            logo_label.grid(row=0, column=0, padx=(0, 15), sticky='w')

        # Titolo dell'applicazione (Transcribeer)
        ttk.Label(logo_title_frame, text=self.T['app_name'], 
                  font=(FONT_FAMILY, 24, 'bold'), 
                  foreground='#333333').grid(row=0, column=1, sticky='w')
        
        # Indicatore Lingua Attiva
        ttk.Label(logo_title_frame, text=self.T['lang_active'] % lang_name, 
                  foreground='#007acc', 
                  font=(FONT_FAMILY, 12, 'bold')).grid(row=1, column=1, sticky='w')

        # === 1. Area Selezione File ===
        ttk.Label(main_frame, text=self.T['select_file_prompt'], font=(FONT_FAMILY, 12, 'bold')).grid(row=1, column=0, sticky='w', pady=(5, 0), padx=5)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(file_frame, textvariable=self.file_path, width=70).grid(row=0, column=0, sticky='ew', padx=(0, 5))
        ttk.Button(file_frame, text=self.T['btn_browse'], command=self.select_file, style='TButton').grid(row=0, column=1, padx=(5, 0))
        
        # === 2. Pulsante Trascrivi ===
        self.transcribe_button = ttk.Button(main_frame, text=self.T['btn_transcribe'], command=self.start_transcription, style='TButton')
        self.transcribe_button.grid(row=3, column=0, pady=10, sticky='ew')
        
        # === 3. Barra di Progresso ===
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate", variable=self.progress_var)
        self.progress_bar.grid(row=4, column=0, pady=10, sticky='ew')
        
        # === 4. Etichetta Stato (Feedback in tempo reale) ===
        self.status_label = ttk.Label(main_frame, text=self.T['status_ready'], foreground='#007acc', font=(FONT_FAMILY, 10, 'italic'))
        self.status_label.grid(row=5, column=0, sticky='w', pady=(0, 10))
        
        # === 5. Area di Testo Trascritto ===
        ttk.Label(main_frame, text=self.T['result_title'], font=(FONT_FAMILY, 12, 'bold')).grid(row=6, column=0, sticky='w', pady=(5, 0))
        
        # Contenitore per Text e Scrollbar
        text_container = ttk.Frame(main_frame)
        text_container.grid(row=7, column=0, sticky='nsew', rowspan=3)
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        self.text_area = tk.Text(text_container, wrap='word', height=15, font=(FONT_FAMILY, 11), 
                                 bd=1, relief="solid", padx=5, pady=5)
        self.text_area.grid(row=0, column=0, sticky='nsew')

        # Scrollbar per l'area di testo
        scrollbar = ttk.Scrollbar(text_container, command=self.text_area.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.text_area.config(yscrollcommand=scrollbar.set)

    def select_file(self):
        """Apre la finestra per la selezione del file audio."""
        f_types = [('Audio Files', '*.mp3 *.wav *.aac *.flac *.ogg *.m4a')]
        filename = filedialog.askopenfilename(filetypes=f_types)
        if filename:
            self.file_path.set(filename)
            self.status_label.config(text=self.T['status_ready'], foreground='#007acc')
            self.text_area.delete('1.0', tk.END)

    def start_transcription(self):
        """Avvia la trascrizione in un thread separato."""
        filepath = self.file_path.get()
        if not filepath:
            self.status_label.config(text=self.T['error_select_file'], foreground='#d32f2f')
            return
        
        if self.transcribing:
            return
            
        self.transcribing = True
        self.transcribe_button.config(state=tk.DISABLED, text=self.T['status_transcribing'])
        self.progress_var.set(0)
        self.text_area.delete('1.0', tk.END)
        self.status_label.config(text=self.T['status_transcribing'], foreground='#ff9800')

        # Avvio la funzione principale di trascrizione in un thread
        threading.Thread(target=self.transcribe_audio_threaded, args=(filepath,)).start()

    def transcribe_audio_threaded(self, filepath):
        """Funzione di trascrizione da eseguire nel thread separato."""
        temp_wav_file = "temp_audio_16k.wav"
        
        try:
            # 1. Conversione Audio (Pre-elaborazione necessaria per Vosk)
            audio = AudioSegment.from_file(filepath)
            
            # Calcola la durata del file e il tempo di attesa stimato
            duration_ms = len(audio)
            duration_sec = duration_ms / 1000
            
            # Tempo stimato: 2.5x la durata reale per pre-elaborazione + trascrizione
            # Questo è solo una stima per dare feedback all'utente.
            estimated_wait_time = max(duration_sec * 2.5, 5) 
            
            # Formattazione del tempo stimato
            if estimated_wait_time < 60:
                wait_str = f"{int(estimated_wait_time)} {self.T['time_sec']}"
            else:
                minutes = int(estimated_wait_time // 60)
                seconds = int(estimated_wait_time % 60)
                wait_str = f"{minutes} {self.T['time_min_sec'] % seconds}"
                
            # Formattazione della durata audio
            audio_minutes = int(duration_sec // 60)
            audio_seconds = int(duration_sec % 60)
            audio_duration_str = self.T['time_audio_format'] % (audio_minutes, audio_seconds)

            # Aggiornamento dello stato con il tempo stimato (durante la conversione)
            status_message = self.T['status_converting_wait'] % (audio_duration_str, wait_str)
            self.master.after(0, lambda: self.status_label.config(text=status_message, foreground='#ff9800'))
            
            # Requisiti Vosk: mono, 16-bit (signed), 16000 Hz sample rate
            audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
            audio.export(temp_wav_file, format="wav")
            
            # 2. Inizializzazione Riconoscitore
            rec = KaldiRecognizer(self.model, 16000)
            
            # 3. Trascrizione a Segmenti con Feedback in Tempo Reale
            self.master.after(0, lambda: self.status_label.config(text=self.T['status_listening'], foreground='#4CAF50'))
            
            # Calcolo le dimensioni per la Progress Bar
            total_size = os.path.getsize(temp_wav_file)
            bytes_read = 0
            
            with open(temp_wav_file, "rb") as wf:
                wf.read(44) # Salta l'intestazione WAV
                
                # Definisco la dimensione del chunk di lettura (circa 2.5 secondi di audio)
                CHUNK_SIZE = 80000 
                
                while True:
                    data = wf.read(CHUNK_SIZE)
                    if not data:
                        break
                        
                    # Processa il Segmento
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text_part = result.get('text', '')
                        
                        if text_part:
                            # === AGGIUNGI PUNTEGGIATURA E CAPITALIZZAZIONE ===
                            punctuated_text = add_simple_punctuation(text_part)
                            
                            # Aggiornamento UI in tempo reale
                            self.master.after(0, lambda t=punctuated_text + ' ': self.text_area.insert(tk.END, t))
                            
                            # Aggiornamento Stato
                            status_text = self.T['status_transcribed'] % (punctuated_text[-30:].strip() if len(punctuated_text) > 30 else punctuated_text.strip())
                            self.master.after(0, lambda s=status_text: self.status_label.config(text=s, foreground='#4CAF50'))

                    # Aggiornamento Progress Bar
                    bytes_read += len(data)
                    progress = (bytes_read / total_size) * 100
                    self.master.after(0, lambda p=progress: self.progress_var.set(p))
                    
            # 4. Risultato Finale
            result = json.loads(rec.FinalResult())
            final_text = result.get('text', '')
            
            # === AGGIUNGI PUNTEGGIATURA E CAPITALIZZAZIONE AL RISULTATO FINALE ===
            final_punctuated_text = add_simple_punctuation(final_text)
            
            # Aggiungo l'ultima parte di testo e il messaggio di completamento
            self.master.after(0, lambda t=final_punctuated_text: self.text_area.insert(tk.END, t + self.T['result_footer']))
            self.master.after(0, lambda: self.status_label.config(text=self.T['status_complete'], foreground='#007acc'))

        except FileNotFoundError:
            self.master.after(0, lambda: messagebox.showerror("Errore Pydub", self.T['error_pydub']))
            self.master.after(0, lambda: self.status_label.config(text=self.T['error_critical'], foreground='#d32f2f'))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Errore Trascrizione", f"Si è verificato un errore durante la trascrizione: {e}"))
            self.master.after(0, lambda: self.status_label.config(text=self.T['error_critical'], foreground='#d32f2f'))
            print(f"Errore di trascrizione: {e}")
            
        finally:
            # Pulizia e reset UI
            if os.path.exists(temp_wav_file):
                os.remove(temp_wav_file)
                
            self.transcribing = False
            self.master.after(0, lambda: self.transcribe_button.config(state=tk.NORMAL, text=self.T['btn_transcribe']))
            self.master.after(0, lambda: self.progress_var.set(100)) 


if __name__ == "__main__":
    # La GUI deve essere eseguita nel thread principale
    root = tk.Tk()
    setup_app = ModelSetupWindow(root)
    root.mainloop()
