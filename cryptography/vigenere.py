"""Implementasi Vigenere Cipher untuk enkripsi teks medis."""


class VigenereCipher:
    """Implementasi algoritma Vigenere Cipher klasik.
    
    Karakteristik:
    - Hanya memproses huruf alfabet (A-Z dan a-z).
    - Mempertahankan spasi, angka, tanda baca, simbol, dan baris baru tanpa perubahan.
    - Menjaga bentuk huruf besar (uppercase) dan huruf kecil (lowercase).
    """

    @staticmethod
    def validate_key(key: str) -> str:
        """Memvalidasi dan membersihkan kunci Vigenere."""
        if not key or not isinstance(key, str):
            raise ValueError("Kunci Vigenere tidak boleh kosong.")

        clean_key = "".join([c.upper() for c in key if c.isalpha()])
        if not clean_key:
            raise ValueError("Kunci Vigenere harus mengandung minimal satu karakter alfabet (A-Z).")
        return clean_key

    @classmethod
    def encrypt(cls, plaintext: str, key: str) -> str:
        """Melakukan enkripsi teks menggunakan Vigenere Cipher."""
        clean_key = cls.validate_key(key)
        key_len = len(clean_key)
        ciphertext_chars = []
        key_index = 0

        for char in plaintext:
            if char.isalpha():
                is_upper = char.isupper()
                base = ord('A') if is_upper else ord('a')
                p_val = ord(char) - base
                k_val = ord(clean_key[key_index % key_len]) - ord('A')
                c_val = (p_val + k_val) % 26
                ciphertext_chars.append(chr(base + c_val))
                key_index += 1
            else:
                ciphertext_chars.append(char)

        return "".join(ciphertext_chars)

    @classmethod
    def decrypt(cls, ciphertext: str, key: str) -> str:
        """Melakukan dekripsi ciphertext menggunakan Vigenere Cipher."""
        clean_key = cls.validate_key(key)
        key_len = len(clean_key)
        plaintext_chars = []
        key_index = 0

        for char in ciphertext:
            if char.isalpha():
                is_upper = char.isupper()
                base = ord('A') if is_upper else ord('a')
                c_val = ord(char) - base
                k_val = ord(clean_key[key_index % key_len]) - ord('A')
                p_val = (c_val - k_val) % 26
                plaintext_chars.append(chr(base + p_val))
                key_index += 1
            else:
                plaintext_chars.append(char)

        return "".join(plaintext_chars)

