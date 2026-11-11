"""Pengelola koneksi database MySQL MediCipher."""
from config.settings import AppConfig

# Coba impor driver mysql.connector secara fleksibel
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    HAS_MYSQL_CONNECTOR = False
    MySQLError = Exception


class DatabaseConnection:
    """Manajer koneksi ke basis data MySQL."""

    _connection = None

    @classmethod
    def get_connection(cls, test_mode: bool = False):
        """Membuka koneksi ke server MySQL.
        
        Jika koneksi belum aktif atau terputus, inisialisasi koneksi baru.
        Jika driver belum terpasang atau server mati, lemparkan ConnectionError deskriptif.
        """
        if not HAS_MYSQL_CONNECTOR:
            raise ConnectionError(
                "Driver mysql-connector-python belum terpasang di sistem. "
                "Silakan pasang dependensi dengan: pip install -r requirements.txt"
            )

        try:
            if cls._connection is None or not cls._connection.is_connected():
                cls._connection = mysql.connector.connect(
                    host=AppConfig.DB_HOST,
                    port=AppConfig.DB_PORT,
                    user=AppConfig.DB_USER,
                    password=AppConfig.DB_PASSWORD,
                    database=AppConfig.DB_NAME,
                    autocommit=False
                )
            return cls._connection
        except MySQLError as exc:
            raise ConnectionError(
                f"Gagal terhubung ke database MySQL ({AppConfig.DB_HOST}:{AppConfig.DB_PORT}): {exc}"
            ) from exc

    @classmethod
    def test_connection(cls) -> tuple[bool, str]:
        """Menguji apakah koneksi ke MySQL berhasil."""
        if not HAS_MYSQL_CONNECTOR:
            return False, "Driver mysql-connector-python belum terpasang."

        try:
            conn = cls.get_connection()
            if conn.is_connected():
                return True, "Koneksi ke database MySQL berhasil."
            return False, "Koneksi terputus."
        except Exception as err:
            return False, str(err)

    @classmethod
    def close_connection(cls):
        """Menutup koneksi database jika sedang terbuka."""
        if cls._connection is not None:
            try:
                if hasattr(cls._connection, "is_connected") and cls._connection.is_connected():
                    cls._connection.close()
            except Exception:
                pass
            cls._connection = None
