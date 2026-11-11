"""Aplikasi Utama MediCipher (Medical Data Encryption and Security System).

Aplikasi desktop pengamanan arsip laboratorium medis berbasis Python, CustomTkinter,
MySQL, Kriptografi Berlapis (Vigenere + AES + HMAC), Steganografi LSB,
Verifikasi Biometrik Wajah (Facenet512), Dongle USB Fisik, dan Simple Blockchain SHA-256.
"""
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# Memastikan direktori root berada dalam sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import AppConfig
from database.migrations import DatabaseMigration
from authentication.login import SessionManager
from ui.theme import CTk, CTkFrame, CTkLabel, CTkButton, MediCipherTheme
from ui.auth_page import AuthPage
from ui.dashboard import DashboardPage
from ui.text_encryption_page import TextEncryptionPage
from ui.file_encryption_page import FileEncryptionPage
from ui.medical_database_page import MedicalDatabasePage
from ui.steganography_page import SteganographyPage
from ui.blockchain_page import BlockchainPage
from ui.settings_page import SettingsPage


class MediCipherApp(CTk):
    """Jendela utama aplikasi desktop MediCipher."""

    def __init__(self):
        super().__init__()
        self.title("MediCipher - Medical Data Encryption and Security System")
        self.geometry("1200x780")
        self.minsize(1050, 700)
        self.configure(bg=MediCipherTheme.BG_DARK)

        # Inisialisasi direktori lokal
        AppConfig.ensure_directories()

        # Binding aktivitas pengguna untuk pemantauan timeout sesi
        self.bind_all("<Any-KeyPress>", self._on_user_interaction)
        self.bind_all("<Any-ButtonPress>", self._on_user_interaction)

        # Daftarkan penanganan penguncian otomatis sesi jika USB dicabut
        SessionManager.set_lock_callback(self._on_session_locked_by_hardware)

        # Kontainer konten dinamis
        self.active_page = None
        self.sidebar_frame = None
        self.content_container = None
        self.sidebar_buttons = {}

        # Periksa status database dan inisialisasi alur autentikasi awal (Login & Register)
        self._init_startup_flow()

        # Mulai timer pengecekan inactivity timeout setiap 10 detik
        self._schedule_inactivity_check()

    def _on_user_interaction(self, event=None):
        """Memperbarui tanda waktu aktivitas terakhir pengguna."""
        if SessionManager.is_authenticated:
            SessionManager.update_activity()

    def _schedule_inactivity_check(self):
        """Pemeriksaan berkala masa kedaluwarsa sesi tidak aktif."""
        if SessionManager.is_authenticated and SessionManager.is_session_timed_out():
            SessionManager.lock_session("Sesi dikunci karena tidak ada aktivitas pengguna (Inactivity Timeout).")
            self._show_auth_screen(initial_tab="login")
            messagebox.showwarning(
                "Sesi Kedaluwarsa",
                f"Sesi dikunci otomatis karena tidak ada aktivitas selama {AppConfig.SESSION_TIMEOUT_MINUTES} menit."
            )
        self.after(10000, self._schedule_inactivity_check)

    def _on_session_locked_by_hardware(self, reason: str):
        """Callback saat sesi dikunci karena pencabutan fisik USB."""
        self.after(0, self._handle_session_lock_ui, reason)

    def _handle_session_lock_ui(self, reason: str):
        self._show_auth_screen(initial_tab="login")
        messagebox.showerror(
            "Keamanan Terpicu: Sesi Dikunci",
            f"Akses aplikasi MediCipher telah dikunci secara otomatis.\nPenyebab: {reason}\n"
            "Silakan hubungkan kembali USB Dongle resmi dan lakukan autentikasi ulang."
        )

    def _init_startup_flow(self):
        """Memeriksa koneksi database MySQL dan membuka layar autentikasi (Login & Register)."""
        try:
            is_first_run = DatabaseMigration.check_is_first_run()
            # Buka layar autentikasi dengan tab awal yang sesuai, namun kedua tab (Login & Register) tetap tersedia
            init_tab = "register" if is_first_run else "login"
            self._show_auth_screen(initial_tab=init_tab)
        except ConnectionError as conn_err:
            # Tampilkan pesan kesalahan koneksi database tanpa menganggap database kosong
            self._show_db_error_screen(str(conn_err))
        except Exception as exc:
            self._show_db_error_screen(f"Terjadi kesalahan inisialisasi: {exc}")

    def _show_db_error_screen(self, error_message: str):
        """Menampilkan layar error koneksi database tanpa mengizinkan bypass."""
        self._clear_window()
        err_frame = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=12)
        err_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.5)

        CTkLabel(
            err_frame,
            text="MEDICIPHER - KONEKSI DATABASE MYSQL GAGAL",
            font=(MediCipherTheme.FONT_FAMILY, 14, "bold"),
            text_color=MediCipherTheme.DANGER
        ).pack(pady=(30, 10))

        CTkLabel(
            err_frame,
            text=(
                "Aplikasi tidak dapat terhubung ke server MySQL.\n"
                "Sesuai standar keamanan, aplikasi TIDAK dapat dibuka dalam mode kosong atau simulasi.\n\n"
                "Rincian Kesalahan:\n" + error_message + "\n\n"
                f"Periksa status server MySQL pada {AppConfig.DB_HOST}:{AppConfig.DB_PORT} atau konfigurasi file .env."
            ),
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED,
            justify="center"
        ).pack(padx=25, pady=(0, 20))

        btn_retry = CTkButton(
            err_frame,
            text="Coba Hubungkan Kembali ke MySQL",
            fg_color=MediCipherTheme.PRIMARY,
            hover_color=MediCipherTheme.PRIMARY_HOVER,
            command=self._init_startup_flow
        )
        btn_retry.pack(pady=5)

    def _clear_window(self):
        """Membersihkan seluruh widget di jendela utama."""
        for widget in self.winfo_children():
            widget.destroy()
        self.sidebar_frame = None
        self.content_container = None
        self.active_page = None
        self.sidebar_buttons = {}

    def _show_auth_screen(self, initial_tab="login"):
        """Membuka layar autentikasi yang memuat opsi Login dan Register sekaligus."""
        self._clear_window()
        self.active_page = AuthPage(
            self,
            on_login_success=self._build_main_app_workspace,
            initial_tab=initial_tab
        )
        self.active_page.pack(fill="both", expand=True)

    def _build_main_app_workspace(self):
        """Membangun antarmuka utama aplikasi lengkap dengan sidebar navigasi dan area kerja."""
        self._clear_window()

        # Sidebar Navigasi Kiri (Lebar 230px)
        self.sidebar_frame = CTkFrame(self, fg_color=MediCipherTheme.SURFACE_DARK, width=230, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Brand / Logo Header
        brand_frame = CTkFrame(self.sidebar_frame, fg_color="transparent")
        brand_frame.pack(fill="x", padx=15, pady=(20, 25))

        CTkLabel(
            brand_frame,
            text="MEDICIPHER",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w")

        CTkLabel(
            brand_frame,
            text="Medical Security System",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_INACTIVE
        ).pack(anchor="w")

        # Tombol Menu Navigasi
        nav_items = [
            ("dashboard", "Dashboard Ringkasan", self._nav_dashboard),
            ("text_enc", "Enkripsi Teks Medis", self._nav_text_encryption),
            ("file_enc", "Enkripsi Dokumen File", self._nav_file_encryption),
            ("database", "Database Medis Aman", self._nav_database),
            ("stego", "Steganografi Citra", self._nav_steganography),
            ("blockchain", "Verifikasi Blockchain", self._nav_blockchain),
            ("settings", "Pengaturan & Status", self._nav_settings),
        ]

        for code, label_text, handler in nav_items:
            btn = CTkButton(
                self.sidebar_frame,
                text=label_text,
                font=(MediCipherTheme.FONT_FAMILY, 9),
                fg_color="transparent",
                text_color=MediCipherTheme.TEXT_MUTED,
                hover_color=MediCipherTheme.CARD_BG,
                anchor="w",
                height=36,
                command=handler
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.sidebar_buttons[code] = btn

        # Bagian Bawah Sidebar (User Info & Logout)
        bottom_frame = CTkFrame(self.sidebar_frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=12, pady=15)

        user_name = SessionManager.current_username or "Administrator"
        CTkLabel(
            bottom_frame,
            text=f"User: {user_name}",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 4))

        btn_logout = CTkButton(
            bottom_frame,
            text="Logout Sesi",
            font=(MediCipherTheme.FONT_FAMILY, 9, "bold"),
            fg_color=MediCipherTheme.DANGER,
            hover_color=MediCipherTheme.DANGER_HOVER,
            height=30,
            command=self._handle_manual_logout
        )
        btn_logout.pack(fill="x")

        # Area Konten Utama Kanan
        self.content_container = CTkFrame(self, fg_color=MediCipherTheme.BG_DARK, corner_radius=0)
        self.content_container.pack(side="right", fill="both", expand=True)

        # Buka Dashboard secara default
        self._nav_dashboard()

    def _highlight_nav_button(self, active_code: str):
        """Memperbarui sorotan tombol menu yang sedang aktif."""
        for code, btn in self.sidebar_buttons.items():
            if code == active_code:
                btn.configure(
                    fg_color=MediCipherTheme.CARD_BG,
                    text_color=MediCipherTheme.PRIMARY
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=MediCipherTheme.TEXT_MUTED
                )

    def _switch_page(self, page_class, page_code: str, **kwargs):
        """Mengganti tampilan di area konten utama."""
        self._highlight_nav_button(page_code)
        if self.active_page is not None:
            self.active_page.destroy()

        self.active_page = page_class(self.content_container, **kwargs)
        self.active_page.pack(fill="both", expand=True)

    def _nav_dashboard(self):
        self._switch_page(DashboardPage, "dashboard", navigate_to=self._switch_page)

    def _nav_text_encryption(self):
        self._switch_page(TextEncryptionPage, "text_enc")

    def _nav_file_encryption(self):
        self._switch_page(FileEncryptionPage, "file_enc")

    def _nav_database(self):
        self._switch_page(MedicalDatabasePage, "database")

    def _nav_steganography(self):
        self._switch_page(SteganographyPage, "stego")

    def _nav_blockchain(self):
        self._switch_page(BlockchainPage, "blockchain")

    def _nav_settings(self):
        self._switch_page(SettingsPage, "settings", on_logout=self._show_auth_screen)

    def _handle_manual_logout(self):
        confirm = messagebox.askyesno(
            "Konfirmasi Logout",
            "Apakah Anda yakin ingin keluar dari sesi aktif MediCipher?"
        )
        if confirm:
            SessionManager.logout()
            self._show_auth_screen(initial_tab="login")


def main():
    """Fungsi entri utama aplikasi."""
    app = MediCipherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
