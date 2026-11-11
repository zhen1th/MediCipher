"""Modul registrasi akun pengguna dan administrator MediCipher."""
from database.repository import (
    UserRepository, FaceTemplateRepository, DongleRepository, AuditLogRepository
)
from authentication.password import PasswordManager
from authentication.face_verification import FaceVerificationManager
from authentication.usb_dongle import USBDongleManager


class RegistrationManager:
    """Pengelola proses registrasi akun sistem MediCipher."""

    @classmethod
    def can_register(cls) -> bool:
        """Memeriksa kesiapan registrasi."""
        return True

    @classmethod
    def register_user(
        cls,
        username: str,
        password: str,
        confirm_password: str,
        face_embedding: list[float],
        usb_drive_path: str
    ) -> int:
        """Menjalankan proses registrasi akun baru secara penuh.
        
        Ketentuan:
        - Validasi keunikan username di database.
        - Password divalidasi kekuatannya dan di-hash dengan Argon2id.
        - Embedding wajah 512-dimensi dienkripsi dengan AES-256-GCM.
        - USB dongle didaftarkan dengan token acak 32-byte dan hash SHA-256.
        """
        # Validasi username
        is_u_valid, u_msg = PasswordManager.validate_username(username)
        if not is_u_valid:
            raise ValueError(u_msg)

        # Cek apakah username sudah pernah digunakan
        existing_user = UserRepository.get_by_username(username)
        if existing_user:
            raise ValueError(f"Username '{username}' sudah terdaftar. Silakan gunakan username lain.")

        # Validasi password
        if password != confirm_password:
            raise ValueError("Konfirmasi kata sandi tidak cocok dengan kata sandi baru.")

        is_p_valid, p_msg = PasswordManager.validate_password_strength(password)
        if not is_p_valid:
            raise ValueError(p_msg)

        # Validasi data wajah
        if not face_embedding or len(face_embedding) < 128:
            raise ValueError("Template representasi wajah tidak valid atau belum direkam melalui kamera.")

        # Validasi USB Dongle
        if not usb_drive_path:
            raise ValueError("USB Flashdisk fisik wajib dipilih untuk didaftarkan sebagai dongle.")

        # 1. Daftarkan USB Dongle dan dapatkan serial + hash token
        volume_serial, token_hash = USBDongleManager.register_device(usb_drive_path)

        # 2. Hash password dengan Argon2id
        password_hash = PasswordManager.hash_password(password)

        # 3. Enkripsi embedding wajah dengan AES-256-GCM
        enc_face, nonce, tag = FaceVerificationManager.encrypt_embedding(face_embedding)

        # 4. Simpan ke database
        user_id = UserRepository.create_user(username, password_hash)
        FaceTemplateRepository.save_template(user_id, enc_face, nonce, tag)
        DongleRepository.register_dongle(user_id, volume_serial, token_hash)

        # 5. Catat log audit
        is_first = (UserRepository.count_users() == 1)
        role_label = "Administrator Utama" if is_first else "Petugas Medis"
        AuditLogRepository.log(f"Registrasi Akun {role_label}: {username}", "SUCCESS", user_id)

        return user_id

    # Alias untuk kompatibilitas
    register_administrator = register_user
