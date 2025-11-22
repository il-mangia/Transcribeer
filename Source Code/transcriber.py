import threading
import whisper
import os
from googletrans import Translator
from utils import convert_to_wav, ffmpeg_exists

class Transcriber:

    def __init__(self, app, file_path, ui_strings, target_lang):
        self.app = app
        self.file_path = file_path
        self.ui = ui_strings
        self.target_lang = target_lang
        self.model_name = "small"

    def log(self, msg):
        self.app.log(msg)

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        try:
            self.log("🔍 FFmpeg check…")
            if not ffmpeg_exists():
                self.log("❌ FFmpeg non trovato.")
                return

            wav_out = self.file_path + "_temp.wav"

            self.log("🎧 Converting audio…")
            convert_to_wav(self.file_path, wav_out)
            self.log(self.ui["converted"])

            self.log("📦 Loading Whisper model…")
            model = whisper.load_model(self.model_name)
            self.log(self.ui["model_loaded"])

            self.log(self.ui["transcribing"])
            result = model.transcribe(wav_out)
            original_text = result["text"]
            lang = result["language"]

            self.log(f"{self.ui['lang_detected']}: {lang.upper()}")

            # TRADUZIONE
            translator = Translator()
            self.log("🌐 Translating…")
            translated = translator.translate(original_text, dest=self.target_lang).text
            self.log(self.ui["translation_done"])

            final_output = (
                f"=== {self.ui['original_text']} ===\n\n" +
                original_text +
                f"\n\n=== {self.ui['translation']} ===\n\n" +
                translated
            )
            self.app.show_text(final_output)

            if os.path.exists(wav_out):
                os.remove(wav_out)

        except Exception as e:
            self.log(f"{self.ui['error']}: {e}")
