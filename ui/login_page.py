"""Halaman login autentikasi multi-faktor (USB Dongle + Password + Biometrik Wajah)."""
import tkinter as tk
from tkinter import messagebox
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, CTkEntry, MediCipherTheme
)
from authentication.login import LoginManager
from authentication.usb_dongle import USBDongleManager
from authentication.face_verification import FaceVerificationManager
from database.repository import DongleRepository


class LoginPage(CTkFrame):
    """Komponen antarmuka login tiga lapisan keamanan MediCipher."""

    def __init__(self, master, on_login_success, on_switch_to_register=None, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.on_login_success = on_login_success
        self.on_switch_to_register = on_switch_to_register
        self.live_face_embedding = None

        self._build_ui()
        self._check_usb_status()

    def _build_ui(self):
        container = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=12)
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.55, relheight=0.92)

        # Header
        CTkLabel(
            container,
            text="AUTENTIKASI MASUK (LOGIN 3FA)",
            font=(MediCipherTheme.FONT_FAMILY, 14, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(pady=(15, 3))

        CTkLabel(
            container,
            text="Ketiga lapisan autentikasi wajib berhasil untuk membuka sesi",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(pady=(0, 10))

        # Lapisan 1: Indikator USB Dongle Fisik
        usb_frame = CTkFrame(container, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        usb_frame.pack(fill="x", padx=35, pady=(0, 8))

        CTkLabel(
            usb_frame,
            text="Lapisan 1: Pengecekan Kunci USB Fisik (Hardware Token)",
            font=(MediCipherTheme.FONT_FAMILY, 9, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(6, 2))

        usb_row = CTkFrame(usb_frame, fg_color="transparent")
        usb_row.pack(fill="x", padx=12, pady=(2, 6))

        self.lbl_usb_indicator = CTkLabel(
            usb_row,
            text="Memeriksa keberadaan USB dongle...",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_usb_indicator.pack(side="left", fill="x", expand=True)

        btn_recheck_usb = CTkButton(
            usb_row,
            text="Periksa USB",
            width=110,
            command=self._check_usb_status
        )
        btn_recheck_usb.pack(side="right")

        # Lapisan 2: Form Kredensial Pengguna
        cred_frame = CTkFrame(container, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        cred_frame.pack(fill="x", padx=35, pady=(0, 8))

        CTkLabel(
            cred_frame,
            text="Lapisan 2: Kredensial Pengguna (Argon2id)",
            font=(MediCipherTheme.FONT_FAMILY, 9, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(6, 4))

        cred_grid = CTkFrame(cred_frame, fg_color="transparent")
        cred_grid.pack(fill="x", padx=12, pady=(0, 8))

        CTkLabel(cred_grid, text="Username:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_username = CTkEntry(cred_grid, placeholder_text="Username Akun", width=260)
        self.entry_username.grid(row=0, column=1, sticky="e", pady=2, padx=(10, 0))

        CTkLabel(cred_grid, text="Password:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_password = CTkEntry(cred_grid, placeholder_text="Kata Sandi Akun", show="*", width=260)
        self.entry_password.grid(row=1, column=1, sticky="e", pady=2, padx=(10, 0))

        # Lapisan 3: Verifikasi Wajah Langsung (Kamera + Facenet512)
        face_frame = CTkFrame(container, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        face_frame.pack(fill="x", padx=35, pady=(0, 10))

        CTkLabel(
            face_frame,
            text="Lapisan 3: Verifikasi Biometrik Wajah Langsung (Facenet512)",
            font=(MediCipherTheme.FONT_FAMILY, 9, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(6, 2))

        face_row = CTkFrame(face_frame, fg_color="transparent")
        face_row.pack(fill="x", padx=12, pady=(2, 6))

        self.btn_verify_face = CTkButton(
            face_row,
            text="Aktifkan Kamera & Verifikasi Wajah",
            command=self._handle_live_face_verification
        )
        self.btn_verify_face.pack(fill="x")

        self.lbl_face_status = CTkLabel(
            face_frame,
            text="Status Biometrik: Wajah belum dipindai untuk sesi ini.",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_face_status.pack(anchor="w", padx=12, pady=(0, 6))

        # Tombol Masuk Utama
        self.btn_login = CTkButton(
            container,
            text="Masuk ke Sistem MediCipher",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            height=36,
            command=self._handle_login_submit
        )
        self.btn_login.pack(fill="x", padx=35, pady=(4, 6))

        # Tombol Alih ke Registrasi
        if callable(self.on_switch_to_register):
            btn_switch = CTkButton(
                container,
                text="Belum memiliki akun? Buat Akun Baru (Register)",
                font=(MediCipherTheme.FONT_FAMILY, 8),
                fg_color="transparent",
                text_color=MediCipherTheme.PRIMARY,
                hover_color=MediCipherTheme.SURFACE_DARK,
                height=26,
                command=self.on_switch_to_register
            )
            btn_switch.pack(pady=(0, 4))

        # Label Informasi Status
        self.lbl_info_status = CTkLabel(
            container,
            text="Ketiga lapisan keamanan wajib berhasil untuk mendapatkan akses.",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_INACTIVE
        )
        self.lbl_info_status.pack(pady=(0, 8))

    def _check_usb_status(self):
        """Memeriksa apakah USB dongle milik pengguna manapun sedang tersambung.

        Memindai seluruh USB fisik yang terhubung dan mencocokkannya
        terhadap semua dongle terdaftar di database.
        """
        try:
            all_dongles = DongleRepository.get_all()
            if not all_dongles:
                self.lbl_usb_indicator.configure(
                    text="Belum ada USB dongle terdaftar. Silakan lakukan registrasi terlebih dahulu.",
                    text_color=MediCipherTheme.WARNING
                )
                return

            # Periksa apakah salah satu dongle terdaftar sedang terhubung
            for dongle in all_dongles:
                vol_serial = dongle["volume_serial"]
                token_hash = dongle["token_hash"]
                is_valid, _msg = USBDongleManager.verify_dongle(vol_serial, token_hash)
                if is_valid:
                    self.lbl_usb_indicator.configure(
                        text=f"[STATUS: TERHUBUNG] Serial: {vol_serial} - Token Kunci Sah. Lanjutkan login.",
                        text_color=MediCipherTheme.SUCCESS
                    )
                    return

            # Tidak ada dongle yang cocok
            self.lbl_usb_indicator.configure(
                text="[STATUS: TIDAK TERHUBUNG] USB dongle terdaftar tidak ditemukan. Hubungkan USB dongle Anda.",
                text_color=MediCipherTheme.DANGER
            )
        except Exception as exc:
            self.lbl_usb_indicator.configure(
                text=f"Kesalahan pemeriksaan USB: {exc}",
                text_color=MediCipherTheme.DANGER
            )

    def _handle_live_face_verification(self):
        """Mengambil sampel wajah saat ini melalui webcam."""
        self.lbl_face_status.configure(
            text="Mengaktifkan kamera dan mendeteksi wajah...",
            text_color=MediCipherTheme.WARNING
        )
        self.update_idletasks()

        try:
            is_cam_ok, cam_msg = FaceVerificationManager.test_camera_availability()
            if not is_cam_ok:
                raise RuntimeError(cam_msg)

            embedding = FaceVerificationManager.capture_and_extract_live_embedding()
            self.live_face_embedding = embedding
            self.lbl_face_status.configure(
                text="[STATUS: WAJAH TEREKAM] Fitur biometrik siap diverifikasi dengan template terdaftar.",
                text_color=MediCipherTheme.SUCCESS
            )
        except Exception as exc:
            self.live_face_embedding = None
            self.lbl_face_status.configure(
                text=f"Gagal memindai wajah: {exc}",
                text_color=MediCipherTheme.DANGER
            )

    def _handle_login_submit(self):
        """Memproses login secara ketat melalui ketiga lapisan autentikasi."""
        username = self.entry_username.get().strip()
        password = self.entry_password.get()

        if not username or not password:
            messagebox.showerror("Akses Ditolak", "Username dan kata sandi wajib diisi.")
            return

        if self.live_face_embedding is None:
            messagebox.showerror(
                "Akses Ditolak",
                "Verifikasi biometrik wajah wajib dilakukan melalui tombol kamera sebelum masuk."
            )
            return

        try:
            success, msg = LoginManager.execute_full_login(
                username=username,
                password=password,
                live_embedding=self.live_face_embedding
            )

            if success:
                messagebox.showinfo("Autentikasi Berhasil", msg)
                if callable(self.on_login_success):
                    self.on_login_success()
            else:
                messagebox.showerror("Akses Ditolak", msg)
                self.live_face_embedding = None
                self.lbl_face_status.configure(
                    text="Autentikasi gagal. Silakan pindai ulang wajah Anda.",
                    text_color=MediCipherTheme.DANGER
                )
        except PermissionError as perm_err:
            messagebox.showerror("Sistem Dikunci", str(perm_err))
        except Exception as exc:
            messagebox.showerror("Autentikasi Gagal", str(exc))
