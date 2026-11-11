"""Pengelola kunci master aplikasi MediCipher menggunakan Windows DPAPI dan HKDF."""
import os
import secrets
import hashlib
import hmac
from pathlib import Path
from config.settings import AppConfig

# Implementasi Windows DPAPI menggunakan ctypes bawaan Windows
import ctypes
from ctypes import wintypes


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte))
    ]


def _dpapi_protect(data: bytes) -> bytes:
    """Melindungi data menggunakan Windows Data Protection API (DPAPI)."""
    # Coba gunakan win32crypt jika tersedia
    try:
        import win32crypt
        return win32crypt.CryptProtectData(data, "MediCipher Master Key", None, None, None, 0)
    except ImportError:
        pass

    # Fallback ke ctypes Windows API langsung
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    b_data = (ctypes.c_byte * len(data))(*data)
    in_blob = DATA_BLOB(len(data), b_data)
    out_blob = DATA_BLOB()
    description = ctypes.c_wchar_p("MediCipher Master Key")

    res = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        description,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob)
    )
    if not res:
        raise OSError("Gagal mengenkripsi data dengan Windows DPAPI.")

    buf = (ctypes.c_byte * out_blob.cbData)()
    kernel32.RtlMoveMemory(buf, out_blob.pbData, out_blob.cbData)
    kernel32.LocalFree(out_blob.pbData)
    return bytes(buf)


def _dpapi_unprotect(data: bytes) -> bytes:
    """Membuka proteksi data Windows DPAPI."""
    try:
        import win32crypt
        desc, unprotected = win32crypt.CryptUnprotectData(data, None, None, None, 0)
        return unprotected
    except ImportError:
        pass

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    b_data = (ctypes.c_byte * len(data))(*data)
    in_blob = DATA_BLOB(len(data), b_data)
    out_blob = DATA_BLOB()

    res = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob)
    )
    if not res:
        raise OSError("Gagal mendekripsi data dengan Windows DPAPI.")

    buf = (ctypes.c_byte * out_blob.cbData)()
    kernel32.RtlMoveMemory(buf, out_blob.pbData, out_blob.cbData)
    kernel32.LocalFree(out_blob.pbData)
    return bytes(buf)


def hkdf_extract_and_expand(salt: bytes, ikm: bytes, info: bytes, length: int) -> bytes:
    """Implementasi HKDF (RFC 5869) berbasis HMAC-SHA256."""
    if not salt:
        salt = bytes([0] * 32)
    # HKDF-Extract: PRK = HMAC-Hash(salt, IKM)
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()

    # HKDF-Expand: OKM = T(1) || T(2) || ...
    n = (length + 31) // 32
    t = b""
    okm = b""
    for i in range(1, n + 1):
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
    return okm[:length]


class KeyManager:
    """Manajer Kunci Aplikasi MediCipher.
    
    Menghasilkan dan mengelola Master Key 256-bit yang terlindungi Windows DPAPI,
    serta menurunkan subkunci spesifik dengan HKDF.
    """

    _cached_master_key = None

    @classmethod
    def get_master_key(cls) -> bytes:
        """Mengambil atau menginisialisasi master key 256-bit."""
        if cls._cached_master_key is not None:
            return cls._cached_master_key

        AppConfig.ensure_directories()
        key_file = AppConfig.APP_SECRET_STORAGE

        if key_file.exists():
            encrypted_key = key_file.read_bytes()
            master_key = _dpapi_unprotect(encrypted_key)
        else:
            # Buat kunci master baru 32 byte (256-bit)
            master_key = secrets.token_bytes(32)
            encrypted_key = _dpapi_protect(master_key)
            key_file.write_bytes(encrypted_key)

        cls._cached_master_key = master_key
        return master_key

    @classmethod
    def derive_key(cls, info: bytes, length: int = 32) -> bytes:
        """Menurunkan kunci kriptografi khusus untuk fungsi tertentu menggunakan HKDF."""
        master = cls.get_master_key()
        salt = b"MediCipher_HKDF_Salt_2026"
        return hkdf_extract_and_expand(salt=salt, ikm=master, info=info, length=length)

    @classmethod
    def get_database_key(cls) -> bytes:
        """Kunci 256-bit khusus enkripsi record database medis."""
        return cls.derive_key(info=b"medicipher_database_encryption_key_v1", length=32)

    @classmethod
    def get_face_key(cls) -> bytes:
        """Kunci 256-bit khusus enkripsi template embedding wajah."""
        return cls.derive_key(info=b"medicipher_face_embedding_key_v1", length=32)

