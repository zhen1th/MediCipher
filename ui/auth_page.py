"""Halaman terpadu autentikasi sistem MediCipher (Tab Login dan Register)."""
import tkinter as tk
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, MediCipherTheme
)
from ui.login_page import LoginPage
from ui.register_page import RegisterPage


class AuthPage(CTkFrame):
    """Komponen antarmuka pembungkus yang menyediakan tab Login dan Register saat aplikasi dibuka."""

    def __init__(self, master, on_login_success, initial_tab="login", **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.on_login_success = on_login_success
        self.current_tab = initial_tab

        self._build_ui()
        self.set_tab(initial_tab)

    def _build_ui(self):
        # Header Brand Terpadu
        brand_container = CTkFrame(self, fg_color="transparent")
        brand_container.pack(fill="x", pady=(15, 8))

        CTkLabel(
            brand_container,
            text="MEDICIPHER",
            font=(MediCipherTheme.FONT_FAMILY, 16, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack()

        CTkLabel(
            brand_container,
            text="Medical Data Encryption and Security System | Akses Multi-Faktor",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(pady=(2, 8))

        # Bilah Tab Pilihan: LOGIN dan REGISTER
        tab_bar = CTkFrame(self, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8, height=42)
        tab_bar.pack(pady=(0, 10))

        self.btn_tab_login = CTkButton(
            tab_bar,
            text="MASUK KE SISTEM (LOGIN)",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            width=210,
            height=34,
            command=lambda: self.set_tab("login")
        )
        self.btn_tab_login.pack(side="left", padx=4, pady=4)

        self.btn_tab_register = CTkButton(
            tab_bar,
            text="DAFTAR AKUN BARU (REGISTER)",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            width=220,
            height=34,
            command=lambda: self.set_tab("register")
        )
        self.btn_tab_register.pack(side="left", padx=4, pady=4)

        # Kontainer Konten Halaman Aktif
        self.container_view = CTkFrame(self, fg_color="transparent")
        self.container_view.pack(fill="both", expand=True)

        self.page_login = None
        self.page_register = None

    def set_tab(self, tab_name: str):
        """Berpindah tampilan antara tab Login dan Register."""
        self.current_tab = tab_name

        # Bersihkan tampilan sebelumnya
        for widget in self.container_view.winfo_children():
            widget.destroy()

        if tab_name == "login":
            # Sorot tombol Login
            self.btn_tab_login.configure(
                fg_color=MediCipherTheme.PRIMARY,
                text_color=MediCipherTheme.TEXT_MAIN
            )
            self.btn_tab_register.configure(
                fg_color="transparent",
                text_color=MediCipherTheme.TEXT_MUTED
            )

            # Muat halaman Login
            self.page_login = LoginPage(
                self.container_view,
                on_login_success=self.on_login_success,
                on_switch_to_register=lambda: self.set_tab("register")
            )
            self.page_login.pack(fill="both", expand=True)

        else:
            # Sorot tombol Register
            self.btn_tab_register.configure(
                fg_color=MediCipherTheme.PRIMARY,
                text_color=MediCipherTheme.TEXT_MAIN
            )
            self.btn_tab_login.configure(
                fg_color="transparent",
                text_color=MediCipherTheme.TEXT_MUTED
            )

            # Muat halaman Register
            self.page_register = RegisterPage(
                self.container_view,
                on_registration_success=lambda: self.set_tab("login"),
                on_switch_to_login=lambda: self.set_tab("login")
            )
            self.page_register.pack(fill="both", expand=True)

