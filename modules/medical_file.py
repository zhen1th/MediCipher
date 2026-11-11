"""Modul layanan enkripsi dan dekripsi berkas dokumen laboratorium (.medcipher)."""
from pathlib import Path
from cryptography.aes_cbc import MedicalFileCipher
from database.repository import AuditLogRepository


class MedicalFileService:
    """Layanan enkripsi dan dekripsi file dokumen (PDF, DOCX, TXT) dengan AES-128-CBC + HMAC-SHA256."""

    @staticmethod
    def encrypt_document(input_path: str | Path, output_path: str | Path | None, passphrase: str) -> Path:
        """Mengenkripsi dokumen laboratorium."""
        result_path = MedicalFileCipher.encrypt_file(input_path, output_path, passphrase)
        AuditLogRepository.log(f"Enkripsi File Medis: {Path(input_path).name}", "SUCCESS")
        return result_path

    @staticmethod
    def decrypt_document(encrypted_path: str | Path, output_path: str | Path, passphrase: str) -> Path:
        """Memverifikasi HMAC dan mendekripsi dokumen laboratorium."""
        result_path = MedicalFileCipher.decrypt_file(encrypted_path, output_path, passphrase)
        AuditLogRepository.log(f"Dekripsi File Medis: {Path(encrypted_path).name}", "SUCCESS")
        return result_path

