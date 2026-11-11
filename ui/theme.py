"""Definisi tema visual dan adapter CustomTkinter MediCipher."""
import sys
import tkinter as tk
from tkinter import ttk

# Deteksi ketersediaan CustomTkinter
try:
    import customtkinter as ctk
    HAS_CUSTOMTKINTER = True
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    HAS_CUSTOMTKINTER = False
    ctk = None


class MediCipherTheme:
    """Palet warna profesional keamanan medis modern."""
    
    BG_DARK = "#0B0F19"
    SURFACE_DARK = "#151D2A"
    CARD_BG = "#1E293B"
    CARD_BORDER = "#334155"
    
    PRIMARY = "#0284C7"
    PRIMARY_HOVER = "#0369A1"
    
    SUCCESS = "#059669"
    SUCCESS_HOVER = "#047857"
    
    DANGER = "#DC2626"
    DANGER_HOVER = "#B91C1C"
    
    WARNING = "#D97706"
    
    TEXT_MAIN = "#F8FAFC"
    TEXT_MUTED = "#94A3B8"
    TEXT_INACTIVE = "#64748B"
    
    FONT_FAMILY = "Segoe UI"


# Jika CustomTkinter tersedia, gunakan kelas aslinya.
# Jika belum terpasang, sediakan wrapper berbasis Tkinter standar yang kompatibel.
if HAS_CUSTOMTKINTER:
    CTk = ctk.CTk
    CTkFrame = ctk.CTkFrame
    CTkLabel = ctk.CTkLabel
    CTkButton = ctk.CTkButton
    CTkEntry = ctk.CTkEntry
    CTkTextbox = ctk.CTkTextbox
    CTkOptionMenu = ctk.CTkOptionMenu
    CTkScrollableFrame = ctk.CTkScrollableFrame
    CTkProgressBar = ctk.CTkProgressBar
    CTkTabview = ctk.CTkTabview
else:
    class CTk(tk.Tk):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.configure(bg=MediCipherTheme.BG_DARK)

    class CTkFrame(tk.Frame):
        def __init__(self, master=None, fg_color=None, corner_radius=0, border_width=0, border_color=None, **kwargs):
            bg = fg_color or MediCipherTheme.SURFACE_DARK
            super().__init__(master, bg=bg, bd=border_width, **kwargs)

    class CTkLabel(tk.Label):
        def __init__(self, master=None, text="", text_color=None, font=None, fg_color=None, **kwargs):
            fg = text_color or MediCipherTheme.TEXT_MAIN
            bg = fg_color or master.cget("bg") if hasattr(master, "cget") else MediCipherTheme.SURFACE_DARK
            font_spec = font if font else (MediCipherTheme.FONT_FAMILY, 10)
            super().__init__(master, text=text, fg=fg, bg=bg, font=font_spec, **kwargs)

    class CTkButton(tk.Button):
        def __init__(self, master=None, text="", command=None, fg_color=None, hover_color=None,
                     text_color=None, font=None, corner_radius=0, width=120, height=32, **kwargs):
            bg = fg_color or MediCipherTheme.PRIMARY
            fg = text_color or MediCipherTheme.TEXT_MAIN
            font_spec = font if font else (MediCipherTheme.FONT_FAMILY, 10, "bold")
            super().__init__(master, text=text, command=command, bg=bg, fg=fg, font=font_spec,
                             relief="flat", cursor="hand2", **kwargs)

    class CTkEntry(tk.Entry):
        def __init__(self, master=None, placeholder_text="", fg_color=None, text_color=None, font=None, **kwargs):
            bg = fg_color or MediCipherTheme.CARD_BG
            fg = text_color or MediCipherTheme.TEXT_MAIN
            font_spec = font if font else (MediCipherTheme.FONT_FAMILY, 10)
            super().__init__(master, bg=bg, fg=fg, insertbackground=fg, font=font_spec, relief="flat", **kwargs)

    class CTkTextbox(tk.Text):
        def __init__(self, master=None, fg_color=None, text_color=None, font=None, **kwargs):
            bg = fg_color or MediCipherTheme.CARD_BG
            fg = text_color or MediCipherTheme.TEXT_MAIN
            font_spec = font if font else (MediCipherTheme.FONT_FAMILY, 10)
            super().__init__(master, bg=bg, fg=fg, insertbackground=fg, font=font_spec, relief="flat", **kwargs)

    class CTkOptionMenu(ttk.Combobox):
        def __init__(self, master=None, values=None, command=None, **kwargs):
            super().__init__(master, values=values or [], state="readonly", **kwargs)
            if command:
                self.bind("<<ComboboxSelected>>", lambda e: command(self.get()))
        def set(self, val):
            self.set(val)

    class CTkScrollableFrame(tk.Frame):
        def __init__(self, master=None, fg_color=None, **kwargs):
            bg = fg_color or MediCipherTheme.SURFACE_DARK
            super().__init__(master, bg=bg, **kwargs)

    class CTkProgressBar(ttk.Progressbar):
        pass

    class CTkTabview(tk.Frame):
        def __init__(self, master=None, **kwargs):
            super().__init__(master, bg=MediCipherTheme.SURFACE_DARK, **kwargs)
            self._tabs = {}
        def add(self, name):
            tab = tk.Frame(self, bg=MediCipherTheme.SURFACE_DARK)
            self._tabs[name] = tab
            tab.pack(fill="both", expand=True)
            return tab
        def tab(self, name):
            return self._tabs.get(name)

