"""Implementasi Steganografi Gambar Medis (LSB + AES-256-GCM) untuk file PNG dan JPG."""
import os
import io
import struct
import hashlib
from pathlib import Path
from PIL import Image
from cryptography.aes_gcm import AESGCMCipher

# Header khusus pengenal payload steganografi MediCipher
STEGO_MAGIC = b"MCIMG01"  # 7 byte


class ImageSteganography:
    """Implementasi penyisipan pesan rahasia ke dalam citra laboratorium PNG dan JPG.
    
    Fitur:
    - Mendukung format citra PNG dan JPG/JPEG.
    - Pra-enkripsi pesan rahasia menggunakan AES-256-GCM.
    - Penyisipan LSB (Least Significant Bit) pada saluran warna RGB piksel.
    - Preservasi data payload terproteksi integritas.
    
    PERINGATAN KLINIS:
    Gunakan hanya gambar contoh atau salinan non-diagnostik.
    Jangan pernah mengubah gambar medis asli yang digunakan untuk interpretasi klinis dokter.
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    @staticmethod
    def _derive_key(passphrase: str, salt: bytes) -> bytes:
        """Menurunkan kunci 256-bit (32 byte) dari passphrase menggunakan PBKDF2."""
        return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 100000, dklen=32)

    @classmethod
    def embed_message(cls, input_image_path: str | Path, output_image_path: str | Path,
                      secret_message: str, passphrase: str) -> Path:
        """Menyisipkan pesan rahasia terenkripsi AES-256-GCM ke dalam gambar PNG atau JPG."""
        src_path = Path(input_image_path)
        if not src_path.is_file():
            raise FileNotFoundError(f"File gambar tidak ditemukan: {input_image_path}")

        src_ext = src_path.suffix.lower()
        if src_ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Format gambar '{src_ext}' tidak didukung. "
                f"Steganografi hanya mendukung format PNG dan JPG/JPEG."
            )

        if not secret_message:
            raise ValueError("Pesan rahasia tidak boleh kosong.")
        if not passphrase:
            raise ValueError("Passphrase enkripsi tidak boleh kosong.")

        # 1. Enkripsi pesan menggunakan AES-256-GCM
        salt = os.urandom(16)
        aes_key = cls._derive_key(passphrase, salt)
        raw_msg_bytes = secret_message.encode("utf-8")
        ciphertext, nonce, tag = AESGCMCipher.encrypt(raw_msg_bytes, aes_key)

        # Paket payload terenkripsi: Salt(16) + Nonce(12) + Tag(16) + Ciphertext(n)
        crypto_payload = salt + nonce + tag + ciphertext

        # Paket steganografi lengkap: Magic(7) + PanjangPayload(4 byte uint) + crypto_payload
        header = STEGO_MAGIC + struct.pack(">I", len(crypto_payload))
        full_package = header + crypto_payload

        # Konversi byte ke bit (array integer 0 atau 1)
        bits_to_hide = []
        for byte in full_package:
            for i in range(7, -1, -1):
                bits_to_hide.append((byte >> i) & 1)

        total_bits = len(bits_to_hide)

        # 2. Buka gambar dan periksa kapasitas LSB
        img = Image.open(src_path).convert("RGB")
        width, height = img.size
        # Setiap piksel memiliki 3 saluran (R, G, B), masing-masing dapat menyimpan 1 bit LSB
        max_bits = width * height * 3

        if total_bits > max_bits:
            raise ValueError(
                f"Kapasitas gambar tidak mencukupi. Diperlukan {total_bits} bit ({len(full_package)} byte), "
                f"namun gambar hanya dapat menampung maksimal {max_bits} bit."
            )

        # 3. Sisipkan bit ke dalam saluran warna piksel (LSB)
        if hasattr(img, "get_flattened_data"):
            pixels = list(img.get_flattened_data())
        else:
            pixels = list(img.getdata())
        new_pixels = []
        bit_idx = 0

        for r, g, b in pixels:
            # Saluran Merah (R)
            if bit_idx < total_bits:
                r = (r & ~1) | bits_to_hide[bit_idx]
                bit_idx += 1
            # Saluran Hijau (G)
            if bit_idx < total_bits:
                g = (g & ~1) | bits_to_hide[bit_idx]
                bit_idx += 1
            # Saluran Biru (B)
            if bit_idx < total_bits:
                b = (b & ~1) | bits_to_hide[bit_idx]
                bit_idx += 1

            new_pixels.append((r, g, b))

        # Buat gambar stego baru
        stego_img = Image.new("RGB", (width, height))
        stego_img.putdata(new_pixels)

        dest_path = Path(output_image_path)
        dest_ext = dest_path.suffix.lower()
        if dest_ext not in cls.SUPPORTED_EXTENSIONS:
            dest_ext = ".png"
            dest_path = dest_path.with_suffix(".png")

        if dest_ext in {".jpg", ".jpeg"}:
            # Simpan sebagai JPEG berkualitas tinggi
            buffer = io.BytesIO()
            stego_img.save(buffer, format="JPEG", quality=98, subsampling=0)
            jpg_bytes = buffer.getvalue()

            # Sisipkan payload setelah penanda EOI (\xff\xd9) agar tahan kompresi JPEG
            eoi_idx = jpg_bytes.rfind(b"\xff\xd9")
            if eoi_idx != -1:
                stego_bytes = jpg_bytes[:eoi_idx + 2] + full_package
            else:
                stego_bytes = jpg_bytes + full_package

            dest_path.write_bytes(stego_bytes)
        else:
            # Simpan sebagai PNG murni (kompresi lossless menjaga LSB secara sempurna)
            stego_img.save(dest_path, format="PNG")

        return dest_path

    @classmethod
    def _extract_from_bytes(cls, data: bytes, passphrase: str) -> str | None:
        """Mengekstrak payload steganografi dari raw byte file gambar (kontainer JPG)."""
        idx = data.find(STEGO_MAGIC)
        if idx == -1:
            return None

        offset = idx + len(STEGO_MAGIC)
        if len(data) < offset + 4:
            return None

        payload_len = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4

        if payload_len < 44 or len(data) < offset + payload_len:
            return None

        crypto_payload = data[offset:offset + payload_len]
        salt = crypto_payload[:16]
        nonce = crypto_payload[16:28]
        tag = crypto_payload[28:44]
        ciphertext = crypto_payload[44:]

        aes_key = cls._derive_key(passphrase, salt)
        decrypted_bytes = AESGCMCipher.decrypt(ciphertext, aes_key, nonce, tag)
        return decrypted_bytes.decode("utf-8")

    @classmethod
    def extract_message(cls, stego_image_path: str | Path, passphrase: str) -> str:
        """Mengekstrak dan mendekripsi pesan rahasia dari gambar PNG atau JPG ber-LSB."""
        src_path = Path(stego_image_path)
        if not src_path.is_file():
            raise FileNotFoundError(f"File gambar steganografi tidak ditemukan: {stego_image_path}")

        src_ext = src_path.suffix.lower()
        if src_ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Format gambar '{src_ext}' tidak didukung. "
                f"Steganografi hanya mendukung format PNG dan JPG/JPEG."
            )

        if not passphrase:
            raise ValueError("Passphrase dekripsi tidak boleh kosong.")

        # Cek apakah payload terdapat di dalam file bytes langsung (kontainer JPG)
        try:
            raw_file_bytes = src_path.read_bytes()
            direct_msg = cls._extract_from_bytes(raw_file_bytes, passphrase)
            if direct_msg is not None:
                return direct_msg
        except Exception:
            pass

        # Ekstraksi melalui bit LSB spasial piksel (format PNG atau bit LSB murni)
        img = Image.open(src_path).convert("RGB")
        if hasattr(img, "get_flattened_data"):
            pixels = list(img.get_flattened_data())
        else:
            pixels = list(img.getdata())

        all_bits = []
        for r, g, b in pixels:
            all_bits.append(r & 1)
            all_bits.append(g & 1)
            all_bits.append(b & 1)

        def get_bytes(bit_list, start_byte, num_bytes):
            out = bytearray()
            for b in range(num_bytes):
                val = 0
                bit_start = (start_byte + b) * 8
                if bit_start + 8 > len(bit_list):
                    raise ValueError("Ukuran gambar terlalu kecil untuk memuat data.")
                for i in range(8):
                    val = (val << 1) | bit_list[bit_start + i]
                out.append(val)
            return bytes(out)

        # 1. Baca Magic Header (7 byte)
        magic = get_bytes(all_bits, 0, 7)
        if magic != STEGO_MAGIC:
            raise ValueError("Tidak ditemukan tanda pesan tersembunyi MediCipher pada gambar ini.")

        # 2. Baca Panjang Payload (4 byte)
        len_bytes = get_bytes(all_bits, 7, 4)
        payload_len = struct.unpack(">I", len_bytes)[0]

        max_possible_bytes = (len(all_bits) // 8) - 11
        if payload_len <= 0 or payload_len > max_possible_bytes:
            raise ValueError("Informasi panjang pesan steganografi rusak atau tidak valid.")

        # 3. Baca Crypto Payload
        if payload_len < 44:
            raise ValueError("Payload terenkripsi tidak lengkap.")

        crypto_payload = get_bytes(all_bits, 11, payload_len)
        salt = crypto_payload[:16]
        nonce = crypto_payload[16:28]
        tag = crypto_payload[28:44]
        ciphertext = crypto_payload[44:]

        # 4. Turunkan kunci dan Dekripsi AES-256-GCM
        aes_key = cls._derive_key(passphrase, salt)
        try:
            decrypted_bytes = AESGCMCipher.decrypt(ciphertext, aes_key, nonce, tag)
            return decrypted_bytes.decode("utf-8")
        except Exception as exc:
            raise ValueError("Gagal mendekripsi pesan: passphrase salah atau gambar telah dimodifikasi.") from exc
