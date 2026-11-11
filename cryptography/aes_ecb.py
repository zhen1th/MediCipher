"""Implementasi AES-128-ECB dan Super Enkripsi Teks Medis (Vigenere + AES-128-ECB + HMAC)."""
import base64
import hashlib
import os
from cryptography.vigenere import VigenereCipher
from cryptography.hashing import HashUtil
from cryptography._aes_core import (
    aes_ecb_encrypt_raw, aes_ecb_decrypt_raw, pkcs7_pad, pkcs7_unpad
)

# Header pengenal format ciphertext super enkripsi teks
MAGIC_HEADER = b"MC_TEXT_V1"  # 10 byte


class MedicalTextCipher:
    """Implementasi Super Enkripsi untuk catatan medis: Vigenere + AES-128-ECB + HMAC-SHA256.
    
    PERINGATAN AKADEMIK:
    AES-128-ECB digunakan untuk memenuhi silabus demonstrasi tugas kuliah Kriptografi.
    Mode ECB memiliki kelemahan analisis pola dan tidak boleh digunakan untuk data pasien sungguhan.
    """

    @staticmethod
    def _derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes]:
        """Menurunkan kunci AES 128-bit (16 byte) dan kunci HMAC-SHA256 (32 byte) menggunakan PBKDF2."""
        derived = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 100000, dklen=48)
        aes_key = derived[:16]
        hmac_key = derived[16:48]
        return aes_key, hmac_key

    @classmethod
    def encrypt(cls, plaintext: str, vigenere_key: str, aes_passphrase: str) -> str:
        """Menjalankan alur Super Enkripsi:
        Plaintext -> Vigenere -> PKCS7 Padding -> AES-128-ECB -> HMAC-SHA256 -> Base64.
        """
        if not plaintext:
            raise ValueError("Teks plaintext tidak boleh kosong.")
        if not aes_passphrase:
            raise ValueError("Passphrase AES tidak boleh kosong.")

        # Tahap 1: Enkripsi Vigenere
        vigenere_result = VigenereCipher.encrypt(plaintext, vigenere_key)
        vigenere_bytes = vigenere_result.encode("utf-8")

        # Tahap 2: Penurunan Kunci AES-128 dan HMAC dari Passphrase
        salt = os.urandom(16)
        aes_key, hmac_key = cls._derive_keys(aes_passphrase, salt)

        # Tahap 3: Padding PKCS7 dan Enkripsi AES-128-ECB
        try:
            # Gunakan pyca/cryptography jika tersedia
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(vigenere_bytes) + padder.finalize()
            cipher = Cipher(algorithms.AES(aes_key), modes.ECB())
            encryptor = cipher.encryptor()
            aes_ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        except ImportError:
            # Fallback ke mesin AES FIPS 197 murni
            aes_ciphertext = aes_ecb_encrypt_raw(vigenere_bytes, aes_key)

        # Tahap 4: Hitung HMAC-SHA256 terhadap (Header + Salt + Ciphertext)
        hmac_payload = MAGIC_HEADER + salt + aes_ciphertext
        hmac_tag = HashUtil.compute_hmac(hmac_key, hmac_payload)

        # Tahap 5: Serialisasi ke dalam format Base64
        # Format payload: Header(10) + Salt(16) + HMAC(32) + Ciphertext(n)
        packed_data = MAGIC_HEADER + salt + hmac_tag + aes_ciphertext
        return base64.b64encode(packed_data).decode("utf-8")

    @classmethod
    def decrypt(cls, ciphertext_b64: str, vigenere_key: str, aes_passphrase: str) -> str:
        """Menjalankan alur Super Dekripsi:
        Base64 -> Verifikasi HMAC -> AES-128-ECB Decryption -> Unpadding PKCS7 -> Vigenere Decryption.
        """
        if not ciphertext_b64:
            raise ValueError("Ciphertext tidak boleh kosong.")
        if not aes_passphrase:
            raise ValueError("Passphrase AES tidak boleh kosong.")

        try:
            packed_data = base64.b64decode(ciphertext_b64.encode("utf-8"))
        except Exception as exc:
            raise ValueError("Format Base64 ciphertext tidak valid.") from exc

        # Periksa panjang minimum: Header(10) + Salt(16) + HMAC(32) + min 1 blok AES(16) = 74 byte
        if len(packed_data) < 74:
            raise ValueError("Ciphertext rusak atau tidak lengkap.")

        header = packed_data[:10]
        if header != MAGIC_HEADER:
            raise ValueError("Header format ciphertext teks medis tidak valid.")

        salt = packed_data[10:26]
        expected_hmac = packed_data[26:58]
        aes_ciphertext = packed_data[58:]

        # Turunkan kunci
        aes_key, hmac_key = cls._derive_keys(aes_passphrase, salt)

        # Verifikasi HMAC-SHA256 sebelum dekripsi
        hmac_payload = MAGIC_HEADER + salt + aes_ciphertext
        if not HashUtil.verify_hmac(hmac_key, hmac_payload, expected_hmac):
            raise ValueError("Integritas ciphertext gagal: HMAC tidak cocok atau passphrase AES salah.")

        # Dekripsi AES-128-ECB
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            cipher = Cipher(algorithms.AES(aes_key), modes.ECB())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(aes_ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            vigenere_bytes = unpadder.update(padded_data) + unpadder.finalize()
        except ImportError:
            vigenere_bytes = aes_ecb_decrypt_raw(aes_ciphertext, aes_key)

        vigenere_text = vigenere_bytes.decode("utf-8", errors="replace")

        # Tahap akhir: Dekripsi Vigenere
        plaintext = VigenereCipher.decrypt(vigenere_text, vigenere_key)
        return plaintext

