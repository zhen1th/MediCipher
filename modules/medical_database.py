"""Modul layanan database rekam medis aman menggunakan enkripsi AES-256-GCM."""
import json
from database.repository import MedicalRecordRepository, AuditLogRepository
from cryptography.aes_gcm import AESGCMCipher
from cryptography.key_manager import KeyManager


class MedicalDatabaseService:
    """Layanan CRUD rekam medis laboratorium dengan enkripsi kolom sensitif AES-256-GCM."""

    @classmethod
    def create_record(
        cls,
        record_code: str,
        patient_code: str,
        patient_name: str,
        exam_type: str,
        exam_date: str,
        result: str,
        notes: str
    ) -> int:
        """Mengenkripsi seluruh data sensitif dan menyimpannya ke tabel medical_records MySQL."""
        if not record_code or not patient_code or not patient_name or not exam_type or not exam_date:
            raise ValueError("Seluruh kolom wajib (ID, Kode, Nama, Jenis, Tanggal) harus diisi.")

        db_key = KeyManager.get_database_key()

        # Enkripsi seluruh atribut sensitif ke dalam satu paket terautentikasi atau per kolom
        # Mengemas field sensitif ke dalam format terstruktur dan mengenkripsinya dengan nonce unik
        payload = {
            "patient_code": patient_code,
            "patient_name": patient_name,
            "exam_type": exam_type,
            "result": result,
            "notes": notes
        }
        payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        # Enkripsi AES-256-GCM dengan Associated Data record_code
        aad = record_code.encode("utf-8")
        ciphertext, nonce, tag = AESGCMCipher.encrypt(payload_bytes, db_key, associated_data=aad)

        # Untuk kompatibilitas skema database dengan kolom terpisah, simpan ciphertext ke kolom terkait
        rec_id = MedicalRecordRepository.create_record(
            record_code=record_code,
            patient_code_enc=ciphertext,
            patient_name_enc=b"",
            exam_type_enc=b"",
            exam_date=exam_date,
            result_enc=b"",
            notes_enc=b"",
            nonce=nonce,
            tag=tag
        )

        AuditLogRepository.log(f"Tambah Rekam Medis: {record_code}", "SUCCESS")
        return rec_id

    @classmethod
    def get_all_records(cls) -> list[dict]:
        """Mengambil seluruh rekam medis dari MySQL dan mendekripsinya untuk ditampilkan pada aplikasi."""
        rows = MedicalRecordRepository.get_all_records()
        db_key = KeyManager.get_database_key()
        decrypted_list = []

        for row in rows:
            record_code = row["record_code"]
            ciphertext = row["patient_code_enc"]
            nonce = row["nonce"]
            tag = row["tag"]
            aad = record_code.encode("utf-8")

            try:
                decrypted_bytes = AESGCMCipher.decrypt(ciphertext, db_key, nonce, tag, associated_data=aad)
                data = json.loads(decrypted_bytes.decode("utf-8"))
            except Exception:
                data = {
                    "patient_code": "[DEKRIPSI GAGAL]",
                    "patient_name": "[DEKRIPSI GAGAL]",
                    "exam_type": "[DEKRIPSI GAGAL]",
                    "result": "[DATA RUSAK ATAU KUNCI BERUBAH]",
                    "notes": "[DEKRIPSI GAGAL]"
                }

            decrypted_list.append({
                "id": row["id"],
                "record_code": record_code,
                "patient_code": data.get("patient_code", ""),
                "patient_name": data.get("patient_name", ""),
                "exam_type": data.get("exam_type", ""),
                "exam_date": str(row["exam_date"]),
                "result": data.get("result", ""),
                "notes": data.get("notes", ""),
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"])
            })

        return decrypted_list

    @classmethod
    def get_record_by_id(cls, record_id: int) -> dict | None:
        """Mengambil dan mendekripsi satu arsip rekam medis berdasarkan ID."""
        row = MedicalRecordRepository.get_by_id(record_id)
        if not row:
            return None

        db_key = KeyManager.get_database_key()
        record_code = row["record_code"]
        ciphertext = row["patient_code_enc"]
        nonce = row["nonce"]
        tag = row["tag"]
        aad = record_code.encode("utf-8")

        decrypted_bytes = AESGCMCipher.decrypt(ciphertext, db_key, nonce, tag, associated_data=aad)
        data = json.loads(decrypted_bytes.decode("utf-8"))

        return {
            "id": row["id"],
            "record_code": record_code,
            "patient_code": data.get("patient_code", ""),
            "patient_name": data.get("patient_name", ""),
            "exam_type": data.get("exam_type", ""),
            "exam_date": str(row["exam_date"]),
            "result": data.get("result", ""),
            "notes": data.get("notes", ""),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"])
        }

    @classmethod
    def update_record(
        cls,
        record_id: int,
        record_code: str,
        patient_code: str,
        patient_name: str,
        exam_type: str,
        exam_date: str,
        result: str,
        notes: str
    ):
        """Memperbarui data arsip rekam medis terenkripsi."""
        db_key = KeyManager.get_database_key()
        payload = {
            "patient_code": patient_code,
            "patient_name": patient_name,
            "exam_type": exam_type,
            "result": result,
            "notes": notes
        }
        payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        aad = record_code.encode("utf-8")

        ciphertext, nonce, tag = AESGCMCipher.encrypt(payload_bytes, db_key, associated_data=aad)

        MedicalRecordRepository.update_record(
            record_id=record_id,
            patient_code_enc=ciphertext,
            patient_name_enc=b"",
            exam_type_enc=b"",
            exam_date=exam_date,
            result_enc=b"",
            notes_enc=b"",
            nonce=nonce,
            tag=tag
        )

        AuditLogRepository.log(f"Pembaruan Rekam Medis: {record_code}", "SUCCESS")

    @classmethod
    def delete_record(cls, record_id: int, record_code: str):
        """Menghapus data arsip rekam medis setelah konfirmasi."""
        MedicalRecordRepository.delete_record(record_id)
        AuditLogRepository.log(f"Penghapusan Rekam Medis: {record_code}", "SUCCESS")

