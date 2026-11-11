"""Halaman registrasi akun administrator dan petugas medis MediCipher."""
import tkinter as tk
from tkinter import messagebox
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkOptionMenu, MediCipherTheme
)
from authentication.register import RegistrationManager
from authentication.usb_dongle import USBDongleManager
from authentication.face_verification import FaceVerificationManager


class RegisterPage(CTkFrame):
    """Komponen antarmuka registrasi sistem."""

    def __init__(self, master, on_registration_success, on_switch_to_login=None, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.on_registration_success = on_registration_success
        self.on_switch_to_login = on_switch_to_login
        self.captured_face_embedding = None
        self.available_drives = []

        self._build_ui()
        self._refresh_usb_drives()

    def _build_ui(self):
        container = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=12)
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.62, relheight=0.92)

        # Judul Halaman
        title_label = CTkLabel(
            container,
            text="PENDAFTARAN AKUN BARU (REGISTER)",
            font=(MediCipherTheme.FONT_FAMILY, 14, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        )
        title_label.pack(pady=(12, 2))

        subtitle_label = CTkLabel(
            container,
            text="Pendaftaran Tiga Komponen Keamanan: Kredensial, Biometrik Wajah, dan USB Fisik",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        subtitle_label.pack(pady=(0, 10))

        # Form Input Kredensial
        form_frame = CTkFrame(container, fg_color="transparent")
        form_frame.pack(fill="x", padx=35, pady=2)

        # Username
        CTkLabel(form_frame, text="Username Pengguna:", font=(MediCipherTheme.FONT_FAMILY, 9)).grid(row=0, column=0, sticky="w", pady=3)
        self.entry_username = CTkEntry(form_frame, placeholder_text="Contoh: analis_medis", width=280)
        self.entry_username.grid(row=0, column=1, sticky="e", pady=3, padx=(10, 0))

        # Password
        CTkLabel(form_frame, text="Password Baru (min. 8 karakter):", font=(MediCipherTheme.FONT_FAMILY, 9)).grid(row=1, column=0, sticky="w", pady=3)
        self.entry_password = CTkEntry(form_frame, placeholder_text="Kombinasi Huruf, Angka & Simbol", show="*", width=280)
        self.entry_password.grid(row=1, column=1, sticky="e", pady=3, padx=(10, 0))

        # Confirm Password
        CTkLabel(form_frame, text="Konfirmasi Password:", font=(MediCipherTheme.FONT_FAMILY, 9)).grid(row=2, column=0, sticky="w", pady=3)
        self.entry_confirm = CTkEntry(form_frame, placeholder_text="Ulangi Password Baru", show="*", width=280)
        self.entry_confirm.grid(row=2, column=1, sticky="e", pady=3, padx=(10, 0))

        # Separator Section 1: USB Flashdisk Dongle
        usb_box = CTkFrame(container, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        usb_box.pack(fill="x", padx=35, pady=(8, 6))

        CTkLabel(
            usb_box,
            text="1. Pendaftaran USB Flashdisk Fisik (Hardware Dongle)",
            font=(MediCipherTheme.FONT_FAMILY, 9, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(6, 2))

        usb_ctrl_frame = CTkFrame(usb_box, fg_color="transparent")
        usb_ctrl_frame.pack(fill="x", padx=12, pady=(2, 4))

        self.usb_option_menu = CTkOptionMenu(usb_ctrl_frame, values=["Memindai drive..."])
        self.usb_option_menu.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_refresh_usb = CTkButton(
            usb_ctrl_frame,
            text="Pindai Ulang",
            width=110,
            command=self._refresh_usb_drives
        )
        btn_refresh_usb.pack(side="right")

        self.lbl_usb_status = CTkLabel(
            usb_box,
            text="Status USB: Menunggu pemilihan drive fisik.",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_usb_status.pack(anchor="w", padx=12, pady=(0, 6))

        # Separator Section 2: Perekaman Biometrik Wajah
        face_box = CTkFrame(container, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=8)
        face_box.pack(fill="x", padx=35, pady=(4, 10))

        CTkLabel(
            face_box,
            text="2. Perekaman Biometrik Wajah Langsung (Facenet512)",
            font=(MediCipherTheme.FONT_FAMILY, 9, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=12, pady=(6, 2))

        face_ctrl_frame = CTkFrame(face_box, fg_color="transparent")
        face_ctrl_frame.pack(fill="x", padx=12, pady=(2, 4))

        self.btn_capture_face = CTkButton(
            face_ctrl_frame,
            text="Ambil Sampel Wajah Melalui Kamera Webcam",
            fg_color=MediCipherTheme.PRIMARY,
            hover_color=MediCipherTheme.PRIMARY_HOVER,
            command=self._handle_capture_face
        )
        self.btn_capture_face.pack(side="left", fill="x", expand=True)

        self.lbl_face_status = CTkLabel(
            face_box,
            text="Status Biometrik: Wajah belum direkam.",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_face_status.pack(anchor="w", padx=12, pady=(0, 6))

        # Tombol Submit Registrasi
        self.btn_submit = CTkButton(
            container,
            text="Selesaikan Pendaftaran Akun",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            height=36,
            command=self._handle_submit_registration
        )
        self.btn_submit.pack(fill="x", padx=35, pady=(2, 4))

        # Tombol Alih ke Login
        if callable(self.on_switch_to_login):
            btn_to_login = CTkButton(
                container,
                text="Sudah memiliki akun? Beralih ke Halaman Masuk (Login)",
                font=(MediCipherTheme.FONT_FAMILY, 8),
                fg_color="transparent",
                text_color=MediCipherTheme.PRIMARY,
                hover_color=MediCipherTheme.SURFACE_DARK,
                height=26,
                command=self.on_switch_to_login
            )
            btn_to_login.pack(pady=(0, 4))

        # Status Notifikasi
        self.lbl_global_msg = CTkLabel(
            container,
            text="",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.WARNING
        )
        self.lbl_global_msg.pack(pady=(0, 6))

    def _refresh_usb_drives(self):
        """Memindai daftar drive yang terhubung ke Windows."""
        try:
            drives = USBDongleManager.list_available_drives()
            self.available_drives = drives
            options = []
            for d in drives:
                rem_tag = "[REMOVABLE USB]" if d["is_removable"] else "[FIXED]"
                vol_name = d["volume_name"] or "Tanpa Nama"
                options.append(f"{d['path']} ({vol_name}) {rem_tag} - Serial: {d['serial_number']}")

            if not options:
                options = ["Tidak ada drive yang terdeteksi"]
                self.usb_option_menu.configure(values=options)
                self.usb_option_menu.set(options[0])
                self.lbl_usb_status.configure(
                    text="Status USB: Tidak ada drive fisik ditemukan. Hubungkan USB flashdisk.",
                    text_color=MediCipherTheme.DANGER
                )
            else:
                self.usb_option_menu.configure(values=options)
                removable_indices = [i for i, d in enumerate(drives) if d["is_removable"]]
                sel_idx = removable_indices[0] if removable_indices else 0
                self.usb_option_menu.set(options[sel_idx])
                self.lbl_usb_status.configure(
                    text=f"Status USB: Siap mendaftarkan {options[sel_idx]}",
                    text_color=MediCipherTheme.SUCCESS
                )
        except Exception as exc:
            self.lbl_usb_status.configure(
                text=f"Status USB: Gagal memindai drive: {exc}",
                text_color=MediCipherTheme.DANGER
            )

    def _handle_capture_face(self):
        """Merekam wajah pengguna langsung dari webcam."""
        self.lbl_face_status.configure(
            text="Status Biometrik: Mengaktifkan kamera, silakan posisikan wajah Anda...",
            text_color=MediCipherTheme.WARNING
        )
        self.update_idletasks()

        try:
            is_cam_ok, cam_msg = FaceVerificationManager.test_camera_availability()
            if not is_cam_ok:
                raise RuntimeError(cam_msg)

            embedding = FaceVerificationManager.capture_and_extract_live_embedding()
            self.captured_face_embedding = embedding
            self.lbl_face_status.configure(
                text="Status Biometrik: Wajah berhasil diverifikasi dan diekstraksi (512 Dimensi).",
                text_color=MediCipherTheme.SUCCESS
            )
        except Exception as exc:
            self.captured_face_embedding = None
            self.lbl_face_status.configure(
                text=f"Status Biometrik Gagal: {exc}",
                text_color=MediCipherTheme.DANGER
            )

    def _handle_submit_registration(self):
        """Validasi dan eksekusi registrasi akun."""
        username = self.entry_username.get().strip()
        password = self.entry_password.get()
        confirm = self.entry_confirm.get()

        selected_drive_str = self.usb_option_menu.get()
        if not selected_drive_str or "Tidak ada drive" in selected_drive_str:
            messagebox.showerror("Kesalahan", "Pilih drive USB fisik yang valid terlebih dahulu.")
            return

        drive_path = selected_drive_str.split(" ")[0].strip()

        if self.captured_face_embedding is None:
            messagebox.showerror("Kesalahan", "Perekaman biometrik wajah wajib dilakukan sebelum mendaftar.")
            return

        try:
            RegistrationManager.register_user(
                username=username,
                password=password,
                confirm_password=confirm,
                face_embedding=self.captured_face_embedding,
                usb_drive_path=drive_path
            )
            messagebox.showinfo(
                "Registrasi Berhasil",
                f"Akun '{username}', template biometrik wajah, dan USB dongle berhasil didaftarkan.\n"
                "Aplikasi akan beralih ke halaman login."
            )
            if callable(self.on_registration_success):
                self.on_registration_success()
        except Exception as exc:
            messagebox.showerror("Registrasi Gagal", str(exc))
