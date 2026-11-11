"""Modul fungsi hash, HMAC, dan hashing password Argon2id."""
import hashlib
import hmac
import os
from pathlib import Path


class PasswordHasher:
    """Pengelola hash kata sandi menggunakan algoritma Argon2id.
    
    Jika modul argon2 belum terpasang di sistem, digunakan fallback PBKDF2-HMAC-SHA256
    dengan salt 16 byte acak dan 600.000 iterasi.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """Menghasilkan hash aman untuk kata sandi."""
        if not password or len(password) < 8:
            raise ValueError("Kata sandi minimal harus 8 karakter.")

        try:
            from argon2 import PasswordHasher as Argon2Hasher
            from argon2.profiles import RFC_9106_LOW_MEMORY
            ph = Argon2Hasher.from_parameters(RFC_9106_LOW_MEMORY)
            return ph.hash(password)
        except ImportError:
            # Fallback berstandar PBKDF2-HMAC-SHA256 600.000 iterasi
            salt = os.urandom(16)
            kdf = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
            return f"$pbkdf2-sha256$i=600000${salt.hex()}${kdf.hex()}"

    @staticmethod
    def verify_password(hash_value: str, password: str) -> bool:
        """Memverifikasi kecocokan kata sandi terhadap hash tersimpan."""
        if not hash_value or not password:
            return False

        if hash_value.startswith("$argon2"):
            try:
                from argon2 import PasswordHasher as Argon2Hasher
                from argon2.exceptions import VerifyMismatchError
                ph = Argon2Hasher()
                ph.verify(hash_value, password)
                return True
            except Exception:
                return False
        elif hash_value.startswith("$pbkdf2-sha256$"):
            try:
                parts = hash_value.split("$")
                # ['', 'pbkdf2-sha256', 'i=600000', salt_hex, kdf_hex]
                iterations = int(parts[2].split("=")[1])
                salt = bytes.fromhex(parts[3])
                expected = bytes.fromhex(parts[4])
                computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
                return hmac.compare_digest(computed, expected)
            except Exception:
                return False
        return False


class HashUtil:
    """Utilitas fungsi hash SHA-256 dan HMAC-SHA256."""

    @staticmethod
    def sha256_text(text: str) -> str:
        """Menghitung hash SHA-256 dari teks."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        """Menghitung hash SHA-256 dari data biner (string heksadesimal)."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sha256_file(file_path: str | Path) -> str:
        """Menghitung hash SHA-256 dari sebuah file fisik secara streaming."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def compute_hmac(key: bytes, data: bytes) -> bytes:
        """Menghitung HMAC-SHA256."""
        return hmac.new(key, data, hashlib.sha256).digest()

    @staticmethod
    def verify_hmac(key: bytes, data: bytes, expected_hmac: bytes) -> bool:
        """Memverifikasi HMAC-SHA256 dengan perbandingan waktu konstan."""
        computed = hmac.new(key, data, hashlib.sha256).digest()
        return hmac.compare_digest(computed, expected_hmac)

