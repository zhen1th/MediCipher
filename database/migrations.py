"""Skrip migrasi dan inisialisasi tabel database MySQL MediCipher."""
from pathlib import Path
from config.settings import AppConfig
from database.connection import DatabaseConnection, HAS_MYSQL_CONNECTOR

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception


class DatabaseMigration:
    """Kelas untuk menginisialisasi skema tabel dan memeriksa status awal aplikasi."""

    @classmethod
    def ensure_database_exists(cls):
        """Membuat database jika belum ada di server MySQL."""
        if not HAS_MYSQL_CONNECTOR:
            raise ConnectionError(
                "Driver mysql-connector-python belum terpasang. Jalankan pip install -r requirements.txt"
            )

        try:
            conn = mysql.connector.connect(
                host=AppConfig.DB_HOST,
                port=AppConfig.DB_PORT,
                user=AppConfig.DB_USER,
                password=AppConfig.DB_PASSWORD
            )
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{AppConfig.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as exc:
            raise ConnectionError(
                f"Gagal memastikan database MySQL '{AppConfig.DB_NAME}' tersedia: {exc}"
            ) from exc

    @classmethod
    def run_migrations(cls):
        """Mengeksekusi skrip schema.sql untuk memastikan semua tabel tersedia."""
        cls.ensure_database_exists()
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"File skema tidak ditemukan di {schema_path}")

        sql_content = schema_path.read_text(encoding="utf-8")
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()

        commands = [cmd.strip() for cmd in sql_content.split(";") if cmd.strip()]
        for command in commands:
            if command.upper().startswith("USE "):
                continue
            try:
                cursor.execute(command)
            except MySQLError as err:
                conn.rollback()
                cursor.close()
                raise RuntimeError(f"Gagal menjalankan query skema: {err}") from err

        conn.commit()
        cursor.close()

    @classmethod
    def check_is_first_run(cls) -> bool:
        """Memeriksa apakah aplikasi pertama kali dijalankan (belum ada akun pengguna)."""
        try:
            conn = DatabaseConnection.get_connection()
        except Exception:
            cls.ensure_database_exists()
            conn = DatabaseConnection.get_connection()

        cursor = conn.cursor()
        try:
            cursor.execute("SHOW TABLES LIKE 'users'")
            res = cursor.fetchone()
            if not res:
                cursor.close()
                cls.run_migrations()
                conn = DatabaseConnection.get_connection()
                cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            cursor.close()
            return count == 0
        except MySQLError as exc:
            if cursor:
                cursor.close()
            raise RuntimeError(f"Gagal memeriksa status tabel users: {exc}") from exc
