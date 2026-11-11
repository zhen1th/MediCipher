"""Modul alur autentikasi multi-faktor (USB Dongle + Password + Wajah) dan penguncian sesi."""
from datetime import datetime, timedelta
import threading
import time
from database.repository import (
    UserRepository, FaceTemplateRepository, DongleRepository, AuditLogRepository
)
from authentication.password import PasswordManager
from authentication.usb_dongle import USBDongleManager
from authentication.face_verification import FaceVerificationManager, cosine_distance
from config.settings import AppConfig


class SessionManager:
    """Pengelola status sesi pengguna yang sedang aktif."""

    current_user_id: int | None = None
    current_username: str | None = None
    registered_volume_serial: str | None = None
    last_activity_time: datetime | None = None
    is_authenticated: bool = False
    _usb_monitor_thread: threading.Thread | None = None
    _stop_monitor_event = threading.Event()
    _on_session_lock_callback = None

    @classmethod
    def set_lock_callback(cls, callback):
        """Mendaftarkan fungsi callback yang dipanggil saat sesi terkunci."""
        cls._on_session_lock_callback = callback

    @classmethod
    def start_session(cls, user_id: int, username: str, volume_serial: str):
        """Memulai sesi aktif setelah seluruh 3 lapisan autentikasi berhasil."""
        cls.current_user_id = user_id
        cls.current_username = username
        cls.registered_volume_serial = volume_serial
        cls.last_activity_time = datetime.now()
        cls.is_authenticated = True

        # Mulai thread pemantauan fisik USB dongle
        cls.stop_usb_monitoring()
        cls._stop_monitor_event.clear()
        cls._usb_monitor_thread = threading.Thread(
            target=cls._monitor_usb_dongle_loop,
            daemon=True,
            name="MediCipher-USBDongleMonitor"
        )
        cls._usb_monitor_thread.start()

    @classmethod
    def update_activity(cls):
        """Memperbarui tanda waktu aktivitas terakhir pengguna."""
        cls.last_activity_time = datetime.now()

    @classmethod
    def is_session_timed_out(cls) -> bool:
        """Memeriksa apakah sesi telah kedaluwarsa karena tidak ada aktivitas."""
        if not cls.is_authenticated or cls.last_activity_time is None:
            return True
        timeout = timedelta(minutes=AppConfig.SESSION_TIMEOUT_MINUTES)
        return datetime.now() - cls.last_activity_time > timeout

    @classmethod
    def lock_session(cls, reason: str = "Sesi dikunci."):
        """Mengunci sesi aktif secara aman."""
        if cls.is_authenticated:
            cls.is_authenticated = False
            AuditLogRepository.log(f"Sesi Dikunci: {reason}", "LOCKED", cls.current_user_id)
            if callable(cls._on_session_lock_callback):
                try:
                    cls._on_session_lock_callback(reason)
                except Exception:
                    pass

    @classmethod
    def logout(cls):
        """Mengakhiri sesi dan mereset status login."""
        cls.stop_usb_monitoring()
        if cls.current_user_id is not None:
            AuditLogRepository.log("Pengguna Logout", "SUCCESS", cls.current_user_id)
        cls.current_user_id = None
        cls.current_username = None
        cls.registered_volume_serial = None
        cls.last_activity_time = None
        cls.is_authenticated = False

    @classmethod
    def stop_usb_monitoring(cls):
        """Menghentikan thread pemantau USB."""
        cls._stop_monitor_event.set()
        if cls._usb_monitor_thread and cls._usb_monitor_thread.is_alive():
            cls._usb_monitor_thread = None

    @classmethod
    def _monitor_usb_dongle_loop(cls):
        """Loop pemantauan keberadaan USB fisik secara berkala.
        
        Jika USB dicabut saat aplikasi sedang berjalan, sesi langsung dikunci.
        """
        while not cls._stop_monitor_event.is_set():
            time.sleep(AppConfig.USB_CHECK_INTERVAL_SECONDS)
            if not cls.is_authenticated or not cls.registered_volume_serial:
                break

            drive = USBDongleManager.get_drive_by_serial(cls.registered_volume_serial)
            if not drive:
                cls.lock_session("USB Dongle fisik dicabut dari sistem.")
                break


class LoginManager:
    """Pengelola alur login tiga lapisan keamanan."""

    # Pembatasan percobaan login untuk mitigasi brute force
    _failed_attempts: int = 0
    MAX_FAILED_ATTEMPTS: int = 5
    _lockout_until: datetime | None = None

    @classmethod
    def check_lockout(cls):
        """Memeriksa apakah terdapat penguncian sementara akibat percobaan gagal berulang."""
        if cls._lockout_until and datetime.now() < cls._lockout_until:
            remaining = int((cls._lockout_until - datetime.now()).total_seconds())
            raise PermissionError(f"Terlalu banyak percobaan gagal. Silakan tunggu {remaining} detik lagi.")

    @classmethod
    def record_failure(cls, username: str, step: str, reason: str):
        """Mencatat kegagalan autentikasi dan memperbarui batasan percobaan."""
        cls._failed_attempts += 1
        AuditLogRepository.log(f"Login Gagal ({step}): {reason} [User: {username}]", "FAILED")
        if cls._failed_attempts >= cls.MAX_FAILED_ATTEMPTS:
            cls._lockout_until = datetime.now() + timedelta(minutes=3)
            cls._failed_attempts = 0
            raise PermissionError("Batas percobaan login terlampaui. Sistem dikunci sementara selama 3 menit.")

    @classmethod
    def record_success(cls, user_id: int):
        """Mereset kegagalan setelah seluruh 3 lapisan berhasil."""
        cls._failed_attempts = 0
        cls._lockout_until = None
        AuditLogRepository.log("Autentikasi Multi-Faktor Berhasil", "SUCCESS", user_id)

    @classmethod
    def authenticate_step_usb(cls, user_id: int) -> tuple[bool, str, str]:
        """Lapisan 1: Verifikasi fisik USB Flashdisk Dongle."""
        dongle = DongleRepository.get_by_user_id(user_id)
        if not dongle:
            return False, "Data USB dongle tidak ditemukan di database.", ""

        vol_serial = dongle["volume_serial"]
        token_hash = dongle["token_hash"]

        is_valid, msg = USBDongleManager.verify_dongle(vol_serial, token_hash)
        return is_valid, msg, vol_serial

    @classmethod
    def authenticate_step_password(cls, username: str, password: str) -> tuple[bool, str, dict | None]:
        """Lapisan 2: Verifikasi Username dan Password (Argon2id)."""
        cls.check_lockout()
        user = UserRepository.get_by_username(username)
        if not user:
            cls.record_failure(username, "Password", "Username tidak ditemukan.")
            return False, "Username atau kata sandi salah.", None

        if not PasswordManager.verify_password(user["password_hash"], password):
            cls.record_failure(username, "Password", "Kata sandi salah.")
            return False, "Username atau kata sandi salah.", None

        return True, "Kredensial username dan kata sandi valid.", user

    @classmethod
    def authenticate_step_face(cls, user_id: int, live_embedding: list[float]) -> tuple[bool, str, float]:
        """Lapisan 3: Verifikasi Biometrik Wajah langsung."""
        template = FaceTemplateRepository.get_by_user_id(user_id)
        if not template:
            return False, "Data template biometrik wajah tidak ditemukan.", 1.0

        try:
            reg_vec = FaceVerificationManager.decrypt_embedding(
                template["encrypted_embedding"],
                template["nonce"],
                template["tag"]
            )
            dist = cosine_distance(live_embedding, reg_vec)
            threshold = AppConfig.FACE_DISTANCE_THRESHOLD

            if dist <= threshold:
                return True, f"Verifikasi wajah berhasil (Jarak: {dist:.4f}).", dist
            else:
                return False, f"Wajah tidak cocok dengan template terdaftar (Jarak: {dist:.4f} > Ambang: {threshold:.4f}).", dist
        except Exception as exc:
            return False, f"Terjadi kesalahan saat verifikasi wajah: {exc}", 1.0

    @classmethod
    def execute_full_login(cls, username: str, password: str, live_embedding: list[float]) -> tuple[bool, str]:
        """Menjalankan ketiga lapisan autentikasi secara berurutan dan ketat."""
        cls.check_lockout()

        # 1. Verifikasi Username & Password
        p_ok, p_msg, user = cls.authenticate_step_password(username, password)
        if not p_ok or not user:
            return False, p_msg

        user_id = user["id"]

        # 2. Verifikasi USB Dongle
        u_ok, u_msg, vol_serial = cls.authenticate_step_usb(user_id)
        if not u_ok:
            cls.record_failure(username, "USB Dongle", u_msg)
            return False, f"Autentikasi USB Dongle gagal: {u_msg}"

        # 3. Verifikasi Wajah
        f_ok, f_msg, _dist = cls.authenticate_step_face(user_id, live_embedding)
        if not f_ok:
            cls.record_failure(username, "Biometrik Wajah", f_msg)
            return False, f"Autentikasi Biometrik Wajah gagal: {f_msg}"

        # Seluruh lapisan sukses
        cls.record_success(user_id)
        SessionManager.start_session(user_id, username, vol_serial)
        return True, "Autentikasi lengkap berhasil. Selamat datang di MediCipher."

