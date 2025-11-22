<p align="center">
  <img src="logo.png" width="150" alt="Transcribeer Logo"/>
</p>

<h1 align="center">Transcribeer</h1>

<p align="center">
  The modern, multilingual audio-to-text & translation tool powered by Whisper.<br>
  Cross-platform for Windows and Linux, with a beautiful UI and automatic system-language detection.
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-download">Download</a> •
  <a href="#-requirements">Requirements</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-languages--ui">Languages & UI</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#️-license">License</a>
</p>

---

## 🚀 Features

🎧 Convert MP3, WAV, M4A, AAC into clean text  
🔍 Whisper-powered automatic language detection  
🌍 Translate transcripts into 10 languages (IT, EN, ES, FR, ZH, HI, PT, AR, RU, JA)  
🖥️ Full multilingual UI, including buttons and labels  
🧠 UI language auto-selected from system language  
🎨 Modern Dark UI  
⚙️ Fast, accurate, lightweight  
🪟 Windows compatible  
🐧 Linux compatible  
📝 Export transcripts into .txt files  
🔧 FFmpeg auto-check with warnings  
🔄 Clean and intuitive workflow  

---

## 📦 Download

Get the latest Windows 64-bit and Linux 64-bit release here:

👉 Latest Release:  
https://github.com/il-mangia/Transcribeer/releases

Available builds:
- Windows EXE installer  
- Windows portable ZIP  
- Linux AppImage  
- Linux tar.gz  
- Source code  

---

## 🛠 Requirements

### Whisper  
Already included inside the app.

### FFmpeg (required)  
Used to preprocess and normalize audio before sending it to Whisper.

---

## ⚙️ FFmpeg Installation

### Windows (winget)  
winget install Gyan.FFmpeg

### Windows (manual)  
Download from: https://www.gyan.dev/ffmpeg/builds/  
Extract it and add the 'bin/' folder to your system PATH.

---

### Linux (Ubuntu / Debian)  
sudo apt update  
sudo apt install ffmpeg  

### Linux (Arch)  
sudo pacman -S ffmpeg  

### Linux (Fedora / RHEL)  
sudo dnf install ffmpeg  

### Linux (OpenSUSE)  
sudo zypper install ffmpeg  

---

## 📥 Installation

### 🪟 Windows  
1. Download the latest release  
2. Run the .exe OR extract the .zip portable build  
3. Open Transcribeer.exe

---

### 🐧 Linux

#### AppImage  
chmod +x Transcribeer-x86_64.AppImage  
./Transcribeer-x86_64.AppImage  

#### tar.gz  
tar -xvf Transcribeer-linux.tar.gz  
cd Transcribeer  
./Transcribeer  

---

## 🧠 How It Works

1. FFmpeg converts your audio to WAV 16 kHz mono  
2. Whisper transcribes and auto-detects the language  
3. Transcript is translated into the selected target language  
4. Both original and translated text are shown  
5. You can save everything into a .txt file  

---

## 🌍 Languages & UI

Supported languages:

IT — Italian  
EN — English  
ES — Spanish  
FR — French  
ZH — Chinese  
HI — Hindi  
PT — Portuguese  
AR — Arabic  
RU — Russian  
JA — Japanese  

UI Features:
- System language detection  
- Dropdown to manually change language  
- All UI strings translated  

---

## 🔧 Development Setup (Optional)

Install dependencies:  
pip install -r requirements.txt  

Run:  
python main.py  

---

## 🧪 Supported Audio Formats  

- MP3  
- WAV  
- AAC  
- M4A  

All are converted to WAV automatically.

---

## 🧰 Tech Stack  

- Python 3  
- Whisper  
- Tkinter  
- FFmpeg  
- Google Translate API  

---

## 📝 Known Limitations  

- Translation requires Internet  
- GPU acceleration planned for future versions  
- Local translation model planned  

---

## ❤️ License  

OPEN SOURCE!!!!!!!!!

---

<p align="center">
  Built with ❤️ by il-mangia — Powered by Whisper
</p>
