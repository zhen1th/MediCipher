"""Halaman Super Enkripsi Teks Medis (Vigenere + AES-128-ECB + HMAC-SHA256)."""
import tkinter as tk
from tkinter import filedialog, messagebox
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkTextbox, MediCipherTheme
)
from modules.medical_text import MedicalTextService


class TextEncryptionPage(CTkFrame):
    """Komponen antarmuka super enkripsi dan dekripsi catatan medis."""

    SAMPLE_MEDICAL_TEXT = (
        "ID Pasien: PSN-001\n"
        "Nama Pasien: Budi Santoso (Data Fiktif Pengujian)\n"
        "Pemeriksaan: Profil Hematologi Rutin\n"
        "Hasil:\n"
        "- Hemoglobin: 13.5 g/dL (Normal: 13.0 - 17.0)\n"
        "- Leukosit: 7.200 /uL (Normal: 4.000 - 10.000)\n"
        "- Trombosit: 250.000 /uL (Normal: 150.000 - 450.000)\n"
        "- Eritrosit: 4.8 juta /uL (Normal: 4.5 - 5.5)\n"
        "Catatan Klinis: Seluruh parameter dalam batas normal. Pasien dalam kondisi stabil."
    )

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        CTkLabel(
            header,
            text="SUPER ENKRIPSI TEKS CATATAN MEDIS",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(anchor="w")

        CTkLabel(
            header,
            text="Algoritma Bertingkat: Vigenere Cipher dilanjutkan AES-128-ECB dengan Verifikasi Integritas HMAC-SHA256",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w")

        # Peringatan Akademik
        warn_box = CTkFrame(self, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=6)
        warn_box.pack(fill="x", padx=25, pady=(0, 12))
        CTkLabel(
            warn_box,
            text="PEMBERITAHUAN AKADEMIK: Mode AES-ECB digunakan untuk memenuhi kriteria demonstrasi tugas kuliah Kriptografi.\nMode ECB tidak menyembunyikan pola data dan tidak untuk data klinis riil.",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.WARNING,
            justify="left"
        ).pack(anchor="w", padx=12, pady=6)

        # Kontainer Utama 2 Kolom (Input & Enkripsi di Kiri, Ciphertext & Dekripsi di Kanan)
        main_grid = CTkFrame(self, fg_color="transparent")
        main_grid.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        main_grid.columnconfigure(0, weight=1)
        main_grid.columnconfigure(1, weight=1)

        # Kolom Kiri: Plaintext dan Form Kunci
        col_left = CTkFrame(main_grid, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        col_left.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        lbl_plain_header = CTkFrame(col_left, fg_color="transparent")
        lbl_plain_header.pack(fill="x", padx=15, pady=(12, 4))
        CTkLabel(
            lbl_plain_header,
            text="1. Teks Medis Plaintext (Input Tak Terbatas)",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(side="left")

        btn_sample = CTkButton(
            lbl_plain_header,
            text="Muat Contoh",
            width=90,
            command=self._load_sample_data
        )
        btn_sample.pack(side="right", padx=(5, 0))

        btn_load_file = CTkButton(
            lbl_plain_header,
            text="Buka File Teks...",
            width=110,
            command=self._load_text_file
        )
        btn_load_file.pack(side="right")

        self.txt_plaintext = CTkTextbox(col_left, height=140, wrap="word")
        self.txt_plaintext.pack(fill="both", expand=True, padx=15, pady=(0, 4))
        self.txt_plaintext.bind("<KeyRelease>", self._update_text_counter)

        # Baris Indikator Kapasitas Tak Terbatas dan Hitung Karakter
        counter_bar = CTkFrame(col_left, fg_color="transparent")
        counter_bar.pack(fill="x", padx=15, pady=(0, 8))

        self.lbl_text_counter = CTkLabel(
            counter_bar,
            text="Panjang: 0 karakter | 0 baris (Kapasitas Tak Terbatas)",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_text_counter.pack(side="left")

        btn_clear_plain = CTkButton(
            counter_bar,
            text="Bersihkan Teks",
            width=95,
            height=22,
            fg_color=MediCipherTheme.SURFACE_DARK,
            hover_color=MediCipherTheme.DANGER,
            command=self._clear_plaintext
        )
        btn_clear_plain.pack(side="right")

        # Input Kunci Vigenere & Passphrase AES
        key_grid = CTkFrame(col_left, fg_color="transparent")
        key_grid.pack(fill="x", padx=15, pady=(0, 8))

        CTkLabel(key_grid, text="Kunci Vigenere (Huruf A-Z):", font=(MediCipherTheme.FONT_FAMILY, 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.entry_vigenere_key = CTkEntry(key_grid, placeholder_text="Contoh: KRIPTOLAB", width=220)
        self.entry_vigenere_key.grid(row=0, column=1, sticky="e", pady=2, padx=(5, 0))

        CTkLabel(key_grid, text="Passphrase AES-128:", font=(MediCipherTheme.FONT_FAMILY, 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.entry_aes_passphrase = CTkEntry(key_grid, placeholder_text="Passphrase Rahasia", show="*", width=220)
        self.entry_aes_passphrase.grid(row=1, column=1, sticky="e", pady=2, padx=(5, 0))

        # Tombol Aksi Enkripsi
        self.btn_encrypt = CTkButton(
            col_left,
            text="Jalankan Super Enkripsi (Vigenere -> AES-128-ECB -> HMAC)",
            fg_color=MediCipherTheme.PRIMARY,
            hover_color=MediCipherTheme.PRIMARY_HOVER,
            command=self._handle_encrypt
        )
        self.btn_encrypt.pack(fill="x", padx=15, pady=(5, 12))

        # Kolom Kanan: Ciphertext Base64 dan Hasil Dekripsi
        col_right = CTkFrame(main_grid, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        col_right.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        lbl_cipher_header = CTkFrame(col_right, fg_color="transparent")
        lbl_cipher_header.pack(fill="x", padx=15, pady=(12, 4))
        CTkLabel(
            lbl_cipher_header,
            text="2. Ciphertext Terproteksi (Format Base64)",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(side="left")

        btn_copy = CTkButton(
            lbl_cipher_header,
            text="Salin",
            width=70,
            command=self._copy_ciphertext
        )
        btn_copy.pack(side="right", padx=(5, 0))

        btn_save_cipher = CTkButton(
            lbl_cipher_header,
            text="Simpan File...",
            width=95,
            command=self._save_ciphertext_file
        )
        btn_save_cipher.pack(side="right")

        self.txt_ciphertext = CTkTextbox(col_right, height=100, wrap="char")
        self.txt_ciphertext.pack(fill="x", padx=15, pady=(0, 6))

        # Tombol Aksi Dekripsi
        self.btn_decrypt = CTkButton(
            col_right,
            text="Jalankan Super Dekripsi (Verifikasi HMAC -> AES -> Vigenere)",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            command=self._handle_decrypt
        )
        self.btn_decrypt.pack(fill="x", padx=15, pady=(2, 8))

        dec_header = CTkFrame(col_right, fg_color="transparent")
        dec_header.pack(fill="x", padx=15, pady=(0, 2))

        CTkLabel(
            dec_header,
            text="Hasil Plaintext Setelah Dekripsi & Verifikasi Integritas:",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(side="left")

        btn_save_dec = CTkButton(
            dec_header,
            text="Simpan Hasil...",
            width=95,
            command=self._save_decrypted_file
        )
        btn_save_dec.pack(side="right")

        self.txt_decrypted = CTkTextbox(col_right, height=100, wrap="word")
        self.txt_decrypted.pack(fill="both", expand=True, padx=15, pady=(0, 12))

    def _update_text_counter(self, event=None):
        """Memperbarui penghitung karakter dan baris teks."""
        text_content = self.txt_plaintext.get("1.0", "end-1c")
        char_count = len(text_content)
        line_count = len(text_content.splitlines()) if text_content else 0
        self.lbl_text_counter.configure(
            text=f"Panjang: {char_count:,} karakter | {line_count:,} baris (Kapasitas Tak Terbatas)"
        )

    def _clear_plaintext(self):
        """Membersihkan area teks plaintext."""
        self.txt_plaintext.delete("1.0", "end")
        self._update_text_counter()

    def _load_text_file(self):
        """Memuat dokumen teks medis dari file tanpa batasan ukuran."""
        path = filedialog.askopenfilename(
            title="Pilih File Teks Medis",
            filetypes=[
                ("File Teks", "*.txt;*.log;*.csv;*.json;*.md"),
                ("Semua File", "*.*")
            ]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.txt_plaintext.delete("1.0", "end")
                self.txt_plaintext.insert("1.0", content)
                self._update_text_counter()
                messagebox.showinfo(
                    "File Dimuat",
                    f"Berhasil memuat {len(content):,} karakter dari file:\n{path}"
                )
            except Exception as exc:
                messagebox.showerror("Gagal Membaca File", str(exc))

    def _load_sample_data(self):
        """Memuat data catatan medis fiktif ke text area."""
        self.txt_plaintext.delete("1.0", "end")
        self.txt_plaintext.insert("1.0", self.SAMPLE_MEDICAL_TEXT)
        self.entry_vigenere_key.delete(0, "end")
        self.entry_vigenere_key.insert(0, "LABORATORIUM")
        self.entry_aes_passphrase.delete(0, "end")
        self.entry_aes_passphrase.insert(0, "KunciSuperMedis2026!")
        self._update_text_counter()

    def _handle_encrypt(self):
        """Menjalankan enkripsi super pada teks berukuran tak terbatas."""
        plaintext = self.txt_plaintext.get("1.0", "end-1c")
        v_key = self.entry_vigenere_key.get().strip()
        a_pass = self.entry_aes_passphrase.get().strip()

        if not plaintext.strip():
            messagebox.showerror("Kesalahan", "Teks medis plaintext tidak boleh kosong.")
            return
        if not v_key:
            messagebox.showerror("Kesalahan", "Kunci Vigenere tidak boleh kosong.")
            return
        if not a_pass:
            messagebox.showerror("Kesalahan", "Passphrase AES tidak boleh kosong.")
            return

        try:
            res = MedicalTextService.encrypt_medical_note(plaintext, v_key, a_pass)
            self.txt_ciphertext.delete("1.0", "end")
            self.txt_ciphertext.insert("1.0", res["ciphertext"])
            messagebox.showinfo(
                "Enkripsi Berhasil",
                f"Teks medis ({len(plaintext):,} karakter) berhasil dienkripsi dan diproteksi HMAC-SHA256."
            )
        except Exception as exc:
            messagebox.showerror("Enkripsi Gagal", str(exc))

    def _handle_decrypt(self):
        """Menjalankan dekripsi super."""
        ciphertext = self.txt_ciphertext.get("1.0", "end-1c").strip()
        v_key = self.entry_vigenere_key.get().strip()
        a_pass = self.entry_aes_passphrase.get().strip()

        if not ciphertext:
            messagebox.showerror("Kesalahan", "Ciphertext tidak boleh kosong.")
            return
        if not v_key or not a_pass:
            messagebox.showerror("Kesalahan", "Kunci Vigenere dan Passphrase AES harus diisi untuk proses dekripsi.")
            return

        try:
            res = MedicalTextService.decrypt_medical_note(ciphertext, v_key, a_pass)
            self.txt_decrypted.delete("1.0", "end")
            self.txt_decrypted.insert("1.0", res["plaintext"])
            messagebox.showinfo(
                "Dekripsi Berhasil",
                f"Integritas HMAC terverifikasi dan teks ({len(res['plaintext']):,} karakter) berhasil didekripsi."
            )
        except Exception as exc:
            messagebox.showerror("Dekripsi Gagal", str(exc))

    def _copy_ciphertext(self):
        """Menyalin ciphertext Base64 ke clipboard."""
        ct = self.txt_ciphertext.get("1.0", "end-1c").strip()
        if ct:
            self.clipboard_clear()
            self.clipboard_append(ct)
            messagebox.showinfo("Disalin", "Ciphertext berhasil disalin ke clipboard.")

    def _save_ciphertext_file(self):
        """Menyimpan ciphertext Base64 ke file dokumen teks."""
        ct = self.txt_ciphertext.get("1.0", "end-1c").strip()
        if not ct:
            messagebox.showerror("Kesalahan", "Ciphertext masih kosong.")
            return
        dest = filedialog.asksaveasfilename(
            title="Simpan Ciphertext",
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("Semua File", "*.*")]
        )
        if dest:
            try:
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(ct)
                messagebox.showinfo("Tersimpan", f"Ciphertext berhasil disimpan ke:\n{dest}")
            except Exception as exc:
                messagebox.showerror("Gagal Menyimpan", str(exc))

    def _save_decrypted_file(self):
        """Menyimpan hasil plaintext dekripsi ke file dokumen teks."""
        plain = self.txt_decrypted.get("1.0", "end-1c")
        if not plain.strip():
            messagebox.showerror("Kesalahan", "Hasil dekripsi masih kosong.")
            return
        dest = filedialog.asksaveasfilename(
            title="Simpan Plaintext Hasil Dekripsi",
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("Semua File", "*.*")]
        )
        if dest:
            try:
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(plain)
                messagebox.showinfo("Tersimpan", f"Plaintext berhasil disimpan ke:\n{dest}")
            except Exception as exc:
                messagebox.showerror("Gagal Menyimpan", str(exc))

