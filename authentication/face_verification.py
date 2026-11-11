"""Modul verifikasi biometrik wajah langsung melalui kamera menggunakan OpenCV dan DeepFace (Facenet512)."""
import json
import math
import os
import shutil
import tempfile
import numpy as np
from pathlib import Path
from config.settings import AppConfig
from cryptography.aes_gcm import AESGCMCipher
from cryptography.key_manager import KeyManager


def cosine_distance(vec_a: list[float], vec_b: list[float]) -> float:
    """Menghitung jarak kosinus (Cosine Distance) antara dua vektor embedding wajah."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Panjang vektor embedding tidak sama.")
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 1.0  # Vektor nol memiliki jarak maksimum

    similarity = dot_product / (norm_a * norm_b)
    # Cosine distance = 1 - cosine similarity
    return max(0.0, min(2.0, 1.0 - similarity))


class FaceVerificationManager:
    """Pengelola verifikasi wajah langsung melalui webcam menggunakan Facenet512."""

    MODEL_NAME = "Facenet512"

    @classmethod
    def test_camera_availability(cls, camera_index: int = 0) -> tuple[bool, str]:
        """Menguji apakah kamera webcam dapat diakses."""
        try:
            import cv2
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                return False, f"Kamera pada indeks {camera_index} tidak dapat dibuka."
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                return False, "Kamera terdeteksi namun gagal membaca frame gambar."
            return True, "Kamera berfungsi dengan baik."
        except ImportError:
            return False, "Library OpenCV (cv2) belum terpasang."
        except Exception as exc:
            return False, f"Terjadi kesalahan saat mengakses kamera: {exc}"

    @classmethod
    def capture_frame(cls, camera_index: int = 0):
        """Mengambil satu frame langsung dari kamera aktif."""
        try:
            import cv2
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                raise RuntimeError(f"Tidak dapat membuka kamera pada port {camera_index}.")
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                raise RuntimeError("Gagal mengambil frame dari kamera.")
            return frame
        except ImportError as exc:
            raise RuntimeError("Library OpenCV (cv2) belum terpasang.") from exc

    @classmethod
    def extract_embedding_from_frame(cls, frame) -> list[float]:
        """Mengekstraksi representasi fitur (embedding) 512-dimensi dari frame gambar menggunakan DeepFace.
        
        Memastikan:
        - Tepat satu wajah yang terdeteksi dalam frame.
        - Frame sementara dibersihkan dari penyimpanan setelah ekstraksi selesai.
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="medicipher_face_"))
        temp_frame_path = temp_dir / "temp_capture.jpg"

        try:
            import cv2
            from deepface import DeepFace

            cv2.imwrite(str(temp_frame_path), frame)

            # DeepFace represent: mengekstraksi embedding Facenet512
            results = DeepFace.represent(
                img_path=str(temp_frame_path),
                model_name=cls.MODEL_NAME,
                enforce_detection=True,
                detector_backend="opencv",
                align=True
            )

            if not results or len(results) == 0:
                raise ValueError("Wajah tidak terdeteksi pada kamera. Arahkan wajah ke depan kamera.")
            if len(results) > 1:
                raise ValueError("Terdeteksi lebih dari satu wajah. Pastikan hanya ada satu orang di depan kamera.")

            embedding = results[0]["embedding"]
            return [float(x) for x in embedding]

        except ImportError as err:
            raise RuntimeError(f"Modul DeepFace atau OpenCV belum siap: {err}") from err
        finally:
            # Bersihkan file dan direktori sementara
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception:
                pass

    @classmethod
    def capture_and_extract_live_embedding(cls, camera_index: int = 0) -> list[float]:
        """Mengambil frame langsung dari kamera dan menghasilkan embedding 512-dimensi."""
        frame = cls.capture_frame(camera_index)
        return cls.extract_embedding_from_frame(frame)

    @classmethod
    def encrypt_embedding(cls, embedding: list[float]) -> tuple[bytes, bytes, bytes]:
        """Mengenkripsi representasi embedding wajah menggunakan AES-256-GCM.
        
        Returns:
            tuple (encrypted_embedding, nonce, tag)
        """
        raw_json = json.dumps(embedding).encode("utf-8")
        face_key = KeyManager.get_face_key()
        ciphertext, nonce, tag = AESGCMCipher.encrypt(raw_json, face_key)
        return ciphertext, nonce, tag

    @classmethod
    def decrypt_embedding(cls, encrypted_embedding: bytes, nonce: bytes, tag: bytes) -> list[float]:
        """Mendekripsi template embedding wajah dari database menggunakan AES-256-GCM."""
        face_key = KeyManager.get_face_key()
        decrypted_json = AESGCMCipher.decrypt(encrypted_embedding, face_key, nonce, tag)
        return json.loads(decrypted_json.decode("utf-8"))

    @classmethod
    def verify_live_face(cls, registered_encrypted: bytes, nonce: bytes, tag: bytes,
                         camera_index: int = 0) -> tuple[bool, float, str]:
        """Melakukan verifikasi wajah langsung terhadap template terdaftar.
        
        Returns:
            tuple (is_verified: bool, distance: float, message: str)
        """
        try:
            # Dekripsi embedding terdaftar
            registered_vec = cls.decrypt_embedding(registered_encrypted, nonce, tag)
            # Ambil embedding wajah saat ini langsung dari kamera
            live_vec = cls.capture_and_extract_live_embedding(camera_index)
            # Hitung jarak kosinus
            dist = cosine_distance(live_vec, registered_vec)

            threshold = AppConfig.FACE_DISTANCE_THRESHOLD
            if dist <= threshold:
                return True, dist, f"Verifikasi wajah berhasil (Jarak: {dist:.4f} <= Ambang: {threshold:.4f})."
            else:
                return False, dist, f"Wajah tidak cocok (Jarak: {dist:.4f} > Ambang: {threshold:.4f})."
        except Exception as exc:
            return False, 1.0, f"Gagal melakukan verifikasi wajah: {exc}"

