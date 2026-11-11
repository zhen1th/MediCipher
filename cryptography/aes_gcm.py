"""Implementasi AES-256-GCM untuk data sensitif database, embedding wajah, dan steganografi."""
import os
from cryptography._aes_core import aes_gcm_encrypt_raw, aes_gcm_decrypt_raw


class AESGCMCipher:
    """Implementasi AES-256-GCM untuk Authenticated Encryption with Associated Data (AEAD)."""

    @classmethod
    def encrypt(cls, plaintext: bytes, key: bytes, associated_data: bytes = b"") -> tuple[bytes, bytes, bytes]:
        """Melakukan enkripsi AES-256-GCM.
        
        Returns:
            tuple (ciphertext, nonce, tag)
        """
        if len(key) != 32:
            raise ValueError(f"Kunci AES-256-GCM harus tepat 32 byte (256-bit), didapat {len(key)} byte.")

        nonce = os.urandom(12)  # Standar NIST 96-bit nonce untuk GCM

        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(key)
            # AESGCM.encrypt mengembalikan ciphertext + 16 byte tag di bagian akhir
            ct_with_tag = aesgcm.encrypt(nonce, plaintext, associated_data)
            ciphertext = ct_with_tag[:-16]
            tag = ct_with_tag[-16:]
            return ciphertext, nonce, tag
        except ImportError:
            ciphertext, tag = aes_gcm_encrypt_raw(plaintext, key, nonce, associated_data)
            return ciphertext, nonce, tag

    @classmethod
    def decrypt(cls, ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes, associated_data: bytes = b"") -> bytes:
        """Melakukan dekripsi dan verifikasi keaslian AES-256-GCM."""
        if len(key) != 32:
            raise ValueError(f"Kunci AES-256-GCM harus tepat 32 byte (256-bit), didapat {len(key)} byte.")
        if len(nonce) not in (12, 16):
            raise ValueError(f"Panjang nonce tidak valid: {len(nonce)} byte.")
        if len(tag) != 16:
            raise ValueError(f"Panjang authentication tag harus 16 byte, didapat {len(tag)} byte.")

        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(key)
            ct_with_tag = ciphertext + tag
            plaintext = aesgcm.decrypt(nonce, ct_with_tag, associated_data)
            return plaintext
        except ImportError:
            return aes_gcm_decrypt_raw(ciphertext, key, nonce, tag, associated_data)

