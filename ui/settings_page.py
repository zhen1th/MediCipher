"""Halaman Pengaturan Keamanan dan Status Sistem MediCipher."""
import tkinter as tk
from tkinter import messagebox
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, MediCipherTheme
)
from authentication.login import SessionManager
from database.connection import DatabaseConnection
from database.repository import UserRepository, DongleRepository, FaceTemplateRepository
from authentication.usb_dongle import USBDongleManager
from config.settings import AppConfig


class SettingsPage(CTkFrame):
    """Komponen antarmuka status keamanan, audit akun, dan koneksi sistem."""

    def __init__(self, master, on_logout=None, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.on_logout = on_logout
        self._build_ui()

    def _build_ui(self):
        # Header
        header = CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        CTkLabel(
            header,
            text="PENGATURAN KEAMANAN & STATUS SISTEM",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(anchor="w")

        CTkLabel(
            header,
            text="Ringkasan Kredensial, Status Dongle Perangkat Keras, dan Parameter Keamanan",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w")

        # Container Kartu-Kartu Pengaturan
        main_box = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        main_box.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # 1. Bagian Akun & Kunci Master DPAPI
        sec1 = CTkFrame(main_box, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        sec1.pack(fill="x", padx=20, pady=(15, 8))

        CTkLabel(
            sec1,
            text="1. Informasi Akun Administrator & Kunci Master",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=15, pady=(8, 4))

        user = UserRepository.get_first_user()
        u_name = user["username"] if user else "Belum terdaftar"
        u_date = str(user["created_at"]) if user else "-"

        CTkLabel(sec1, text=f"Username Aktif: {u_name} (ID: {user['id'] if user else '-'})", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=1)
        CTkLabel(sec1, text=f"Terdaftar Sejak: {u_date}", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=1)
        CTkLabel(sec1, text="Proteksi Kunci Master: Windows Data Protection API (DPAPI) + HKDF SHA-256", font=(MediCipherTheme.FONT_FAMILY, 9), text_color=MediCipherTheme.SUCCESS).pack(anchor="w", padx=15, pady=(1, 8))

        # 2. Bagian Biometrik Wajah
        sec2 = CTkFrame(main_box, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        sec2.pack(fill="x", padx=20, pady=(0, 8))

        CTkLabel(
            sec2,
            text="2. Parameter Biometrik Wajah",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=15, pady=(8, 4))

        template = FaceTemplateRepository.get_by_user_id(user["id"]) if user else None
        tmpl_status = "Template Aktif (512 Dimensi Terenkripsi AES-256-GCM)" if template else "Template Belum Ada"

        CTkLabel(sec2, text=f"Model Pengenalan: Facenet512", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=1)
        CTkLabel(sec2, text=f"Ambang Batas Jarak Kosinus: {AppConfig.FACE_DISTANCE_THRESHOLD}", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=1)
        CTkLabel(sec2, text=f"Status Template: {tmpl_status}", font=(MediCipherTheme.FONT_FAMILY, 9), text_color=MediCipherTheme.SUCCESS if template else MediCipherTheme.WARNING).pack(anchor="w", padx=15, pady=(1, 8))

        # 3. Bagian Status USB Dongle Fisik
        sec3 = CTkFrame(main_box, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        sec3.pack(fill="x", padx=20, pady=(0, 8))

        CTkLabel(
            sec3,
            text="3. Konfigurasi USB Flashdisk Fisik (Dongle)",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=15, pady=(8, 4))

        dongle = DongleRepository.get_by_user_id(user["id"]) if user else None
        vol_serial = dongle["volume_serial"] if dongle else "-"
        reg_time = str(dongle["registered_at"]) if dongle else "-"

        CTkLabel(sec3, text=f"Serial Volume Terdaftar: {vol_serial}", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=1)
        CTkLabel(sec3, text=f"Waktu Registrasi Dongle: {reg_time}", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=1)

        usb_row = CTkFrame(sec3, fg_color="transparent")
        usb_row.pack(fill="x", padx=15, pady=(2, 8))

        self.lbl_usb_live = CTkLabel(
            usb_row,
            text="Status Koneksi Saat Ini: Memeriksa...",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_usb_live.pack(side="left")

        btn_chk_usb = CTkButton(
            usb_row,
            text="Uji Dongle Sekarang",
            width=130,
            command=self._test_usb_dongle
        )
        btn_chk_usb.pack(side="right")

        # 4. Bagian Status Basis Data MySQL
        sec4 = CTkFrame(main_box, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        sec4.pack(fill="x", padx=20, pady=(0, 15))

        CTkLabel(
            sec4,
            text="4. Status Koneksi Basis Data MySQL",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=15, pady=(8, 4))

        CTkLabel(sec4, text=f"Host Server: {AppConfig.DB_HOST}:{AppConfig.DB_PORT} | Database: {AppConfig.DB_NAME}", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=1)

        db_row = CTkFrame(sec4, fg_color="transparent")
        db_row.pack(fill="x", padx=15, pady=(2, 8))

        self.lbl_db_live = CTkLabel(
            db_row,
            text="Status MySQL: Terhubung",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.SUCCESS
        )
        self.lbl_db_live.pack(side="left")

        btn_chk_db = CTkButton(
            db_row,
            text="Uji Koneksi MySQL",
            width=130,
            command=self._test_db_connection
        )
        btn_chk_db.pack(side="right")

        # Tombol Logout Keluar Sesi
        btn_logout = CTkButton(
            main_box,
            text="Keluar dari Sesi (Logout Sesi Aman)",
            fg_color=MediCipherTheme.DANGER,
            hover_color=MediCipherTheme.DANGER_HOVER,
            height=36,
            command=self._handle_logout
        )
        btn_logout.pack(fill="x", padx=20, pady=(0, 15))

        self._test_usb_dongle()

    def _test_usb_dongle(self):
        """Menguji kehadiran dan validitas fisik USB dongle saat ini."""
        if not SessionManager.registered_volume_serial:
            self.lbl_usb_live.configure(
                text="Status Koneksi: Dongle belum didaftarkan.",
                text_color=MediCipherTheme.WARNING
            )
            return

        drive = USBDongleManager.get_drive_by_serial(SessionManager.registered_volume_serial)
        if drive:
            self.lbl_usb_live.configure(
                text=f"Status Koneksi: [TERHUBUNG] Drive {drive['letter']} (Serial: {drive['serial_number']})",
                text_color=MediCipherTheme.SUCCESS
            )
        else:
            self.lbl_usb_live.configure(
                text=f"Status Koneksi: [TERPUTUS] Serial {SessionManager.registered_volume_serial} tidak ditemukan!",
                text_color=MediCipherTheme.DANGER
            )

    def _test_db_connection(self):
        """Menguji koneksi ke basis data MySQL."""
        is_ok, msg = DatabaseConnection.test_connection()
        if is_ok:
            self.lbl_db_live.configure(text=f"Status MySQL: [AKTIF] {msg}", text_color=MediCipherTheme.SUCCESS)
            messagebox.showinfo("Koneksi Database", msg)
        else:
            self.lbl_db_live.configure(text=f"Status MySQL: [GAGAL] {msg}", text_color=MediCipherTheme.DANGER)
            messagebox.showerror("Koneksi Database", msg)

    def _handle_logout(self):
        """Memproses logout aman."""
        confirm = messagebox.askyesno(
            "Konfirmasi Logout",
            "Apakah Anda yakin ingin keluar dari sesi aktif MediCipher?"
        )
        if confirm:
            SessionManager.logout()
            if callable(self.on_logout):
                self.on_logout()

