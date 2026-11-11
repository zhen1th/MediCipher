"""Modul layanan verifikasi aset digital laboratorium berbasis blockchain hash chain."""
from pathlib import Path
from blockchain.chain import BlockchainManager
from database.repository import MedicalAssetRepository, BlockchainBlockRepository


class AssetVerificationService:
    """Layanan pencatatan dan verifikasi integritas aset digital medis."""

    @staticmethod
    def register_asset(file_path: str | Path, asset_code: str, description: str):
        """Mendaftarkan aset ke database dan membuat blok baru di blockchain."""
        return BlockchainManager.register_asset_to_blockchain(file_path, asset_code, description)

    @staticmethod
    def verify_asset(asset_id: int, file_to_check: str | Path | None = None) -> tuple[str, str, dict]:
        """Melakukan verifikasi aset: hash file, konsistensi rantai, dan integritas blok."""
        return BlockchainManager.verify_asset(asset_id, file_to_check)

    @staticmethod
    def get_all_registered_assets():
        """Mengambil seluruh daftar aset medis yang telah terdaftar."""
        return MedicalAssetRepository.get_all_assets()

    @staticmethod
    def get_blockchain_ledger():
        """Mengambil seluruh riwayat buku besar blockchain."""
        return BlockchainBlockRepository.get_all_blocks()

