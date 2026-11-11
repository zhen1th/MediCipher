"""Halaman ringkasan Dashboard MediCipher."""
import tkinter as tk
from tkinter import ttk
from ui.theme import (
    CTkFrame, CTkLabel, CTkButton, MediCipherTheme
)
from database.repository import (
    MedicalRecordRepository, MedicalAssetRepository,
    BlockchainBlockRepository, AuditLogRepository
)
from authentication.login import SessionManager
from authentication.usb_dongle import USBDongleManager


class DashboardPage(CTkFrame):
    """Komponen tampilan ringkasan metrik dan audit keamanan."""

    def __init__(self, master, navigate_to=None, **kwargs):
        super().__init__(master, fg_color=MediCipherTheme.BG_DARK, **kwargs)
        self.navigate_to = navigate_to
        self._build_ui()

    def _build_ui(self):
        # Header Dashboard
        header_frame = CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(20, 15))

        CTkLabel(
            header_frame,
            text="DASHBOARD PENGAMANAN DATA MEDIS",
            font=(MediCipherTheme.FONT_FAMILY, 15, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(anchor="w")

        username_str = SessionManager.current_username or "Administrator"
        CTkLabel(
            header_frame,
            text=f"Sesi Aktif: {username_str} | Sistem Kriptografi & Blockchain Lokal MediCipher",
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w")

        # Kartu Ringkasan Metrik
        metrics_frame = CTkFrame(self, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=25, pady=(0, 15))
        metrics_frame.columnconfigure((0, 1, 2, 3), weight=1)

        total_records = MedicalRecordRepository.count_records()
        total_assets = MedicalAssetRepository.count_assets()
        total_blocks = BlockchainBlockRepository.count_blocks()

        # Cek status USB
        usb_status_str = "TERHUBUNG"
        usb_color = MediCipherTheme.SUCCESS
        if SessionManager.registered_volume_serial:
            drive = USBDongleManager.get_drive_by_serial(SessionManager.registered_volume_serial)
            if not drive:
                usb_status_str = "TERPUTUS"
                usb_color = MediCipherTheme.DANGER
        else:
            usb_status_str = "TIDAK TERDAFTAR"
            usb_color = MediCipherTheme.WARNING

        self._create_metric_card(metrics_frame, 0, "Arsip Pemeriksaan Medis", str(total_records), "Database AES-256-GCM")
        self._create_metric_card(metrics_frame, 1, "Dokumen Laboratorium", str(total_assets), "File AES-128-CBC (.medcipher)")
        self._create_metric_card(metrics_frame, 2, "Buku Besar Blockchain", str(total_blocks), "Blok SHA-256 Hash Chain")
        self._create_metric_card(metrics_frame, 3, "Status USB Dongle", usb_status_str, f"Serial: {SessionManager.registered_volume_serial or '-'}", usb_color)

        # Bagian Log Audit Aktivitas Terbaru
        log_frame = CTkFrame(self, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        log_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        log_header = CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=(12, 8))

        CTkLabel(
            log_header,
            text="Catatan Log Audit & Keamanan Sistem Terbaru",
            font=(MediCipherTheme.FONT_FAMILY, 11, "bold"),
            text_color=MediCipherTheme.TEXT_MAIN
        ).pack(side="left")

        btn_refresh = CTkButton(
            log_header,
            text="Muat Ulang Log",
            width=110,
            command=self._refresh_logs
        )
        btn_refresh.pack(side="right")

        # Treeview Tabel Log
        table_container = tk.Frame(log_frame, bg=MediCipherTheme.SURFACE_DARK)
        table_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("id", "waktu", "aktivitas", "status")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=10)
        self.tree.heading("id", text="ID")
        self.tree.heading("waktu", text="Waktu Kejadian")
        self.tree.heading("aktivitas", text="Aktivitas / Operasi")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("waktu", width=160, anchor="w")
        self.tree.column("aktivitas", width=360, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._refresh_logs()

    def _create_metric_card(self, parent, col, title, value, subtitle, val_color=MediCipherTheme.PRIMARY):
        card = CTkFrame(parent, fg_color=MediCipherTheme.CARD_BG, corner_radius=10)
        card.grid(row=0, column=col, padx=6, pady=5, sticky="nsew")

        CTkLabel(
            card,
            text=title,
            font=(MediCipherTheme.FONT_FAMILY, 9),
            text_color=MediCipherTheme.TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(10, 2))

        CTkLabel(
            card,
            text=value,
            font=(MediCipherTheme.FONT_FAMILY, 16, "bold"),
            text_color=val_color
        ).pack(anchor="w", padx=12, pady=(0, 2))

        CTkLabel(
            card,
            text=subtitle,
            font=(MediCipherTheme.FONT_FAMILY, 8),
            text_color=MediCipherTheme.TEXT_INACTIVE
        ).pack(anchor="w", padx=12, pady=(0, 10))

    def _refresh_logs(self):
        """Memuat riwayat log audit terbaru ke dalam tabel."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            logs = AuditLogRepository.get_recent_logs(limit=40)
            for log in logs:
                self.tree.insert("", "end", values=(
                    log["id"],
                    str(log["created_at"]),
                    log["activity"],
                    f"[{log['status']}]"
                ))
        except Exception:
            pass

