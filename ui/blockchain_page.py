"""Halaman Verifikasi Keaslian Aset Medis Berbasis Blockchain SHA-256 Hash Chain."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkTextbox, MediCipherTheme
)
from modules.asset_verification import AssetVerificationService
from cryptography.hashing import HashUtil


class BlockchainPage(CTkFrame):
    """Komponen antarmuka pencatatan dan verifikasi integritas rantai blok aset medis."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.selected_file_for_reg = None
        self._build_ui()
        self._load_ledger()

    def _build_ui(self):
        # Header
        header = CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        CTkLabel(
            header,
            text="VERIFIKASI INTEGRITAS ASET MEDIS BERBASIS BLOCKCHAIN (SHA-256 HASH CHAIN)",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(anchor="w")

        CTkLabel(
            header,
            text="Pencatatan Imutabel Berkas Medis ke Dalam Rantai Blok Lokal Tersimpan di Basis Data MySQL",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w")

        # Catatan Transparansi
        note_box = CTkFrame(self, fg_color=MediCipherTheme.SURFACE_DARK, corner_radius=6)
        note_box.pack(fill="x", padx=25, pady=(0, 12))
        CTkLabel(
            note_box,
            text="CATATAN TEKNIS: Fitur ini merupakan demonstrasi blockchain lokal berbasis SHA-256 Hash Chain untuk membuktikan keutuhan data.\nBukan blockchain terdistribusi (konsensus desentralisasi).",
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_MUTED,
            justify="left"
        ).pack(anchor="w", padx=12, pady=5)

        # Kontainer Pembagian: Bagian Pendaftaran Aset Baru & Bagian Verifikasi
        top_grid = CTkFrame(self, fg_color="transparent")
        top_grid.pack(fill="x", padx=25, pady=(0, 12))
        top_grid.columnconfigure(0, weight=1)
        top_grid.columnconfigure(1, weight=1)

        # 1. Panel Registrasi Aset Baru
        reg_panel = CTkFrame(top_grid, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        reg_panel.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        CTkLabel(
            reg_panel,
            text="1. Pencatatan Aset Baru ke Rantai Blok",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(anchor="w", padx=15, pady=(12, 6))

        file_pick_bar = CTkFrame(reg_panel, fg_color="transparent")
        file_pick_bar.pack(fill="x", padx=15, pady=(0, 4))
        btn_pick = CTkButton(file_pick_bar, text="Pilih Berkas Aset", command=self._browse_asset_file)
        btn_pick.pack(side="left")

        self.lbl_picked_file = CTkLabel(file_pick_bar, text="Berkas: -", font=(MediCipherTheme.FONT_FAMILY, 8))
        self.lbl_picked_file.pack(side="left", padx=10)

        # Input ID Aset & Keterangan
        form_reg = CTkFrame(reg_panel, fg_color="transparent")
        form_reg.pack(fill="x", padx=15, pady=(0, 8))
        form_reg.columnconfigure((0, 1), weight=1)

        CTkLabel(form_reg, text="Kode Aset:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=0, sticky="w")
        self.entry_asset_code = CTkEntry(form_reg, placeholder_text="AST-2026-001")
        self.entry_asset_code.grid(row=1, column=0, sticky="ew", padx=(0, 5))

        CTkLabel(form_reg, text="Keterangan Aset Medis:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=1, sticky="w")
        self.entry_description = CTkEntry(form_reg, placeholder_text="Hasil Lab Darah Pasien 001")
        self.entry_description.grid(row=1, column=1, sticky="ew")

        self.btn_submit_blockchain = CTkButton(
            reg_panel,
            text="Hitung Hash SHA-256 & Buat Blok Baru di Blockchain",
            fg_color=MediCipherTheme.PRIMARY,
            hover_color=MediCipherTheme.PRIMARY_HOVER,
            command=self._handle_add_to_blockchain
        )
        self.btn_submit_blockchain.pack(fill="x", padx=15, pady=(0, 12))

        # 2. Panel Verifikasi Aset & Integritas Rantai
        verify_panel = CTkFrame(top_grid, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        verify_panel.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        CTkLabel(
            verify_panel,
            text="2. Verifikasi Integritas Aset & Rantai Blok",
            font=(MediCipherTheme.FONT_FAMILY, 10, "bold"),
            text_color=MediCipherTheme.SUCCESS
        ).pack(anchor="w", padx=15, pady=(12, 6))

        btn_verify_bar = CTkFrame(verify_panel, fg_color="transparent")
        btn_verify_bar.pack(fill="x", padx=15, pady=(0, 6))

        btn_verify_selected = CTkButton(
            btn_verify_bar,
            text="Verifikasi Aset Terpilih di Tabel",
            fg_color=MediCipherTheme.SUCCESS,
            hover_color=MediCipherTheme.SUCCESS_HOVER,
            command=self._handle_verify_selected_asset
        )
        btn_verify_selected.pack(side="left", padx=(0, 8))

        btn_test_tamper = CTkButton(
            btn_verify_bar,
            text="Uji File Lain (Uji Manipulasi)",
            command=self._handle_verify_custom_file
        )
        btn_test_tamper.pack(side="left")

        # Status Hasil Verifikasi
        self.lbl_verif_status = CTkLabel(
            verify_panel,
            text="Status Verifikasi: Belum dijalankan.",
            font=(MediCipherTheme.FONT_FAMILY, 9, "bold"),
            text_color=MediCipherTheme.TEXT_MUTED
        )
        self.lbl_verif_status.pack(anchor="w", padx=15, pady=(0, 4))

        self.txt_verif_detail = CTkTextbox(verify_panel, height=65)
        self.txt_verif_detail.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # 3. Buku Besar Blockchain (Tabel Riwayat Blok)
        ledger_card = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        ledger_card.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        tbl_top = CTkFrame(ledger_card, fg_color="transparent")
        tbl_top.pack(fill="x", padx=15, pady=(10, 4))

        CTkLabel(
            tbl_top,
            text="Buku Besar Rantai Blok (Blockchain Ledger)",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(side="left")

        btn_refresh_tbl = CTkButton(tbl_top, text="Muat Ulang Buku Besar", width=130, command=self._load_ledger)
        btn_refresh_tbl.pack(side="right")

        tbl_container = tk.Frame(ledger_card, bg=MediCipherTheme.SURFACE_DARK)
        tbl_container.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        columns = ("block_index", "asset_id", "file_name", "file_hash", "prev_hash", "curr_hash", "timestamp")
        self.tree = ttk.Treeview(tbl_container, columns=columns, show="headings", height=8)

        self.tree.heading("block_index", text="Index")
        self.tree.heading("asset_id", text="ID Aset")
        self.tree.heading("file_name", text="Nama Berkas")
        self.tree.heading("file_hash", text="File Hash (SHA-256)")
        self.tree.heading("prev_hash", text="Previous Hash")
        self.tree.heading("curr_hash", text="Current Hash")
        self.tree.heading("timestamp", text="Waktu Blok")

        self.tree.column("block_index", width=50, anchor="center")
        self.tree.column("asset_id", width=60, anchor="center")
        self.tree.column("file_name", width=130, anchor="w")
        self.tree.column("file_hash", width=150, anchor="w")
        self.tree.column("prev_hash", width=140, anchor="w")
        self.tree.column("curr_hash", width=140, anchor="w")
        self.tree.column("timestamp", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(tbl_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _browse_asset_file(self):
        """Memilih file untuk dicatat ke blockchain."""
        path = filedialog.askopenfilename(
            title="Pilih Dokumen atau Citra Medis",
            filetypes=[("Seluruh File", "*.*")]
        )
        if path:
            self.selected_file_for_reg = Path(path)
            self.lbl_picked_file.configure(text=f"Berkas: {self.selected_file_for_reg.name}")
            if not self.entry_asset_code.get():
                import random
                self.entry_asset_code.insert(0, f"AST-{random.randint(1000, 9999)}")
            if not self.entry_description.get():
                self.entry_description.insert(0, f"Arsip pemeriksaan {self.selected_file_for_reg.name}")

    def _handle_add_to_blockchain(self):
        """Menambahkan aset ke blockchain."""
        if not self.selected_file_for_reg:
            messagebox.showerror("Kesalahan", "Pilih file aset medis terlebih dahulu.")
            return

        code = self.entry_asset_code.get().strip()
        desc = self.entry_description.get().strip()

        if not code:
            messagebox.showerror("Kesalahan", "Kode aset wajib diisi.")
            return

        try:
            asset_id, block = AssetVerificationService.register_asset(
                self.selected_file_for_reg, code, desc
            )
            messagebox.showinfo(
                "Pencatatan Berhasil",
                f"Aset {code} berhasil dicatatkan ke Blok Index {block.block_index}.\n"
                f"Current Hash: {block.current_hash[:16]}..."
            )
            self.entry_asset_code.delete(0, "end")
            self.entry_description.delete(0, "end")
            self.selected_file_for_reg = None
            self.lbl_picked_file.configure(text="Berkas: -")
            self._load_ledger()
        except Exception as exc:
            messagebox.showerror("Gagal Mencatat", str(exc))

    def _load_ledger(self):
        """Memuat seluruh isi blok rantai blockchain ke tabel."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            blocks = AssetVerificationService.get_blockchain_ledger()
            import json
            for b in blocks:
                asset_id_str = str(b["asset_id"]) if b["asset_id"] else "-"
                try:
                    b_data = json.loads(b["block_data"])
                    fname = b_data.get("file_name", "-")
                    fhash = b_data.get("file_hash", "-")
                except Exception:
                    fname = "-"
                    fhash = "-"

                self.tree.insert("", "end", values=(
                    b["block_index"],
                    asset_id_str,
                    fname,
                    fhash[:18] + "...",
                    b["previous_hash"][:18] + "...",
                    b["current_hash"][:18] + "...",
                    str(b["timestamp"])
                ))
        except Exception as exc:
            pass

    def _handle_verify_selected_asset(self):
        """Memverifikasi aset yang dipilih dari baris tabel."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Peringatan", "Pilih salah satu baris blok aset pada tabel buku besar terlebih dahulu.")
            return

        item = self.tree.item(selected_items[0])
        values = item["values"]
        asset_id_val = values[1]

        if str(asset_id_val) in ("-", "None", ""):
            messagebox.showinfo("Informasi", "Blok yang dipilih adalah Genesis Block yang tidak terikat file aset.")
            return

        asset_id = int(asset_id_val)
        self._execute_verification(asset_id, None)

    def _handle_verify_custom_file(self):
        """Memverifikasi aset terhadap file lain di komputer (untuk demonstrasi deteksi manipulasi file)."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Peringatan", "Pilih aset yang ingin diuji dari tabel terlebih dahulu.")
            return

        item = self.tree.item(selected_items[0])
        values = item["values"]
        asset_id_val = values[1]

        if str(asset_id_val) in ("-", "None", ""):
            return

        test_file = filedialog.askopenfilename(
            title="Pilih Berkas untuk Pengujian Keaslian Hash",
            filetypes=[("Seluruh File", "*.*")]
        )
        if test_file:
            self._execute_verification(int(asset_id_val), test_file)

    def _execute_verification(self, asset_id: int, file_path_override: str | None):
        """Menjalankan verifikasi hash dan rantai blok."""
        status, msg, info = AssetVerificationService.verify_asset(asset_id, file_path_override)

        if status == "VALID":
            self.lbl_verif_status.configure(
                text="[STATUS: VALID] Aset asli terbukti identik dan seluruh rantai blok valid.",
                text_color=MediCipherTheme.SUCCESS
            )
        elif status == "INVALID":
            self.lbl_verif_status.configure(
                text="[STATUS: INVALID] Integritas aset rusak atau file telah dimodifikasi!",
                text_color=MediCipherTheme.DANGER
            )
        else:
            self.lbl_verif_status.configure(
                text="[STATUS: CHAIN INVALID] Kerusakan pada buku besar blockchain terdeteksi!",
                text_color=MediCipherTheme.DANGER
            )

        detail_text = (
            f"Status Hasil: [{status}]\n"
            f"Keterangan: {msg}\n"
        )
        if info:
            detail_text += (
                f"Kode Aset: {info.get('asset_code', '-')}\n"
                f"Nama File: {info.get('file_name', '-')}\n"
                f"Hash Aktual File: {info.get('computed_hash', '-')}\n"
                f"Hash Terdaftar di Blockchain: {info.get('recorded_block_hash', '-')}\n"
                f"Blok Index: {info.get('block_index', '-')} | Current Block Hash: {info.get('block_hash', '-')}\n"
            )

        self.txt_verif_detail.delete("1.0", "end")
        self.txt_verif_detail.insert("1.0", detail_text)

