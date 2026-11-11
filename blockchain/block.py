"""Model struktur blok data blockchain berbasis SHA-256."""
import json
import hashlib
from datetime import datetime


class Block:
    """Representasi satu blok pada rantai hash SHA-256."""

    def __init__(
        self,
        block_index: int,
        asset_id: int | None,
        file_name: str,
        file_hash: str,
        timestamp: str,
        description: str,
        previous_hash: str,
        current_hash: str = ""
    ):
        self.block_index = block_index
        self.asset_id = asset_id
        self.file_name = file_name
        self.file_hash = file_hash
        self.timestamp = timestamp
        self.description = description
        self.previous_hash = previous_hash
        self.current_hash = current_hash or self.calculate_hash()

    def get_block_data_dict(self) -> dict:
        """Mengembalikan kamus data payload blok."""
        return {
            "block_index": self.block_index,
            "asset_id": self.asset_id,
            "file_name": self.file_name,
            "file_hash": self.file_hash,
            "timestamp": self.timestamp,
            "description": self.description,
            "previous_hash": self.previous_hash
        }

    def serialize_data(self) -> str:
        """Serialisasi data blok secara deterministik (kunci terurut) untuk penghitungan hash."""
        return json.dumps(self.get_block_data_dict(), sort_keys=True, separators=(",", ":"))

    def calculate_hash(self) -> str:
        """Menghitung hash SHA-256 dari serialisasi data blok."""
        serialized = self.serialize_data()
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def create_genesis_block(cls) -> "Block":
        """Membuat blok pertama (Genesis Block) sebagai jangkar rantai blok."""
        return cls(
            block_index=0,
            asset_id=None,
            file_name="GENESIS_BLOCK",
            file_hash="0" * 64,
            timestamp="2026-01-01T00:00:00",
            description="Genesis Block MediCipher Security Ledger",
            previous_hash="0" * 64
        )

