"""Halaman Enkripsi dan Dekripsi Berkas Dokumen Laboratorium (.medcipher)."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, CTkEntry, MediCipherTheme
)
from modules.medical_file import MedicalFileService
from cryptography.hashing import HashUtil


class FileEncryptionPage(CTkFrame):
    """Komponen antarmuka pengamanan berkas dokumen medis dengan AES-128-CBC dan HMAC-SHA256."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.selected_enc_input_path = None
        self.selected_dec_input_path = None
        self._build_ui()

    def _build_ui(self):
        # Header
        header = CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        CTkLabel(
            header,
            text="PENGAMANAN BERKAS DOKUMEN LABORATORIUM (.MEDCIPHER)",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(anchor="w")

        CTkLabel(
            header,
            text="Enkripsi AES-128-CBC dengan IV Acak per Operasi dan Verifikasi Keaslian HMAC-SHA256",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w")

        # Kontainer 2 Kolom (Enkripsi di Kiri, Dekripsi di Kanan)
        grid_container = CTkFrame(self, fg_color="transparent")
        grid_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        grid_container.columnconfigure(0, weight=1)
        grid_container.columnconfigure(1, weight=1)

        # ----------------- PANEL KIRI: ENKRIPSI FILE -----------------
        panel_enc = CTkFrame(grid_container, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        panel_enc.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        CTkLabel(
            panel_enc,
            text="1. Enkripsi Dokumen Asli (.pdf, .docx, .txt)",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 8))

        btn_browse_enc = CTkButton(
            panel_enc,
            text="Pilih Berkas Dokumen",
            command=self._browse_file_for_encryption
        )
        btn_browse_enc.pack(fill="x", padx=15, pady=(0, 8))

        # Informasi Berkas Terpilih
        info_box_enc = CTkFrame(panel_enc, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=6)
        info_box_enc.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_enc_file_name = CTkLabel(info_box_enc, text="Nama File: -", font=(MediCipherTheme.FONT_FAMILY, 8))
        self.lbl_enc_file_name.pack(anchor="w", padx=10, pady=(6, 2))

        self.lbl_enc_file_size = CTkLabel(info_box_enc, text="Ukuran: -", font=(MediCipherTheme.FONT_FAMILY, 8))
        self.lbl_enc_file_size.pack(anchor="w", padx=10, pady=(0, 2))

        self.lbl_enc_file_hash = CTkLabel(info_box_enc, text="SHA-256: -", font=(MediCipherTheme.FONT_FAMILY, 8), text_color=MediCipherTheme.TEXT_INACTIVE)
        self.lbl_enc_file_hash.pack(anchor="w", padx=10, pady=(0, 6))

        # Passphrase Enkripsi
        CTkLabel(panel_enc, text="Passphrase Enkripsi Dokumen:", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=(0, 2))
        self.entry_enc_passphrase = CTkEntry(panel_enc, placeholder_text="Passphrase Pengamanan", show="*")
        self.entry_enc_passphrase.pack(fill="x", padx=15, pady=(0, 12))

        self.btn_run_encrypt = CTkButton(
            panel_enc,
            text="Enkripsi ke Format .medcipher",
            fg_color=MediCipherTheme.PRIMARY,
            hover_color=MediCipherTheme.PRIMARY_HOVER,
            command=self._handle_encrypt_file
        )
        self.btn_run_encrypt.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_enc_result = CTkLabel(panel_enc, text="", font=(MediCipherTheme.FONT_FAMILY, 8), text_color=MediCipherTheme.SUCCESS)
        self.lbl_enc_result.pack(anchor="w", padx=15, pady=(0, 10))

        # ----------------- PANEL KANAN: DEKRIPSI FILE -----------------
        panel_dec = CTkFrame(grid_container, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        panel_dec.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        CTkLabel(
            panel_dec,
            text="2. Dekripsi Berkas Terproteksi (.medcipher)",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.SUCCESS
        ).pack(anchor="w", padx=15, pady=(15, 8))

        btn_browse_dec = CTkButton(
            panel_dec,
            text="Pilih File .medcipher",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            command=self._browse_file_for_decryption
        )
        btn_browse_dec.pack(fill="x", padx=15, pady=(0, 8))

        # Informasi Berkas Terenkripsi Terpilih
        info_box_dec = CTkFrame(panel_dec, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=6)
        info_box_dec.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_dec_file_name = CTkLabel(info_box_dec, text="Nama File: -", font=(MediCipherTheme.FONT_FAMILY, 8))
        self.lbl_dec_file_name.pack(anchor="w", padx=10, pady=(6, 2))

        self.lbl_dec_file_size = CTkLabel(info_box_dec, text="Ukuran: -", font=(MediCipherTheme.FONT_FAMILY, 8))
        self.lbl_dec_file_size.pack(anchor="w", padx=10, pady=(0, 2))

        self.lbl_dec_status_tag = CTkLabel(info_box_dec, text="Format: Belum dipilih", font=(MediCipherTheme.FONT_FAMILY, 8), text_color=MediCipherTheme.TEXT_INACTIVE)
        self.lbl_dec_status_tag.pack(anchor="w", padx=10, pady=(0, 6))

        # Passphrase Dekripsi
        CTkLabel(panel_dec, text="Passphrase Dekripsi:", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=(0, 2))
        self.entry_dec_passphrase = CTkEntry(panel_dec, placeholder_text="Passphrase yang Digunakan saat Enkripsi", show="*")
        self.entry_dec_passphrase.pack(fill="x", padx=15, pady=(0, 12))

        self.btn_run_decrypt = CTkButton(
            panel_dec,
            text="Verifikasi HMAC & Dekripsi File",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            command=self._handle_decrypt_file
        )
        self.btn_run_decrypt.pack(fill="x", padx=15, pady=(0, 10))

        self.lbl_dec_result = CTkLabel(panel_dec, text="", font=(MediCipherTheme.FONT_FAMILY, 8), text_color=MediCipherTheme.SUCCESS)
        self.lbl_dec_result.pack(anchor="w", padx=15, pady=(0, 10))

    def _browse_file_for_encryption(self):
        """Memilih berkas dokumen yang akan dienkripsi."""
        path = filedialog.askopenfilename(
            title="Pilih Berkas Dokumen Medis",
            filetypes=[
                ("Dokumen Laboratorium", "*.pdf;*.docx;*.txt"),
                ("Seluruh File", "*.*")
            ]
        )
        if path:
            self.selected_enc_input_path = Path(path)
            size_kb = os.path.getsize(path) / 1024
            f_hash = HashUtil.sha256_file(path)
            self.lbl_enc_file_name.configure(text=f"Nama File: {self.selected_enc_input_path.name}")
            self.lbl_enc_file_size.configure(text=f"Ukuran: {size_kb:.2f} KB")
            self.lbl_enc_file_hash.configure(text=f"SHA-256: {f_hash[:24]}...")
            self.lbl_enc_result.configure(text="")

    def _browse_file_for_decryption(self):
        """Memilih berkas .medcipher yang akan didekripsi."""
        path = filedialog.askopenfilename(
            title="Pilih Berkas Terenkripsi MediCipher",
            filetypes=[
                ("MediCipher Encrypted Files", "*.medcipher"),
                ("Seluruh File", "*.*")
            ]
        )
        if path:
            self.selected_dec_input_path = Path(path)
            size_kb = os.path.getsize(path) / 1024
            self.lbl_dec_file_name.configure(text=f"Nama File: {self.selected_dec_input_path.name}")
            self.lbl_dec_file_size.configure(text=f"Ukuran: {size_kb:.2f} KB")
            self.lbl_dec_status_tag.configure(text="Format: Terdeteksi ekstensi .medcipher")
            self.lbl_dec_result.configure(text="")

    def _handle_encrypt_file(self):
        """Eksekusi proses enkripsi file."""
        if not self.selected_enc_input_path:
            messagebox.showerror("Kesalahan", "Pilih file yang ingin dienkripsi terlebih dahulu.")
            return

        passphrase = self.entry_enc_passphrase.get().strip()
        if not passphrase:
            messagebox.showerror("Kesalahan", "Passphrase enkripsi tidak boleh kosong.")
            return

        # Tentukan lokasi penyimpanan
        default_output = self.selected_enc_input_path.with_name(self.selected_enc_input_path.name + ".medcipher")
        dest = filedialog.asksaveasfilename(
            title="Simpan File Terenkripsi",
            initialfile=default_output.name,
            initialdir=str(default_output.parent),
            defaultextension=".medcipher",
            filetypes=[("MediCipher Encrypted File", "*.medcipher")]
        )
        if not dest:
            return

        try:
            out_path = MedicalFileService.encrypt_document(
                self.selected_enc_input_path, dest, passphrase
            )
            self.lbl_enc_result.configure(
                text=f"Sukses! Tersimpan di: {out_path.name}",
                text_color=MediCipherTheme.SUCCESS
            )
            messagebox.showinfo("Enkripsi Berhasil", f"File berhasil dienkripsi dan diproteksi HMAC.\nOutput: {out_path}")
        except Exception as exc:
            messagebox.showerror("Enkripsi Gagal", str(exc))

    def _handle_decrypt_file(self):
        """Eksekusi proses dekripsi file."""
        if not self.selected_dec_input_path:
            messagebox.showerror("Kesalahan", "Pilih file .medcipher yang ingin didekripsi.")
            return

        passphrase = self.entry_dec_passphrase.get().strip()
        if not passphrase:
            messagebox.showerror("Kesalahan", "Passphrase dekripsi tidak boleh kosong.")
            return

        # Tebak nama file asli dengan menghapus ekstensi .medcipher jika ada
        suggested_name = self.selected_dec_input_path.name.replace(".medcipher", "")
        dest = filedialog.asksaveasfilename(
            title="Simpan File Hasil Dekripsi",
            initialfile="DEKRIPSI_" + suggested_name,
            initialdir=str(self.selected_dec_input_path.parent)
        )
        if not dest:
            return

        try:
            out_path = MedicalFileService.decrypt_document(
                self.selected_dec_input_path, dest, passphrase
            )
            self.lbl_dec_result.configure(
                text=f"Sukses! File asli didekripsi ke: {out_path.name}",
                text_color=MediCipherTheme.SUCCESS
            )
            messagebox.showinfo("Dekripsi Berhasil", f"Integritas HMAC terverifikasi valid!\nFile asli tersimpan di: {out_path}")
        except Exception as exc:
            messagebox.showerror("Dekripsi Gagal", str(exc))

