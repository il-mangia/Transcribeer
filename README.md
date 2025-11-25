<p align="center">
  <img src="logo.png" width="150" alt="Transcribeer Logo"/>
</p>

<h1 align="center">Transcribeer</h1>

<p align="center">
  The modern, multilingual audio-to-text transcription tool powered by Vosk.<br>
  Cross-platform for Windows and Linux, with beautiful UI and AI-powered (GEMINI API REQUIRED) text enhancement.
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-download">Download</a> •
  <a href="#-requirements">Requirements</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-languages--models">Languages & Models</a> •
  <a href="#-ai-enhancement">AI Enhancement</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-troubleshooting">Troubleshooting</a> •
  <a href="#️-license">License</a>
</p>

---

## 🚀 Features

### 🎧 Audio Transcription
- **Multi-format Support**: MP3, WAV, M4A, OGG, FLAC
- **Automatic Conversion**: Converts audio to optimal format for speech recognition
- **Real-time Progress**: Live progress bar and status updates

### 🌍 Multilingual Support
- **8 Languages**: Italian, English, French, German, Spanish, Portuguese, Russian, Chinese
- **Auto-language Detection**: UI automatically matches your system language
- **Model Auto-download**: Downloads speech recognition models on first use

### 🤖 AI-Powered Enhancement
- **Google Gemini Integration**: Improves punctuation and text flow
- **Smart Punctuation**: Automatic sentence capitalization and punctuation
- **Text Refinement**: Enhances readability while preserving meaning

### 🎨 Modern Interface
- **Dark Theme**: Easy on the eyes modern UI
- **CustomTkinter**: Beautiful, customizable interface
- **Intuitive Workflow**: Simple and user-friendly

### ⚡ Technical Features
- **Offline Capable**: Works without internet (except AI features)
- **Cross-Platform**: Windows and Linux support
- **Lightweight**: Fast and efficient processing

---

## 📦 Download & Installation

### Windows
**Requirements:**
- Windows 10 or later
- FFmpeg (`winget install Gyan.FFmpeg`)

**Download:**
👉 [Latest Windows Release](https://github.com/il-mangia/Transcribeer/releases)

### Linux
**Requirements:**
- Ubuntu/Debian: `sudo apt install ffmpeg`
- Fedora: `sudo dnf install ffmpeg`
- Arch: `sudo pacman -S ffmpeg`
**Download:**
👉 [Latest Linux Release](https://github.com/il-mangia/Transcribeer/releases)

### From source code folder (dev only)
# Clone repository
git clone https://github.com/il-mangia/
cd Transcribeer
# Install dependencies
pip install -r requirements.txt
# Run application
python main.py

## 🧠 How It Works

1. FFmpeg converts your audio to WAV 16 kHz mono  
2. Vosk (https://alphacephei.com/vosk/) transcribes and auto-detects the language  
3. Transcript is translated into italian only
4. Both original and translated text are shown  
5. You can save everything into a .txt file  

---

## 🌍 Languages & UI

Supported languages:

🇮🇹 Italian (it) - Vosk Small IT 0.22
🇺🇸 English (en) - Vosk Small EN-US 0.15
🇫🇷 Francais	(fr) -	Vosk Small FR 0.22
🇩🇪 Detusch (de) - Vosk Small DE-Zamia 0.3
🇪🇸 Spanish	(es) - Vosk Small ES 0.42
🇵🇹 Portoughese	(pt) - Vosk Small PT 0.3
🇷🇺 Russian (ru) - Vosk Small RU 0.22
🇨🇳 Chinese	(cn) - Vosk Small CN 0.22

---

## 🔧 Development Setup (Source code folder)

Install dependencies:  
pip install -r requirements.txt  

Run:  
python main.py  

---

## 🧪 Supported media Formats  

- MP3  
- WAV  
- AAC  
- M4A  

All are converted to WAV automatically.

---

## 🧰 Tech Stack  

- Python 3  
- Vosk  
- Customtkinter 
- FFmpeg  
- Google Gemini API

---

## 📝 Known Limitations  

- AI function requires Internet  
- GPU acceleration planned for future versions  
- Local translation model planned

---

## ❤️ License  

OPEN SOURCE!!!!!!!!!

---

<p align="center">
  Built with ❤️ by il-mangia — Powered by Whisper
</p>
