import subprocess
import shutil
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_THEME = {
    "bg": "#101010",
    "bg2": "#1a1a1a",
    "fg": "#ffffff",
    "fg2": "#cccccc",
    "accent": "#5aa2ff",
    "accent_dark": "#2e6fd9"
}

def read_json(path, default=None):
    full = os.path.join(BASE_DIR, path)

    # se non esiste e ho un default → lo creo
    if not os.path.exists(full) and default is not None:
        with open(full, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)

    # leggo in utf-8 (con fallback utf-8-sig)
    try:
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(full, "r", encoding="utf-8-sig") as f:
            return json.load(f)

def read_theme():
    return read_json("themes.json", DEFAULT_THEME)

def read_languages():
    return read_json("languages.json", {})

def ffmpeg_exists():
    return shutil.which("ffmpeg") is not None

def convert_to_wav(input_path, output_path):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", output_path]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get_logo_path():
    return os.path.join(BASE_DIR, "logo.png")
