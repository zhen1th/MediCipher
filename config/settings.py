"""Modul pengaturan dan konfigurasi aplikasi MediCipher."""
import os
from pathlib import Path

# Membaca konfigurasi dari file .env secara manual jika modul dotenv belum terpasang
def load_env_file(env_path: Path):
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("\"'")
                if key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass

# Coba gunakan python-dotenv jika tersedia
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_env_file(BASE_DIR / ".env")


class AppConfig:
    """Kelas konfigurasi utama sistem MediCipher."""

    BASE_DIR = BASE_DIR
    STORAGE_DIR = BASE_DIR / "storage"
    ASSETS_DIR = BASE_DIR / "assets"

    # Konfigurasi Database MySQL
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "medicipher_db")

    # Keamanan & File Master Key
    APP_SECRET_STORAGE = BASE_DIR / os.getenv("APP_SECRET_STORAGE", "storage/master.key.enc")
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "15"))
    USB_CHECK_INTERVAL_SECONDS = int(os.getenv("USB_CHECK_INTERVAL_SECONDS", "3"))

    # Ambang Batas Verifikasi Wajah (Cosine Distance Facenet512)
    FACE_DISTANCE_THRESHOLD = float(os.getenv("FACE_DISTANCE_THRESHOLD", "0.30"))

    # Nama file kunci fisik pada USB Flashdisk
    DONGLE_KEY_FILENAME = "MEDICIPHER_DEVICE.key"

    @classmethod
    def ensure_directories(cls):
        """Membuat direktori kerja lokal jika belum ada."""
        cls.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)

