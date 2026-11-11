"""Modul layanan super enkripsi teks catatan medis."""
from cryptography.aes_ecb import MedicalTextCipher
from database.repository import AuditLogRepository


class MedicalTextService:
    """Layanan enkripsi dan dekripsi teks hasil pemeriksaan medis."""

    @staticmethod
    def encrypt_medical_note(plaintext: str, vigenere_key: str, aes_passphrase: str) -> dict:
        """Melakukan super enkripsi catatan medis dan mencatat log aktivitas."""
        ciphertext_b64 = MedicalTextCipher.encrypt(plaintext, vigenere_key, aes_passphrase)
        AuditLogRepository.log("Super Enkripsi Teks Medis", "SUCCESS")
        return {
            "algorithm": "Vigenere Cipher + AES-128-ECB (PKCS7) + HMAC-SHA256",
            "ciphertext": ciphertext_b64,
            "status": "Sukses terenkripsi."
        }

    @staticmethod
    def decrypt_medical_note(ciphertext_b64: str, vigenere_key: str, aes_passphrase: str) -> dict:
        """Melakukan verifikasi HMAC dan super dekripsi catatan medis."""
        plaintext = MedicalTextCipher.decrypt(ciphertext_b64, vigenere_key, aes_passphrase)
        AuditLogRepository.log("Super Dekripsi Teks Medis", "SUCCESS")
        return {
            "algorithm": "HMAC-SHA256 Verify -> AES-128-ECB Decrypt -> Vigenere Decrypt",
            "plaintext": plaintext,
            "status": "Dekripsi dan verifikasi integritas berhasil."
        }

