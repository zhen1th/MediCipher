"""Modul deteksi dan manajemen fisik USB Dongle pada sistem Windows."""
import os
import secrets
import hashlib
import hmac
from pathlib import Path
import ctypes
from ctypes import wintypes
from config.settings import AppConfig

# Konstanta tipe drive Windows API
DRIVE_UNKNOWN = 0
DRIVE_NO_ROOT_DIR = 1
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4
DRIVE_CDROM = 5
DRIVE_RAMDISK = 6


class USBDongleManager:
    """Pengelola autentikasi fisik USB Flashdisk menggunakan Windows API."""

    @classmethod
    def list_available_drives(cls) -> list[dict]:
        """Mendeteksi semua drive yang terhubung ke sistem Windows menggunakan Windows API."""
        kernel32 = ctypes.windll.kernel32
        bitmask = kernel32.GetLogicalDrives()
        drives = []

        for char_code in range(ord('A'), ord('Z') + 1):
            letter = chr(char_code)
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                drive_type = kernel32.GetDriveTypeW(drive_path)
                
                vol_name_buf = ctypes.create_unicode_buffer(1024)
                fs_name_buf = ctypes.create_unicode_buffer(1024)
                serial_number = wintypes.DWORD()

                res = kernel32.GetVolumeInformationW(
                    drive_path,
                    vol_name_buf,
                    ctypes.sizeof(vol_name_buf),
                    ctypes.byref(serial_number),
                    None,
                    None,
                    fs_name_buf,
                    ctypes.sizeof(fs_name_buf)
                )

                serial_hex = f"{serial_number.value:08X}" if res else "UNKNOWN"
                is_removable = (drive_type == DRIVE_REMOVABLE)
                
                drives.append({
                    "letter": letter,
                    "path": drive_path,
                    "type": drive_type,
                    "is_removable": is_removable,
                    "volume_name": vol_name_buf.value if res else "",
                    "serial_number": serial_hex,
                    "filesystem": fs_name_buf.value if res else ""
                })
            bitmask >>= 1

        return drives

    @classmethod
    def get_drive_by_serial(cls, target_serial: str) -> dict | None:
        """Mencari drive yang sedang aktif dengan volume serial tertentu."""
        clean_target = target_serial.strip().upper()
        for drive in cls.list_available_drives():
            if drive["serial_number"].upper() == clean_target:
                return drive
        return None

    @classmethod
    def register_device(cls, drive_path: str) -> tuple[str, str]:
        """Mendaftarkan USB Flashdisk sebagai dongle aplikasi MediCipher.
        
        Langkah:
        1. Validasi keberadaan drive.
        2. Dapatkan volume serial number dari drive.
        3. Buat token perangkat acak 32 byte menggunakan secrets.token_bytes(32).
        4. Tulis token ke dalam file MEDICIPHER_DEVICE.key pada root USB.
        5. Hitung SHA-256 dari token.
        6. Kembalikan (volume_serial, token_hash) untuk disimpan di database.
        
        PERHATIAN KEAMANAN: Token asli tidak pernah disimpan di database atau dicetak ke log.
        """
        path_obj = Path(drive_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Drive {drive_path} tidak ditemukan atau tidak dapat diakses.")

        # Ambil volume serial
        drives = cls.list_available_drives()
        target_drive = None
        for d in drives:
            if d["path"].upper() == str(path_obj).upper() or d["letter"].upper() == path_obj.drive.replace(":", "").upper():
                target_drive = d
                break

        if not target_drive:
            raise RuntimeError(f"Tidak dapat mengidentifikasi volume fisik drive {drive_path}.")

        volume_serial = target_drive["serial_number"]
        if volume_serial in ("00000000", "UNKNOWN", ""):
            raise RuntimeError("Volume serial drive tidak valid atau tidak terbaca.")

        # Buat token kriptografis 32 byte (256-bit)
        device_token = secrets.token_bytes(32)

        # Simpan token ke file khusus pada USB
        key_file_path = path_obj / AppConfig.DONGLE_KEY_FILENAME
        try:
            key_file_path.write_bytes(device_token)
        except Exception as exc:
            raise PermissionError(
                f"Gagal menulis file token dongle ke {key_file_path}. Pastikan USB memiliki izin tulis: {exc}"
            ) from exc

        # Hitung hash token menggunakan SHA-256
        token_hash = hashlib.sha256(device_token).hexdigest()

        return volume_serial, token_hash

    @classmethod
    def verify_dongle(cls, registered_volume_serial: str, registered_token_hash: str) -> tuple[bool, str]:
        """Memverifikasi keberadaan dan keaslian fisik USB dongle.
        
        Tahap verifikasi:
        1. Cari drive fisik dengan volume serial terdaftar.
        2. Periksa apakah file MEDICIPHER_DEVICE.key tersedia.
        3. Baca token dari file.
        4. Hitung hash token dan bandingkan dengan hash terdaftar.
        """
        if not registered_volume_serial or not registered_token_hash:
            return False, "Data registrasi USB dongle pada database tidak lengkap."

        drive = cls.get_drive_by_serial(registered_volume_serial)
        if not drive:
            return False, f"USB Dongle dengan volume serial {registered_volume_serial} tidak terhubung."

        key_file_path = Path(drive["path"]) / AppConfig.DONGLE_KEY_FILENAME
        if not key_file_path.is_file():
            return False, f"File kunci dongle '{AppConfig.DONGLE_KEY_FILENAME}' tidak ditemukan pada drive {drive['letter']}."

        try:
            token_bytes = key_file_path.read_bytes()
        except Exception as exc:
            return False, f"Gagal membaca file kunci dari USB: {exc}"

        if len(token_bytes) != 32:
            return False, "Ukuran file kunci dongle tidak valid (harus tepat 32 byte)."

        computed_hash = hashlib.sha256(token_bytes).hexdigest()

        # Bandingkan hash dengan perbandingan waktu konstan
        if hmac.compare_digest(computed_hash.lower(), registered_token_hash.lower()):
            return True, f"USB Dongle fisik terverifikasi pada drive {drive['letter']} (Serial: {drive['serial_number']})."
        else:
            return False, "Token kunci USB tidak cocok dengan hash database (Perangkat tidak sah)."

