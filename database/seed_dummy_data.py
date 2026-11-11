"""Skrip pengisian data medis fiktif (Seeder) untuk pengujian dan demonstrasi sistem MediCipher.

PERINGATAN ETIKA:
Seluruh data yang dihasilkan adalah data simulasi fiktif untuk keperluan tugas akademik Kriptografi,
bukan data pasien sungguhan.
"""
from datetime import date
from pathlib import Path
import sys

# Tambahkan direktori root ke sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.migrations import DatabaseMigration
from modules.medical_database import MedicalDatabaseService
from modules.asset_verification import AssetVerificationService


DUMMY_RECORDS = [
    {
        "record_code": "LAB-2026-001",
        "patient_code": "PSN-101",
        "patient_name": "Budi Santoso (Data Fiktif)",
        "exam_type": "Hematologi Lengkap",
        "exam_date": str(date.today()),
        "result": "Hb: 14.2 g/dL, Leukosit: 6.800 /uL, Trombosit: 248.000 /uL, Hematokrit: 42.5%",
        "notes": "Seluruh parameter dalam batas normal. Pasien dalam kondisi stabil, disarankan kontrol rutin 6 bulan."
    },
    {
        "record_code": "LAB-2026-002",
        "patient_code": "PSN-102",
        "patient_name": "Siti Nurhaliza (Data Fiktif)",
        "exam_type": "Glukosa Darah Puasa",
        "exam_date": str(date.today()),
        "result": "Glukosa Puasa: 92 mg/dL (Normal: 70 - 100 mg/dL), HbA1c: 5.4% (Normal: < 5.7%)",
        "notes": "Gula darah puasa dan kontrol glikemik normal. Tidak terdeteksi tanda-tanda resistensi insulin."
    },
    {
        "record_code": "LAB-2026-003",
        "patient_code": "PSN-103",
        "patient_name": "Dedi Kurniawan (Data Fiktif)",
        "exam_type": "Profil Lipid Lengkap",
        "exam_date": str(date.today()),
        "result": "Kolesterol Total: 185 mg/dL, HDL: 52 mg/dL, LDL: 110 mg/dL, Trigliserida: 135 mg/dL",
        "notes": "Profil lipid berada dalam rentang aman klinis. Disarankan mempertahankan pola makan rendah lemak jenuh."
    },
    {
        "record_code": "LAB-2026-004",
        "patient_code": "PSN-104",
        "patient_name": "Ratna Dewi (Data Fiktif)",
        "exam_type": "Uji Fungsi Ginjal",
        "exam_date": str(date.today()),
        "result": "Ureum: 24 mg/dL (Normal: 15 - 40 mg/dL), Kreatinin: 0.85 mg/dL (Normal: 0.6 - 1.1 mg/dL), eGFR: > 90 mL/min",
        "notes": "Laju filtrasi glomerulus dan fungsi ekskresi ginjal normal tanpa proteinuria."
    },
    {
        "record_code": "LAB-2026-005",
        "patient_code": "PSN-105",
        "patient_name": "Eko Prasetyo (Data Fiktif)",
        "exam_type": "Uji Fungsi Hati",
        "exam_date": str(date.today()),
        "result": "SGOT (AST): 22 U/L (Normal: < 35 U/L), SGPT (ALT): 28 U/L (Normal: < 45 U/L), Bilirubin Total: 0.7 mg/dL",
        "notes": "Aktivitas enzim transaminase hati dalam batas fisiologis normal. Tidak ada tanda sitolisis hepatik."
    }
]


def seed():
    print("Memulai inisialisasi dan pengisian data fiktif MediCipher...")
    try:
        # 1. Pastikan tabel tersedia
        DatabaseMigration.run_migrations()
        print("Tabel database MySQL terverifikasi.")

        # 2. Isi catatan rekam medis terenkripsi AES-256-GCM
        existing_records = MedicalDatabaseService.get_all_records()
        existing_codes = {r["record_code"] for r in existing_records}

        added_count = 0
        for rec in DUMMY_RECORDS:
            if rec["record_code"] not in existing_codes:
                MedicalDatabaseService.create_record(
                    record_code=rec["record_code"],
                    patient_code=rec["patient_code"],
                    patient_name=rec["patient_name"],
                    exam_type=rec["exam_type"],
                    exam_date=rec["exam_date"],
                    result=rec["result"],
                    notes=rec["notes"]
                )
                print(f"Berhasil menambahkan rekam medis terenkripsi: {rec['record_code']}")
                added_count += 1
            else:
                print(f"Rekam medis {rec['record_code']} sudah ada, melewati.")

        print(f"Selesai! {added_count} rekam medis terenkripsi baru berhasil ditambahkan.")

        # 3. Daftarkan aset contoh ke blockchain jika tersedia di folder assets
        assets_dir = BASE_DIR / "assets"
        sample_txt = assets_dir / "sample_lab_report.txt"
        sample_img = assets_dir / "sample_microscope_cell.png"

        if sample_txt.is_file():
            try:
                AssetVerificationService.register_asset(
                    file_path=sample_txt,
                    asset_code="AST-LAB-REPORT-001",
                    description="Laporan Hasil Laboratorium Patologi Darah Lengkap"
                )
                print("Berhasil mencatat sample_lab_report.txt ke blockchain.")
            except Exception as e:
                print(f"Pencatatan aset teks ke blockchain: {e}")

        if sample_img.is_file():
            try:
                AssetVerificationService.register_asset(
                    file_path=sample_img,
                    asset_code="AST-MICROSCOPE-001",
                    description="Citra Pengamatan Mikroskopis Sel Darah Merah dan Putih"
                )
                print("Berhasil mencatat sample_microscope_cell.png ke blockchain.")
            except Exception as e:
                print(f"Pencatatan aset gambar ke blockchain: {e}")

        print("Inisialisasi data fiktif selesai dengan sukses.")

    except Exception as exc:
        print(f"Gagal melakukan seeding data: {exc}")
        print("Pastikan server MySQL sedang aktif dan file .env telah dikonfigurasi.")


if __name__ == "__main__":
    seed()

