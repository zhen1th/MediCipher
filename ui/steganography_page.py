"""Halaman Steganografi Citra Laboratorium Medis (LSB + AES-256-GCM) untuk PNG dan JPG."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkTextbox, MediCipherTheme
)
from modules.medical_image import MedicalImageService


class SteganographyPage(CTkFrame):
    """Komponen antarmuka penyisipan dan ekstraksi pesan tersembunyi pada citra PNG dan JPG laboratorium."""

    SAMPLE_SECRET = (
        "ID Pemeriksaan: LAB-2026-001\n"
        "Kode Pasien: PSN-101\n"
        "Jenis Sampel: Darah EDTA\n"
        "Kode Dokumen Verifikasi: MED-2026-SECURE"
    )

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.selected_embed_img_path = None
        self.selected_extract_img_path = None
        self.preview_image_ref = None
        self._build_ui()

    def _build_ui(self):
        # Header
        header = CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        CTkLabel(
            header,
            text="STEGANOGRAFI CITRA LABORATORIUM MEDIS (LSB + AES-256-GCM)",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(anchor="w")

        CTkLabel(
            header,
            text="Penyisipan Informasi Rahasia pada Citra Medis PNG dan JPG dengan Pra-Enkripsi AES-256-GCM",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w")

        # Peringatan Etika Klinis
        warn_box = CTkFrame(self, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=6)
        warn_box.pack(fill="x", padx=25, pady=(0, 10))
        CTkLabel(
            warn_box,
            text="PERINGATAN KLINIS: Gunakan hanya gambar contoh atau salinan non-diagnostik.\nJangan pernah memodifikasi citra medis primer yang dijadikan rujukan diagnosa dokter.",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.WARNING,
            justify="left"
        ).pack(anchor="w", padx=12, pady=5)

        # Kontainer 2 Kolom (Penyisipan di Kiri, Ekstraksi di Kanan)
        grid_container = CTkFrame(self, fg_color="transparent")
        grid_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        grid_container.columnconfigure(0, weight=1)
        grid_container.columnconfigure(1, weight=1)

        # ----------------- PANEL KIRI: PENYISIPAN PESAN -----------------
        panel_embed = CTkFrame(grid_container, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        panel_embed.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        CTkLabel(
            panel_embed,
            text="1. Penyisipan Pesan ke Gambar (PNG / JPG)",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=15, pady=(12, 6))

        # Kontrol Pilih Gambar & Preview
        top_embed_bar = CTkFrame(panel_embed, fg_color="transparent")
        top_embed_bar.pack(fill="x", padx=15, pady=(0, 6))

        btn_browse_img = CTkButton(
            top_embed_bar,
            text="Pilih Gambar PNG / JPG",
            command=self._browse_image_for_embed
        )
        btn_browse_img.pack(side="left")

        self.lbl_embed_capacity = CTkLabel(
            top_embed_bar,
            text="Kapasitas Maksimal: -",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_embed_capacity.pack(side="right")

        # Thumbnail Preview Frame
        self.lbl_preview_img = CTkLabel(
            panel_embed,
            text="[Preview Gambar]",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_INACTIVE,
            fg_color=MediCipherTheme.SURFACE_DARK,
            height=100
        )
        self.lbl_preview_img.pack(fill="x", padx=15, pady=(0, 8))

        # Text Area Pesan Rahasia
        msg_header = CTkFrame(panel_embed, fg_color="transparent")
        msg_header.pack(fill="x", padx=15, pady=(0, 2))
        CTkLabel(msg_header, text="Pesan Rahasia yang Akan Disisipkan:", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(side="left")
        btn_sample_msg = CTkButton(msg_header, text="Muat Contoh Pesan", width=120, command=self._load_sample_message)
        btn_sample_msg.pack(side="right")

        self.txt_embed_message = CTkTextbox(panel_embed, height=80)
        self.txt_embed_message.pack(fill="x", padx=15, pady=(0, 6))

        # Passphrase Enkripsi Stegano
        CTkLabel(panel_embed, text="Passphrase Enkripsi Pesan (AES-256-GCM):", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=(0, 2))
        self.entry_embed_pass = CTkEntry(panel_embed, placeholder_text="Passphrase Steganografi", show="*")
        self.entry_embed_pass.pack(fill="x", padx=15, pady=(0, 10))

        self.btn_run_embed = CTkButton(
            panel_embed,
            text="Sisipkan Pesan & Simpan Gambar Stego",
            fg_color=MediCipherTheme.PRIMARY,
            hover_color=MediCipherTheme.PRIMARY_HOVER,
            command=self._handle_embed
        )
        self.btn_run_embed.pack(fill="x", padx=15, pady=(0, 12))

        # ----------------- PANEL KANAN: EKSTRAKSI PESAN -----------------
        panel_extract = CTkFrame(grid_container, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        panel_extract.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        CTkLabel(
            panel_extract,
            text="2. Ekstraksi Pesan dari Gambar Stego (PNG / JPG)",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.SUCCESS
        ).pack(anchor="w", padx=15, pady=(12, 6))

        btn_browse_stego = CTkButton(
            panel_extract,
            text="Pilih Gambar Stego (PNG / JPG)",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            command=self._browse_image_for_extract
        )
        btn_browse_stego.pack(fill="x", padx=15, pady=(0, 6))

        self.lbl_extract_file = CTkLabel(
            panel_extract,
            text="File Terpilih: -",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_extract_file.pack(anchor="w", padx=15, pady=(0, 8))

        # Passphrase Dekripsi Stegano
        CTkLabel(panel_extract, text="Passphrase Dekripsi Pesan:", font=(MediCipherTheme.FONT_FAMILY, 9)).pack(anchor="w", padx=15, pady=(0, 2))
        self.entry_extract_pass = CTkEntry(panel_extract, placeholder_text="Passphrase saat Penyisipan", show="*")
        self.entry_extract_pass.pack(fill="x", padx=15, pady=(0, 10))

        self.btn_run_extract = CTkButton(
            panel_extract,
            text="Ekstrak & Dekripsi Pesan Rahasia",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            command=self._handle_extract
        )
        self.btn_run_extract.pack(fill="x", padx=15, pady=(0, 8))

        CTkLabel(
            panel_extract,
            text="Hasil Pesan Rahasia yang Berhasil Diekstraksi:",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w", padx=15, pady=(0, 2))

        self.txt_extracted_message = CTkTextbox(panel_extract, height=140)
        self.txt_extracted_message.pack(fill="both", expand=True, padx=15, pady=(0, 12))

    def _browse_image_for_embed(self):
        """Memilih file gambar PNG atau JPG untuk disisipi pesan."""
        path = filedialog.askopenfilename(
            title="Pilih Gambar Laboratorium (PNG atau JPG)",
            filetypes=[
                ("Citra Medis (PNG, JPG, JPEG)", "*.png;*.jpg;*.jpeg"),
                ("PNG Images", "*.png"),
                ("JPEG Images", "*.jpg;*.jpeg"),
                ("Semua File", "*.*")
            ]
        )
        if path:
            self.selected_embed_img_path = Path(path)
            try:
                img = Image.open(path)
                w, h = img.size
                capacity_bytes = (w * h * 3) // 8
                self.lbl_embed_capacity.configure(
                    text=f"Format: {img.format} | {w}x{h} px | Kapasitas: ~{capacity_bytes} byte"
                )

                # Thumbnail preview
                thumb = img.copy()
                thumb.thumbnail((260, 90))
                self.preview_image_ref = ImageTk.PhotoImage(thumb)
                self.lbl_preview_img.configure(image=self.preview_image_ref, text="")
            except Exception as exc:
                messagebox.showerror("Format Gagal", f"Tidak dapat membaca gambar: {exc}")

    def _load_sample_message(self):
        """Memuat contoh pesan medis rahasia."""
        self.txt_embed_message.delete("1.0", "end")
        self.txt_embed_message.insert("1.0", self.SAMPLE_SECRET)
        self.entry_embed_pass.delete(0, "end")
        self.entry_embed_pass.insert(0, "KunciStegano2026!")

    def _handle_embed(self):
        """Eksekusi proses penyisipan LSB + AES-256-GCM."""
        if not self.selected_embed_img_path:
            messagebox.showerror("Kesalahan", "Pilih file gambar PNG atau JPG asli terlebih dahulu.")
            return

        msg = self.txt_embed_message.get("1.0", "end").strip()
        passphrase = self.entry_embed_pass.get().strip()

        if not msg:
            messagebox.showerror("Kesalahan", "Pesan rahasia tidak boleh kosong.")
            return
        if not passphrase:
            messagebox.showerror("Kesalahan", "Passphrase enkripsi tidak boleh kosong.")
            return

        src_suffix = self.selected_embed_img_path.suffix.lower()
        if src_suffix not in {".png", ".jpg", ".jpeg"}:
            src_suffix = ".png"

        default_dest = self.selected_embed_img_path.with_name(
            self.selected_embed_img_path.stem + "_stego" + src_suffix
        )
        dest = filedialog.asksaveasfilename(
            title="Simpan Citra Steganografi",
            initialfile=default_dest.name,
            initialdir=str(default_dest.parent),
            defaultextension=src_suffix,
            filetypes=[
                ("Format Sumber Sama", f"*{src_suffix}"),
                ("PNG Image (Lossless)", "*.png"),
                ("JPEG Image", "*.jpg;*.jpeg"),
                ("Semua File", "*.*")
            ]
        )
        if not dest:
            return

        try:
            out_path = MedicalImageService.embed_secret(
                self.selected_embed_img_path, dest, msg, passphrase
            )
            messagebox.showinfo(
                "Penyisipan Berhasil",
                f"Pesan rahasia berhasil dienkripsi AES-256-GCM dan disisipkan ke citra baru:\n{out_path.name}"
            )
        except Exception as exc:
            messagebox.showerror("Penyisipan Gagal", str(exc))

    def _browse_image_for_extract(self):
        """Memilih file gambar stego untuk diekstraksi."""
        path = filedialog.askopenfilename(
            title="Pilih Citra PNG atau JPG Berisi Pesan Rahasia",
            filetypes=[
                ("Citra Medis Stego (PNG, JPG, JPEG)", "*.png;*.jpg;*.jpeg"),
                ("PNG Images", "*.png"),
                ("JPEG Images", "*.jpg;*.jpeg"),
                ("Semua File", "*.*")
            ]
        )
        if path:
            self.selected_extract_img_path = Path(path)
            self.lbl_extract_file.configure(
                text=f"File Terpilih: {self.selected_extract_img_path.name}"
            )

    def _handle_extract(self):
        """Eksekusi proses ekstraksi dan dekripsi LSB."""
        if not self.selected_extract_img_path:
            messagebox.showerror("Kesalahan", "Pilih file gambar PNG atau JPG ber-stego terlebih dahulu.")
            return

        passphrase = self.entry_extract_pass.get().strip()
        if not passphrase:
            messagebox.showerror("Kesalahan", "Passphrase dekripsi wajib diisi.")
            return

        try:
            extracted_msg = MedicalImageService.extract_secret(
                self.selected_extract_img_path, passphrase
            )
            self.txt_extracted_message.delete("1.0", "end")
            self.txt_extracted_message.insert("1.0", extracted_msg)
            messagebox.showinfo(
                "Ekstraksi Berhasil",
                "Integritas payload steganografi terverifikasi dan pesan berhasil didekripsi."
            )
        except Exception as exc:
            messagebox.showerror("Ekstraksi Gagal", str(exc))

