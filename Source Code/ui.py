import tkinter as tk
from tkinter import filedialog, scrolledtext
from utils import read_theme, read_languages, get_logo_path
from PIL import Image, ImageTk
import locale
import os

class UI:

    def __init__(self, root, start_cb, save_cb):
        self.root = root
        self.start_cb = start_cb
        self.save_cb = save_cb

        self.theme = read_theme()
        self.langs = read_languages()

        # Lingua sistema
        system_lang = locale.getdefaultlocale()[0][:2].upper()
        self.current_lang = system_lang if system_lang in self.langs else "IT"
        self.strings = self.langs[self.current_lang]

        root.title("Transcribeer")
        root.geometry("1000x650")
        root.config(bg=self.theme["bg"])

        # HEADER ---------------------------------------------------
        header = tk.Frame(root, bg=self.theme["bg"])
        header.pack(fill="x", pady=10)

        logo_path = get_logo_path()
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((60, 60))
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(header, image=self.logo, bg=self.theme["bg"]).pack(side="left", padx=15)

        tk.Label(
            header,
            text="Transcribeer",
            fg=self.theme["accent"],
            bg=self.theme["bg"],
            font=("Segoe UI", 28, "bold")
        ).pack(side="left")

        # MENU LINGUE
        self.lang_var = tk.StringVar(value=self.current_lang)

        lang_display = []
        for code, data in self.langs.items():
            lang_display.append(f"{code} ({data['name']})")

        lang_menu = tk.OptionMenu(header, self.lang_var, *lang_display, command=self.change_language)
        lang_menu.config(bg=self.theme["bg2"], fg=self.theme["fg"])
        lang_menu.pack(side="right", padx=15)

        # CONTROLLI -------------------------------------------------
        controls = tk.Frame(root, bg=self.theme["bg"])
        controls.pack(fill="x", pady=10)

        self.file_label = tk.Label(
            controls,
            text=self.strings["no_file"],
            fg=self.theme["fg"],
            bg=self.theme["bg"],
            font=("Segoe UI", 12)
        )
        self.file_label.pack(side="left", padx=10)

        self.btn_choose = tk.Button(
            controls,
            text=self.strings["choose_file"],
            bg=self.theme["accent_dark"],
            fg="white",
            font=("Segoe UI", 12),
            command=self.select_file
        )
        self.btn_choose.pack(side="right", padx=5)

        self.btn_save = tk.Button(
            controls,
            text=self.strings["save_text"],
            bg="#27a844",
            fg="white",
            font=("Segoe UI", 12),
            command=self.save_cb
        )
        self.btn_save.pack(side="right", padx=5)

        self.btn_trans = tk.Button(
            controls,
            text=self.strings["transcribe"],
            bg=self.theme["accent"],
            fg="white",
            font=("Segoe UI", 12),
            command=self.start_cb
        )
        self.btn_trans.pack(side="right", padx=5)

        # STATUS ---------------------------------------------------
        self.status = tk.Label(
            root,
            text=self.strings["ready"],
            fg=self.theme["fg2"],
            bg=self.theme["bg"],
            font=("Segoe UI", 12)
        )
        self.status.pack(fill="x")

        # OUTPUT ---------------------------------------------------
        self.out = scrolledtext.ScrolledText(
            root,
            fg=self.theme["fg"],
            bg=self.theme["bg2"],
            font=("Consolas", 12),
            insertbackground="white"
        )
        self.out.pack(fill="both", expand=True, padx=15, pady=10)

        self.file_path = None

    # CAMBIO LINGUA ------------------------------------------------
    def change_language(self, selection):
        code = selection.split(" ")[0]  
        self.current_lang = code
        self.strings = self.langs[code]

        self.btn_choose.config(text=self.strings["choose_file"])
        self.btn_trans.config(text=self.strings["transcribe"])
        self.btn_save.config(text=self.strings["save_text"])
        self.file_label.config(text=self.strings["no_file"])
        self.status.config(text=self.strings["ready"])

    # -----------------------------------------------
    def select_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.m4a *.aac")]
        )
        if path:
            self.file_path = path
            self.file_label.config(text=path)

    def get_params(self):
        return self.file_path, self.current_lang

    def log(self, msg):
        self.status.config(text=msg)
        self.out.insert("end", msg + "\n")
        self.out.see("end")

    def show_text(self, text):
        self.out.insert("end", "\n" + text + "\n")
        self.out.see("end")
