"""Implementasi referensi AES (Advanced Encryption Standard - FIPS 197).
Mendukung panjang kunci 128-bit dan 256-bit, mode ECB, CBC, serta GHASH untuk GCM.
Digunakan sebagai mesin fallback saat library C cryptography belum terpasang.
"""
import os
import struct

# Tabel Substitusi S-Box FIPS 197
S_BOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
]

INV_S_BOX = [0] * 256
for _i, _v in enumerate(S_BOX):
    INV_S_BOX[_v] = _i

RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]


def _xtime(a):
    return (((a << 1) ^ 0x1B) & 0xFF) if (a & 0x80) else (a << 1)


def _mul(a, b):
    res = 0
    while b:
        if b & 1:
            res ^= a
        a = _xtime(a)
        b >>= 1
    return res


class AESCipher:
    """Implementasi murni AES FIPS 197."""

    def __init__(self, key: bytes):
        if len(key) not in (16, 32):
            raise ValueError(f"Kunci AES harus 16 byte (128-bit) atau 32 byte (256-bit), didapat {len(key)} byte.")
        self.key = key
        self.Nk = len(key) // 4
        self.Nr = 10 if self.Nk == 4 else 14
        self.round_keys = self._key_expansion(key)

    def _sub_word(self, word):
        return [S_BOX[b] for b in word]

    def _rot_word(self, word):
        return word[1:] + word[:1]

    def _key_expansion(self, key):
        w = [list(key[4 * i:4 * i + 4]) for i in range(self.Nk)]
        i = self.Nk
        while i < 4 * (self.Nr + 1):
            temp = list(w[i - 1])
            if i % self.Nk == 0:
                temp = self._sub_word(self._rot_word(temp))
                temp[0] ^= RCON[i // self.Nk]
            elif self.Nk > 6 and (i % self.Nk == 4):
                temp = self._sub_word(temp)
            new_word = [w[i - self.Nk][j] ^ temp[j] for j in range(4)]
            w.append(new_word)
            i += 1
        return [w[4 * r: 4 * r + 4] for r in range(self.Nr + 1)]

    def _add_round_key(self, state, rk):
        for c in range(4):
            for r in range(4):
                state[r][c] ^= rk[c][r]

    def _sub_bytes(self, state):
        for r in range(4):
            for c in range(4):
                state[r][c] = S_BOX[state[r][c]]

    def _inv_sub_bytes(self, state):
        for r in range(4):
            for c in range(4):
                state[r][c] = INV_S_BOX[state[r][c]]

    def _shift_rows(self, state):
        state[1] = state[1][1:] + state[1][:1]
        state[2] = state[2][2:] + state[2][:2]
        state[3] = state[3][3:] + state[3][:3]

    def _inv_shift_rows(self, state):
        state[1] = state[1][-1:] + state[1][:-1]
        state[2] = state[2][-2:] + state[2][:-2]
        state[3] = state[3][-3:] + state[3][:-3]

    def _mix_columns(self, state):
        for c in range(4):
            a0, a1, a2, a3 = state[0][c], state[1][c], state[2][c], state[3][c]
            state[0][c] = _mul(a0, 2) ^ _mul(a1, 3) ^ a2 ^ a3
            state[1][c] = a0 ^ _mul(a1, 2) ^ _mul(a2, 3) ^ a3
            state[2][c] = a0 ^ a1 ^ _mul(a2, 2) ^ _mul(a3, 3)
            state[3][c] = _mul(a0, 3) ^ a1 ^ a2 ^ _mul(a3, 2)

    def _inv_mix_columns(self, state):
        for c in range(4):
            a0, a1, a2, a3 = state[0][c], state[1][c], state[2][c], state[3][c]
            state[0][c] = _mul(a0, 0x0e) ^ _mul(a1, 0x0b) ^ _mul(a2, 0x0d) ^ _mul(a3, 0x09)
            state[1][c] = _mul(a0, 0x09) ^ _mul(a1, 0x0e) ^ _mul(a2, 0x0b) ^ _mul(a3, 0x0d)
            state[2][c] = _mul(a0, 0x0d) ^ _mul(a1, 0x09) ^ _mul(a2, 0x0e) ^ _mul(a3, 0x0b)
            state[3][c] = _mul(a0, 0x0b) ^ _mul(a1, 0x0d) ^ _mul(a2, 0x09) ^ _mul(a3, 0x0e)

    def encrypt_block(self, block: bytes) -> bytes:
        if len(block) != 16:
            raise ValueError("Panjang blok enkripsi AES harus tepat 16 byte.")
        state = [[block[r + 4 * c] for c in range(4)] for r in range(4)]
        self._add_round_key(state, self.round_keys[0])

        for r in range(1, self.Nr):
            self._sub_bytes(state)
            self._shift_rows(state)
            self._mix_columns(state)
            self._add_round_key(state, self.round_keys[r])

        self._sub_bytes(state)
        self._shift_rows(state)
        self._add_round_key(state, self.round_keys[self.Nr])

        out = bytearray(16)
        for c in range(4):
            for r in range(4):
                out[r + 4 * c] = state[r][c]
        return bytes(out)

    def decrypt_block(self, block: bytes) -> bytes:
        if len(block) != 16:
            raise ValueError("Panjang blok dekripsi AES harus tepat 16 byte.")
        state = [[block[r + 4 * c] for c in range(4)] for r in range(4)]
        self._add_round_key(state, self.round_keys[self.Nr])
        self._inv_shift_rows(state)
        self._inv_sub_bytes(state)

        for r in range(self.Nr - 1, 0, -1):
            self._add_round_key(state, self.round_keys[r])
            self._inv_mix_columns(state)
            self._inv_shift_rows(state)
            self._inv_sub_bytes(state)

        self._add_round_key(state, self.round_keys[0])

        out = bytearray(16)
        for c in range(4):
            for r in range(4):
                out[r + 4 * c] = state[r][c]
        return bytes(out)


def pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def pkcs7_unpad(data: bytes, block_size: int = 16) -> bytes:
    if not data or len(data) % block_size != 0:
        raise ValueError("Data ciphertext tidak valid (panjang bukan kelipatan blok).")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > block_size:
        raise ValueError("Nilai padding PKCS7 tidak valid.")
    if data[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError("Integritas padding PKCS7 rusak.")
    return data[:-pad_len]


# Mode ECB
def aes_ecb_encrypt_raw(plaintext: bytes, key: bytes) -> bytes:
    padded = pkcs7_pad(plaintext, 16)
    cipher = AESCipher(key)
    out = bytearray()
    for i in range(0, len(padded), 16):
        out.extend(cipher.encrypt_block(padded[i:i + 16]))
    return bytes(out)


def aes_ecb_decrypt_raw(ciphertext: bytes, key: bytes) -> bytes:
    if len(ciphertext) % 16 != 0:
        raise ValueError("Panjang ciphertext AES-ECB harus kelipatan 16 byte.")
    cipher = AESCipher(key)
    out = bytearray()
    for i in range(0, len(ciphertext), 16):
        out.extend(cipher.decrypt_block(ciphertext[i:i + 16]))
    return pkcs7_unpad(bytes(out), 16)


# Mode CBC
def aes_cbc_encrypt_raw(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    if len(iv) != 16:
        raise ValueError("Panjang IV untuk AES-CBC harus 16 byte.")
    padded = pkcs7_pad(plaintext, 16)
    cipher = AESCipher(key)
    out = bytearray()
    prev = iv
    for i in range(0, len(padded), 16):
        block = bytes(a ^ b for a, b in zip(padded[i:i + 16], prev))
        enc = cipher.encrypt_block(block)
        out.extend(enc)
        prev = enc
    return bytes(out)


def aes_cbc_decrypt_raw(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    if len(iv) != 16:
        raise ValueError("Panjang IV untuk AES-CBC harus 16 byte.")
    if len(ciphertext) % 16 != 0:
        raise ValueError("Panjang ciphertext AES-CBC harus kelipatan 16 byte.")
    cipher = AESCipher(key)
    out = bytearray()
    prev = iv
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i + 16]
        dec = cipher.decrypt_block(block)
        out.extend(bytes(a ^ b for a, b in zip(dec, prev)))
        prev = block
    return pkcs7_unpad(bytes(out), 16)


# GCM GHASH dan Mode CTR untuk AES-GCM
def _gf_mult(x: int, y: int) -> int:
    r = 0xe1000000000000000000000000000000
    z = 0
    v = x
    for i in range(127, -1, -1):
        if (y >> i) & 1:
            z ^= v
        if v & 1:
            v = (v >> 1) ^ r
        else:
            v >>= 1
    return z


def _ghash(h_int: int, data: bytes) -> int:
    y = 0
    for i in range(0, len(data), 16):
        block = data[i:i + 16].ljust(16, b"\x00")
        b_int = int.from_bytes(block, "big")
        y = _gf_mult(y ^ b_int, h_int)
    return y


def aes_gcm_encrypt_raw(plaintext: bytes, key: bytes, nonce: bytes, aad: bytes = b"") -> tuple[bytes, bytes]:
    """AES-GCM Authenticated Encryption (NIST SP 800-38D)."""
    cipher = AESCipher(key)
    h_bytes = cipher.encrypt_block(b"\x00" * 16)
    h_int = int.from_bytes(h_bytes, "big")

    if len(nonce) == 12:
        j0 = nonce + b"\x00\x00\x00\x01"
    else:
        len_nonce_bits = len(nonce) * 8
        s = (16 - (len(nonce) % 16)) % 16
        padded = nonce + (b"\x00" * s) + (b"\x00" * 8) + struct.pack(">Q", len_nonce_bits)
        j0 = _ghash(h_int, padded).to_bytes(16, "big")

    # Enkripsi CTR
    ciphertext = bytearray()
    cb = bytearray(j0)
    for i in range(0, len(plaintext), 16):
        # Increment counter (32-bit terakhir)
        ctr_val = (int.from_bytes(cb[12:], "big") + 1) & 0xFFFFFFFF
        cb[12:] = ctr_val.to_bytes(4, "big")
        keystream = cipher.encrypt_block(bytes(cb))
        chunk = plaintext[i:i + 16]
        ciphertext.extend(bytes(a ^ b for a, b in zip(chunk, keystream[:len(chunk)])))

    # GHASH over AAD || Ciphertext || len(AAD) || len(C)
    s_aad = (16 - (len(aad) % 16)) % 16
    s_c = (16 - (len(ciphertext) % 16)) % 16
    pad_aad = aad + (b"\x00" * s_aad)
    pad_c = bytes(ciphertext) + (b"\x00" * s_c)
    len_block = struct.pack(">QQ", len(aad) * 8, len(ciphertext) * 8)
    s_tag = _ghash(h_int, pad_aad + pad_c + len_block)

    # Tag = S ^ E_K(J0)
    tag_keystream = cipher.encrypt_block(j0)
    tag = (s_tag ^ int.from_bytes(tag_keystream, "big")).to_bytes(16, "big")
    return bytes(ciphertext), tag


def aes_gcm_decrypt_raw(ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes, aad: bytes = b"") -> bytes:
    """AES-GCM Authenticated Decryption."""
    cipher = AESCipher(key)
    h_bytes = cipher.encrypt_block(b"\x00" * 16)
    h_int = int.from_bytes(h_bytes, "big")

    if len(nonce) == 12:
        j0 = nonce + b"\x00\x00\x00\x01"
    else:
        len_nonce_bits = len(nonce) * 8
        s = (16 - (len(nonce) % 16)) % 16
        padded = nonce + (b"\x00" * s) + (b"\x00" * 8) + struct.pack(">Q", len_nonce_bits)
        j0 = _ghash(h_int, padded).to_bytes(16, "big")

    # Verifikasi Tag terlebih dahulu
    s_aad = (16 - (len(aad) % 16)) % 16
    s_c = (16 - (len(ciphertext) % 16)) % 16
    pad_aad = aad + (b"\x00" * s_aad)
    pad_c = ciphertext + (b"\x00" * s_c)
    len_block = struct.pack(">QQ", len(aad) * 8, len(ciphertext) * 8)
    s_tag = _ghash(h_int, pad_aad + pad_c + len_block)

    tag_keystream = cipher.encrypt_block(j0)
    expected_tag = (s_tag ^ int.from_bytes(tag_keystream, "big")).to_bytes(16, "big")

    # Constant-time comparison
    diff = 0
    for a, b in zip(tag, expected_tag):
        diff |= a ^ b
    if diff != 0:
        raise ValueError("Verifikasi autentikasi AES-GCM gagal (Tag tidak cocok atau data dimanipulasi).")

    # Dekripsi CTR
    plaintext = bytearray()
    cb = bytearray(j0)
    for i in range(0, len(ciphertext), 16):
        ctr_val = (int.from_bytes(cb[12:], "big") + 1) & 0xFFFFFFFF
        cb[12:] = ctr_val.to_bytes(4, "big")
        keystream = cipher.encrypt_block(bytes(cb))
        chunk = ciphertext[i:i + 16]
        plaintext.extend(bytes(a ^ b for a, b in zip(chunk, keystream[:len(chunk)])))

    return bytes(plaintext)
