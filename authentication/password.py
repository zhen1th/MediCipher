"""Modul validasi dan hashing kata sandi pengguna."""
import re
from cryptography.hashing import PasswordHasher


class PasswordManager:
    """Manajer validasi dan keamanan kata sandi."""

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """Memvalidasi format username."""
        if not username:
            return False, "Username tidak boleh kosong."
        username = username.strip()
        if len(username) < 3 or len(username) > 32:
            return False, "Panjang username harus antara 3 hingga 32 karakter."
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            return False, "Username hanya boleh mengandung huruf, angka, dan underscore (_)."
        return True, "Format username valid."

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Memeriksa kekuatan kata sandi sesuai standar keamanan."""
        if not password:
            return False, "Password tidak boleh kosong."
        if len(password) < 8:
            return False, "Password minimal harus memiliki 8 karakter."
        if not any(c.isupper() for c in password):
            return False, "Password harus mengandung minimal satu huruf besar (A-Z)."
        if not any(c.islower() for c in password):
            return False, "Password harus mengandung minimal satu huruf kecil (a-z)."
        if not any(c.isdigit() for c in password):
            return False, "Password harus mengandung minimal satu angka (0-9)."
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password harus mengandung minimal satu karakter simbol khusus (!@#$%^&*...)."
        return True, "Password memenuhi kriteria keamanan."

    @staticmethod
    def hash_password(password: str) -> str:
        """Menghasilkan hash kata sandi dengan Argon2id."""
        return PasswordHasher.hash_password(password)

    @staticmethod
    def verify_password(hash_value: str, password: str) -> bool:
        """Memverifikasi kecocokan kata sandi."""
        return PasswordHasher.verify_password(hash_value, password)

