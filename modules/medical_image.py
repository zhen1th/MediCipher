"""Modul layanan steganografi citra laboratorium medis."""
from pathlib import Path
from steganography.lsb import ImageSteganography
from database.repository import AuditLogRepository


class MedicalImageService:
    """Layanan penyisipan dan ekstraksi pesan tersembunyi pada citra medis PNG dan JPG."""

    @staticmethod
    def embed_secret(image_path: str | Path, output_path: str | Path, secret_text: str, passphrase: str) -> Path:
        """Menyisipkan pesan rahasia ke citra medis laboratorium (PNG atau JPG)."""
        result_path = ImageSteganography.embed_message(image_path, output_path, secret_text, passphrase)
        AuditLogRepository.log(f"Penyisipan Pesan Steganografi: {Path(image_path).name}", "SUCCESS")
        return result_path

    @staticmethod
    def extract_secret(image_path: str | Path, passphrase: str) -> str:
        """Mengekstrak pesan rahasia dari citra medis laboratorium (PNG atau JPG)."""
        secret_text = ImageSteganography.extract_message(image_path, passphrase)
        AuditLogRepository.log(f"Ekstraksi Pesan Steganografi: {Path(image_path).name}", "SUCCESS")
        return secret_text

