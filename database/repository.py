"""Repository akses data dan transaksi database MySQL MediCipher."""
from datetime import datetime
from database.connection import DatabaseConnection


class UserRepository:
    """Akses data untuk akun pengguna."""

    @staticmethod
    def create_user(username: str, password_hash: str) -> int:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
            cursor.execute(query, (username, password_hash))
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def get_by_username(username: str):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, username, password_hash, created_at FROM users WHERE username = %s LIMIT 1"
            cursor.execute(query, (username,))
            return cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def get_first_user():
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, username, password_hash, created_at FROM users ORDER BY id ASC LIMIT 1"
            cursor.execute(query)
            return cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def count_users() -> int:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()


class FaceTemplateRepository:
    """Akses data template wajah terenkripsi."""

    @staticmethod
    def save_template(user_id: int, encrypted_embedding: bytes, nonce: bytes, tag: bytes):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            # Hapus template lama jika ada agar 1 pengguna memiliki 1 template aktif
            cursor.execute("DELETE FROM face_templates WHERE user_id = %s", (user_id,))
            query = """
                INSERT INTO face_templates (user_id, encrypted_embedding, nonce, tag, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, encrypted_embedding, nonce, tag, datetime.now()))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def get_by_user_id(user_id: int):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, user_id, encrypted_embedding, nonce, tag FROM face_templates WHERE user_id = %s LIMIT 1"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()


class DongleRepository:
    """Akses data perangkat USB dongle terdaftar."""

    @staticmethod
    def register_dongle(user_id: int, volume_serial: str, token_hash: str):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM dongle_devices WHERE user_id = %s", (user_id,))
            query = """
                INSERT INTO dongle_devices (user_id, volume_serial, token_hash, registered_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, volume_serial, token_hash, datetime.now()))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def get_by_user_id(user_id: int):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, user_id, volume_serial, token_hash, registered_at FROM dongle_devices WHERE user_id = %s LIMIT 1"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def get_all():
        """Mengambil seluruh data dongle terdaftar dari semua pengguna."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, user_id, volume_serial, token_hash, registered_at FROM dongle_devices ORDER BY id ASC"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()


class MedicalRecordRepository:
    """Akses data arsip rekam medis terenkripsi."""

    @staticmethod
    def create_record(record_code: str, patient_code_enc: bytes, patient_name_enc: bytes,
                      exam_type_enc: bytes, exam_date: str, result_enc: bytes, notes_enc: bytes,
                      nonce: bytes, tag: bytes):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO medical_records 
                (record_code, patient_code_enc, patient_name_enc, exam_type_enc, exam_date,
                 result_enc, notes_enc, nonce, tag, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            now = datetime.now()
            cursor.execute(query, (
                record_code, patient_code_enc, patient_name_enc, exam_type_enc, exam_date,
                result_enc, notes_enc, nonce, tag, now, now
            ))
            rec_id = cursor.lastrowid
            conn.commit()
            return rec_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def get_all_records():
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT id, record_code, patient_code_enc, patient_name_enc, exam_type_enc,
                       exam_date, result_enc, notes_enc, nonce, tag, created_at, updated_at
                FROM medical_records ORDER BY id DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

    @staticmethod
    def get_by_id(record_id: int):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT id, record_code, patient_code_enc, patient_name_enc, exam_type_enc,
                       exam_date, result_enc, notes_enc, nonce, tag, created_at, updated_at
                FROM medical_records WHERE id = %s
            """
            cursor.execute(query, (record_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def update_record(record_id: int, patient_code_enc: bytes, patient_name_enc: bytes,
                      exam_type_enc: bytes, exam_date: str, result_enc: bytes, notes_enc: bytes,
                      nonce: bytes, tag: bytes):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                UPDATE medical_records 
                SET patient_code_enc = %s, patient_name_enc = %s, exam_type_enc = %s,
                    exam_date = %s, result_enc = %s, notes_enc = %s, nonce = %s, tag = %s,
                    updated_at = %s
                WHERE id = %s
            """
            cursor.execute(query, (
                patient_code_enc, patient_name_enc, exam_type_enc, exam_date,
                result_enc, notes_enc, nonce, tag, datetime.now(), record_id
            ))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def delete_record(record_id: int):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            query = "DELETE FROM medical_records WHERE id = %s"
            cursor.execute(query, (record_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def count_records() -> int:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM medical_records")
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()


class MedicalAssetRepository:
    """Akses data aset berkas dokumen dan citra medis."""

    @staticmethod
    def create_asset(asset_code: str, file_name: str, file_path: str, file_hash: str, description: str = "") -> int:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO medical_assets (asset_code, file_name, file_path, file_hash, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (asset_code, file_name, file_path, file_hash, description, datetime.now()))
            asset_id = cursor.lastrowid
            conn.commit()
            return asset_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def get_all_assets():
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, asset_code, file_name, file_path, file_hash, description, created_at FROM medical_assets ORDER BY id DESC"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

    @staticmethod
    def get_by_id(asset_id: int):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, asset_code, file_name, file_path, file_hash, description, created_at FROM medical_assets WHERE id = %s"
            cursor.execute(query, (asset_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def count_assets() -> int:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM medical_assets")
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()


class BlockchainBlockRepository:
    """Akses data rantai blok SHA-256."""

    @staticmethod
    def add_block(block_index: int, asset_id: int | None, block_data: str, previous_hash: str, current_hash: str, timestamp: datetime):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO blockchain_blocks (block_index, asset_id, block_data, previous_hash, current_hash, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (block_index, asset_id, block_data, previous_hash, current_hash, timestamp))
            block_id = cursor.lastrowid
            conn.commit()
            return block_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def get_all_blocks():
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT id, block_index, asset_id, block_data, previous_hash, current_hash, timestamp
                FROM blockchain_blocks ORDER BY block_index ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

    @staticmethod
    def get_latest_block():
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT id, block_index, asset_id, block_data, previous_hash, current_hash, timestamp
                FROM blockchain_blocks ORDER BY block_index DESC LIMIT 1
            """
            cursor.execute(query)
            return cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def count_blocks() -> int:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM blockchain_blocks")
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()


class AuditLogRepository:
    """Akses data pencatatan aktivitas dan keamanan."""

    @staticmethod
    def log(activity: str, status: str, user_id: int | None = None):
        try:
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO audit_logs (user_id, activity, status, created_at) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, activity, status, datetime.now()))
            conn.commit()
            cursor.close()
        except Exception:
            pass  # Logging tidak boleh menghentikan alur utama jika gagal

    @staticmethod
    def get_recent_logs(limit: int = 50):
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, user_id, activity, status, created_at FROM audit_logs ORDER BY id DESC LIMIT %s"
            cursor.execute(query, (limit,))
            return cursor.fetchall()
        finally:
            cursor.close()

