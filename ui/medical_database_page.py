"""Halaman Manajemen Arsip Rekam Medis Terenkripsi AES-256-GCM."""
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkTextbox, MediCipherTheme
)
from modules.medical_database import MedicalDatabaseService


class MedicalDatabasePage(CTkFrame):
    """Komponen antarmuka basis data rekam medis terenkripsi AES-256-GCM."""

    SAMPLE_RECORDS = [
        ("LAB-2026-001", "PSN-101", "Ahmad Fauzi (Fiktif)", "Hematologi Lengkap", str(date.today()), "Hb: 14.2 g/dL, Leukosit: 6.800/uL", "Kondisi stabil, pemeriksaan rutin berkala."),
        ("LAB-2026-002", "PSN-102", "Siti Nurhaliza (Fiktif)", "Glukosa Darah Puasa", str(date.today()), "Glukosa: 92 mg/dL (Normal)", "Gula darah normal, disarankan pola makan sehat."),
        ("LAB-2026-003", "PSN-103", "Dedi Kurniawan (Fiktif)", "Profil Lipid Lengkap", str(date.today()), "Kolesterol: 185 mg/dL, HDL: 52 mg/dL", "Parameter lipid dalam rentang aman klinis.")
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.selected_record_id = None
        self._build_ui()
        self._load_records()

    def _build_ui(self):
        # Header
        header = CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        CTkLabel(
            header,
            text="BASIS DATA ARSIP PEMERIKSAAN MEDIS TERENKRIPSI (AES-256-GCM)",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(anchor="w")

        CTkLabel(
            header,
            text="Informasi Sensitif Pasien Terenkripsi di MySQL dan Hanya Didekripsi Saat Ditampilkan oleh Aplikasi",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w")

        # Kontainer Utama: Form Input di Atas, Tabel Data di Bawah
        # 1. Panel Form Input
        form_card = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        form_card.pack(fill="x", padx=25, pady=(0, 15))

        form_top = CTkFrame(form_card, fg_color="transparent")
        form_top.pack(fill="x", padx=15, pady=(12, 6))

        CTkLabel(
            form_top,
            text="Formulir Arsip Rekam Medis",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.PRIMARY
        ).pack(side="left")

        btn_sample = CTkButton(
            form_top,
            text="Muat Data Fiktif",
            width=120,
            command=self._load_sample_form
        )
        btn_sample.pack(side="right")

        # Grid Input Baris 1: ID Pemeriksaan, Kode Pasien, Nama Pasien, Jenis Pemeriksaan, Tanggal
        grid_row1 = CTkFrame(form_card, fg_color="transparent")
        grid_row1.pack(fill="x", padx=15, pady=(0, 6))
        grid_row1.columnconfigure((0, 1, 2, 3, 4), weight=1)

        CTkLabel(grid_row1, text="ID Pemeriksaan:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=0, sticky="w")
        self.entry_record_code = CTkEntry(grid_row1, placeholder_text="LAB-2026-001")
        self.entry_record_code.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        CTkLabel(grid_row1, text="Kode Pasien:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=1, sticky="w")
        self.entry_patient_code = CTkEntry(grid_row1, placeholder_text="PSN-001")
        self.entry_patient_code.grid(row=1, column=1, sticky="ew", padx=(0, 6))

        CTkLabel(grid_row1, text="Nama Pasien (Fiktif):", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=2, sticky="w")
        self.entry_patient_name = CTkEntry(grid_row1, placeholder_text="Nama Pasien")
        self.entry_patient_name.grid(row=1, column=2, sticky="ew", padx=(0, 6))

        CTkLabel(grid_row1, text="Jenis Pemeriksaan:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=3, sticky="w")
        self.entry_exam_type = CTkEntry(grid_row1, placeholder_text="Hematologi / Glukosa")
        self.entry_exam_type.grid(row=1, column=3, sticky="ew", padx=(0, 6))

        CTkLabel(grid_row1, text="Tanggal (YYYY-MM-DD):", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=4, sticky="w")
        self.entry_exam_date = CTkEntry(grid_row1, placeholder_text=str(date.today()))
        self.entry_exam_date.grid(row=1, column=4, sticky="ew")

        # Grid Input Baris 2: Hasil Pemeriksaan & Catatan
        grid_row2 = CTkFrame(form_card, fg_color="transparent")
        grid_row2.pack(fill="x", padx=15, pady=(0, 8))
        grid_row2.columnconfigure((0, 1), weight=1)

        CTkLabel(grid_row2, text="Hasil Pemeriksaan Medis:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=0, sticky="w")
        self.entry_result = CTkEntry(grid_row2, placeholder_text="Parameter Hasil dan Nilai Rujukan")
        self.entry_result.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        CTkLabel(grid_row2, text="Catatan Hasil Pemeriksaan:", font=(MediCipherTheme.FONT_FAMILY, 8)).grid(row=0, column=1, sticky="w")
        self.entry_notes = CTkEntry(grid_row2, placeholder_text="Catatan atau Rekomendasi Klinis")
        self.entry_notes.grid(row=1, column=1, sticky="ew")

        # Tombol Aksi Form
        btn_bar = CTkFrame(form_card, fg_color="transparent")
        btn_bar.pack(fill="x", padx=15, pady=(0, 12))

        self.btn_save_record = CTkButton(
            btn_bar,
            text="Simpan Rekam Medis (Enkripsi AES-256-GCM ke MySQL)",
            fg_color=MediCipherTheme.PRIMARY,
            hover_color=MediCipherTheme.PRIMARY_HOVER,
            command=self._handle_save_record
        )
        self.btn_save_record.pack(side="left", padx=(0, 8))

        btn_clear = CTkButton(
            btn_bar,
            text="Bersihkan Form",
            width=110,
            command=self._clear_form
        )
        btn_clear.pack(side="left")

        # 2. Panel Daftar Arsip Pemeriksaan
        table_card = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        table_card.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        table_top = CTkFrame(table_card, fg_color="transparent")
        table_top.pack(fill="x", padx=15, pady=(12, 6))

        CTkLabel(
            table_top,
            text="Daftar Arsip Pemeriksaan Laboratorium (Didekripsi Secara Dinamis)",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(side="left")

        btn_reload = CTkButton(
            table_top,
            text="Muat Ulang Data",
            width=110,
            command=self._load_records
        )
        btn_reload.pack(side="right")

        btn_delete = CTkButton(
            table_top,
            text="Hapus Data Terpilih",
            fg_color=MediCipherTheme.DANGER,
            hover_color=MediCipherTheme.DANGER_HOVER,
            width=130,
            command=self._handle_delete_record
        )
        btn_delete.pack(side="right", padx=8)

        # Tabel Treeview
        tbl_container = tk.Frame(table_card, bg=MediCipherTheme.SURFACE_DARK)
        tbl_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("id", "record_code", "patient_code", "patient_name", "exam_type", "exam_date", "result", "notes")
        self.tree = ttk.Treeview(tbl_container, columns=columns, show="headings", height=8)

        self.tree.heading("id", text="ID")
        self.tree.heading("record_code", text="Kode Record")
        self.tree.heading("patient_code", text="Kode Pasien")
        self.tree.heading("patient_name", text="Nama Pasien")
        self.tree.heading("exam_type", text="Jenis Pemeriksaan")
        self.tree.heading("exam_date", text="Tanggal")
        self.tree.heading("result", text="Hasil Pemeriksaan")
        self.tree.heading("notes", text="Catatan Medis")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("record_code", width=100, anchor="center")
        self.tree.column("patient_code", width=90, anchor="center")
        self.tree.column("patient_name", width=140, anchor="w")
        self.tree.column("exam_type", width=130, anchor="w")
        self.tree.column("exam_date", width=90, anchor="center")
        self.tree.column("result", width=180, anchor="w")
        self.tree.column("notes", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(tbl_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    def _load_sample_form(self):
        """Mengisi formulir dengan data fiktif laboratorium."""
        import random
        sample = random.choice(self.SAMPLE_RECORDS)
        # Hasilkan suffix unik agar tidak terjadi duplicate key
        suffix = random.randint(100, 999)
        code = f"{sample[0]}-{suffix}"

        self.entry_record_code.delete(0, "end")
        self.entry_record_code.insert(0, code)
        self.entry_patient_code.delete(0, "end")
        self.entry_patient_code.insert(0, sample[1])
        self.entry_patient_name.delete(0, "end")
        self.entry_patient_name.insert(0, sample[2])
        self.entry_exam_type.delete(0, "end")
        self.entry_exam_type.insert(0, sample[3])
        self.entry_exam_date.delete(0, "end")
        self.entry_exam_date.insert(0, sample[4])
        self.entry_result.delete(0, "end")
        self.entry_result.insert(0, sample[5])
        self.entry_notes.delete(0, "end")
        self.entry_notes.insert(0, sample[6])

    def _clear_form(self):
        """Mengosongkan form input."""
        self.selected_record_id = None
        for entry in (
            self.entry_record_code, self.entry_patient_code, self.entry_patient_name,
            self.entry_exam_type, self.entry_exam_date, self.entry_result, self.entry_notes
        ):
            entry.delete(0, "end")
        self.entry_exam_date.insert(0, str(date.today()))
        self.btn_save_record.configure(text="Simpan Rekam Medis (Enkripsi AES-256-GCM ke MySQL)")

    def _handle_save_record(self):
        """Menyimpan atau memperbarui data rekam medis terenkripsi."""
        r_code = self.entry_record_code.get().strip()
        p_code = self.entry_patient_code.get().strip()
        p_name = self.entry_patient_name.get().strip()
        e_type = self.entry_exam_type.get().strip()
        e_date = self.entry_exam_date.get().strip()
        result = self.entry_result.get().strip()
        notes = self.entry_notes.get().strip()

        if not r_code or not p_code or not p_name or not e_type or not e_date:
            messagebox.showerror("Kesalahan", "Seluruh kolom data wajib diisi sebelum menyimpan.")
            return

        try:
            if self.selected_record_id is None:
                MedicalDatabaseService.create_record(
                    record_code=r_code,
                    patient_code=p_code,
                    patient_name=p_name,
                    exam_type=e_type,
                    exam_date=e_date,
                    result=result,
                    notes=notes
                )
                messagebox.showinfo("Sukses", f"Data rekam medis {r_code} berhasil dienkripsi AES-256-GCM dan disimpan ke MySQL.")
            else:
                MedicalDatabaseService.update_record(
                    record_id=self.selected_record_id,
                    record_code=r_code,
                    patient_code=p_code,
                    patient_name=p_name,
                    exam_type=e_type,
                    exam_date=e_date,
                    result=result,
                    notes=notes
                )
                messagebox.showinfo("Sukses", f"Data rekam medis {r_code} berhasil diperbarui.")

            self._clear_form()
            self._load_records()
        except Exception as exc:
            messagebox.showerror("Penyimpanan Gagal", str(exc))

    def _load_records(self):
        """Memuat seluruh arsip rekam medis dari MySQL dan mendekripsinya ke tabel."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            records = MedicalDatabaseService.get_all_records()
            for r in records:
                self.tree.insert("", "end", values=(
                    r["id"],
                    r["record_code"],
                    r["patient_code"],
                    r["patient_name"],
                    r["exam_type"],
                    r["exam_date"],
                    r["result"],
                    r["notes"]
                ))
        except Exception as exc:
            messagebox.showerror("Gagal Membaca Data", f"Gagal mengambil rekam medis: {exc}")

    def _on_row_selected(self, event):
        """Mengisi formulir saat baris tabel dipilih untuk edit."""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item = self.tree.item(selected_items[0])
        values = item["values"]
        if not values:
            return

        self.selected_record_id = values[0]
        self.entry_record_code.delete(0, "end")
        self.entry_record_code.insert(0, str(values[1]))
        self.entry_patient_code.delete(0, "end")
        self.entry_patient_code.insert(0, str(values[2]))
        self.entry_patient_name.delete(0, "end")
        self.entry_patient_name.insert(0, str(values[3]))
        self.entry_exam_type.delete(0, "end")
        self.entry_exam_type.insert(0, str(values[4]))
        self.entry_exam_date.delete(0, "end")
        self.entry_exam_date.insert(0, str(values[5]))
        self.entry_result.delete(0, "end")
        self.entry_result.insert(0, str(values[6]))
        self.entry_notes.delete(0, "end")
        self.entry_notes.insert(0, str(values[7]))

        self.btn_save_record.configure(text="Perbarui Rekam Medis (Enkripsi Ulang AES-256-GCM)")

    def _handle_delete_record(self):
        """Menghapus data rekam medis dengan konfirmasi pengguna."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Peringatan", "Pilih baris rekam medis yang ingin dihapus.")
            return

        item = self.tree.item(selected_items[0])
        values = item["values"]
        rec_id = values[0]
        rec_code = values[1]

        confirm = messagebox.askyesno(
            "Konfirmasi Penghapusan",
            f"Apakah Anda yakin ingin menghapus rekam medis '{rec_code}' secara permanen dari database?"
        )
        if not confirm:
            return

        try:
            MedicalDatabaseService.delete_record(rec_id, rec_code)
            messagebox.showinfo("Terhapus", f"Rekam medis {rec_code} berhasil dihapus.")
            self._clear_form()
            self._load_records()
        except Exception as exc:
            messagebox.showerror("Gagal Menghapus", str(exc))

