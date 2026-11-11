"""Implementasi Enkripsi File Medis menggunakan AES-128-CBC dan HMAC-SHA256 (.medcipher)."""
import hashlib
import os
from pathlib import Path
from cryptography.hashing import HashUtil
from cryptography._aes_core import (
    aes_cbc_encrypt_raw, aes_cbc_decrypt_raw, pkcs7_pad, pkcs7_unpad
)

# Header pengenal file terenkripsi MediCipher
FILE_MAGIC_HEADER = b"MEDCIPHER_V1"  # 12 byte
FILE_EXTENSION = ".medcipher"


class MedicalFileCipher:
    """Implementasi pengamanan file dokumen laboratorium (.pdf, .docx, .txt)
    menggunakan AES-128-CBC dan HMAC-SHA256.
    """

    @staticmethod
    def _derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes]:
        """Menurunkan kunci 48 byte: 16 byte pertama untuk AES-128, 32 byte kedua untuk HMAC-SHA256."""
        derived = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 100000, dklen=48)
        aes_key = derived[:16]
        hmac_key = derived[16:48]
        return aes_key, hmac_key

    @classmethod
    def encrypt_bytes(cls, data: bytes, passphrase: str) -> bytes:
        """Melakukan enkripsi data biner menggunakan AES-128-CBC dan HMAC-SHA256."""
        if not data:
            raise ValueError("Data file tidak boleh kosong.")
        if not passphrase:
            raise ValueError("Passphrase enkripsi tidak boleh kosong.")

        salt = os.urandom(16)
        iv = os.urandom(16)  # Setiap enkripsi wajib menggunakan IV acak baru
        aes_key, hmac_key = cls._derive_keys(passphrase, salt)

        # Enkripsi AES-128-CBC dengan padding PKCS7
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        except ImportError:
            ciphertext = aes_cbc_encrypt_raw(data, aes_key, iv)

        # Hitung HMAC-SHA256 terhadap (Header + Salt + IV + Ciphertext)
        hmac_payload = FILE_MAGIC_HEADER + salt + iv + ciphertext
        hmac_tag = HashUtil.compute_hmac(hmac_key, hmac_payload)

        # Format: Header(12) + Salt(16) + IV(16) + HMAC(32) + Ciphertext(n)
        return FILE_MAGIC_HEADER + salt + iv + hmac_tag + ciphertext

    @classmethod
    def decrypt_bytes(cls, encrypted_data: bytes, passphrase: str) -> bytes:
        """Melakukan verifikasi HMAC dan dekripsi AES-128-CBC."""
        if not encrypted_data:
            raise ValueError("Data terenkripsi tidak boleh kosong.")
        if not passphrase:
            raise ValueError("Passphrase dekripsi tidak boleh kosong.")

        # Minimum: 12 (magic) + 16 (salt) + 16 (iv) + 32 (hmac) + 16 (min 1 blok) = 92 byte
        if len(encrypted_data) < 92:
            raise ValueError("Format file terenkripsi tidak valid atau data terpotong.")

        magic = encrypted_data[:12]
        if magic != FILE_MAGIC_HEADER:
            raise ValueError("Format file tidak dikenali. Bukan file .medcipher yang valid.")

        salt = encrypted_data[12:28]
        iv = encrypted_data[28:44]
        expected_hmac = encrypted_data[44:76]
        ciphertext = encrypted_data[76:]

        aes_key, hmac_key = cls._derive_keys(passphrase, salt)

        # Verifikasi HMAC terlebih dahulu sebelum mendekripsi data
        hmac_payload = FILE_MAGIC_HEADER + salt + iv + ciphertext
        if not HashUtil.verify_hmac(hmac_key, hmac_payload, expected_hmac):
            raise ValueError("Verifikasi integritas file gagal: file telah dimodifikasi atau passphrase salah.")

        # Dekripsi AES-128-CBC
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_data) + unpadder.finalize()
        except ImportError:
            plaintext = aes_cbc_decrypt_raw(ciphertext, aes_key, iv)

        return plaintext

    @classmethod
    def encrypt_file(cls, input_file_path: str | Path, output_file_path: str | Path | None, passphrase: str) -> Path:
        """Membaca file asli, mengenkripsi, dan menyimpannya sebagai file .medcipher."""
        src_path = Path(input_file_path)
        if not src_path.is_file():
            raise FileNotFoundError(f"File sumber tidak ditemukan: {input_file_path}")

        raw_bytes = src_path.read_bytes()
        encrypted_bytes = cls.encrypt_bytes(raw_bytes, passphrase)

        if output_file_path is None:
            dest_path = src_path.with_name(src_path.name + FILE_EXTENSION)
        else:
            dest_path = Path(output_file_path)

        dest_path.write_bytes(encrypted_bytes)
        return dest_path

    @classmethod
    def decrypt_file(cls, encrypted_file_path: str | Path, output_file_path: str | Path, passphrase: str) -> Path:
        """Membaca file .medcipher, memverifikasi, mendekripsi, dan menyimpannya kembali."""
        src_path = Path(encrypted_file_path)
        if not src_path.is_file():
            raise FileNotFoundError(f"File terenkripsi tidak ditemukan: {encrypted_file_path}")

        encrypted_bytes = src_path.read_bytes()
        decrypted_bytes = cls.decrypt_bytes(encrypted_bytes, passphrase)

        dest_path = Path(output_file_path)
        dest_path.write_bytes(decrypted_bytes)
        return dest_path

