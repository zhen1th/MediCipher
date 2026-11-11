"""Manajer rantai blok (Simple Blockchain berbasis Hash Chain SHA-256) terintegrasi MySQL."""
from datetime import datetime
import json
from pathlib import Path
from blockchain.block import Block
from database.repository import BlockchainBlockRepository, MedicalAssetRepository, AuditLogRepository
from cryptography.hashing import HashUtil


class BlockchainManager:
    """Pengelola pencatatan dan verifikasi keaslian dokumen medis pada blockchain lokal."""

    @classmethod
    def initialize_chain_if_empty(cls):
        """Membuat Genesis Block jika rantai blok masih kosong pada database MySQL."""
        count = BlockchainBlockRepository.count_blocks()
        if count == 0:
            genesis = Block.create_genesis_block()
            BlockchainBlockRepository.add_block(
                block_index=genesis.block_index,
                asset_id=genesis.asset_id,
                block_data=genesis.serialize_data(),
                previous_hash=genesis.previous_hash,
                current_hash=genesis.current_hash,
                timestamp=datetime.fromisoformat(genesis.timestamp)
            )
            AuditLogRepository.log("Inisialisasi Genesis Block Blockchain", "SUCCESS")

    @classmethod
    def register_asset_to_blockchain(
        cls,
        file_path: str | Path,
        asset_code: str,
        description: str
    ) -> tuple[int, Block]:
        """Mendaftarkan berkas dokumen atau citra medis baru ke dalam database dan rantai blok.
        
        Langkah:
        1. Pastikan Genesis Block sudah ada.
        2. Hitung SHA-256 dari file secara streaming.
        3. Simpan metadata aset ke medical_assets.
        4. Ambil hash blok terakhir (previous_hash).
        5. Buat blok baru dan hitung current_hash.
        6. Simpan blok baru ke blockchain_blocks.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

        cls.initialize_chain_if_empty()

        file_hash = HashUtil.sha256_file(path)
        file_name = path.name

        # Simpan ke medical_assets
        asset_id = MedicalAssetRepository.create_asset(
            asset_code=asset_code,
            file_name=file_name,
            file_path=str(path.resolve()),
            file_hash=file_hash,
            description=description
        )

        # Ambil blok terakhir
        latest_row = BlockchainBlockRepository.get_latest_block()
        if not latest_row:
            cls.initialize_chain_if_empty()
            latest_row = BlockchainBlockRepository.get_latest_block()

        new_index = latest_row["block_index"] + 1
        prev_hash = latest_row["current_hash"]
        now_dt = datetime.now()
        timestamp_str = now_dt.isoformat()

        # Buat blok baru
        block = Block(
            block_index=new_index,
            asset_id=asset_id,
            file_name=file_name,
            file_hash=file_hash,
            timestamp=timestamp_str,
            description=description,
            previous_hash=prev_hash
        )

        # Simpan blok ke MySQL
        BlockchainBlockRepository.add_block(
            block_index=block.block_index,
            asset_id=block.asset_id,
            block_data=block.serialize_data(),
            previous_hash=block.previous_hash,
            current_hash=block.current_hash,
            timestamp=now_dt
        )

        AuditLogRepository.log(f"Pencatatan Aset {asset_code} ke Blockchain", "SUCCESS")
        return asset_id, block

    @classmethod
    def verify_blockchain_chain(cls) -> tuple[bool, str, list[dict]]:
        """Memverifikasi integritas seluruh rantai blok dari Genesis Block hingga blok terakhir."""
        blocks = BlockchainBlockRepository.get_all_blocks()
        if not blocks:
            return False, "Rantai blok kosong.", []

        details = []
        for i, row in enumerate(blocks):
            b_idx = row["block_index"]
            b_prev = row["previous_hash"]
            b_curr = row["current_hash"]
            b_data_str = row["block_data"]

            # 1. Cek hubungan previous_hash
            if i == 0:
                if b_idx != 0 or b_prev != ("0" * 64):
                    return False, f"Genesis Block (Index {b_idx}) tidak valid.", details
            else:
                prev_row = blocks[i - 1]
                if b_prev != prev_row["current_hash"]:
                    return False, (
                        f"Hubungan rantai terputus pada Blok {b_idx}: previous_hash ({b_prev[:8]}...) "
                        f"tidak cocok dengan current_hash blok sebelumnya ({prev_row['current_hash'][:8]}...)."
                    ), details

            # 2. Cek integritas data blok terhadap current_hash
            try:
                data_dict = json.loads(b_data_str)
            except Exception:
                return False, f"Format data JSON pada Blok {b_idx} rusak.", details

            recalc_hash = HashUtil.sha256_text(
                json.dumps(data_dict, sort_keys=True, separators=(",", ":"))
            )

            if recalc_hash != b_curr:
                return False, f"Integritas isi Blok {b_idx} telah dimanipulasi (Hash berubah).", details

            details.append({
                "index": b_idx,
                "asset_id": row["asset_id"],
                "current_hash": b_curr,
                "previous_hash": b_prev,
                "valid": True
            })

        return True, "Seluruh rantai blok utuh dan terverifikasi secara kriptografis.", details

    @classmethod
    def verify_asset(cls, asset_id: int, file_to_check: str | Path | None = None) -> tuple[str, str, dict]:
        """Melakukan verifikasi komprehensif terhadap aset digital medis.
        
        Status Hasil:
        - VALID: File memiliki hash yang sama dengan catatan blockchain dan seluruh rantai lolos validasi.
        - INVALID: File telah berubah atau hash tidak sesuai catatan.
        - CHAIN INVALID: Terdapat manipulasi pada isi blok atau keterhubungan rantai blockchain.
        
        Returns:
            tuple (status: str, message: str, info: dict)
        """
        # 1. Periksa integritas rantai blok terlebih dahulu
        is_chain_valid, chain_msg, _ = cls.verify_blockchain_chain()
        if not is_chain_valid:
            return "CHAIN INVALID", f"Verifikasi gagal karena kerusakan rantai: {chain_msg}", {}

        # 2. Ambil data aset
        asset = MedicalAssetRepository.get_by_id(asset_id)
        if not asset:
            return "INVALID", f"Aset dengan ID {asset_id} tidak ditemukan pada registrasi aset.", {}

        # Cari blok yang memuat asset_id ini
        blocks = BlockchainBlockRepository.get_all_blocks()
        matching_block = None
        for b in blocks:
            if b["asset_id"] == asset_id:
                matching_block = b
                break

        if not matching_block:
            return "INVALID", f"Aset {asset['asset_code']} belum dicatatkan ke dalam blok blockchain.", {}

        # 3. Verifikasi file fisik
        target_path = Path(file_to_check) if file_to_check else Path(asset["file_path"])
        if not target_path.is_file():
            return "INVALID", f"File fisik pada path '{target_path}' tidak ditemukan untuk diperiksa.", {}

        computed_file_hash = HashUtil.sha256_file(target_path)
        recorded_asset_hash = asset["file_hash"]

        block_data = json.loads(matching_block["block_data"])
        recorded_block_file_hash = block_data.get("file_hash", "")

        info = {
            "asset_code": asset["asset_code"],
            "file_name": target_path.name,
            "computed_hash": computed_file_hash,
            "recorded_asset_hash": recorded_asset_hash,
            "recorded_block_hash": recorded_block_file_hash,
            "block_index": matching_block["block_index"],
            "block_hash": matching_block["current_hash"]
        }

        if computed_file_hash != recorded_asset_hash or computed_file_hash != recorded_block_file_hash:
            return "INVALID", (
                f"File telah dimodifikasi atau hash tidak cocok. "
                f"Hash aktual: {computed_file_hash[:16]}... vs Terdaftar: {recorded_asset_hash[:16]}..."
            ), info

        return "VALID", "Aset digital medis terbukti asli, identik, dan rantai blok valid.", info

